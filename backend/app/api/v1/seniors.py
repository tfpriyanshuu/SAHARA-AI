from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.core.database import get_db
from app.models.senior import Senior, FamilySeniorRelation
from app.models.risk import DailyRiskAssessment
from app.models.alert import Alert
from app.models.user import User
from app.models.signal import CallNote, ExtractedCue
from app.schemas.senior import SeniorCreate, SeniorUpdate, SeniorListItem, SeniorDetailResponse
from app.api.deps import get_current_user, require_roles, log_audit

router = APIRouter()


@router.get("", response_model=List[SeniorListItem])
def list_seniors(
    risk_category: Optional[str] = None,
    city: Optional[str] = None,
    coordinator_id: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 300,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Senior)

    # Role-based restriction:
    if current_user.role == "coordinator":
        query = query.filter(Senior.assigned_coordinator_id == current_user.id)
    elif current_user.role == "family":
        # Only linked seniors
        linked_ids = [r.senior_id for r in db.query(FamilySeniorRelation).filter(FamilySeniorRelation.family_user_id == current_user.id).all()]
        query = query.filter(Senior.id.in_(linked_ids))

    if city:
        query = query.filter(Senior.city == city)
    if coordinator_id:
        query = query.filter(Senior.assigned_coordinator_id == coordinator_id)
    if search:
        search_fmt = f"%{search}%"
        query = query.filter((Senior.full_name.ilike(search_fmt)) | (Senior.id.ilike(search_fmt)))

    seniors = query.offset(skip).limit(limit).all()
    results = []

    for s in seniors:
        # Get latest risk assessment
        latest_risk = db.query(DailyRiskAssessment).filter(DailyRiskAssessment.senior_id == s.id).order_by(DailyRiskAssessment.id.desc()).first()
        active_alert = db.query(Alert).filter(Alert.senior_id == s.id, Alert.status.in_(["PENDING", "ACKNOWLEDGED", "ESCALATED"])).first()
        
        # Check latest voice note or call note
        latest_note = db.query(CallNote).filter(CallNote.senior_id == s.id).order_by(CallNote.id.desc()).first()
        voice_transcript = latest_note.note_text if latest_note else None
        has_voice = bool(latest_note and latest_note.contact_type == "SENIOR_VOICE_NOTE")
        ai_summary = latest_note.ai_call_summary if latest_note and latest_note.ai_call_summary else None
        audio_url = latest_note.audio_url if latest_note else None

        note_cues = []
        if latest_note:
            cues_objs = db.query(ExtractedCue).filter(ExtractedCue.call_note_id == latest_note.id).all()
            for co in cues_objs:
                note_cues.append({
                    "cue_type": co.cue_type,
                    "confidence": co.confidence,
                    "is_negated": co.is_negated
                })

        score = latest_risk.risk_score if latest_risk else 15.0
        cat = latest_risk.risk_category if latest_risk else "LOW"
        change = latest_risk.score_change if latest_risk else 0.0

        if risk_category and cat.upper() != risk_category.upper():
            continue

        has_mismatch = any(c.get("cue_type") == "pill_box_mismatch" for c in note_cues)

        s_item = SeniorListItem(
            id=s.id,
            full_name=s.full_name,
            age=s.age,
            gender=s.gender,
            city=s.city,
            primary_language=s.primary_language,
            family_consent=s.family_consent,
            assigned_coordinator_id=s.assigned_coordinator_id,
            coordinator_name=s.coordinator.full_name if s.coordinator else "Unassigned",
            senior_phone=getattr(s, "senior_phone", "+91 98260 11234") or "+91 98260 11234",
            family_phone=getattr(s, "family_phone", "+91 98260 99887") or "+91 98260 99887",
            family_contact_name=getattr(s, "family_contact_name", "Rajesh Sharma (Son)") or "Rajesh Sharma (Son)",
            home_hub_status=getattr(s, "home_hub_status", "ONLINE") or "ONLINE",
            home_hub_device_id=getattr(s, "home_hub_device_id", "HUB-IND-003") or "HUB-IND-003",
            latest_voice_transcript=voice_transcript,
            latest_ai_call_summary=ai_summary,
            latest_audio_url=audio_url,
            latest_cues=note_cues,
            has_voice_note=has_voice,
            pill_box_mismatch=has_mismatch,
            routine_call_status="Routine Call Logged (Exotel + Sarvam AI)" if voice_transcript else "Scheduled 10:00 AM",
            current_risk_score=score,
            risk_category=cat,
            score_change=change,
            primary_signal="🎙️ Voice Transcript & Home Hub" if has_voice else ("SpO2 & Mobility" if cat in ("URGENT", "HIGH") else "Baseline Stable"),
            last_check_in="Today, 09:30 AM",
            alert_status=active_alert.status if active_alert else None,
            recommended_action="Urgent Safety Verification" if cat == "URGENT" else ("Vital Review" if cat == "HIGH" else "Routine Observation")
        )
        results.append(s_item)

    # Sort descending by risk score
    results = sorted(results, key=lambda x: x.current_risk_score, reverse=True)
    return results


@router.get("/{senior_id}", response_model=SeniorDetailResponse)
def get_senior_detail(
    senior_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    senior = db.query(Senior).filter(Senior.id == senior_id).first()
    if not senior:
        raise HTTPException(status_code=404, detail="Senior not found")

    # Access boundary validation:
    if current_user.role == "coordinator" and senior.assigned_coordinator_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied: Senior assigned to a different coordinator.")
    elif current_user.role == "family":
        rel = db.query(FamilySeniorRelation).filter(FamilySeniorRelation.family_user_id == current_user.id, FamilySeniorRelation.senior_id == senior_id).first()
        if not rel:
            raise HTTPException(status_code=403, detail="Access denied: You are not authorized for this senior.")

    log_audit(db, current_user, action="VIEW_SENIOR_DETAIL", resource_type="SENIOR", resource_id=senior_id)

    latest_note = db.query(CallNote).filter(CallNote.senior_id == senior_id).order_by(CallNote.id.desc()).first()
    audio_url = latest_note.audio_url if latest_note else None

    return SeniorDetailResponse(
        id=senior.id,
        full_name=senior.full_name,
        age=senior.age,
        gender=senior.gender,
        city=senior.city,
        primary_language=senior.primary_language,
        address=senior.address,
        emergency_contact=senior.emergency_contact,
        senior_phone=getattr(senior, "senior_phone", "+91 98260 11234") or "+91 98260 11234",
        family_phone=getattr(senior, "family_phone", "+91 98260 99887") or "+91 98260 99887",
        family_contact_name=getattr(senior, "family_contact_name", "Rajesh Sharma (Son)") or "Rajesh Sharma (Son)",
        home_hub_status=getattr(senior, "home_hub_status", "ONLINE") or "ONLINE",
        home_hub_device_id=getattr(senior, "home_hub_device_id", "HUB-IND-003") or "HUB-IND-003",
        latest_audio_url=audio_url,
        family_consent=senior.family_consent,
        assigned_coordinator_id=senior.assigned_coordinator_id,
        baseline_spo2=senior.baseline_spo2,
        baseline_sys_bp=senior.baseline_sys_bp,
        baseline_dia_bp=senior.baseline_dia_bp,
        baseline_sugar=senior.baseline_sugar,
        baseline_inactivity_hours=senior.baseline_inactivity_hours,
        baseline_night_bathroom=senior.baseline_night_bathroom,
        baseline_door_events=senior.baseline_door_events,
        created_at=senior.created_at,
        coordinator_name=senior.coordinator.full_name if senior.coordinator else "Anvesha Sharma"
    )


@router.post("", response_model=SeniorDetailResponse)
def create_senior(
    senior_in: SeniorCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    import uuid
    import datetime

    # Generate ID if not provided
    count = db.query(Senior).count()
    s_id = senior_in.id or f"SEN_{count + 1:03d}"
    
    # Check if senior already exists
    existing = db.query(Senior).filter(Senior.id == s_id).first()
    if existing:
        s_id = f"SEN_{count + 1:03d}_{str(uuid.uuid4())[:4]}"

    coord_id = senior_in.assigned_coordinator_id
    if current_user.role == "coordinator":
        coord_id = current_user.id
    if not coord_id:
        coord_id = 1

    hub_id = senior_in.home_hub_device_id or f"HUB-{senior_in.city[:3].upper()}-{s_id.split('_')[-1]}"

    new_senior = Senior(
        id=s_id,
        full_name=senior_in.full_name,
        age=senior_in.age,
        gender=senior_in.gender or "Male",
        city=senior_in.city,
        primary_language=senior_in.primary_language or "Hindi",
        address=senior_in.address or f"{senior_in.city}, India",
        emergency_contact=f"{senior_in.family_phone} ({senior_in.family_contact_name})",
        senior_phone=senior_in.senior_phone or "+91 98260 11234",
        family_phone=senior_in.family_phone or "+91 98260 99887",
        family_contact_name=senior_in.family_contact_name or "Family Caregiver",
        home_hub_status="ONLINE",
        home_hub_device_id=hub_id,
        family_consent=senior_in.family_consent,
        assigned_coordinator_id=coord_id,
        baseline_spo2=96.5,
        baseline_sys_bp=126.0,
        baseline_dia_bp=80.0,
        baseline_sugar=115.0,
        baseline_inactivity_hours=6.0,
        baseline_night_bathroom=1.0,
        baseline_door_events=5.0
    )
    db.add(new_senior)
    db.commit()
    db.refresh(new_senior)

    today_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    initial_risk = DailyRiskAssessment(
        senior_id=new_senior.id,
        date=today_str,
        risk_score=14.0,
        risk_category="LOW",
        top_contributors=json.dumps([]),
        suggested_action=json.dumps({"action": "Routine Observation", "urgency": "LOW"})
    )
    db.add(initial_risk)
    db.commit()

    log_audit(db, current_user, action="CREATE_SENIOR", resource_type="SENIOR", resource_id=new_senior.id, details=f"Created senior: {new_senior.full_name}")

    return SeniorDetailResponse(
        id=new_senior.id,
        full_name=new_senior.full_name,
        age=new_senior.age,
        gender=new_senior.gender,
        city=new_senior.city,
        primary_language=new_senior.primary_language,
        address=new_senior.address,
        emergency_contact=new_senior.emergency_contact,
        senior_phone=new_senior.senior_phone,
        family_phone=new_senior.family_phone,
        family_contact_name=new_senior.family_contact_name,
        home_hub_status=new_senior.home_hub_status,
        home_hub_device_id=new_senior.home_hub_device_id,
        latest_audio_url=None,
        family_consent=new_senior.family_consent,
        assigned_coordinator_id=new_senior.assigned_coordinator_id,
        baseline_spo2=new_senior.baseline_spo2,
        baseline_sys_bp=new_senior.baseline_sys_bp,
        baseline_dia_bp=new_senior.baseline_dia_bp,
        baseline_sugar=new_senior.baseline_sugar,
        baseline_inactivity_hours=new_senior.baseline_inactivity_hours,
        baseline_night_bathroom=new_senior.baseline_night_bathroom,
        baseline_door_events=new_senior.baseline_door_events,
        created_at=new_senior.created_at,
        coordinator_name=new_senior.coordinator.full_name if new_senior.coordinator else "Anvesha Sharma"
    )


@router.patch("/{senior_id}")
def update_senior(
    senior_id: str,
    update_data: SeniorUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    senior = db.query(Senior).filter(Senior.id == senior_id).first()
    if not senior:
        raise HTTPException(status_code=404, detail="Senior not found")

    update_dict = update_data.dict(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(senior, k, v)

    db.commit()
    db.refresh(senior)
    log_audit(db, current_user, action="UPDATE_SENIOR", resource_type="SENIOR", resource_id=senior_id, details=f"Updated: {list(update_dict.keys())}")
    return {"message": "Senior updated successfully", "senior_id": senior.id}

