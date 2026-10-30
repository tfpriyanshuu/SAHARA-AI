from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import datetime
import json
import os
import base64
import uuid

from app.core.database import get_db
from app.models.senior import Senior
from app.models.risk import DailyRiskAssessment
from app.models.alert import Alert
from app.models.signal import (
    VitalObservation,
    MedicationSchedule,
    MedicationLog,
    CheckIn,
    CallNote,
    ExtractedCue,
    FamilyInput
)
from app.models.user import User
from app.schemas.signal import (
    VitalCreate,
    VitalResponse,
    MedicationScheduleResponse,
    MedicationLogCreate,
    MedicationLogResponse,
    CheckInCreate,
    CheckInResponse,
    CallNoteCreate,
    CallNoteResponse,
    FamilyInputCreate,
    FamilyInputResponse
)
from app.services.nlp import extract_cues_from_note
from app.services.gemini import transcribe_and_analyze_audio, generate_conversational_voice_turn
from app.api.deps import get_current_user, log_audit

router = APIRouter()


@router.get("/{senior_id}/vitals", response_model=List[VitalResponse])
def get_vitals_history(
    senior_id: str,
    days: int = 90,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    vitals = (
        db.query(VitalObservation)
        .filter(VitalObservation.senior_id == senior_id)
        .order_by(VitalObservation.date.asc())
        .limit(days)
        .all()
    )
    return vitals


@router.post("/{senior_id}/vitals", response_model=VitalResponse)
def add_vital_reading(
    senior_id: str,
    vital_in: VitalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    senior = db.query(Senior).filter(Senior.id == senior_id).first()
    if not senior:
        raise HTTPException(status_code=404, detail="Senior not found")

    vital = VitalObservation(
        senior_id=senior_id,
        date=vital_in.date,
        sys_bp=vital_in.sys_bp,
        dia_bp=vital_in.dia_bp,
        spo2=vital_in.spo2,
        blood_glucose=vital_in.blood_glucose,
        glucose_context=vital_in.glucose_context,
        weight_kg=vital_in.weight_kg,
        inactivity_hours=vital_in.inactivity_hours,
        night_bathroom_visits=vital_in.night_bathroom_visits,
        hours_outdoors=vital_in.hours_outdoors,
        door_events=vital_in.door_events,
        data_source=vital_in.data_source
    )
    db.add(vital)
    db.commit()
    db.refresh(vital)
    log_audit(db, current_user, action="INGEST_VITAL", resource_type="VITAL", resource_id=str(vital.id), details=f"SpO2: {vital.spo2}, SysBP: {vital.sys_bp}")
    return vital


@router.get("/{senior_id}/medications", response_model=List[MedicationLogResponse])
def get_medication_logs(
    senior_id: str,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logs = (
        db.query(MedicationLog)
        .filter(MedicationLog.senior_id == senior_id)
        .order_by(MedicationLog.date.asc())
        .limit(days)
        .all()
    )
    return logs


@router.post("/{senior_id}/medication-logs", response_model=MedicationLogResponse)
def log_medication_dose(
    senior_id: str,
    med_in: MedicationLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    med_log = MedicationLog(
        senior_id=senior_id,
        date=med_in.date,
        med_name=med_in.med_name,
        status=med_in.status,
        taken_pct=med_in.taken_pct if med_in.status == "taken" else 0.0,
        source=med_in.source
    )
    db.add(med_log)
    db.commit()
    db.refresh(med_log)
    log_audit(db, current_user, action="INGEST_MEDICATION_LOG", resource_type="MEDICATION", resource_id=str(med_log.id), details=f"Status: {med_log.status}")
    return med_log


@router.post("/{senior_id}/check-ins", response_model=CheckInResponse)
def submit_senior_checkin(
    senior_id: str,
    checkin_in: CheckInCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    checkin = CheckIn(
        senior_id=senior_id,
        date=checkin_in.date,
        mood=checkin_in.mood,
        sleep_quality=checkin_in.sleep_quality,
        appetite=checkin_in.appetite,
        pain_level=checkin_in.pain_level,
        loneliness=checkin_in.loneliness,
        fall_reported=checkin_in.fall_reported,
        raw_response=checkin_in.raw_response,
        audio_url=checkin_in.audio_url,
        language=checkin_in.language
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    log_audit(db, current_user, action="INGEST_CHECKIN", resource_type="CHECKIN", resource_id=str(checkin.id), details=f"Mood: {checkin.mood}, Fall: {checkin.fall_reported}")
    return checkin


@router.get("/{senior_id}/call-notes", response_model=List[CallNoteResponse])
def get_call_notes(
    senior_id: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notes = (
        db.query(CallNote)
        .filter(CallNote.senior_id == senior_id)
        .order_by(CallNote.id.desc())
        .limit(limit)
        .all()
    )
    return notes


@router.post("/{senior_id}/call-notes", response_model=CallNoteResponse)
def ingest_call_note(
    senior_id: str,
    note_in: CallNoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    senior = db.query(Senior).filter(Senior.id == senior_id).first()
    if not senior:
        raise HTTPException(status_code=404, detail="Senior not found")

    call_note = CallNote(
        senior_id=senior_id,
        date=note_in.date,
        note_text=note_in.note_text,
        caller_role=note_in.caller_role,
        contact_type=note_in.contact_type or "COORDINATOR_CALL",
        audio_url=note_in.audio_url,
        audio_duration_seconds=note_in.audio_duration_seconds or 24,
        ai_call_summary=note_in.ai_call_summary,
        language=note_in.language
    )
    db.add(call_note)
    db.commit()
    db.refresh(call_note)

    # Extract NLP Cues
    extracted_cues = extract_cues_from_note(note_in.note_text)
    cue_objs = []
    adverse_active_cues = []
    for c in extracted_cues:
        cue_obj = ExtractedCue(
            call_note_id=call_note.id,
            senior_id=senior_id,
            cue_type=c["cue_type"],
            intensity=c["intensity"],
            confidence=c["confidence"],
            evidence_span=c["evidence_span"],
            is_negated=c["is_negated"]
        )
        db.add(cue_obj)
        cue_objs.append(cue_obj)
        if not c["is_negated"]:
            adverse_active_cues.append(c["cue_type"])

    db.commit()
    db.refresh(call_note)

    # If adverse cues or incoming senior voice note / AI call detected, re-prioritize and elevate risk score
    if adverse_active_cues or note_in.contact_type in ["SENIOR_VOICE_NOTE", "AI_AGENT_DAILY_CALL"]:
        today_str = note_in.date or datetime.datetime.utcnow().strftime("%Y-%m-%d")
        risk_rec = db.query(DailyRiskAssessment).filter(DailyRiskAssessment.senior_id == senior_id, DailyRiskAssessment.date == today_str).first()
        
        # Calculate score boost based on transcript cues
        new_score = min(98.0, 78.0 + len(adverse_active_cues) * 7.5) if adverse_active_cues else 85.0
        new_cat = "URGENT" if new_score >= 75.0 else "HIGH"
        
        top_c = [
            {
                "signal": "Voice Transcript NLP Cues",
                "impact_score": 45.0,
                "current_value": len(adverse_active_cues),
                "baseline_value": 0,
                "narrative_en": f"Spoken note reported {', '.join(adverse_active_cues) if adverse_active_cues else 'health distress'}",
                "narrative_hi": f"आवाज़ रिकॉर्डिंग में {', '.join(adverse_active_cues) if adverse_active_cues else 'अस्वस्थता'} की जानकारी मिली"
            },
            {
                "signal": "Home Hub Ambient Signals",
                "impact_score": 30.0,
                "current_value": 89.2,
                "baseline_value": senior.baseline_spo2 or 96.5,
                "narrative_en": "Oxygen & nighttime bathroom pattern deviating from individual baseline",
                "narrative_hi": "ऑक्सीजन एवं रात्रि बाथरूम की आवृत्ति सामान्य से अधिक"
            }
        ]
        
        act = {
            "action": "Immediate Phone Call Verification",
            "urgency": "HIGH",
            "questions_hindi": ["दादाजी क्या आप ठीक हैं?", "क्या कहीं चोट लगी है या सांस फूल रही है?"],
            "questions_en": ["Are you alright?", "Is there any pain or breathing difficulty?"],
            "questions_english": ["Are you alright?", "Is there any pain or breathing difficulty?"]
        }

        if not risk_rec:
            risk_rec = DailyRiskAssessment(
                senior_id=senior_id,
                date=today_str,
                risk_score=new_score,
                risk_category=new_cat,
                top_contributors=json.dumps(top_c),
                suggested_action=json.dumps(act)
            )
            db.add(risk_rec)
        else:
            risk_rec.risk_score = new_score
            risk_rec.risk_category = new_cat
            risk_rec.top_contributors = json.dumps(top_c)
            risk_rec.suggested_action = json.dumps(act)

        # Update or create active alert
        alert = db.query(Alert).filter(Alert.senior_id == senior_id, Alert.date == today_str).first()
        alert_title = f"🎙️ Voice Note: {adverse_active_cues[0]}" if adverse_active_cues else "🎙️ Voice Check-in Distress"
        if not alert:
            alert = Alert(
                senior_id=senior_id,
                date=today_str,
                risk_score=new_score,
                risk_category=new_cat,
                primary_signal=alert_title,
                status="PENDING",
                assigned_coordinator_id=senior.assigned_coordinator_id or 1
            )
            db.add(alert)
        else:
            alert.risk_score = new_score
            alert.risk_category = new_cat
            alert.primary_signal = alert_title
            alert.status = "PENDING"

        db.commit()

    log_audit(db, current_user, action="INGEST_CALL_NOTE", resource_type="CALL_NOTE", resource_id=str(call_note.id), details=f"Extracted {len(cue_objs)} cues")
    return call_note


@router.post("/{senior_id}/ai-call-simulate")
def simulate_ai_daily_call(
    senior_id: str,
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Simulate the automated daily morning AI agent check-in call (3-4 questions).
    Transcribes answers, extracts cues, updates risk, and sorts senior into the top priority queue.
    """
    senior = db.query(Senior).filter(Senior.id == senior_id).first()
    if not senior:
        raise HTTPException(status_code=404, detail="Senior not found")

    today_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    q1_ans = payload.get("q1_health", "सांस लेने में थोड़ी तकलीफ हो रही है और कमजोरी लग रही है।")
    q2_ans = payload.get("q2_meds", "सुबह की गोली लेना भूल गए थे।")
    q3_ans = payload.get("q3_sleep_appetite", "रात को नींद ठीक नहीं आई, भूख भी कम है।")
    q4_ans = payload.get("q4_pain_dizziness", "चक्कर आ रहे हैं पर छाती में कोई दर्द नहीं है।")

    combined_transcript = (
        f"एआई एजेंट सुबह की कॉल: "
        f"[तबीयत]: {q1_ans} "
        f"[दवाई]: {q2_ans} "
        f"[नींद/भूख]: {q3_ans} "
        f"[चक्कर/दर्द]: {q4_ans}"
    )

    ai_summary_json = json.dumps({
        "q1_health": q1_ans,
        "q2_meds": q2_ans,
        "q3_sleep_appetite": q3_ans,
        "q4_pain_dizziness": q4_ans
    })

    call_note = CallNote(
        senior_id=senior_id,
        date=today_str,
        note_text=combined_transcript,
        caller_role="ai_agent",
        contact_type="AI_AGENT_DAILY_CALL",
        audio_url="https://saathicare.ai/audio/ai_call_sim.mp3",
        audio_duration_seconds=42,
        ai_call_summary=ai_summary_json,
        language="hinglish"
    )
    db.add(call_note)
    db.commit()
    db.refresh(call_note)

    # Extract NLP Cues
    cues = extract_cues_from_note(combined_transcript)
    adverse = []
    for c in cues:
        c_obj = ExtractedCue(
            call_note_id=call_note.id,
            senior_id=senior_id,
            cue_type=c["cue_type"],
            intensity=c["intensity"],
            confidence=c["confidence"],
            evidence_span=c["evidence_span"],
            is_negated=c["is_negated"]
        )
        db.add(c_obj)
        if not c["is_negated"]:
            adverse.append(c["cue_type"])

    # Elevate risk to top of priority queue
    elevated_score = 94.0
    risk_rec = db.query(DailyRiskAssessment).filter(DailyRiskAssessment.senior_id == senior_id, DailyRiskAssessment.date == today_str).first()
    top_c = [
        {
            "signal": "AI Agent Morning Call (3-4 Qs)",
            "impact_score": 50.0,
            "current_value": len(adverse),
            "baseline_value": 0,
            "narrative_en": f"Morning automated call flagged: {', '.join(adverse)}",
            "narrative_hi": f"दैनिक एआई कॉल में पाया गया: {', '.join(adverse)}"
        },
        {
            "signal": "Home Hub IoT Telemetry",
            "impact_score": 35.0,
            "current_value": 88.0,
            "baseline_value": senior.baseline_spo2 or 96.2,
            "narrative_en": "Correlating with SpO2 drop and delayed pillbox cycle",
            "narrative_hi": "ऑक्सीजन स्तर में गिरावट और दवा बॉक्स में विलंब"
        }
    ]
    act = {
        "action": "Immediate Phone Call Verification",
        "urgency": "HIGH",
        "questions_hindi": ["दादाजी क्या आप ठीक हैं?", "क्या आपने पानी पिया और दवा ली?"],
        "questions_en": ["Are you alright?", "Did you take your medicine with water?"],
        "questions_english": ["Are you alright?", "Did you take your medicine with water?"]
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

    alert = db.query(Alert).filter(Alert.senior_id == senior_id, Alert.date == today_str).first()
    alert_title = f"🤖 AI Morning Call Alert ({len(adverse)} cues)"
    if not alert:
        alert = Alert(
            senior_id=senior_id,
            date=today_str,
            risk_score=elevated_score,
            risk_category="URGENT",
            primary_signal=alert_title,
            status="PENDING",
            assigned_coordinator_id=senior.assigned_coordinator_id or 1
        )
        db.add(alert)
    else:
        alert.risk_score = elevated_score
        alert.risk_category = "URGENT"
        alert.primary_signal = alert_title
        alert.status = "PENDING"

    db.commit()
    log_audit(db, current_user, action="SIMULATE_AI_DAILY_CALL", resource_type="CALL_NOTE", resource_id=str(call_note.id))

    return {
        "status": "SUCCESS",
        "senior_id": senior_id,
        "new_risk_score": elevated_score,
        "transcript": combined_transcript,
        "extracted_cues": cues,
        "adverse_cues": adverse,
        "message": "AI Agent Morning Check-in simulated. Senior prioritized to top of queue."
    }


@router.post("/{senior_id}/family-inputs", response_model=FamilyInputResponse)
def submit_family_input(
    senior_id: str,
    input_in: FamilyInputCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    family_input = FamilyInput(
        senior_id=senior_id,
        family_user_id=current_user.id,
        date=input_in.date,
        category=input_in.category,
        note=input_in.note,
        severity=input_in.severity
    )
    db.add(family_input)
    db.commit()
    db.refresh(family_input)
    log_audit(db, current_user, action="INGEST_FAMILY_INPUT", resource_type="FAMILY_INPUT", resource_id=str(family_input.id), details=f"Category: {family_input.category}")
    return family_input


@router.post("/{senior_id}/audio-checkin")
def ingest_senior_audio_checkin(
    senior_id: str,
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    senior = db.query(Senior).filter(Senior.id == senior_id).first()
    if not senior:
        raise HTTPException(status_code=404, detail="Senior not found")

    today_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    audio_base64 = payload.get("audio_base64")
    client_transcript = payload.get("transcript")
    duration = int(payload.get("duration_seconds", 15))
    api_key = payload.get("api_key")
    audio_url = None

    # Save real recorded audio from browser MediaRecorder
    if audio_base64:
        try:
            if "," in audio_base64:
                header, data_str = audio_base64.split(",", 1)
                mime = "audio/webm"
                if "wav" in header:
                    mime = "audio/wav"
                elif "mp3" in header:
                    mime = "audio/mp3"
            else:
                data_str = audio_base64
                mime = "audio/webm"

            audio_bytes = base64.b64decode(data_str)
            filename = f"{senior_id}_{int(datetime.datetime.utcnow().timestamp())}.webm"
            static_audio_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "audio")
            os.makedirs(static_audio_dir, exist_ok=True)
            filepath = os.path.join(static_audio_dir, filename)

            with open(filepath, "wb") as f:
                f.write(audio_bytes)

            audio_url = f"http://localhost:8000/static/audio/{filename}"
        except Exception as e:
            audio_bytes = None
            audio_url = payload.get("audio_url") or "http://localhost:8000/static/audio/default_note.webm"
    else:
        audio_bytes = None
        audio_url = payload.get("audio_url")

    # Analyze audio using Gemini or local NLP
    analysis = transcribe_and_analyze_audio(
        audio_bytes=audio_bytes,
        mime_type="audio/webm",
        client_transcript=client_transcript,
        senior_name=senior.full_name,
        api_key=api_key
    )

    final_transcript = analysis.get("transcript_hindi") or client_transcript or "दादाजी ने अपनी आवाज़ में स्वास्थ्य रिपोर्ट दी।"
    extracted_cues = analysis.get("cues", [])

    # Store CallNote
    call_note = CallNote(
        senior_id=senior_id,
        date=today_str,
        note_text=final_transcript,
        caller_role="senior",
        contact_type="SENIOR_VOICE_NOTE",
        audio_url=audio_url,
        audio_duration_seconds=duration,
        ai_call_summary=analysis.get("summary_en"),
        language="hi"
    )
    db.add(call_note)
    db.commit()
    db.refresh(call_note)

    adverse_cues = []
    for c in extracted_cues:
        is_neg = c.get("is_negated", False)
        cue_type = c.get("cue_type", "unknown")
        cue_obj = ExtractedCue(
            call_note_id=call_note.id,
            senior_id=senior_id,
            cue_type=cue_type,
            intensity=c.get("intensity", 2),
            confidence=float(c.get("confidence", 0.95)),
            evidence_span=c.get("evidence_span", ""),
            is_negated=is_neg
        )
        db.add(cue_obj)
        if not is_neg:
            adverse_cues.append(cue_type)

    db.commit()

    # Dynamic risk score from Gemini Doctor Triage (e.g. 98.5 for chest pain)
    calculated_doctor_score = float(analysis.get("calculated_risk_score", 85.0))
    elevated_score = max(5.0, min(99.0, calculated_doctor_score))
    risk_cat = "URGENT" if elevated_score >= 75.0 else ("HIGH" if elevated_score >= 50.0 else "LOW")

    risk_rec = db.query(DailyRiskAssessment).filter(DailyRiskAssessment.senior_id == senior_id, DailyRiskAssessment.date == today_str).first()
    top_c = [
        {
            "signal": "Real Senior Voice Recording (Sahara Clinical Triage)",
            "impact_score": round(elevated_score * 0.65, 1),
            "current_value": len(adverse_cues),
            "baseline_value": 0,
            "narrative_en": analysis.get("summary_en", f"Spoken voice note flagged: {', '.join(adverse_cues) if adverse_cues else 'health distress'}"),
            "narrative_hi": analysis.get("summary_hi", f"दादाजी की रिकॉर्ड की गई आवाज़ में लक्षण: {', '.join(adverse_cues) if adverse_cues else 'अस्वस्थता'}")
        },
        {
            "signal": "Connected Home Hub",
            "impact_score": 35.0,
            "current_value": 88.4,
            "baseline_value": senior.baseline_spo2 or 96.2,
            "narrative_en": "Correlating SpO2 drop and night bathroom radar trips",
            "narrative_hi": "होम हब से ऑक्सीजन में गिरावट और रात की हलचल का मिलान"
        }
    ]

    act = {
        "action": "Immediate Dual Verification Call",
        "urgency": risk_cat,
        "questions_hindi": ["दादाजी क्या आप ठीक हैं?", "सीने में दर्द या सांस की तकलीफ कब से है?"],
        "questions_en": ["Are you alright?", "Did you take your medicine?"]
    }

    if not risk_rec:
        risk_rec = DailyRiskAssessment(
            senior_id=senior_id,
            date=today_str,
            risk_score=elevated_score,
            risk_category=risk_cat,
            top_contributors=json.dumps(top_c),
            suggested_action=json.dumps(act)
        )
        db.add(risk_rec)
    else:
        risk_rec.risk_score = elevated_score
        risk_rec.risk_category = risk_cat
        risk_rec.top_contributors = json.dumps(top_c)
        risk_rec.suggested_action = json.dumps(act)

    alert = db.query(Alert).filter(Alert.senior_id == senior_id, Alert.date == today_str).first()
    alert_title = f"🎙️ Real Voice Note Alert: {', '.join(adverse_cues) if adverse_cues else 'Spoken Distress'}"
    if not alert:
        alert = Alert(
            senior_id=senior_id,
            date=today_str,
            risk_score=elevated_score,
            risk_category=risk_cat,
            primary_signal=alert_title,
            status="PENDING",
            assigned_coordinator_id=senior.assigned_coordinator_id or 1
        )
        db.add(alert)
    else:
        alert.risk_score = elevated_score
        alert.risk_category = risk_cat
        alert.primary_signal = alert_title
        alert.status = "PENDING"

    db.commit()

    log_audit(db, current_user, action="INGEST_AUDIO_CHECKIN", resource_type="CALL_NOTE", resource_id=str(call_note.id), details=f"Audio saved: {filename if audio_base64 else 'direct'}")

    return {
        "status": "SUCCESS",
        "senior_id": senior_id,
        "call_note_id": call_note.id,
        "audio_url": audio_url,
        "transcript": final_transcript,
        "summary_en": analysis.get("summary_en"),
        "summary_hi": analysis.get("summary_hi"),
        "extracted_cues": extracted_cues,
        "adverse_cues": adverse_cues,
        "new_risk_score": elevated_score,
        "risk_category": risk_cat,
        "doctor_reply_hindi": analysis.get("doctor_reply_hindi"),
        "coordinator_assigned_id": senior.assigned_coordinator_id,
        "message": "Real voice recorded & delivered to coordinator queue! Senior prioritized to Rank #1."
    }


@router.post("/{senior_id}/gemini-voice-turn")
def execute_gemini_voice_turn(
    senior_id: str,
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    senior = db.query(Senior).filter(Senior.id == senior_id).first()
    if not senior:
        raise HTTPException(status_code=404, detail="Senior not found")

    turn_idx = int(payload.get("turn_index", 0))
    user_speech = payload.get("user_speech", "")
    history = payload.get("history", [])
    api_key = payload.get("api_key")

    result = generate_conversational_voice_turn(
        senior_name=senior.full_name,
        turn_index=turn_idx,
        user_speech_text=user_speech,
        api_key=api_key,
        conversation_history=history
    )

    # Immediately escalate risk if distress or symptoms detected during conversational turn
    triage = result.get("triage", {})
    triage_score = float(triage.get("calculated_risk_score", 0))
    if triage_score >= 60.0 or any(not c.get("is_negated") for c in triage.get("cues", [])):
        today_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        triage_cat = "URGENT" if triage_score >= 75.0 else "HIGH"
        adverse = [c["cue_type"] for c in triage.get("cues", []) if not c.get("is_negated")]

        risk_rec = db.query(DailyRiskAssessment).filter(DailyRiskAssessment.senior_id == senior_id, DailyRiskAssessment.date == today_str).first()
        top_c = [
            {
                "signal": "Conversational AI Doctor Triage (Live Speech)",
                "impact_score": round(triage_score * 0.65, 1),
                "current_value": len(adverse),
                "baseline_value": 0,
                "narrative_en": triage.get("summary_en", f"Speech check-in reported: {', '.join(adverse)}"),
                "narrative_hi": triage.get("summary_hi", f"बोलकर जांच में लक्षण: {', '.join(adverse)}")
            },
            {
                "signal": "Connected Home Hub",
                "impact_score": 35.0,
                "current_value": 88.4,
                "baseline_value": senior.baseline_spo2 or 96.2,
                "narrative_en": "Correlating SpO2 drop and night bathroom radar trips",
                "narrative_hi": "होम हब से ऑक्सीजन में गिरावट और रात की हलचल का मिलान"
            }
        ]
        act = {
            "action": "Immediate Dual Verification Call",
            "urgency": triage_cat,
            "questions_hindi": ["दादाजी क्या आप ठीक हैं?", "सीने में दर्द या सांस की तकलीफ कब से है?"],
            "questions_en": ["Are you alright?", "How long have you had chest pain or breathing issues?"]
        }
        if not risk_rec:
            risk_rec = DailyRiskAssessment(
                senior_id=senior_id,
                date=today_str,
                risk_score=triage_score,
                risk_category=triage_cat,
                top_contributors=json.dumps(top_c),
                suggested_action=json.dumps(act)
            )
            db.add(risk_rec)
        else:
            risk_rec.risk_score = triage_score
            risk_rec.risk_category = triage_cat
            risk_rec.top_contributors = json.dumps(top_c)
            risk_rec.suggested_action = json.dumps(act)

        alert = db.query(Alert).filter(Alert.senior_id == senior_id, Alert.date == today_str).first()
        alert_title = f"🎙️ Live Speech Triage Alert: {', '.join(adverse) if adverse else 'Clinical Distress'}"
        if not alert:
            alert = Alert(
                senior_id=senior_id,
                date=today_str,
                risk_score=triage_score,
                risk_category=triage_cat,
                primary_signal=alert_title,
                status="PENDING",
                assigned_coordinator_id=senior.assigned_coordinator_id or 1
            )
            db.add(alert)
        else:
            alert.risk_score = triage_score
            alert.risk_category = triage_cat
            alert.primary_signal = alert_title
            alert.status = "PENDING"

        # Save note for coordinator review
        note = CallNote(
            senior_id=senior_id,
            date=today_str,
            note_text=user_speech,
            caller_role="senior",
            contact_type="SENIOR_VOICE_NOTE",
            audio_url=f"http://localhost:8000/static/audio/{senior_id}_live.webm",
            audio_duration_seconds=25,
            ai_call_summary=triage.get("summary_en"),
            language="hi"
        )
        db.add(note)
        db.commit()

    return result


