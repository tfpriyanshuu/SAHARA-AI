import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    senior_id = Column(String(50), nullable=True)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    urgency = Column(String(20), default="INFO")  # INFO, WARNING, URGENT
    is_read = Column(Boolean, default=False)
    notification_type = Column(String(50), default="ALERT")  # ALERT, ASSIGNMENT, OVERDUE, FAMILY_UPDATE
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="notifications")

