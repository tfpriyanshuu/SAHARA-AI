import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class VitalObservation(Base):
    __tablename__ = "vital_observations"

    id = Column(Integer, primary_key=True, index=True)
    senior_id = Column(String(50), ForeignKey("seniors.id"), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    sys_bp = Column(Float, nullable=True)
    dia_bp = Column(Float, nullable=True)
    spo2 = Column(Float, nullable=True)
    blood_glucose = Column(Float, nullable=True)
    glucose_context = Column(String(30), nullable=True, default="random")  # fasting, post_meal, random
    weight_kg = Column(Float, nullable=True)
    
    # Activity and sleep ambient readings
    inactivity_hours = Column(Float, nullable=True)
    night_bathroom_visits = Column(Float, nullable=True)
    hours_outdoors = Column(Float, nullable=True)
    door_events = Column(Float, nullable=True)

    data_source = Column(String(50), default="bluetooth_monitor")  # smart_device, coordinator_entry, self_report

    senior = relationship("Senior", back_populates="vitals")


class MedicationSchedule(Base):
    __tablename__ = "medication_schedules"

    id = Column(Integer, primary_key=True, index=True)
    senior_id = Column(String(50), ForeignKey("seniors.id"), nullable=False, index=True)
    med_name = Column(String(100), nullable=False)
    dosage = Column(String(50), nullable=False)
    frequency = Column(String(50), default="Daily")
    morning = Column(Boolean, default=True)
    afternoon = Column(Boolean, default=False)
    evening = Column(Boolean, default=True)
    instructions = Column(String(255), default="Take with water after meals")
    is_active = Column(Boolean, default=True)


class MedicationLog(Base):
    __tablename__ = "medication_logs"

    id = Column(Integer, primary_key=True, index=True)
    senior_id = Column(String(50), ForeignKey("seniors.id"), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    med_name = Column(String(100), default="Prescribed Daily Regimen")
    status = Column(String(20), default="taken")  # taken, missed, delayed, unknown
    taken_pct = Column(Float, default=1.0)
    source = Column(String(50), default="smart_pillbox")

    senior = relationship("Senior", back_populates="medication_logs")


class CheckIn(Base):
    __tablename__ = "check_ins"

    id = Column(Integer, primary_key=True, index=True)
    senior_id = Column(String(50), ForeignKey("seniors.id"), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    mood = Column(String(50), default="Good")  # Good, Low, Anxious, Sad
    sleep_quality = Column(String(50), default="Normal")  # Restful, Disturbed, Poor
    appetite = Column(String(50), default="Normal")  # Normal, Reduced, None
    pain_level = Column(String(50), default="None")  # None, Mild, Moderate, Severe
    loneliness = Column(Boolean, default=False)
    fall_reported = Column(Boolean, default=False)
    
    raw_response = Column(Text, nullable=True)
    audio_url = Column(String(255), nullable=True)
    language = Column(String(20), default="hi")

    senior = relationship("Senior", back_populates="check_ins")


class CallNote(Base):
    __tablename__ = "call_notes"

    id = Column(Integer, primary_key=True, index=True)
    senior_id = Column(String(50), ForeignKey("seniors.id"), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    note_text = Column(Text, nullable=False)
    caller_role = Column(String(30), default="care_coordinator")
    contact_type = Column(String(40), default="COORDINATOR_CALL")
    audio_url = Column(String(255), nullable=True)
    audio_duration_seconds = Column(Integer, default=0)
    ai_call_summary = Column(Text, nullable=True)
    language = Column(String(20), default="hinglish")

    senior = relationship("Senior", back_populates="call_notes")
    cues = relationship("ExtractedCue", back_populates="call_note")


class ExtractedCue(Base):
    __tablename__ = "extracted_cues"

    id = Column(Integer, primary_key=True, index=True)
    call_note_id = Column(Integer, ForeignKey("call_notes.id"), nullable=False, index=True)
    senior_id = Column(String(50), ForeignKey("seniors.id"), nullable=False, index=True)
    cue_type = Column(String(50), nullable=False, index=True)  # pain, breathlessness, confusion, low_appetite, etc.
    intensity = Column(Integer, default=1)  # 1 (mild), 2 (moderate), 3 (severe)
    confidence = Column(Float, default=0.95)
    evidence_span = Column(String(255), nullable=True)
    is_negated = Column(Boolean, default=False)

    call_note = relationship("CallNote", back_populates="cues")


class FamilyInput(Base):
    __tablename__ = "family_inputs"

    id = Column(Integer, primary_key=True, index=True)
    senior_id = Column(String(50), ForeignKey("seniors.id"), nullable=False, index=True)
    family_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    category = Column(String(50), default="routine_change")  # health_concern, mood, visitor, trip
    note = Column(Text, nullable=False)
    severity = Column(String(20), default="LOW")  # LOW, MEDIUM, HIGH

