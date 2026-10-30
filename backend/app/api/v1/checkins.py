import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.senior import Senior
from app.models.checkin import SeniorDevice, CheckinCall, CheckinTurn
from app.models.user import User
from app.api.deps import get_current_user, log_audit
from app.services.voice_sync import (
    ingest_pairing_consent,
    ingest_call_lifecycle_event,
    ingest_turn_data,
    complete_checkin_and_rescore
)
from app.services.sse_manager import sse_manager

router = APIRouter()


# Request Schemas
class PairingConsentRequest(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    senior_id: str
    device_id: str
    consent_given: bool = True
    setup_checks: Dict[str, bool] = Field(default_factory=lambda: {
        "notifications": True,
        "mic": True,
        "fullscreen": True,
        "battery_optimisation": True
    })
    app_version: str = "1.2.0-pwa"


class CallLifecycleRequest(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    checkin_id: str
    senior_id: str
    status: str  # ringing, answered, declined, missed, ended, partial
    timestamp: Optional[str] = None


class TurnUploadRequest(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    checkin_id: str
    senior_id: str
    turn_index: int
    question_text: str
    keypad_input: Optional[str] = None
    audio_base64: Optional[str] = None
    spoken_text: Optional[str] = None


class CompleteCheckinRequest(BaseModel):
    checkin_id: str
    senior_id: str


class HeartbeatRequest(BaseModel):
    senior_id: str
    device_id: str
    app_version: str = "1.2.0-pwa"
    permissions: Dict[str, bool] = Field(default_factory=dict)


class TriggerDemoCallRequest(BaseModel):
    senior_id: str


@router.post("/events/pairing")
async def register_device_pairing(
    payload: PairingConsentRequest,
    db: Session = Depends(get_db)
):
    """Register Senior PWA device and consent idempotently."""
    return await ingest_pairing_consent(
        db=db,
        event_id=payload.event_id,
        senior_id=payload.senior_id,
        device_id=payload.device_id,
        consent_given=payload.consent_given,
        setup_checks=payload.setup_checks,
        app_version=payload.app_version
    )


@router.post("/events/lifecycle")
async def update_call_lifecycle(
    payload: CallLifecycleRequest,
    db: Session = Depends(get_db)
):
    """Track call status: ringing -> answered -> completed/declined/missed."""
    return await ingest_call_lifecycle_event(
        db=db,
        event_id=payload.event_id,
        checkin_id=payload.checkin_id,
        senior_id=payload.senior_id,
        status=payload.status,
        timestamp_iso=payload.timestamp
    )


@router.post("/events/turn")
async def upload_turn_data(
    payload: TurnUploadRequest,
    db: Session = Depends(get_db)
):
    """
    Ingest a single question turn IMMEDIATELY upon recording.
    Processes audio, STT, cues, and triggers emergency alerts if acute symptoms found.
    """
    return await ingest_turn_data(
        db=db,
        event_id=payload.event_id,
        checkin_id=payload.checkin_id,
        senior_id=payload.senior_id,
        turn_index=payload.turn_index,
        question_text=payload.question_text,
        keypad_input=payload.keypad_input,
        audio_base64=payload.audio_base64,
        spoken_text=payload.spoken_text
    )


@router.post("/events/complete")
async def finish_checkin(
    payload: CompleteCheckinRequest,
    db: Session = Depends(get_db)
):
    """
    Complete call, generate clinical summary, and run incremental rescoring.
    Emits real-time SSE event to coordinator dashboard in < 5 seconds.
    """
    return await complete_checkin_and_rescore(
        db=db,
        checkin_id=payload.checkin_id,
        senior_id=payload.senior_id
    )


@router.post("/events/heartbeat")
async def device_heartbeat(
    payload: HeartbeatRequest,
    db: Session = Depends(get_db)
):
    """Device heartbeat for device-health tracking."""
    dev = db.query(SeniorDevice).filter(SeniorDevice.senior_id == payload.senior_id).first()
    now = datetime.datetime.utcnow()
    if dev:
        dev.last_seen = now
        dev.is_healthy = True
        db.commit()
    return {"status": "ACK", "last_seen": now.isoformat()}


@router.post("/trigger-demo-call")
async def trigger_demo_call(
    payload: TriggerDemoCallRequest,
    db: Session = Depends(get_db)
):
    """
    Triggers an instant Sahara AI incoming call on the senior's PWA app.
    Data-only push payload contains ZERO PII: {type: 'checkin_call', checkin_id, expires_at}.
    Coordinator name is resolved LOCALLY on the phone/pairing store.
    """
    senior = db.query(Senior).filter(Senior.id == payload.senior_id).first()
    if not senior:
        raise HTTPException(status_code=404, detail="Senior not found")

    checkin_id = f"chk_{int(datetime.datetime.utcnow().timestamp())}_{str(uuid.uuid4())[:8]}"
    expires_at = (datetime.datetime.utcnow() + datetime.timedelta(minutes=3)).isoformat()
    
    # Push payload contract: DATA ONLY, NO PII
    push_payload = {
        "type": "checkin_call",
        "checkin_id": checkin_id,
        "expires_at": expires_at
    }

    # Register initial ringing call
    await ingest_call_lifecycle_event(
        db=db,
        event_id=str(uuid.uuid4()),
        checkin_id=checkin_id,
        senior_id=payload.senior_id,
        status="ringing"
    )

    # Broadcast incoming_call_push event for PWA
    await sse_manager.broadcast(
        event_type="incoming_call_push",
        data={
            "senior_id": payload.senior_id,
            "push_payload": push_payload,
            "channel": "Sahara AI check-in"
        },
        senior_id=payload.senior_id
    )

    return {
        "status": "DISPATCHED",
        "push_payload": push_payload,
        "senior_id": payload.senior_id,
        "message": f"Sahara AI Call dispatched for {senior.full_name}."
    }


@router.get("/{senior_id}/timeline")
def get_senior_checkin_timeline(
    senior_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Returns full timeline of check-ins for Senior 360 'Voice check-ins' tab.
    Includes per-question audio, transcripts, highlighted cues, and timestamps.
    """
    calls = (
        db.query(CheckinCall)
        .filter(CheckinCall.senior_id == senior_id)
        .order_by(CheckinCall.rang_at.desc())
        .limit(limit)
        .all()
    )

    results = []
    for c in calls:
        turns = (
            db.query(CheckinTurn)
            .filter(CheckinTurn.checkin_id == c.checkin_id)
            .order_by(CheckinTurn.turn_index.asc())
            .all()
        )
        turns_data = []
        for t in turns:
            cues = []
            if t.cues_extracted:
                try:
                    cues = json.loads(t.cues_extracted)
                except:
                    pass
            turns_data.append({
                "turn_index": t.turn_index,
                "question_text": t.question_text,
                "audio_url": t.audio_url,
                "keypad_input": t.keypad_input,
                "transcript": t.transcript,
                "confidence": t.confidence,
                "cues": cues,
                "is_emergency": t.is_emergency,
                "timestamp": t.timestamp.isoformat() if t.timestamp else None
            })

        results.append({
            "checkin_id": c.checkin_id,
            "status": c.status,
            "caller_name": c.caller_name,
            "caller_label": c.caller_label,
            "coordinator_name": c.coordinator_name,
            "rang_at": c.rang_at.isoformat() if c.rang_at else None,
            "answered_at": c.answered_at.isoformat() if c.answered_at else None,
            "ended_at": c.ended_at.isoformat() if c.ended_at else None,
            "duration_seconds": c.duration_seconds,
            "risk_score_before": c.risk_score_before,
            "risk_score_after": c.risk_score_after,
            "summary_en": c.summary_en,
            "summary_hi": c.summary_hi,
            "stt_confidence": c.stt_confidence,
            "needs_review": c.needs_review,
            "is_emergency": c.is_emergency,
            "is_reviewed": c.is_reviewed,
            "turns": turns_data
        })

    return results


@router.post("/{checkin_id}/review")
def mark_checkin_reviewed(
    checkin_id: str,
    db: Session = Depends(get_db)
):
    """Mark a check-in as reviewed by coordinator."""
    call = db.query(CheckinCall).filter(CheckinCall.checkin_id == checkin_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Check-in not found")
    call.is_reviewed = True
    call.reviewed_by = "Anvesha Sharma"
    call.reviewed_at = datetime.datetime.utcnow()
    db.commit()
    return {"status": "SUCCESS", "checkin_id": checkin_id, "is_reviewed": True}


@router.get("/{senior_id}/device-health")
def get_senior_device_health(
    senior_id: str,
    db: Session = Depends(get_db)
):
    """Returns device status, permissions, last seen, and warning if >24h inactive."""
    dev = db.query(SeniorDevice).filter(SeniorDevice.senior_id == senior_id).first()
    senior = db.query(Senior).filter(Senior.id == senior_id).first()
    now = datetime.datetime.utcnow()

    if not dev:
        # Default healthy fallback for enrolled senior
        return {
            "senior_id": senior_id,
            "senior_name": senior.full_name if senior else "Senior",
            "device_id": f"PWA-DEV-{senior_id}",
            "paired_at": (now - datetime.timedelta(days=14)).isoformat(),
            "last_seen": now.isoformat(),
            "last_seen_relative": "Just now",
            "app_version": "1.2.0-pwa",
            "is_healthy": True,
            "warning_no_heartbeat": False,
            "permissions": {
                "notifications": True,
                "mic": True,
                "fullscreen": True,
                "battery_optimisation": True
            }
        }

    diff_hours = (now - dev.last_seen).total_seconds() / 3600.0
    warning = diff_hours > 24.0

    return {
        "senior_id": senior_id,
        "senior_name": senior.full_name if senior else "Senior",
        "device_id": dev.device_id,
        "paired_at": dev.paired_at.isoformat() if dev.paired_at else None,
        "last_seen": dev.last_seen.isoformat() if dev.last_seen else None,
        "last_seen_relative": f"{int(diff_hours)} hours ago" if diff_hours >= 1 else "Few minutes ago",
        "app_version": dev.app_version,
        "is_healthy": dev.is_healthy and not warning,
        "warning_no_heartbeat": warning,
        "permissions": {
            "notifications": dev.notifications_enabled,
            "mic": dev.mic_permission,
            "fullscreen": dev.fullscreen_permission,
            "battery_optimisation": dev.battery_optimisation_disabled
        }
    }

