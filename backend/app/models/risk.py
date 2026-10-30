import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class DailyRiskAssessment(Base):
    __tablename__ = "daily_risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    senior_id = Column(String(50), ForeignKey("seniors.id"), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    
    risk_score = Column(Float, nullable=False)  # 0 to 100
    risk_category = Column(String(20), nullable=False, index=True)  # LOW, MODERATE, HIGH, URGENT
    prev_risk_score = Column(Float, default=0.0)
    score_change = Column(Float, default=0.0)
    
    rules_score = Column(Float, default=0.0)
    anomaly_score = Column(Float, default=0.0)
    
    is_benign_suppressed = Column(Boolean, default=False)
    suppression_reason = Column(String(100), nullable=True)  # e.g., "BENIGN_TRAVEL_ROUTINE", "BENIGN_FESTIVAL"
    
    top_contributors = Column(Text, nullable=True)  # JSON list of {signal, impact, current, baseline, narrative}
    suggested_action = Column(Text, nullable=True)  # JSON dict of {action_code, title, priority, questions}
    missing_data_caveat = Column(String(255), nullable=True)
    
    calculated_at = Column(DateTime, default=datetime.datetime.utcnow)

    senior = relationship("Senior", back_populates="risk_assessments")

