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

# In-memory latest hardware state for live widget display
LATEST_HARDWARE_STATE: Dict[str, Any] = {
    "fall_status": "NORMAL",  # NORMAL | PENDING_CONFIRMATION | ACUTE_FALL_NO_RESPONSE | MANUAL_SOS
    "last_fall_event": None,
    "last_fall_time": None,
    "pillbox_state": "CLOSED",  # OPEN | CLOSED
    "pillbox_last_opened": None,
    "pillbox_last_closed": None,
    "today_dose_verified": False,
    "door_state": "CLOSED",  # OPEN | CLOSED
    "last_door_event": None,
    "bathroom_motion": False,
    "kitchen_motion": False,
    "last_motion_time": None,
    "hub_online": True,
    "last_hub_sync": datetime.datetime.utcnow().isoformat()
}


@router.post("/event")
async def ingest_hardware_event(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Ingests live telemetry from the 3 user ESP32 hardware devices:
    1. Fall Detection Pendant (ADXL345 + SOS + OK Button)
       - MANUAL_SOS
       - POSSIBLE_FALL
       - NO_RESPONSE
       - USER_OK
    2. Home Hub & Motion System (Bathroom/Kitchen PIR + Magnetic Door)
       - BATHROOM_MOTION
       - KITCHEN_MOTION
       - DOOR_OPEN / DOOR_CLOSED
       - LIVE_STATUS
    3. Smart Pill Box (Reed Switch Pin 27 + Buzzer + LED)
       - BOX_OPENED
       - BOX_CLOSED
    All data routes into Harshit Thakur (SEN_001).
    """
    senior_id = payload.get("senior_id", "SEN_001")
    event_type = str(payload.get("event", "")).upper().strip()
    raw_message = payload.get("message", "")
    metadata = payload.get("metadata", {})

    senior = db.query(Senior).filter(Senior.id == senior_id).first()
    if not senior:
        raise HTTPException(status_code=404, detail=f"Senior {senior_id} not found")

    now = datetime.datetime.utcnow()
    time_str = now.strftime("%I:%M:%S %p")
    date_str = now.strftime("%Y-%m-%d")

    LATEST_HARDWARE_STATE["hub_online"] = True
    LATEST_HARDWARE_STATE["last_hub_sync"] = now.isoformat()

    # =========================================================================
    # 1. FALL DETECTION PENDANT EVENTS
    # =========================================================================
    if event_type in ["MANUAL_SOS", "SOS_ACTIVATED"]:
        logger.warning(f"🚨 HARDWARE: MANUAL SOS pressed by {senior.full_name}!")
        LATEST_HARDWARE_STATE["fall_status"] = "MANUAL_SOS"
        LATEST_HARDWARE_STATE["last_fall_event"] = "Pendant Emergency SOS Button Pressed"
        LATEST_HARDWARE_STATE["last_fall_time"] = time_str

        # Spike Risk Score to 99.0
        latest_risk = db.query(DailyRiskAssessment).filter(DailyRiskAssessment.senior_id == senior_id).order_by(DailyRiskAssessment.date.desc()).first()
        if latest_risk:
            latest_risk.overall_risk_score = 99.0
            latest_risk.risk_category = "URGENT"
            latest_risk.why_alerted_en = "ESP32 Pendant SOS: Harshit Thakur pressed the emergency SOS button on wearable pendant!"
            latest_risk.why_alerted_hi = "ईएसपी32 पेंडेंट एसओएस: हर्षित ठाकुर जी ने पेंडेंट का आपातकालीन एसओएस बटन दबाया है!"
            latest_risk.updated_at = now

        # Add High Alert
        alert = Alert(
            senior_id=senior_id,
            date=date_str,
            risk_score=99.0,
            risk_category="URGENT",
            primary_signal="ESP32 Pendant: Manual SOS Emergency Button Pressed",
            status="PENDING",
            assigned_coordinator_id=senior.assigned_coordinator_id or 1,
            created_at=now
        )
        db.add(alert)
        db.commit()

        # Broadcast SSE
        await sse_manager.broadcast(
            event_type="urgent_flag",
            data={
                "senior_id": senior_id,
                "senior_name": senior.full_name,
                "alert_type": "MANUAL_SOS",
                "severity": "CRITICAL",
                "risk_score": 99.0,
                "time": time_str,
                "message": f"🚨 EMERGENCY: Harshit Thakur pressed Pendant SOS Button!"
            },
            senior_id=senior_id
        )
        return {"status": "SUCCESS", "event": event_type, "action": "CRITICAL_SOS_DISPATCHED", "time": time_str}

    elif event_type in ["POSSIBLE_FALL", "FALL_DETECTED"]:
        logger.warning(f"⚠️ HARDWARE: Possible Fall detected by ADXL345 for {senior.full_name}")
        LATEST_HARDWARE_STATE["fall_status"] = "PENDING_CONFIRMATION"
        LATEST_HARDWARE_STATE["last_fall_event"] = "ADXL345 Sudden Impact (30s Confirmation Started)"
        LATEST_HARDWARE_STATE["last_fall_time"] = time_str

        # Broadcast warning
        await sse_manager.broadcast(
            event_type="urgent_flag",
            data={
                "senior_id": senior_id,
                "senior_name": senior.full_name,
                "alert_type": "POSSIBLE_FALL",
                "severity": "MODERATE",
                "time": time_str,
                "message": f"⚠️ Possible Fall impact detected by ADXL345 for {senior.full_name}. Awaiting senior confirmation."
            },
            senior_id=senior_id
        )
        return {"status": "SUCCESS", "event": event_type, "action": "CONFIRMATION_COUNTDOWN_STARTED", "time": time_str}

    elif event_type in ["NO_RESPONSE", "FALL_CONFIRMED"]:
        logger.critical(f"🚨 HARDWARE: UNRESPONSIVE FALL DETECTED FOR {senior.full_name}!")
        LATEST_HARDWARE_STATE["fall_status"] = "ACUTE_FALL_NO_RESPONSE"
        LATEST_HARDWARE_STATE["last_fall_event"] = "Unresponsive Fall (No 'I AM OK' response for 30s)"
        LATEST_HARDWARE_STATE["last_fall_time"] = time_str

        # Spike Risk Score to 98.5 URGENT
        latest_risk = db.query(DailyRiskAssessment).filter(DailyRiskAssessment.senior_id == senior_id).order_by(DailyRiskAssessment.date.desc()).first()
        if latest_risk:
            latest_risk.overall_risk_score = 98.5
            latest_risk.risk_category = "URGENT"
            latest_risk.why_alerted_en = "ESP32 Fall Detection: Unresponsive acute fall detected! Senior did not press I AM OK within 30s."
            latest_risk.why_alerted_hi = "ईएसपी32 फॉल सेंसर: गंभीर गिरावट दर्ज! 30 सेकंड तक वरिष्ठ नागरिक से कोई प्रतिक्रिया नहीं मिली।"
            latest_risk.updated_at = now

        alert = Alert(
            senior_id=senior_id,
            date=date_str,
            risk_score=98.5,
            risk_category="URGENT",
            primary_signal="ESP32 ADXL345: Confirmed Acute Fall (No Response for 30s)",
            status="PENDING",
            assigned_coordinator_id=senior.assigned_coordinator_id or 1,
            created_at=now
        )
        db.add(alert)
        db.commit()

        # Broadcast SSE
        await sse_manager.broadcast(
            event_type="urgent_flag",
            data={
                "senior_id": senior_id,
                "senior_name": senior.full_name,
                "alert_type": "FALL_UNRESPONSIVE",
                "severity": "HIGH",
                "risk_score": 98.5,
                "time": time_str,
                "message": f"🚨 URGENT FALL: Harshit Thakur did not respond to fall alert! Call Anvesha Sharma & Anchal Mishra!"
            },
            senior_id=senior_id
        )
        return {"status": "SUCCESS", "event": event_type, "action": "UNRESPONSIVE_FALL_ALERT_TRIGGERED", "risk_score": 98.5}

    elif event_type in ["USER_OK", "FALL_CANCELLED"]:
        logger.info(f"✅ HARDWARE: User confirmed safe via OK button")
        LATEST_HARDWARE_STATE["fall_status"] = "NORMAL"
        LATEST_HARDWARE_STATE["last_fall_event"] = "User pressed I AM OK Button — Safe"
        LATEST_HARDWARE_STATE["last_fall_time"] = time_str

        await sse_manager.broadcast(
            event_type="device_health_changed",
            data={
                "senior_id": senior_id,
                "senior_name": senior.full_name,
                "message": f"✅ Harshit Thakur confirmed safe (pressed 'I AM OK' button)."
            },
            senior_id=senior_id
        )
        return {"status": "SUCCESS", "event": event_type, "action": "FALL_DISMISSED_BY_USER", "time": time_str}

    # =========================================================================
    # 2. SMART PILL BOX EVENTS (Reed Switch Pin 27)
    # =========================================================================
    elif event_type in ["BOX_OPENED", "PILL_OPENED"]:
        logger.info(f"💊 HARDWARE: Smart Pill Box OPENED for {senior.full_name}")
        LATEST_HARDWARE_STATE["pillbox_state"] = "OPEN"
        LATEST_HARDWARE_STATE["pillbox_last_opened"] = time_str
        LATEST_HARDWARE_STATE["today_dose_verified"] = True

        senior.home_hub_status = "ONLINE"

        # Log verified medication take
        med_log = MedicationLog(
            senior_id=senior_id,
            date=date_str,
            timestamp=now,
            med_name="Amlodipine 5mg (Prescribed Dose)",
            status="taken",
            taken_pct=1.0,
            source="ESP32_SMART_PILLBOX_REED_27"
        )
        db.add(med_log)

        # Update senior latest pill box status
        latest_vital = db.query(VitalObservation).filter(VitalObservation.senior_id == senior_id).order_by(VitalObservation.date.desc()).first()
        if latest_vital:
            latest_vital.data_source = "ESP32_PILLBOX_VERIFIED"
        db.commit()

        # Broadcast SSE
        await sse_manager.broadcast(
            event_type="device_health_changed",
            data={
                "senior_id": senior_id,
                "senior_name": senior.full_name,
                "device_type": "smart_pillbox",
                "status": "DOSE_TAKEN_VERIFIED",
                "time": time_str,
                "message": f"💊 Smart Pill Box opened at {time_str} — Dose verified taken for Harshit Thakur!"
            },
            senior_id=senior_id
        )
        return {"status": "SUCCESS", "event": event_type, "action": "MEDICATION_VERIFIED_TAKEN", "time": time_str}

    elif event_type in ["BOX_CLOSED", "PILL_CLOSED"]:
        logger.info(f"💊 HARDWARE: Smart Pill Box CLOSED for {senior.full_name}")
        LATEST_HARDWARE_STATE["pillbox_state"] = "CLOSED"
        LATEST_HARDWARE_STATE["pillbox_last_closed"] = time_str
        return {"status": "SUCCESS", "event": event_type, "action": "PILLBOX_CLOSED", "time": time_str}

    # =========================================================================
    # 3. HOME HUB SENSOR EVENTS (PIR + Door Sensor)
    # =========================================================================
    elif "DOOR_OPEN" in event_type or event_type == "MAIN_DOOR_OPENED":
        logger.info(f"🚪 HARDWARE: Main door opened for {senior.full_name}")
        LATEST_HARDWARE_STATE["door_state"] = "OPEN"
        LATEST_HARDWARE_STATE["last_door_event"] = f"Door opened at {time_str}"
        return {"status": "SUCCESS", "event": "DOOR_OPEN", "door_state": "OPEN", "time": time_str}

    elif "DOOR_CLOSE" in event_type or event_type == "MAIN_DOOR_CLOSED":
        logger.info(f"🚪 HARDWARE: Main door closed for {senior.full_name}")
        LATEST_HARDWARE_STATE["door_state"] = "CLOSED"
        LATEST_HARDWARE_STATE["last_door_event"] = f"Door closed at {time_str}"
        return {"status": "SUCCESS", "event": "DOOR_CLOSED", "door_state": "CLOSED", "time": time_str}

    elif "BATHROOM" in event_type:
        LATEST_HARDWARE_STATE["bathroom_motion"] = "DETECTED" in event_type
        LATEST_HARDWARE_STATE["last_motion_time"] = time_str
        return {"status": "SUCCESS", "event": event_type, "room": "bathroom", "time": time_str}

    elif "KITCHEN" in event_type:
        LATEST_HARDWARE_STATE["kitchen_motion"] = "DETECTED" in event_type
        LATEST_HARDWARE_STATE["last_motion_time"] = time_str
        return {"status": "SUCCESS", "event": event_type, "room": "kitchen", "time": time_str}

    # Default Heartbeat
    senior.home_hub_status = "ONLINE"
    db.commit()
    return {"status": "SUCCESS", "event": "HEARTBEAT", "time": time_str}


@router.get("/status/{senior_id}")
def get_hardware_status(senior_id: str = "SEN_001", db: Session = Depends(get_db)):
    """Returns real-time telemetry from the user's 3 connected ESP32 systems."""
    senior = db.query(Senior).filter(Senior.id == senior_id).first()
    if not senior:
        raise HTTPException(status_code=404, detail="Senior not found")

    return {
        "senior_id": senior_id,
        "senior_name": senior.full_name,
        "live_telemetry": LATEST_HARDWARE_STATE,
        "devices": {
            "pendant": {
                "name": "Fall Detection Pendant (ADXL345 + SOS + OK)",
                "pins": "SDA: GPIO 32, SCL: GPIO 33, SOS: GPIO 26, OK: GPIO 27",
                "status": LATEST_HARDWARE_STATE["fall_status"],
                "last_event": LATEST_HARDWARE_STATE["last_fall_event"] or "Active (Monitoring normal movement)",
                "last_event_time": LATEST_HARDWARE_STATE["last_fall_time"]
            },
            "pillbox": {
                "name": "Smart Pill Box (Reed Switch)",
                "pins": "Reed: GPIO 27, LED: GPIO 25, Buzzer: GPIO 26",
                "state": LATEST_HARDWARE_STATE["pillbox_state"],
                "dose_verified": LATEST_HARDWARE_STATE["today_dose_verified"],
                "last_opened": LATEST_HARDWARE_STATE["pillbox_last_opened"] or "09:08 AM",
                "last_closed": LATEST_HARDWARE_STATE["pillbox_last_closed"]
            },
            "home_hub": {
                "name": "Home Hub & Motion System",
                "pins": "Bathroom PIR: GPIO 32, Kitchen PIR: GPIO 33, Main Door: GPIO 19",
                "status": "ONLINE",
                "door_state": LATEST_HARDWARE_STATE["door_state"],
                "last_door_event": LATEST_HARDWARE_STATE["last_door_event"] or "Main Door: CLOSED",
                "bathroom_motion": LATEST_HARDWARE_STATE["bathroom_motion"],
                "kitchen_motion": LATEST_HARDWARE_STATE["kitchen_motion"],
                "last_motion": LATEST_HARDWARE_STATE["last_motion_time"]
            }
        }
    }
