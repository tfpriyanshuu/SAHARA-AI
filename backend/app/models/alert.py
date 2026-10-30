import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    senior_id = Column(String(50), ForeignKey("seniors.id"), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)
    risk_score = Column(Float, nullable=False)
    risk_category = Column(String(20), nullable=False, index=True)  # HIGH, URGENT
    primary_signal = Column(String(100), nullable=False)
    
    status = Column(String(30), default="PENDING", index=True)  # PENDING, ACKNOWLEDGED, ESCALATED, RESOLVED, FALSE_ALARM
    assigned_coordinator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    senior = relationship("Senior", back_populates="alerts")
    assigned_coordinator = relationship("User", back_populates="alerts_assigned", foreign_keys=[assigned_coordinator_id])
    feedback = relationship("AlertFeedback", back_populates="alert", uselist=False)
    follow_ups = relationship("FollowUp", back_populates="alert")


class AlertFeedback(Base):
    __tablename__ = "alert_feedback"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(String(30), nullable=False)  # useful, false_alarm, distractor
    feedback_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    alert = relationship("Alert", back_populates="feedback")

