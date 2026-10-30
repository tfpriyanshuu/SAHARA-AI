import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Senior(Base):
    __tablename__ = "seniors"

    id = Column(String(50), primary_key=True, index=True)  # e.g. "SEN_001"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # optional link to senior login
    full_name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(20), default="Female")
    city = Column(String(50), nullable=False, index=True)
    primary_language = Column(String(30), default="Hindi")
    address = Column(String(255), default="Indore, Madhya Pradesh")
    emergency_contact = Column(String(100), default="Rajesh Sharma (Son) +91-98260 99887")
    senior_phone = Column(String(50), default="+91 98260 11234")
    family_phone = Column(String(50), default="+91 98260 99887")
    family_contact_name = Column(String(100), default="Rajesh Sharma (Son)")
    home_hub_status = Column(String(50), default="ONLINE")
    home_hub_device_id = Column(String(50), default="HUB-IND-003")
    family_consent = Column(Boolean, default=True)
    
    assigned_coordinator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Established Personal Baseline Numbers (from lagged window)
    baseline_spo2 = Column(Float, default=97.5)
    baseline_sys_bp = Column(Float, default=124.0)
    baseline_dia_bp = Column(Float, default=80.0)
    baseline_sugar = Column(Float, default=115.0)
    baseline_inactivity_hours = Column(Float, default=6.5)
    baseline_night_bathroom = Column(Float, default=1.0)
    baseline_door_events = Column(Float, default=10.0)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    coordinator = relationship("User", back_populates="assigned_seniors", foreign_keys=[assigned_coordinator_id])
    family_relations = relationship("FamilySeniorRelation", back_populates="senior")
    vitals = relationship("VitalObservation", back_populates="senior")
    medication_logs = relationship("MedicationLog", back_populates="senior")
    check_ins = relationship("CheckIn", back_populates="senior")
    call_notes = relationship("CallNote", back_populates="senior")
    risk_assessments = relationship("DailyRiskAssessment", back_populates="senior")
    alerts = relationship("Alert", back_populates="senior")
    follow_ups = relationship("FollowUp", back_populates="senior")


class FamilySeniorRelation(Base):
    __tablename__ = "family_senior_relations"

    id = Column(Integer, primary_key=True, index=True)
    family_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    senior_id = Column(String(50), ForeignKey("seniors.id"), nullable=False)
    relationship_type = Column(String(50), default="Son/Daughter")
    is_emergency_contact = Column(Boolean, default=True)
    can_view_vitals = Column(Boolean, default=True)
    can_view_medication = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    family_user = relationship("User", back_populates="family_relations")
    senior = relationship("Senior", back_populates="family_relations")

