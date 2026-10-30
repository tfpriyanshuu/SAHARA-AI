from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime
import json

from app.core.database import get_db
from app.models.alert import Alert, AlertFeedback
from app.models.senior import Senior
from app.models.risk import DailyRiskAssessment
from app.models.workflow import FollowUp, CoordinatorActionLog
from app.models.user import User
from app.schemas.alert import (
    AlertResponse,
    AlertFeedbackCreate,
    AlertFeedbackResponse,
    AlertAssignRequest,
    AlertResolveRequest,
    AlertStatusUpdate
)
from app.schemas.workflow import FollowUpCreate, FollowUpResponse
from app.api.deps import get_current_user, log_audit

router = APIRouter()


@router.get("", response_model=List[AlertResponse])
def list_alerts(
    status: Optional[str] = None,
    coordinator_id: Optional[int] = None,
    date: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Alert)

    if current_user.role == "coordinator":
        query = query.filter(Alert.assigned_coordinator_id == current_user.id)
    elif coordinator_id:
        query = query.filter(Alert.assigned_coordinator_id == coordinator_id)

    if status:
        query = query.filter(Alert.status == status)
    if date:
        query = query.filter(Alert.date == date)

    alerts = query.order_by(Alert.risk_score.desc()).limit(limit).all()
    results = []
    for a in alerts:
        # Load embedded risk assessment details
        risk_rec = db.query(DailyRiskAssessment).filter(DailyRiskAssessment.senior_id == a.senior_id, DailyRiskAssessment.date == a.date).first()
        top_c = json.loads(risk_rec.top_contributors) if risk_rec and risk_rec.top_contributors else []
        act = json.loads(risk_rec.suggested_action) if risk_rec and risk_rec.suggested_action else None

        coord_name = a.assigned_coordinator.full_name if a.assigned_coordinator else "Unassigned"
        senior_name = a.senior.full_name if a.senior else "Unknown Senior"
        city = a.senior.city if a.senior else "Indore"

        hi_expl = "ऑक्सीजन एवं दिनचर्या में व्यक्तिगत बेसलाइन से विचलन।"
        en_expl = "SpO2 and activity deviate from personal baseline numbers."

        results.append(AlertResponse(
            id=a.id,
            senior_id=a.senior_id,
            senior_name=senior_name,
            city=city,
            date=a.date,
            risk_score=a.risk_score,
            risk_category=a.risk_category,
            primary_signal=a.primary_signal,
            status=a.status,
            assigned_coordinator_id=a.assigned_coordinator_id,
            coordinator_name=coord_name,
            acknowledged_at=a.acknowledged_at,
            resolved_at=a.resolved_at,
            resolution_notes=a.resolution_notes,
            created_at=a.created_at,
            top_contributors=top_c,
            suggested_action=act,
            explanation_hindi=hi_expl,
            explanation_english=en_expl
        ))
    return results


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert_detail(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    a = db.query(Alert).filter(Alert.id == alert_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")

    risk_rec = db.query(DailyRiskAssessment).filter(DailyRiskAssessment.senior_id == a.senior_id, DailyRiskAssessment.date == a.date).first()
    top_c = json.loads(risk_rec.top_contributors) if risk_rec and risk_rec.top_contributors else []
    act = json.loads(risk_rec.suggested_action) if risk_rec and risk_rec.suggested_action else None

    return AlertResponse(
        id=a.id,
        senior_id=a.senior_id,
        senior_name=a.senior.full_name,
        city=a.senior.city,
        date=a.date,
        risk_score=a.risk_score,
        risk_category=a.risk_category,
        primary_signal=a.primary_signal,
        status=a.status,
        assigned_coordinator_id=a.assigned_coordinator_id,
        coordinator_name=a.assigned_coordinator.full_name if a.assigned_coordinator else "Unassigned",
        acknowledged_at=a.acknowledged_at,
        resolved_at=a.resolved_at,
        resolution_notes=a.resolution_notes,
        created_at=a.created_at,
        top_contributors=top_c,
        suggested_action=act,
        explanation_hindi="ऑक्सीजन स्तर में व्यक्तिगत बेसलाइन से गिरावट।",
        explanation_english="SpO2 and activity trajectory deviate from personal baseline."
    )


@router.patch("/{alert_id}")
def update_alert_status(
    alert_id: int,
    status_update: AlertStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = status_update.status
    if status_update.status == "ACKNOWLEDGED":
        alert.acknowledged_at = datetime.datetime.utcnow()
    elif status_update.status in ("RESOLVED", "FALSE_ALARM"):
        alert.resolved_at = datetime.datetime.utcnow()
        alert.resolution_notes = status_update.notes

    db.commit()
    log_audit(db, current_user, action="UPDATE_ALERT_STATUS", resource_type="ALERT", resource_id=str(alert.id), details=f"Status: {status_update.status}")
    return {"message": f"Alert marked as {status_update.status}", "alert_id": alert.id}


@router.post("/{alert_id}/assign")
def assign_alert(
    alert_id: int,
    assign_req: AlertAssignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    coord = db.query(User).filter(User.id == assign_req.coordinator_id).first()
    if not coord:
        raise HTTPException(status_code=404, detail="Coordinator user not found")

    alert.assigned_coordinator_id = coord.id
    db.commit()
    log_audit(db, current_user, action="ASSIGN_ALERT", resource_type="ALERT", resource_id=str(alert.id), details=f"Assigned to {coord.full_name}")
    return {"message": f"Alert assigned to {coord.full_name}", "alert_id": alert.id}


@router.post("/{alert_id}/follow-ups", response_model=FollowUpResponse)
def schedule_follow_up(
    alert_id: int,
    follow_up_in: FollowUpCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    follow_up = FollowUp(
        senior_id=alert.senior_id,
        alert_id=alert.id,
        coordinator_id=current_user.id,
        due_date=follow_up_in.due_date,
        action_type=follow_up_in.action_type or "Phone Check-In",
        notes=follow_up_in.notes,
        status="PENDING"
    )
    db.add(follow_up)
    db.commit()
    db.refresh(follow_up)
    log_audit(db, current_user, action="SCHEDULE_FOLLOW_UP", resource_type="FOLLOW_UP", resource_id=str(follow_up.id), details=f"Due: {follow_up.due_date}")
    
    return FollowUpResponse(
        id=follow_up.id,
        senior_id=follow_up.senior_id,
        alert_id=follow_up.alert_id,
        due_date=follow_up.due_date,
        action_type=follow_up.action_type,
        notes=follow_up.notes,
        coordinator_id=follow_up.coordinator_id,
        status=follow_up.status,
        completed_at=follow_up.completed_at,
        created_at=follow_up.created_at,
        senior_name=alert.senior.full_name if alert.senior else "Senior"
    )


@router.post("/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    resolve_req: AlertResolveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "RESOLVED"
    alert.resolved_at = datetime.datetime.utcnow()
    alert.resolution_notes = resolve_req.resolution_notes

    # Store or update feedback
    fb = db.query(AlertFeedback).filter(AlertFeedback.alert_id == alert.id).first()
    if fb:
        fb.rating = resolve_req.outcome_rating or "useful"
        fb.feedback_notes = resolve_req.resolution_notes
    else:
        fb = AlertFeedback(
            alert_id=alert.id,
            user_id=current_user.id,
            rating=resolve_req.outcome_rating or "useful",
            feedback_notes=resolve_req.resolution_notes
        )
        db.add(fb)
    db.commit()
    log_audit(db, current_user, action="RESOLVE_ALERT", resource_type="ALERT", resource_id=str(alert.id), details=f"Outcome: {resolve_req.outcome_rating}")
    return {"message": "Alert resolved successfully", "alert_id": alert.id}


@router.post("/{alert_id}/feedback", response_model=AlertFeedbackResponse)
def record_alert_feedback(
    alert_id: int,
    fb_in: AlertFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    existing_fb = db.query(AlertFeedback).filter(AlertFeedback.alert_id == alert_id).first()
    if existing_fb:
        existing_fb.rating = fb_in.rating
        existing_fb.feedback_notes = fb_in.feedback_notes
        db.commit()
        db.refresh(existing_fb)
        return existing_fb

    fb = AlertFeedback(
        alert_id=alert_id,
        user_id=current_user.id,
        rating=fb_in.rating,
        feedback_notes=fb_in.feedback_notes
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    log_audit(db, current_user, action="RECORD_ALERT_FEEDBACK", resource_type="FEEDBACK", resource_id=str(fb.id), details=f"Rating: {fb.rating}")
    return fb
