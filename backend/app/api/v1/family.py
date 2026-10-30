from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import datetime

from app.core.database import get_db
from app.models.senior import Senior, FamilySeniorRelation
from app.models.risk import DailyRiskAssessment
from app.models.signal import VitalObservation, MedicationLog
from app.models.alert import Alert
from app.models.notification import Notification
from app.models.user import User
from app.schemas.senior import FamilyConsentUpdate
from app.schemas.notification import NotificationResponse
from app.api.deps import get_current_user, log_audit

router = APIRouter()


@router.get("/weekly-summary")
def get_family_weekly_summary(
    senior_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Retrieve reassuring, non-alarming weekly wellbeing summary for family role.
    Strictly consent-gated: If family_consent is False, acute alerts are suppressed.
    """
    if current_user.role == "family":
        rel = db.query(FamilySeniorRelation).filter(FamilySeniorRelation.family_user_id == current_user.id).first()
        if not rel:
            raise HTTPException(status_code=403, detail="No senior linked to family account.")
        senior_id = rel.senior_id

    if not senior_id:
        senior_id = "SEN_003"

    senior = db.query(Senior).filter(Senior.id == senior_id).first()
    if not senior:
        raise HTTPException(status_code=404, detail="Senior not found")

    consent = senior.family_consent

    # Get recent 7 days vitals
    vitals_7d = db.query(VitalObservation).filter(VitalObservation.senior_id == senior_id).order_by(VitalObservation.date.desc()).limit(7).all()
    avg_spo2 = round(sum(v.spo2 for v in vitals_7d if v.spo2) / max(1, len([v for v in vitals_7d if v.spo2])), 1) if vitals_7d else 97.4
    
    # Get recent 7 days med logs
    meds_7d = db.query(MedicationLog).filter(MedicationLog.senior_id == senior_id).order_by(MedicationLog.date.desc()).limit(7).all()
    taken_count = sum(1 for m in meds_7d if m.status == "taken")
    adherence_pct = round((taken_count / max(1, len(meds_7d))) * 100, 0) if meds_7d else 95.0

    # Check serious alert
    latest_alert = db.query(Alert).filter(Alert.senior_id == senior_id, Alert.status.in_(["PENDING", "ACKNOWLEDGED"])).order_by(Alert.id.desc()).first()
    has_serious_alert = bool(latest_alert and latest_alert.risk_score >= 70.0)

    if has_serious_alert:
        status_badge = "NEEDS_ATTENTION"
        status_text_en = "Routine indicator changes observed this week. Dedicated Care Coordinator is monitoring closely."
        status_text_hi = "इस सप्ताह स्वास्थ्य संकेतों में बदलाव देखे गए हैं। समर्पित केयर कोऑर्डिनेटर लगातार स्थिति पर नजर रखे हुए हैं।"
    elif adherence_pct < 80.0:
        status_badge = "ROUTINE_DRIFT"
        status_text_en = "Some morning/evening routines missed this week. Main health indicators remain stable."
        status_text_hi = "इस सप्ताह दवा या सुबह की दिनचर्या में कुछ अंतर देखा गया है। मुख्य स्वास्थ्य संकेत सामान्य हैं।"
    else:
        status_badge = "NORMAL_STABLE"
        status_text_en = "Senior routine, daily activity, and indicators are steady within normal personal baseline."
        status_text_hi = "वरिष्ठ की दिनचर्या, शारीरिक सक्रियता और सभी स्वास्थ्य संकेत अपने व्यक्तिगत सामान्य स्तर के अनुकूल स्थिर हैं।"

    log_audit(db, current_user, action="VIEW_FAMILY_SUMMARY", resource_type="FAMILY_PORTAL", resource_id=senior_id)

    return {
        "senior_id": senior.id,
        "senior_name": senior.full_name,
        "family_consent": consent,
        "status_badge": status_badge,
        "status_text_en": status_text_en,
        "status_text_hi": status_text_hi,
        "avg_spo2_7d": avg_spo2,
        "med_adherence_7d_pct": adherence_pct,
        "has_serious_alert": has_serious_alert,
        "show_alert_banner": consent and has_serious_alert,
        "assigned_coordinator_name": senior.coordinator.full_name if senior.coordinator else "Anvesha Sharma (Care Team)",
        "consent_notice": "Family emergency notifications are ACTIVE." if consent else "Family emergency notifications are PAUSED per your privacy settings."
    }


@router.patch("/consent")
def update_family_consent(
    consent_update: FamilyConsentUpdate,
    senior_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "family":
        rel = db.query(FamilySeniorRelation).filter(FamilySeniorRelation.family_user_id == current_user.id).first()
        if not rel:
            raise HTTPException(status_code=403, detail="No senior linked to family user.")
        senior_id = rel.senior_id

    if not senior_id:
        senior_id = "SEN_003"

    senior = db.query(Senior).filter(Senior.id == senior_id).first()
    if not senior:
        raise HTTPException(status_code=404, detail="Senior not found")

    senior.family_consent = consent_update.family_consent
    db.commit()
    log_audit(db, current_user, action="UPDATE_FAMILY_CONSENT", resource_type="CONSENT", resource_id=senior.id, details=f"Consent set to {consent_update.family_consent}")
    return {"message": "Family consent preference updated successfully", "family_consent": senior.family_consent}


@router.get("/notifications", response_model=List[NotificationResponse])
def get_family_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notifications = db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.id.desc()).limit(20).all()
    return notifications

