from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any
import datetime
import json

from app.core.database import get_db
from app.models.senior import Senior
from app.models.signal import VitalObservation, MedicationLog, CheckIn, CallNote, ExtractedCue
from app.models.risk import DailyRiskAssessment
from app.models.alert import Alert
from app.models.notification import Notification
from app.models.user import User
from app.api.deps import get_current_user, log_audit

router = APIRouter()


@router.post("/scenarios/trigger")
def trigger_demo_scenario(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    scenario = payload.get("scenario", "fall_emergency")
    senior_id = payload.get("senior_id", "SEN_003")
    today_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    senior = db.query(Senior).filter(Senior.id == senior_id).first()
    if not senior:
        raise HTTPException(status_code=404, detail="Senior not found")

    if scenario == "fall_emergency":
        # 1. Ingest fall check-in
        ch = CheckIn(
            senior_id=senior_id,
            date=today_str,
            mood="Anxious",
            sleep_quality="Disturbed",
            appetite="Reduced",
            pain_level="Moderate",
            fall_reported=True,
            raw_response="Achanak bathroom ke paas paer fisal gaya, kamar me chot lagi hai.",
            language="hi"
        )
        db.add(ch)

        # 2. Update Risk Assessment to URGENT
        risk_rec = db.query(DailyRiskAssessment).filter(DailyRiskAssessment.senior_id == senior_id, DailyRiskAssessment.date == today_str).first()
        top_c_demo = [
            {
                "signal": "Reported Fall / Slip Event",
                "impact_score": 50.0,
                "current_value": 1.0,
                "baseline_value": 0.0,
                "narrative_en": "Acute fall/slip event reported requiring immediate check-in",
                "narrative_hi": "आकस्मिक गिरने की घटना दर्ज हुई, तत्काल सत्यापन आवश्यक"
            }
        ]
        act_demo = {
            "action": "Immediate Phone Call Verification",
            "urgency": "HIGH",
            "questions_hindi": ["दादाजी क्या आप ठीक हैं?", "क्या कहीं चोट लगी है?"],
            "questions_en": ["Are you alright?", "Is there any pain?"],
            "questions_english": ["Are you alright?", "Is there any pain?"]
        }
        if not risk_rec:
            risk_rec = DailyRiskAssessment(senior_id=senior_id, date=today_str, risk_score=94.5, risk_category="URGENT", top_contributors=json.dumps(top_c_demo), suggested_action=json.dumps(act_demo))
            db.add(risk_rec)
        else:
            risk_rec.risk_score = 94.5
            risk_rec.risk_category = "URGENT"
            risk_rec.top_contributors = json.dumps(top_c_demo)
            risk_rec.suggested_action = json.dumps(act_demo)

        # 3. Create or update Alert
        alert = db.query(Alert).filter(Alert.senior_id == senior_id, Alert.date == today_str).first()
        if not alert:
            alert = Alert(
                senior_id=senior_id,
                date=today_str,
                risk_score=94.5,
                risk_category="URGENT",
                primary_signal="Reported Fall / Slip",
                status="PENDING",
                assigned_coordinator_id=senior.assigned_coordinator_id or 1
            )
            db.add(alert)
        else:
            alert.risk_score = 94.5
            alert.status = "PENDING"
            alert.primary_signal = "Reported Fall / Slip"

        # 4. Trigger In-App Notification
        notif = Notification(
            user_id=senior.assigned_coordinator_id or 1,
            senior_id=senior_id,
            title=f"🚨 URGENT: Fall Report for {senior.full_name}",
            message=f"A fall was reported for senior {senior.full_name} ({senior_id}). Conduct immediate physical verification protocol.",
            urgency="URGENT",
            notification_type="ALERT"
        )
        db.add(notif)
        db.commit()

        log_audit(db, current_user, action="DEMO_TRIGGER_FALL", resource_type="DEMO", resource_id=senior_id)
        return {
            "status": "SUCCESS",
            "scenario": "fall_emergency",
            "senior_id": senior_id,
            "new_risk_score": 94.5,
            "category": "URGENT",
            "message": f"Fall event successfully injected. Priority queue and coordinator alerts updated live."
        }

    elif scenario == "med_confusion":
        for i in range(3):
            d_str = (datetime.datetime.utcnow() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            m = MedicationLog(senior_id=senior_id, date=d_str, status="missed", taken_pct=0.0, source="smart_pillbox")
            db.add(m)

        alert = db.query(Alert).filter(Alert.senior_id == senior_id, Alert.date == today_str).first()
        if not alert:
            alert = Alert(
                senior_id=senior_id,
                date=today_str,
                risk_score=72.0,
                risk_category="HIGH",
                primary_signal="3 Consecutive Missed Medications",
                status="PENDING",
                assigned_coordinator_id=senior.assigned_coordinator_id or 1
            )
            db.add(alert)

        db.commit()
        return {"status": "SUCCESS", "scenario": "med_confusion", "new_risk_score": 72.0}

    elif scenario == "benign_travel":
        # Ingest high door events and travel input
        v = VitalObservation(
            senior_id=senior_id,
            date=today_str,
            door_events=18.0,
            hours_outdoors=4.5,
            inactivity_hours=3.5,
            spo2=senior.baseline_spo2
        )
        db.add(v)
        # Suppress risk score
        risk_rec = db.query(DailyRiskAssessment).filter(DailyRiskAssessment.senior_id == senior_id, DailyRiskAssessment.date == today_str).first()
        if risk_rec:
            risk_rec.is_benign_suppressed = True
            risk_rec.suppression_reason = "BENIGN_TRAVEL_ROUTINE"
            risk_rec.risk_score = 22.0
            risk_rec.risk_category = "LOW"
        db.commit()
        return {"status": "SUCCESS", "scenario": "benign_travel", "suppression_reason": "BENIGN_TRAVEL_ROUTINE", "new_risk_score": 22.0}

    return {"status": "UNKNOWN_SCENARIO"}
