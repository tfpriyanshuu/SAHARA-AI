from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ContributorItem(BaseModel):
    signal: str
    impact_score: float
    current_value: Optional[float] = None
    baseline_value: Optional[float] = None
    narrative: str


class SuggestedAction(BaseModel):
    action_code: str
    title: str
    priority: str
    description: str
    questions_hindi: List[str] = []
    questions_english: List[str] = []
    questions_hinglish: List[str] = []


class DailyRiskResponse(BaseModel):
    id: int
    senior_id: str
    date: str
    risk_score: float
    risk_category: str
    prev_risk_score: float
    score_change: float
    rules_score: float
    anomaly_score: float
    is_benign_suppressed: bool
    suppression_reason: Optional[str] = None
    top_contributors: List[Dict[str, Any]] = []
    suggested_action: Optional[Dict[str, Any]] = None
    missing_data_caveat: Optional[str] = None
    calculated_at: datetime

    class Config:
        from_attributes = True


class RiskHistoryItem(BaseModel):
    date: str
    risk_score: float
    risk_category: str
    score_change: float
    spo2: Optional[float] = None
    sys_bp: Optional[float] = None
    med_adherence: Optional[float] = None
    inactivity_hours: Optional[float] = None


class RiskExplanationResponse(BaseModel):
    senior_id: str
    senior_name: str
    date: str
    risk_score: float
    risk_category: str
    score_change: float
    top_contributors: List[Dict[str, Any]]
    combined_explanation_hindi: str
    combined_explanation_english: str
    suggested_action: Dict[str, Any]
    missing_data_warning: Optional[str] = None

