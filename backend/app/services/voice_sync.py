"""Real-time Voice Sync & Incremental Risk Engine for Sahara AI.
Handles turn-by-turn audio ingestion, STT, clinical cue extraction,
emergency detection, and incremental single-senior rescoring.
Emits real-time SSE events to Coordinator Command Center.
"""

import os
import json
import time
import base64
import logging
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.senior import Senior
from app.models.checkin import SeniorDevice, CheckinCall, CheckinTurn, ClientEventLog
from app.models.signal import CallNote, ExtractedCue, VitalObservation, MedicationLog, CheckIn, FamilyInput
from app.models.risk import DailyRiskAssessment
from app.models.alert import Alert
from app.services.sarvam import transcribe_speech_sarvam, synthesize_speech_sarvam
from app.services.gemini import doctor_triage_analysis, clean_hindi_speech_text
from app.services.nlp import extract_cues_from_note
from app.services.routine_call import check_emergency_symptoms
from app.services.scoring import calculate_daily_risk
from app.services.sse_manager import sse_manager

logger = logging.getLogger(__name__)

AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)


async def ingest_pairing_consent(
    db: Session,
    event_id: str,
    senior_id: str,
    device_id: str,
    consent_given: bool,
    setup_checks: Dict[str, bool],
    app_version: str = "1.2.0-pwa"
) -> Dict[str, Any]:
    """Idempotently process PWA device pairing and consent setup."""
    # Idempotency check
    existing_log = db.query(ClientEventLog).filter(ClientEventLog.event_id == event_id).first()
    if existing_log:
        return {"status": "ALREADY_PROCESSED", "event_id": event_id}

    dev = db.query(SeniorDevice).filter(SeniorDevice.senior_id == senior_id).first()
    now = datetime.datetime.utcnow()
    if not dev:
        dev = SeniorDevice(
            senior_id=senior_id,
            device_id=device_id,
            app_version=app_version,
            paired_at=now,
            last_seen=now,
            notifications_enabled=setup_checks.get("notifications", True),
            mic_permission=setup_checks.get("mic", True),
            fullscreen_permission=setup_checks.get("fullscreen", True),
            battery_optimisation_disabled=setup_checks.get("battery_optimisation", True),
            is_healthy=True
        )
        db.add(dev)
    else:
        dev.device_id = device_id
        dev.last_seen = now
        dev.app_version = app_version
        dev.notifications_enabled = setup_checks.get("notifications", dev.notifications_enabled)
        dev.mic_permission = setup_checks.get("mic", dev.mic_permission)
        dev.fullscreen_permission = setup_checks.get("fullscreen", dev.fullscreen_permission)
        dev.battery_optimisation_disabled = setup_checks.get("battery_optimisation", dev.battery_optimisation_disabled)

    senior = db.query(Senior).filter(Senior.id == senior_id).first()
    if senior:
        senior.family_consent = consent_given

    log = ClientEventLog(
        event_id=event_id,
        senior_id=senior_id,
        event_type="pairing",
        payload=json.dumps({"consent": consent_given, "setup": setup_checks})
    )
    db.add(log)
    db.commit()

    coord_id = senior.assigned_coordinator_id if senior else 1
    await sse_manager.broadcast(
        event_type="device_health_changed",
        data={
            "senior_id": senior_id,
            "device_id": device_id,
            "is_healthy": True,
            "last_seen": now.isoformat(),
            "permissions": setup_checks
        },
        senior_id=senior_id,
        coordinator_id=coord_id
    )

    return {"status": "PAIRED", "senior_id": senior_id, "device_id": device_id}


async def ingest_call_lifecycle_event(
    db: Session,
    event_id: str,
    checkin_id: str,
    senior_id: str,
    status: str,  # ringing, answered, declined, missed, ended, partial
    timestamp_iso: Optional[str] = None
) -> Dict[str, Any]:
    """Process call status transitions with immediate SSE notification."""
    existing_log = db.query(ClientEventLog).filter(ClientEventLog.event_id == event_id).first()
    if existing_log:
        return {"status": "ALREADY_PROCESSED", "checkin_id": checkin_id}

    senior = db.query(Senior).filter(Senior.id == senior_id).first()
    coord_id = senior.assigned_coordinator_id if senior else 1
    coord_name = senior.coordinator.full_name if (senior and senior.coordinator) else "Anvesha Sharma"

    now = datetime.datetime.utcnow()
    call = db.query(CheckinCall).filter(CheckinCall.checkin_id == checkin_id).first()
    
    if not call:
        # Get baseline or previous risk score
        latest_risk = db.query(DailyRiskAssessment).filter(DailyRiskAssessment.senior_id == senior_id).order_by(DailyRiskAssessment.id.desc()).first()
        score_before = latest_risk.risk_score if latest_risk else 25.0
        
        call = CheckinCall(
            checkin_id=checkin_id,
            event_id=event_id,
            senior_id=senior_id,
            coordinator_id=coord_id,
            coordinator_name=coord_name,
            caller_name="Sahara AI",
            caller_label="सहारा AI",
            status=status,
            rang_at=now,
            risk_score_before=score_before
        )
        db.add(call)
    else:
        call.status = status
        if status == "answered" and not call.answered_at:
            call.answered_at = now
        elif status in ("ended", "completed", "declined", "missed", "partial"):
            call.ended_at = now
            if call.answered_at:
                call.duration_seconds = int((now - call.answered_at).total_seconds())

    # If missed or declined, write engagement flag
    if status in ("missed", "declined"):
        dev = db.query(SeniorDevice).filter(SeniorDevice.senior_id == senior_id).first()
        if dev:
            dev.is_healthy = False

    log = ClientEventLog(
        event_id=event_id,
        senior_id=senior_id,
        event_type="call_lifecycle",
        payload=json.dumps({"status": status, "checkin_id": checkin_id})
    )
    db.add(log)
    db.commit()

    # Emit SSE to dashboard
    await sse_manager.broadcast(
        event_type="checkin_status_changed",
        data={
            "checkin_id": checkin_id,
            "senior_id": senior_id,
            "senior_name": senior.full_name if senior else "Senior",
            "coordinator_name": coord_name,
            "status": status,
            "timestamp": now.isoformat(),
            "duration_seconds": call.duration_seconds
        },
        senior_id=senior_id,
        coordinator_id=coord_id
    )

    return {"status": "SUCCESS", "checkin_id": checkin_id, "current_status": status}


async def ingest_turn_data(
    db: Session,
    event_id: str,
    checkin_id: str,
    senior_id: str,
    turn_index: int,
    question_text: str,
    keypad_input: Optional[str] = None,
    audio_base64: Optional[str] = None,
    spoken_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Ingest a single question turn IMMEDIATELY upon recording.
    Runs STT, extracts clinical cues, checks emergency, and emits live turn_added event.
    """
    start_time = time.time()
    existing_log = db.query(ClientEventLog).filter(ClientEventLog.event_id == event_id).first()
    if existing_log:
        return {"status": "ALREADY_PROCESSED", "turn_index": turn_index}

    audio_url = None
    transcript = spoken_text or ""
    confidence = 0.95

    # 1. Save turn audio if present
    if audio_base64:
        try:
            raw_b64 = audio_base64.split(",")[-1]
            raw_bytes = base64.b64decode(raw_b64)
            filename = f"turn_{checkin_id}_{turn_index}_{int(time.time())}.wav"
            filepath = os.path.join(AUDIO_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(raw_bytes)
            audio_url = f"http://localhost:8000/static/audio/{filename}"

            # Run STT via Sarvam saaras:v1 if transcript wasn't already provided
            if not transcript:
                stt_res = transcribe_speech_sarvam(filepath)
                if stt_res and stt_res.get("transcript"):
                    transcript = stt_res.get("transcript", "")
                    confidence = 0.96
        except Exception as e:
            logger.warning(f"Audio turn processing warning: {e}")

    # Fallback keypad transcription if audio not present
    if not transcript and keypad_input:
        if turn_index == 1:
            transcript = "अच्छा महसूस हो रहा है (1)" if keypad_input == "1" else ("ठीक-ठाक (2)" if keypad_input == "2" else "अच्छा नहीं लग रहा (3)")
        elif turn_index == 3:
            transcript = "हाँ दवाई ले ली" if keypad_input in ("1", "haan") else "दवाई नहीं ली"
        else:
            transcript = f"जवाब: {keypad_input}"

    # 2. Extract Cues
    cues = extract_cues_from_note(transcript)
    is_emergency = check_emergency_symptoms(transcript) or any(c["cue_type"] == "chest_pain" and not c["is_negated"] for c in cues)

    # 3. Store CheckinTurn
    turn = CheckinTurn(
        checkin_id=checkin_id,
        event_id=event_id,
        turn_index=turn_index,
        question_text=question_text,
        audio_url=audio_url,
        keypad_input=keypad_input,
        transcript=transcript,
        confidence=confidence,
        cues_extracted=json.dumps(cues),
        is_emergency=is_emergency,
        timestamp=datetime.datetime.utcnow()
    )
    db.add(turn)

    log = ClientEventLog(
        event_id=event_id,
        senior_id=senior_id,
        event_type="turn_upload",
        payload=json.dumps({"turn": turn_index, "transcript": transcript})
    )
    db.add(log)
    db.commit()

    senior = db.query(Senior).filter(Senior.id == senior_id).first()
    coord_id = senior.assigned_coordinator_id if senior else 1

    # 4. If Emergency: Immediately escalate risk and create urgent alert
    if is_emergency:
        today_str = datetime.date.today().isoformat()
        risk_rec = db.query(DailyRiskAssessment).filter(DailyRiskAssessment.senior_id == senior_id, DailyRiskAssessment.date == today_str).first()
        if not risk_rec:
            risk_rec = DailyRiskAssessment(
                senior_id=senior_id,
                date=today_str,
                risk_score=98.5,
                risk_category="URGENT",
                top_contributors=json.dumps([{"signal": "🚨 Real-Time Voice Alert: Acute Emergency", "impact_score": 98.5, "narrative_hi": transcript}]),
                suggested_action=json.dumps({"action": "Immediate Phone Safety Call", "urgency": "URGENT"})
            )
            db.add(risk_rec)
        else:
            risk_rec.risk_score = 98.5
            risk_rec.risk_category = "URGENT"

        alert = db.query(Alert).filter(Alert.senior_id == senior_id).first()
        if not alert:
            alert = Alert(
                senior_id=senior_id,
                date=today_str,
                risk_score=98.5,
                risk_category="URGENT",
                primary_signal=f"🚨 Sahara AI Voice Check-in: {transcript[:80]}",
                status="PENDING",
                assigned_coordinator_id=coord_id
            )
            db.add(alert)
        else:
            alert.risk_score = 98.5
            alert.risk_category = "URGENT"
            alert.status = "PENDING"
            alert.primary_signal = f"🚨 Sahara AI Voice Check-in: {transcript[:80]}"

        db.commit()

        # Emit urgent_flag SSE
        await sse_manager.broadcast(
            event_type="urgent_flag",
            data={
                "senior_id": senior_id,
                "senior_name": senior.full_name if senior else "Senior",
                "checkin_id": checkin_id,
                "turn_index": turn_index,
                "reason": transcript,
                "score": 98.5,
                "category": "URGENT"
            },
            senior_id=senior_id,
            coordinator_id=coord_id
        )

    # 5. Emit turn_added SSE
    latency_ms = round((time.time() - start_time) * 1000, 1)
    await sse_manager.broadcast(
        event_type="turn_added",
        data={
            "checkin_id": checkin_id,
            "senior_id": senior_id,
            "turn_index": turn_index,
            "question": question_text,
            "transcript": transcript,
            "confidence": confidence,
            "cues": cues,
            "audio_url": audio_url,
            "is_emergency": is_emergency,
            "latency_ms": latency_ms
        },
        senior_id=senior_id,
        coordinator_id=coord_id
    )

    return {
        "status": "SAVED",
        "turn_index": turn_index,
        "transcript": transcript,
        "cues": cues,
        "is_emergency": is_emergency,
        "latency_ms": latency_ms
    }


async def complete_checkin_and_rescore(
    db: Session,
    checkin_id: str,
    senior_id: str
) -> Dict[str, Any]:
    """
    Called when a call finishes (or timeouts).
    Builds clinical summary, recomputes target senior's features & risk score INCREMENTALLY,
    re-evaluates alert gating and priority rank, and broadcasts checkin_completed via SSE.
    Target latency: < 5-10 seconds.
    """
    start_time = time.time()
    call = db.query(CheckinCall).filter(CheckinCall.checkin_id == checkin_id).first()
    senior = db.query(Senior).filter(Senior.id == senior_id).first()
    if not call or not senior:
        return {"status": "ERROR", "message": "Call or Senior not found"}

    now = datetime.datetime.utcnow()
    call.status = "completed"
    call.ended_at = now
    if call.answered_at:
        call.duration_seconds = int((now - call.answered_at).total_seconds())

    # Collect all turns
    turns = db.query(CheckinTurn).filter(CheckinTurn.checkin_id == checkin_id).order_by(CheckinTurn.turn_index.asc()).all()
    all_transcripts = [f"Q{t.turn_index}: {t.transcript}" for t in turns if t.transcript]
    combined_notes = " | ".join(all_transcripts)

    # Collect all cues
    all_cues = []
    has_emergency = False
    for t in turns:
        if t.is_emergency:
            has_emergency = True
        if t.cues_extracted:
            try:
                parsed = json.loads(t.cues_extracted)
                all_cues.extend(parsed)
            except:
                pass

    # Generate 3-line clinical summary
    triage = doctor_triage_analysis(
        transcript=combined_notes or "Sahara AI routine checkin completed.",
        senior_name=senior.full_name,
        audio_duration=call.duration_seconds or 15
    )
    call.summary_en = triage.get("clinical_summary_en", triage.get("clinical_summary", "Voice check-in completed."))
    call.summary_hi = triage.get("clinical_summary_hi", triage.get("hindi_summary", "दैनिक वॉइस चेक-इन पूरा हुआ।"))
    call.is_emergency = has_emergency
    call.needs_review = len(all_cues) > 0 or has_emergency

    # Also log to CallNote for permanent history
    today_str = datetime.date.today().isoformat()
    note_rec = CallNote(
        senior_id=senior_id,
        date=today_str,
        note_text=combined_notes or "Sahara AI 5-Question Check-in Completed",
        caller_role="sahara_ai_agent",
        contact_type="VOICE_CHECKIN",
        audio_url=turns[0].audio_url if turns else None,
        audio_duration_seconds=call.duration_seconds,
        ai_call_summary=call.summary_en
    )
    db.add(note_rec)
    db.commit()

    # INCREMENTAL RESCORING FOR ONLY THIS SENIOR
    vitals_7d = db.query(VitalObservation).filter(VitalObservation.senior_id == senior_id, VitalObservation.date <= today_str).order_by(VitalObservation.date.desc()).limit(7).all()
    meds_14d = db.query(MedicationLog).filter(MedicationLog.senior_id == senior_id, MedicationLog.date <= today_str).order_by(MedicationLog.date.desc()).limit(14).all()
    checkins_7d = db.query(CheckIn).filter(CheckIn.senior_id == senior_id, CheckIn.date <= today_str).order_by(CheckIn.date.desc()).limit(7).all()
    notes_7d = db.query(CallNote).filter(CallNote.senior_id == senior_id, CallNote.date <= today_str).order_by(CallNote.date.desc()).limit(7).all()
    fam_7d = db.query(FamilyInput).filter(FamilyInput.senior_id == senior_id, FamilyInput.date <= today_str).order_by(FamilyInput.date.desc()).limit(7).all()

    risk_dict = calculate_daily_risk(senior, vitals_7d, meds_14d, checkins_7d, notes_7d, fam_7d)
    
    # If acute emergency was flagged, preserve emergency ceiling
    if has_emergency:
        risk_dict["risk_score"] = max(98.5, risk_dict["risk_score"])
        risk_dict["risk_category"] = "URGENT"

    call.risk_score_after = risk_dict["risk_score"]

    # Update DailyRiskAssessment
    risk_rec = db.query(DailyRiskAssessment).filter(DailyRiskAssessment.senior_id == senior_id, DailyRiskAssessment.date == today_str).first()
    if risk_rec:
        risk_rec.prev_risk_score = risk_rec.risk_score
        risk_rec.risk_score = risk_dict["risk_score"]
        risk_rec.risk_category = risk_dict["risk_category"]
        risk_rec.score_change = round(risk_rec.risk_score - risk_rec.prev_risk_score, 1)
        risk_rec.top_contributors = json.dumps(risk_dict["top_contributors"])
        risk_rec.suggested_action = json.dumps(risk_dict["suggested_action"])
    else:
        risk_rec = DailyRiskAssessment(
            senior_id=senior_id,
            date=today_str,
            risk_score=risk_dict["risk_score"],
            risk_category=risk_dict["risk_category"],
            prev_risk_score=call.risk_score_before or 25.0,
            score_change=round(risk_dict["risk_score"] - (call.risk_score_before or 25.0), 1),
            top_contributors=json.dumps(risk_dict["top_contributors"]),
            suggested_action=json.dumps(risk_dict["suggested_action"])
        )
        db.add(risk_rec)

    # Re-evaluate Alert Gating
    coord_id = senior.assigned_coordinator_id or 1
    alert = db.query(Alert).filter(Alert.senior_id == senior_id).first()
    if risk_dict["risk_score"] >= 70.0 or has_emergency:
        primary_sig = f"Voice Check-in: {call.summary_en[:80]}"
        if not alert:
            alert = Alert(
                senior_id=senior_id,
                date=today_str,
                risk_score=risk_dict["risk_score"],
                risk_category=risk_dict["risk_category"],
                primary_signal=primary_sig,
                status="PENDING",
                assigned_coordinator_id=coord_id
            )
            db.add(alert)
        else:
            alert.risk_score = risk_dict["risk_score"]
            alert.risk_category = risk_dict["risk_category"]
            alert.primary_signal = primary_sig
            alert.status = "PENDING"

    db.commit()
    elapsed_seconds = round(time.time() - start_time, 2)

    # Broadcast checkin_completed and senior_rescored via SSE
    await sse_manager.broadcast(
        event_type="checkin_completed",
        data={
            "checkin_id": checkin_id,
            "senior_id": senior_id,
            "senior_name": senior.full_name,
            "status": "completed",
            "duration_seconds": call.duration_seconds,
            "summary_en": call.summary_en,
            "summary_hi": call.summary_hi,
            "new_score": risk_dict["risk_score"],
            "risk_category": risk_dict["risk_category"],
            "needs_review": call.needs_review,
            "latency_seconds": elapsed_seconds
        },
        senior_id=senior_id,
        coordinator_id=coord_id
    )

    await sse_manager.broadcast(
        event_type="senior_rescored",
        data={
            "senior_id": senior_id,
            "new_score": risk_dict["risk_score"],
            "risk_category": risk_dict["risk_category"],
            "score_change": risk_rec.score_change if risk_rec else 0.0,
            "primary_signal": "🎙️ Voice check-in"
        },
        senior_id=senior_id,
        coordinator_id=coord_id
    )

    return {
        "status": "COMPLETED",
        "checkin_id": checkin_id,
        "senior_id": senior_id,
        "duration_seconds": call.duration_seconds,
        "new_score": risk_dict["risk_score"],
        "category": risk_dict["risk_category"],
        "summary": call.summary_en,
        "latency_seconds": elapsed_seconds
    }
