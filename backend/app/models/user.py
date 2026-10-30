import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(30), nullable=False, index=True)  # coordinator, senior, family, ops_manager
    city = Column(String(50), nullable=True, default="Delhi")
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    assigned_seniors = relationship("Senior", back_populates="coordinator", foreign_keys="Senior.assigned_coordinator_id")
    family_relations = relationship("FamilySeniorRelation", back_populates="family_user")
    alerts_assigned = relationship("Alert", back_populates="assigned_coordinator")
    notifications = relationship("Notification", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")

