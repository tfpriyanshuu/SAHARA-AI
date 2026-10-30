from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FollowUpCreate(BaseModel):
    senior_id: str
    alert_id: Optional[int] = None
    due_date: str
    action_type: Optional[str] = "Phone Check-In"
    notes: Optional[str] = None


class FollowUpResponse(FollowUpCreate):
    id: int
    coordinator_id: int
    status: str
    completed_at: Optional[datetime] = None
    created_at: datetime
    senior_name: Optional[str] = None

    class Config:
        from_attributes = True


class CoordinatorActionCreate(BaseModel):
    senior_id: str
    date: str
    action_type: str  # CALLED, ESCALATED, SNOOZED, VISIT_SCHEDULED
    notes: Optional[str] = None


class CoordinatorActionResponse(CoordinatorActionCreate):
    id: int
    coordinator_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

