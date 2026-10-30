import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    role = Column(String(30), nullable=False)
    action = Column(String(50), nullable=False)  # VIEW_SENIOR, VIEW_ALERTS, ACKNOWLEDGE_ALERT, TOGGLE_CONSENT, etc.
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(50), nullable=True)
    details_masked = Column(Text, nullable=True)  # Strictly zero unmasked PII

    user = relationship("User", back_populates="audit_logs")

