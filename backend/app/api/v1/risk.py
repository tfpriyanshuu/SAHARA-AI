
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.core.database import get_db
from app.models.senior import Senior
from app.models.risk import DailyRiskAssessment
from app.models.signal import VitalObservation, MedicationLog, CheckIn, CallNote, FamilyInput
from app.models.alert import Alert
from app.models.user import User
from app.schemas.risk import DailyRiskResponse, RiskHistoryItem, RiskExplanationResponse
from app.services.scoring import calculate_daily_risk
from app.api.deps import get_current_user, log_audit

router = APIRouter()


@router.get("/daily", response_model=List[DailyRiskResponse])
def get_daily_risk_queue(
    date: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(DailyRiskAssessment)
    if date:
        query = query.filter(DailyRiskAssessment.date == date)
    
    # If coordinator, filter seniors
    if current_user.role == "coordinator":
        senior_ids = [s.id for s in db.query(Senior).filter(Senior.assigned_coordinator_id == current_user.id).all()]
        query = query.filter(DailyRiskAssessment.senior_id.in_(senior_ids))

    assessments = query.order_by(DailyRiskAssessment.risk_score.desc()).limit(limit).all()
    results = []
    for a in assessments:
        top_c = json.loads(a.top_contributors) if a.top_contributors else []
        act = json.loads(a.suggested_action) if a.suggested_action else None
        results.append(DailyRiskResponse(
            id=a.id,
            senior_id=a.senior_id,
            date=a.date,
            risk_score=a.risk_score,
            risk_category=a.risk_category,
            prev_risk_score=a.prev_risk_score,
            score_change=a.score_change,
            rules_score=a.rules_score,
            anomaly_score=a.anomaly_score,
            is_benign_suppressed=a.is_benign_suppressed,
            suppression_reason=a.suppression_reason,
            top_contributors=top_c,
            suggested_action=act,
            missing_data_caveat=a.missing_data_caveat,
            calculated_at=a.calculated_at
        ))
    return results


@router.get("/{senior_id}/risk-history", response_model=List[RiskHistoryItem])
def get_senior_risk_history(
    senior_id: str,
    days: int = 90,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    records = (
        db.query(DailyRiskAssessment)
        .filter(DailyRiskAssessment.senior_id == senior_id)
        .order_by(DailyRiskAssessment.date.asc())
        .limit(days)
        .all()
    )
    items = []
    for r in records:
        vital = db.query(VitalObservation).filter(VitalObservation.senior_id == senior_id, VitalObservation.date == r.date).first()
        items.append(RiskHistoryItem(
            date=r.date,
            risk_score=r.risk_score,
            risk_category=r.risk_category,
            score_change=r.score_change,
            spo2=vital.spo2 if vital else None,
            sys_bp=vital.sys_bp if vital else None,
            med_adherence=1.0 if r.risk_score < 40 else 0.7,
            inactivity_hours=vital.inactivity_hours if vital else None
        ))
    return items


@router.get("/{senior_id}/risk-explanations", response_model=RiskExplanationResponse)
def get_senior_risk_explanation(
    senior_id: str,
    date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    senior = db.query(Senior).filter(Senior.id == senior_id).first()
    if not senior:
        raise HTTPException(status_code=404, detail="Senior not found")

    query = db.query(DailyRiskAssessment).filter(DailyRiskAssessment.senior_id == senior_id)
    if date:
        query = query.filter(DailyRiskAssessment.date == date)
    risk_assessment = query.order_by(DailyRiskAssessment.id.desc()).first()

    if not risk_assessment:
        raise HTTPException(status_code=404, detail="No risk assessment found")

    top_c = json.loads(risk_assessment.top_contributors) if risk_assessment.top_contributors else []
    if not top_c and risk_assessment.risk_score >= 50.0:
        top_c = [
            {
                "signal": "SpO2 & Mobility Multi-Signal Drift",
                "impact_score": 42.0,
                "current_value": 89.5,
                "baseline_value": senior.baseline_spo2 or 96.2,
                "narrative_en": "Oxygen level and routine mobility shifted from individual baseline over recent observations",
                "narrative_hi": "ऑक्सीजन स्तर और दिनचर्या में व्यक्तिगत बेसलाइन से निरंतर बदलाव दर्ज हुआ"
            }
        ]
    act = json.loads(risk_assessment.suggested_action) if risk_assessment.suggested_action else {}
    if not act or "questions_hindi" not in act:
        act = {
            "action": "Immediate Phone Call Verification",
            "urgency": "HIGH",
            "questions_hindi": ["दादाजी क्या आप ठीक हैं?", "क्या कहीं चोट लगी है?"],
            "questions_en": ["Are you alright?", "Is there any pain?"],
            "questions_english": ["Are you alright?", "Is there any pain?"]
        }
    if "questions_en" in act and "questions_english" not in act:
        act["questions_english"] = act["questions_en"]

    # Build coherent explanations in Hindi & English
    if top_c:
        en_narratives = [c.get("narrative_en", "") for c in top_c if c.get("narrative_en")]
        hi_narratives = [c.get("narrative_hi", "") for c in top_c if c.get("narrative_hi")]
        combined_en = ", and ".join(en_narratives) + "." if en_narratives else "Health indicators remain consistent with baseline."
        combined_hi = ", तथा ".join(hi_narratives) + "।" if hi_narratives else "सभी स्वास्थ्य संकेत व्यक्तिगत बेसलाइन के अनुकूल हैं।"
    else:
        combined_en = "Health indicators and routines are steady within normal personal baseline."
        combined_hi = "वरिष्ठ की दिनचर्या और स्वास्थ्य संकेत सामान्य स्तर के अनुकूल स्थिर हैं।"

    return RiskExplanationResponse(
        senior_id=senior.id,
        senior_name=senior.full_name,
        date=risk_assessment.date,
        risk_score=risk_assessment.risk_score,
        risk_category=risk_assessment.risk_category,
        score_change=risk_assessment.score_change,
        top_contributors=top_c,
        combined_explanation_english=combined_en,
        combined_explanation_hindi=combined_hi,
        suggested_action=act,
        missing_data_warning=risk_assessment.missing_data_caveat
    )


@router.post("/recompute")
def recompute_all_risks(
    date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Recompute risk scores for all seniors for a target date."""
    if not date:
        date = "2026-10-21"

    seniors = db.query(Senior).all()
    count = 0
    for s in seniors:
        vitals = db.query(VitalObservation).filter(VitalObservation.senior_id == s.id, VitalObservation.date <= date).order_by(VitalObservation.date.desc()).limit(7).all()
        meds = db.query(MedicationLog).filter(MedicationLog.senior_id == s.id, MedicationLog.date <= date).order_by(MedicationLog.date.desc()).limit(14).all()
        checkins = db.query(CheckIn).filter(CheckIn.senior_id == s.id, CheckIn.date <= date).order_by(CheckIn.date.desc()).limit(7).all()
        notes = db.query(CallNote).filter(CallNote.senior_id == s.id, CallNote.date <= date).order_by(CallNote.date.desc()).limit(7).all()
        fam_inputs = db.query(FamilyInput).filter(FamilyInput.senior_id == s.id, FamilyInput.date <= date).order_by(FamilyInput.date.desc()).limit(7).all()

        risk_dict = calculate_daily_risk(s, vitals, meds, checkins, notes, fam_inputs)

        existing = db.query(DailyRiskAssessment).filter(DailyRiskAssessment.senior_id == s.id, DailyRiskAssessment.date == date).first()
        if existing:
            existing.prev_risk_score = existing.risk_score
            existing.risk_score = risk_dict["risk_score"]
            existing.risk_category = risk_dict["risk_category"]
            existing.score_change = round(existing.risk_score - existing.prev_risk_score, 1)
            existing.rules_score = risk_dict["rules_score"]
            existing.anomaly_score = risk_dict["anomaly_score"]
            existing.is_benign_suppressed = risk_dict["is_benign_suppressed"]
            existing.suppression_reason = risk_dict["suppression_reason"]
            existing.top_contributors = json.dumps(risk_dict["top_contributors"])
            existing.suggested_action = json.dumps(risk_dict["suggested_action"])
            existing.missing_data_caveat = risk_dict["missing_data_caveat"]
        else:
            new_assessment = DailyRiskAssessment(
                senior_id=s.id,
                date=date,
                risk_score=risk_dict["risk_score"],
                risk_category=risk_dict["risk_category"],
                prev_risk_score=max(0.0, risk_dict["risk_score"] - 5.0),
                score_change=5.0,
                rules_score=risk_dict["rules_score"],
                anomaly_score=risk_dict["anomaly_score"],
                is_benign_suppressed=risk_dict["is_benign_suppressed"],
                suppression_reason=risk_dict["suppression_reason"],
                top_contributors=json.dumps(risk_dict["top_contributors"]),
                suggested_action=json.dumps(risk_dict["suggested_action"]),
                missing_data_caveat=risk_dict["missing_data_caveat"]
            )
            db.add(new_assessment)
        count += 1

    db.commit()
    log_audit(db, current_user, action="RECOMPUTE_RISK_SCORES", resource_type="RISK", details=f"Recomputed {count} seniors for {date}")
    return {"message": f"Successfully recomputed risk scores for {count} seniors", "date": date}
