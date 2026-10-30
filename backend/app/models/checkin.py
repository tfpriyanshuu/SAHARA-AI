import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class SeniorDevice(Base):
    __tablename__ = "senior_devices"

    id = Column(Integer, primary_key=True, index=True)
    senior_id = Column(String(50), ForeignKey("seniors.id"), unique=True, index=True, nullable=False)
    device_id = Column(String(100), nullable=False)
    app_version = Column(String(30), default="1.2.0-pwa")
    paired_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    
    push_token = Column(String(255), nullable=True)
    last_push_received_at = Column(DateTime, nullable=True)
    
    notifications_enabled = Column(Boolean, default=True)
    mic_permission = Column(Boolean, default=True)
    fullscreen_permission = Column(Boolean, default=True)
    battery_optimisation_disabled = Column(Boolean, default=True)
    is_healthy = Column(Boolean, default=True)

    senior = relationship("Senior", backref="device_info")


class CheckinCall(Base):
    __tablename__ = "checkin_calls"

    id = Column(Integer, primary_key=True, index=True)
    checkin_id = Column(String(100), unique=True, index=True, nullable=False)
    event_id = Column(String(100), unique=True, index=True, nullable=False)
    senior_id = Column(String(50), ForeignKey("seniors.id"), index=True, nullable=False)
    coordinator_id = Column(Integer, nullable=True)
    coordinator_name = Column(String(100), default="Anvesha Sharma")
    
    caller_name = Column(String(50), default="Sahara AI")
    caller_label = Column(String(50), default="सहारा AI")
    
    status = Column(String(30), default="ringing", index=True)  # ringing, answered, declined, missed, completed, partial
    rang_at = Column(DateTime, default=datetime.datetime.utcnow)
    answered_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0)
    
    risk_score_before = Column(Float, nullable=True)
    risk_score_after = Column(Float, nullable=True)
    
    summary_en = Column(Text, nullable=True)
    summary_hi = Column(Text, nullable=True)
    stt_confidence = Column(Float, default=0.96)
    needs_review = Column(Boolean, default=False)
    is_emergency = Column(Boolean, default=False)
    
    is_reviewed = Column(Boolean, default=False)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    senior = relationship("Senior", backref="checkin_calls")
    turns = relationship("CheckinTurn", back_populates="call", cascade="all, delete-orphan", order_by="CheckinTurn.turn_index")


class CheckinTurn(Base):
    __tablename__ = "checkin_turns"

    id = Column(Integer, primary_key=True, index=True)
    checkin_id = Column(String(100), ForeignKey("checkin_calls.checkin_id"), index=True, nullable=False)
    event_id = Column(String(100), unique=True, index=True, nullable=False)
    turn_index = Column(Integer, nullable=False)  # 1 to 5
    question_text = Column(String(255), nullable=False)
    audio_url = Column(String(255), nullable=True)
    keypad_input = Column(String(50), nullable=True)
    transcript = Column(Text, nullable=True)
    confidence = Column(Float, default=0.95)
    cues_extracted = Column(Text, nullable=True)  # JSON serialized
    is_emergency = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    call = relationship("CheckinCall", back_populates="turns")


class ClientEventLog(Base):
    __tablename__ = "client_event_logs"

    event_id = Column(String(100), primary_key=True, index=True)
    senior_id = Column(String(50), index=True, nullable=False)
    event_type = Column(String(50), nullable=False)
    payload = Column(Text, nullable=True)
    received_at = Column(DateTime, default=datetime.datetime.utcnow)

