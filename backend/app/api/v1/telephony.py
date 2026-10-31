from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import datetime
import json
import logging

from app.core.database import get_db
from app.models.senior import Senior
from app.models.risk import DailyRiskAssessment
from app.models.alert import Alert
from app.models.signal import CallNote, ExtractedCue, VitalObservation
from app.models.user import User
from app.api.deps import get_current_user, log_audit
from app.services.sarvam import synthesize_speech_sarvam, transcribe_speech_sarvam
from app.services.exotel import initiate_exotel_call, process_exotel_webhook_event
from app.services.routine_call import get_routine_call_step, check_emergency_symptoms
from app.services.gemini import doctor_triage_analysis

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/trigger-routine-call")
def trigger_routine_call(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Trigger automated 10:00 AM Sahara routine check-in call to any specific phone number.
    Dispatches outbound call via Exotel to the specified phone_number,
    and synthesizes opening greeting with Sarvam Bulbul (Priya voice).
    """
    senior_id = payload.get("senior_id", "SEN_003")
    senior = db.query(Senior).filter(Senior.id == senior_id).first()

    senior_name = payload.get("senior_name") or (senior.full_name if senior else "रामेश्वर प्रसाद शर्मा")
    coordinator_name = payload.get("coordinator_name") or (senior.coordinator.full_name if (senior and senior.coordinator) else "अनिता देशमुख")
    phone_to_call = (
        payload.get("phone_number")
        or payload.get("custom_phone")
        or (senior.senior_phone if senior else "+91 98260 11234")
        or "+91 98260 11234"
    )

    # Clean phone formatting (supports 10-digit Indian numbers or +91)
    cleaned_phone = phone_to_call.replace(" ", "").replace("-", "")
    if len(cleaned_phone) == 10 and not cleaned_phone.startswith("+"):
        cleaned_phone = f"+91{cleaned_phone}"
    elif not cleaned_phone.startswith("+") and len(cleaned_phone) > 10:
        cleaned_phone = f"+{cleaned_phone}"

    # Strict Security Whitelist: Only numbers registered on coordinator dashboard are dialable!
    authorized_seniors = db.query(Senior).all()
    clean_target = cleaned_phone.replace("+", "").strip()

    is_authorized = False
    matched_senior = None
    for s in authorized_seniors:
        s_ph = (s.senior_phone or "").replace(" ", "").replace("-", "").replace("+", "").strip()
        f_ph = (s.family_phone or "").replace(" ", "").replace("-", "").replace("+", "").strip()
        if s_ph and (clean_target in s_ph or s_ph in clean_target):
            is_authorized = True
            matched_senior = s
            break
        if f_ph and (clean_target in f_ph or f_ph in clean_target):
            is_authorized = True
            matched_senior = s
            break

    if not is_authorized:
        raise HTTPException(
            status_code=403,
            detail=f"सुरक्षा प्रतिबंध (Security Block): कॉल केवल डैशबोर्ड पर रजिस्टर्ड सीनियर्स (हर्षित: 9451818283, अन्वेषा: 8267069623, आंचल: 8957266841, प्रियांशु: 6307120421, विकास: 8445168405, सेजल: 7017464158) के नंबर पर ही लगाई जा सकती है। किसी भी अनधिकृत नंबर ({phone_to_call}) पर कॉल प्रतिबंधित है।"
        )

    target_senior = matched_senior or senior
    senior_id = target_senior.id if target_senior else "SEN_001"
    senior_name = target_senior.full_name if target_senior else senior_name

    # 1. Trigger Exotel Outbound Call to this verified senior number
    exotel_result = initiate_exotel_call(
        senior_phone=cleaned_phone,
        senior_id=senior_id,
        coordinator_name=coordinator_name
    )

    # 2. Synthesize Opening Sahara Script with Sarvam AI Priya Voice
    step_0 = get_routine_call_step(
        senior_name=senior_name,
        coordinator_name=coordinator_name,
        step_index=0
    )

    return {
        "status": "SUCCESS",
        "senior_id": senior_id,
        "senior_name": senior_name,
        "phone_called": cleaned_phone,
        "coordinator_name": coordinator_name,
        "telephony": exotel_result,
        "initial_step": step_0,
        "message": f"Sahara 10:00 AM Routine Call dispatched via Exotel & Sarvam AI to {senior_name} ({cleaned_phone})."
    }


@router.post("/routine-step")
def progress_routine_step(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Progress through the Sahara 5-Question flow.
    Supports voice transcript or DTMF digits (1/2/3).
    Synthesizes each question using Sarvam Bulbul (Priya voice).
    Escalates immediately if an emergency symptom is detected.
    """
    senior_id = payload.get("senior_id", "SEN_003")
    step_index = int(payload.get("step_index", 0))
    user_reply = payload.get("user_reply")
    dtmf_digit = payload.get("dtmf_digit")
    accumulated = payload.get("accumulated", {})

    senior = db.query(Senior).filter(Senior.id == senior_id).first()
    senior_name = senior.full_name if senior else "Rameshwar Prasad Sharma"
    coordinator_name = senior.coordinator.full_name if (senior and senior.coordinator) else "Priya Deshmukh"

    step_result = get_routine_call_step(
        senior_name=senior_name,
        coordinator_name=coordinator_name,
        step_index=step_index,
        user_reply=user_reply,
        dtmf_digit=dtmf_digit,
        accumulated_data=accumulated
    )

    # If Emergency flagged during routine call
    if step_result.get("is_emergency"):
        today_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        elevated_score = 98.5

        # Create or update Risk Record
        risk_rec = db.query(DailyRiskAssessment).filter(DailyRiskAssessment.senior_id == senior_id, DailyRiskAssessment.date == today_str).first()
        top_c = [
            {
                "signal": "🚨 Sahara Call Acute Emergency Intercept",
                "impact_score": 60.0,
                "current_value": 1,
                "baseline_value": 0,
                "narrative_en": f"Emergency verbal cue detected during routine call: '{user_reply}'",
                "narrative_hi": f"10:00 AM कॉल के दौरान आपातकालीन लक्षण: '{user_reply}'"
            }
        ]
        act = {
            "action": "Immediate Dual Verification Call & Caregiver Escalation",
            "urgency": "URGENT",
            "questions_hindi": ["दादाजी क्या आप ठीक हैं?", "सीने में दर्द या सांस की तकलीफ कब से है?"],
            "questions_en": ["Are you alright?", "How long have you felt this?"]
        }
        if not risk_rec:
            risk_rec = DailyRiskAssessment(
                senior_id=senior_id,
                date=today_str,
                risk_score=elevated_score,
                risk_category="URGENT",
                top_contributors=json.dumps(top_c),
                suggested_action=json.dumps(act)
            )
            db.add(risk_rec)
        else:
            risk_rec.risk_score = elevated_score
            risk_rec.risk_category = "URGENT"
            risk_rec.top_contributors = json.dumps(top_c)
            risk_rec.suggested_action = json.dumps(act)

        # Trigger Immediate Alert to push to Rank #1
        alert = db.query(Alert).filter(Alert.senior_id == senior_id, Alert.date == today_str).first()
        alert_title = f"🚨 Routine Call Emergency Intercept: {user_reply[:40]}"
        if not alert:
            alert = Alert(
                senior_id=senior_id,
                date=today_str,
                risk_score=elevated_score,
                risk_category="URGENT",
                primary_signal=alert_title,
                status="PENDING",
                assigned_coordinator_id=senior.assigned_coordinator_id or 1 if senior else 1
            )
            db.add(alert)
        else:
            alert.risk_score = elevated_score
            alert.risk_category = "URGENT"
            alert.primary_signal = alert_title
            alert.status = "PENDING"

        # Log emergency note
        emergency_note = CallNote(
            senior_id=senior_id,
            date=today_str,
            note_text=f"आपातकालीन कॉल इंटरसेप्ट: '{user_reply}'. एजेंट ने सवाल रोक कर तुरंत कोऑर्डिनेटर {coordinator_name} को सूचित किया।",
            caller_role="senior",
            contact_type="SENIOR_VOICE_NOTE",
            ai_call_summary="CRITICAL: Acute symptom verbalized during 10:00 AM Sahara routine call. Immediate coordinator intervention required.",
            language="hi"
        )
        db.add(emergency_note)
        db.commit()

    return step_result


@router.post("/save-completed-call")
def save_completed_routine_call(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Saves completed Sahara 5-Question call results into database.
    Performs Pill Box Hardware Cross-Verification.
    Performs Gemini Clinical Doctor Triage and updates Dashboard.
    """
    senior_id = payload.get("senior_id", "SEN_003")
    accumulated = payload.get("accumulated", {})
    recording_url = payload.get("audio_url") or "http://localhost:8000/static/audio/default_note.webm"
    today_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    senior = db.query(Senior).filter(Senior.id == senior_id).first()
    if not senior:
        raise HTTPException(status_code=404, detail="Senior not found")

    mood_scale = accumulated.get("mood_scale", 2)
    took_meds_self = accumulated.get("took_medicine", True)
    ate_today = accumulated.get("ate_today_reply", "खाना सामान्य खाया")
    symptoms = accumulated.get("symptoms_reported", "")
    open_remarks = accumulated.get("open_remarks", "")

    # Compile structured transcript from real dialogue or answers
    dialogue = accumulated.get("dialogue", [])
    if dialogue and len(dialogue) > 0:
        lines = [f"{senior.full_name.split()[0] if m.get('sender') == 'senior' else 'सहारा AI'}: {m.get('text')}" for m in dialogue]
        transcript_full = " \n".join(lines)
    else:
        mood_str = "अच्छा (1)" if mood_scale == 1 else ("ठीक-ठाक (2)" if mood_scale == 2 else "अच्छा नहीं (3)")
        transcript_full = f"1. सेहत/मूड: {mood_str} | 2. खाना: {ate_today} | 3. दवा: {'हाँ, ले ली' if took_meds_self else 'नहीं ली/भूल गए'} | 4. लक्षण: {symptoms or 'कोई नहीं'} | 5. टिप्पणी: {open_remarks or 'कोई अन्य बात नहीं'}"

    # Hardware Pill Box Mismatch Verification
    # (Check if hardware reported 0 door/pill dispenses while senior self-reported took_meds)
    pill_box_mismatch = False
    if took_meds_self:
        # Check today's vital / hardware observations
        vital_obs = db.query(VitalObservation).filter(VitalObservation.senior_id == senior_id, VitalObservation.date == today_str).first()
        if vital_obs and vital_obs.door_events == 0:
            pill_box_mismatch = True

    # Gemini Clinical Doctor Triage
    triage = doctor_triage_analysis(transcript_full, senior.full_name)
    calculated_risk = float(triage.get("calculated_risk_score", 45.0))

    if pill_box_mismatch:
        calculated_risk = max(calculated_risk, 78.0)
    if mood_scale == 3:
        calculated_risk = max(calculated_risk, 76.0)

    category = "URGENT" if calculated_risk >= 75.0 else ("HIGH" if calculated_risk >= 50.0 else "LOW")

    # Save CallNote with playable Sarvam / Exotel recording
    call_note = CallNote(
        senior_id=senior_id,
        date=today_str,
        note_text=transcript_full,
        caller_role="senior",
        contact_type="SENIOR_VOICE_NOTE",
        audio_url=recording_url,
        audio_duration_seconds=75,
        ai_call_summary=triage.get("summary_en"),
        language="hi"
    )
    db.add(call_note)
    db.commit()
    db.refresh(call_note)

    # Save cues
    cues_data = triage.get("cues", [])
    if pill_box_mismatch:
        cues_data.append({"cue_type": "pill_box_mismatch", "confidence": 0.96, "is_negated": False, "evidence_span": "Self-reported took meds but hardware shows 0 dispenses"})
    if not took_meds_self:
        cues_data.append({"cue_type": "missed_medication", "confidence": 0.98, "is_negated": False, "evidence_span": "dawai nahi li / refill needed"})

    for c in cues_data:
        cue_obj = ExtractedCue(
            call_note_id=call_note.id,
            senior_id=senior_id,
            cue_type=c.get("cue_type", "unknown"),
            confidence=float(c.get("confidence", 0.95)),
            is_negated=c.get("is_negated", False),
            evidence_span=c.get("evidence_span", "")
        )
        db.add(cue_obj)

    # Update Daily Risk Assessment
    top_c = [
        {
            "signal": "10:00 AM Sahara Routine Call (Sarvam AI & Exotel)",
            "impact_score": round(calculated_risk * 0.6, 1),
            "current_value": mood_scale,
            "baseline_value": 1,
            "narrative_en": triage.get("summary_en", f"Sahara routine check completed. Mood: {mood_scale}, Meds: {took_meds_self}"),
            "narrative_hi": triage.get("summary_hi", f"सहारा दैनिक कॉल संपन्न। सेहत स्केल: {mood_scale}, दवा: {'ली' if took_meds_self else 'छूटी'}")
        }
    ]
    if pill_box_mismatch:
        top_c.append({
            "signal": "Hardware Pill Box Discrepancy",
            "impact_score": 38.0,
            "current_value": 0,
            "baseline_value": 1,
            "narrative_en": "Self-report claimed taken, but IoT sensor registered zero drawer openings.",
            "narrative_hi": "दादाजी ने दवा लेना बताया, पर आईओटी पिल बॉक्स सेंसर में कोई हलचल दर्ज नहीं हुई।"
        })

    act = {
        "action": "Routine Touchpoint" if category == "LOW" else "Medication & Health Review",
        "urgency": category,
        "questions_hindi": ["नमस्ते दादाजी, क्या आपकी दवा समय पर ली गई?", "आज का खाना कैसा रहा?"],
        "questions_en": ["Did you take your medication on time?", "How was your meal today?"]
    }

    risk_rec = db.query(DailyRiskAssessment).filter(DailyRiskAssessment.senior_id == senior_id, DailyRiskAssessment.date == today_str).first()
    if not risk_rec:
        risk_rec = DailyRiskAssessment(
            senior_id=senior_id,
            date=today_str,
            risk_score=calculated_risk,
            risk_category=category,
            top_contributors=json.dumps(top_c),
            suggested_action=json.dumps(act)
        )
        db.add(risk_rec)
    else:
        risk_rec.risk_score = calculated_risk
        risk_rec.risk_category = category
        risk_rec.top_contributors = json.dumps(top_c)
        risk_rec.suggested_action = json.dumps(act)

    # Update Alert
    alert = db.query(Alert).filter(Alert.senior_id == senior_id, Alert.date == today_str).first()
    alert_title = f"📞 10 AM Sahara Routine Call: Mood {mood_scale} • {'Pill Mismatch' if pill_box_mismatch else ('Meds Missed' if not took_meds_self else 'Stable')}"
    if not alert:
        alert = Alert(
            senior_id=senior_id,
            date=today_str,
            risk_score=calculated_risk,
            risk_category=category,
            primary_signal=alert_title,
            status="PENDING" if category in ("URGENT", "HIGH") else "RESOLVED",
            assigned_coordinator_id=senior.assigned_coordinator_id or 1
        )
        db.add(alert)
    else:
        alert.risk_score = calculated_risk
        alert.risk_category = category
        alert.primary_signal = alert_title
        if category in ("URGENT", "HIGH"):
            alert.status = "PENDING"

    db.commit()

    return {
        "status": "SUCCESS",
        "senior_id": senior.id,
        "call_note_id": call_note.id,
        "transcript": transcript_full,
        "audio_url": recording_url,
        "risk_score": calculated_risk,
        "risk_category": category,
        "pill_box_mismatch": pill_box_mismatch,
        "cues": cues_data,
        "message": "Sahara 10:00 AM Routine Call successfully logged and prioritized on Coordinator Dashboard!"
    }


@router.post("/exotel/webhook/{senior_id}")
async def exotel_incoming_webhook(
    senior_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Exotel Webhook for call events (Dialpad DTMF digits & Call recording completed).
    """
    form_data = await request.form()
    event_dict = dict(form_data)
    logger.info(f"Received Exotel webhook for {senior_id}: {event_dict}")

    processed = process_exotel_webhook_event(senior_id, event_dict)
    rec_url = processed.get("recording_url")

    # If call finished with a recording URL, link to latest call note
    if rec_url:
        latest_note = db.query(CallNote).filter(CallNote.senior_id == senior_id).order_by(CallNote.id.desc()).first()
        if latest_note:
            latest_note.audio_url = rec_url
            db.commit()

    return {"status": "SUCCESS", "processed": processed}

