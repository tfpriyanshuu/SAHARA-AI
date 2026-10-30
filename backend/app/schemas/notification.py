from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    senior_id: Optional[str] = None
    title: str
    message: str
    urgency: str
    is_read: bool
    notification_type: str
    created_at: datetime

    class Config:
        from_attributes = True

