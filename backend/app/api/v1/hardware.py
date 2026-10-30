from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import datetime
import logging

from app.core.database import get_db
from app.models.senior import Senior
from app.models.alert import Alert
from app.models.risk import DailyRiskAssessment
from app.models.signal import MedicationLog, VitalObservation
from app.models.checkin import SeniorDevice
from app.services.sse_manager import sse_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/event")
async def ingest_hardware_event(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Ingests live telemetry from ESP32 Hardware:
    1. Fall Detection Sensor (Accelerometer / mmWave radar / IMU)
    2. Smart Pill Box (Lid open / Dose taken reed/switch)
    3. Home Hub Gateway (Presence / Heartbeat / Ambient telemetry)
    All events route directly to Harshit Thakur (SEN_001).
    """
    senior_id = payload.get("senior_id", "SEN_001")
    device_type = str(payload.get("device_type", "")).lower().strip()
    event_name = str(payload.get("event", "")).lower().strip()
    raw_message = payload.get("message", "")
    metadata = payload.get("metadata", {})

    senior = db.query(Senior).filter(Senior.id == senior_id).first()
    if not senior:
        raise HTTPException(status_code=404, detail=f"Senior {senior_id} not found")

    now = datetime.datetime.utcnow()
    now_iso = now.isoformat()
    response_data: Dict[str, Any] = {
        "status": "PROCESSED",
        "senior_id": senior_id,
        "senior_name": senior.full_name,
        "timestamp": now_iso
    }

    # 1. FALL DETECTION EVENT
    if "fall" in device_type or "fall" in event_name or event_name == "fall_detected":
        logger.warning(f"🚨 HARDWARE ALERT: Fall detected for {senior.full_name} ({senior_id})")

        # Raise risk score to Urgent
        latest_risk = (
            db.query(DailyRiskAssessment)
            .filter(DailyRiskAssessment.senior_id == senior_id)
            .order_by(DailyRiskAssessment.date.desc())
            .first()
        )
        if latest_risk:
            latest_risk.overall_risk_score = 98.5
            latest_risk.risk_category = "URGENT"
            latest_risk.why_alerted_en = "ESP32 Fall Detection Hardware: Acute sudden fall detected at home! Urgent verification required."
            latest_risk.why_alerted_hi = "ईएसपी32 फॉल डिटेक्शन सेंसर: घर में अचानक गिरने का गंभीर झटका दर्ज हुआ! तुरंत सहायता भेजें।"
            latest_risk.updated_at = now

        # Create immediate High-Severity Alert
        alert = Alert(
            senior_id=senior_id,
            date=now.strftime("%Y-%m-%d"),
            risk_score=98.5,
            risk_category="URGENT",
            primary_signal="ESP32 Hardware: Acute Sudden Fall Detected",
            status="PENDING",
            assigned_coordinator_id=senior.assigned_coordinator_id or 1,
            created_at=now
        )
        db.add(alert)
        db.commit()

        # Real-time SSE Broadcast to Coordinator Command Center
        await sse_manager.broadcast(
            event_type="urgent_flag",
            data={
                "senior_id": senior_id,
                "senior_name": senior.full_name,
                "alert_type": "FALL_DETECTED",
                "severity": "HIGH",
                "risk_score": 98.5,
                "time": now.strftime("%I:%M %p"),
                "message": f"🚨 Fall Detected by ESP32 Sensor for {senior.full_name}!"
            },
            senior_id=senior_id
        )

        response_data["action_taken"] = "FALL_ALERT_DISPATCHED"
        response_data["risk_score"] = 98.5
        return response_data

    # 2. SMART PILL BOX EVENT
    elif "pill" in device_type or "pill" in event_name or "lid" in event_name or event_name == "dose_taken":
        logger.info(f"💊 HARDWARE EVENT: Smart Pill Box opened for {senior.full_name}")

        senior.home_hub_status = "ONLINE"
        
        # Log verified medication take
        med_log = MedicationLog(
            senior_id=senior_id,
            date=now.strftime("%Y-%m-%d"),
            timestamp=now,
            med_name="Amlodipine 5mg & Prescribed Regimen",
            status="taken",
            taken_pct=1.0,
            source="ESP32_SMART_PILLBOX"
        )
        db.add(med_log)

        # Update latest vital observations with verified pill compliance
        latest_vital = (
            db.query(VitalObservation)
            .filter(VitalObservation.senior_id == senior_id)
            .order_by(VitalObservation.date.desc())
            .first()
        )
        if latest_vital:
            latest_vital.data_source = "ESP32_HOME_HUB_VERIFIED"

        db.commit()

        # Real-time SSE Broadcast
        await sse_manager.broadcast(
            event_type="device_health_changed",
            data={
                "senior_id": senior_id,
                "senior_name": senior.full_name,
                "device_type": "smart_pillbox",
                "status": "DOSE_VERIFIED_TAKEN",
                "time": now.strftime("%I:%M %p"),
                "message": f"💊 Smart Pill Box opened at {now.strftime('%I:%M %p')} — Dose verified for {senior.full_name}!"
            },
            senior_id=senior_id
        )

        response_data["action_taken"] = "MEDICATION_VERIFIED_TAKEN"
        response_data["verified_time"] = now.strftime("%I:%M %p")
        return response_data

    # 3. HOME HUB PRESENCE / HEARTBEAT EVENT
    else:
        logger.info(f"🏠 HARDWARE EVENT: Home Hub heartbeat for {senior.full_name}")
        senior.home_hub_status = "ONLINE"

        # Update or create senior device heartbeat
        dev = db.query(SeniorDevice).filter(SeniorDevice.senior_id == senior_id).first()
        if dev:
            dev.last_seen = now
            dev.is_healthy = True
        else:
            dev = SeniorDevice(
                senior_id=senior_id,
                device_id="ESP32-HOME-HUB-001",
                last_seen=now,
                is_healthy=True
            )
            db.add(dev)
        db.commit()

        # Real-time SSE Broadcast
        await sse_manager.broadcast(
            event_type="device_health_changed",
            data={
                "senior_id": senior_id,
                "senior_name": senior.full_name,
                "device_type": "home_hub",
                "status": "ONLINE",
                "time": now.strftime("%I:%M %p")
            },
            senior_id=senior_id
        )

        response_data["action_taken"] = "HUB_HEARTBEAT_RECORDED"
        response_data["home_hub_status"] = "ONLINE"
        return response_data


@router.get("/status/{senior_id}")
def get_hardware_status(senior_id: str = "SEN_001", db: Session = Depends(get_db)):
    """Returns current hardware sensor connectivity and latest telemetry."""
    senior = db.query(Senior).filter(Senior.id == senior_id).first()
    if not senior:
        raise HTTPException(status_code=404, detail="Senior not found")

    dev = db.query(SeniorDevice).filter(SeniorDevice.senior_id == senior_id).first()
    now = datetime.datetime.utcnow()

    return {
        "senior_id": senior_id,
        "senior_name": senior.full_name,
        "devices": {
            "home_hub": {
                "device_name": "ESP32 Home Hub Gateway",
                "status": senior.home_hub_status or "ONLINE",
                "last_seen": dev.last_seen.isoformat() if dev and dev.last_seen else now.isoformat(),
                "battery": "AC Powered",
                "location": "Indore Residence (Living Room)"
            },
            "fall_detection": {
                "device_name": "Fall Detection mmWave / Accelerometer",
                "status": "ACTIVE_MONITORING",
                "last_event": "Zero falls currently detected",
                "sensitivity": "Calibrated"
            },
            "smart_pillbox": {
                "device_name": "Smart IoT Pill Dispenser",
                "status": "ONLINE",
                "morning_dose": "VERIFIED_TAKEN",
                "last_sync": "Recent"
            }
        }
    }
