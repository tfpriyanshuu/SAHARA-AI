import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id = Column(Integer, primary_key=True, index=True)
    senior_id = Column(String(50), ForeignKey("seniors.id"), nullable=False, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=True)
    coordinator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    due_date = Column(String(10), nullable=False)
    action_type = Column(String(50), default="Phone Check-In")
    status = Column(String(30), default="PENDING", index=True)  # PENDING, COMPLETED, OVERDUE
    notes = Column(Text, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    senior = relationship("Senior", back_populates="follow_ups")
    alert = relationship("Alert", back_populates="follow_ups")


class CoordinatorActionLog(Base):
    __tablename__ = "coordinator_action_logs"

    id = Column(Integer, primary_key=True, index=True)
    coordinator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    senior_id = Column(String(50), ForeignKey("seniors.id"), nullable=False, index=True)
    date = Column(String(10), nullable=False)
    action_type = Column(String(50), nullable=False)  # CALLED, ESCALATED, SNOOZED, VISIT_SCHEDULED
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

