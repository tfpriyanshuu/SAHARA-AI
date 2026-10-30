from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class AlertFeedbackCreate(BaseModel):
    rating: str  # useful, false_alarm, distractor
    feedback_notes: Optional[str] = None


class AlertFeedbackResponse(AlertFeedbackCreate):
    id: int
    alert_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AlertAssignRequest(BaseModel):
    coordinator_id: int


class AlertResolveRequest(BaseModel):
    resolution_notes: str
    outcome_rating: Optional[str] = "useful"  # useful, false_alarm


class AlertStatusUpdate(BaseModel):
    status: str  # ACKNOWLEDGED, ESCALATED, SNOOZED, RESOLVED, FALSE_ALARM
    notes: Optional[str] = None


class AlertResponse(BaseModel):
    id: int
    senior_id: str
    senior_name: str
    city: str
    date: str
    risk_score: float
    risk_category: str
    primary_signal: str
    status: str
    assigned_coordinator_id: Optional[int] = None
    coordinator_name: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    
    # Embedded explanations
    top_contributors: List[Dict[str, Any]] = []
    suggested_action: Optional[Dict[str, Any]] = None
    explanation_hindi: Optional[str] = None
    explanation_english: Optional[str] = None

    class Config:
        from_attributes = True

