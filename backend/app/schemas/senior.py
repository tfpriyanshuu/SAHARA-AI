from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SeniorBase(BaseModel):
    id: str
    full_name: str
    age: int
    gender: Optional[str] = "Female"
    city: str
    primary_language: Optional[str] = "Hindi"
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    family_consent: Optional[bool] = True
    assigned_coordinator_id: Optional[int] = None


class SeniorCreate(BaseModel):
    id: Optional[str] = None
    full_name: str
    age: int = 75
    gender: Optional[str] = "Male"
    city: str = "Indore"
    primary_language: Optional[str] = "Hindi"
    address: Optional[str] = "Scheme 54, Indore, MP"
    emergency_contact: Optional[str] = None
    senior_phone: Optional[str] = "+91 98260 11234"
    family_phone: Optional[str] = "+91 98260 99887"
    family_contact_name: Optional[str] = "Rajesh Sharma (Son)"
    family_consent: Optional[bool] = True
    assigned_coordinator_id: Optional[int] = 1
    home_hub_device_id: Optional[str] = None


class SeniorUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    city: Optional[str] = None
    primary_language: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    senior_phone: Optional[str] = None
    family_phone: Optional[str] = None
    family_contact_name: Optional[str] = None
    family_consent: Optional[bool] = None
    assigned_coordinator_id: Optional[int] = None


class SeniorListItem(BaseModel):
    id: str
    full_name: str
    age: int
    gender: str
    city: str
    primary_language: str
    family_consent: bool
    assigned_coordinator_id: Optional[int] = None
    coordinator_name: Optional[str] = None
    
    # Contact info
    senior_phone: Optional[str] = "+91 98260 11234"
    family_phone: Optional[str] = "+91 98260 99887"
    family_contact_name: Optional[str] = "Rajesh Sharma (Son)"
    home_hub_status: Optional[str] = "ONLINE"
    home_hub_device_id: Optional[str] = "HUB-IND-003"
    latest_voice_transcript: Optional[str] = None
    latest_ai_call_summary: Optional[str] = None
    latest_audio_url: Optional[str] = None
    latest_cues: Optional[List[dict]] = None
    has_voice_note: bool = False
    pill_box_mismatch: Optional[bool] = False
    routine_call_status: Optional[str] = "Completed (Exotel + Sarvam AI)"

    # Live risk indicators
    current_risk_score: float = 0.0
    risk_category: str = "LOW"
    score_change: float = 0.0
    primary_signal: Optional[str] = None
    last_check_in: Optional[str] = None
    alert_status: Optional[str] = None
    recommended_action: Optional[str] = None

    class Config:
        from_attributes = True


class SeniorDetailResponse(SeniorBase):
    senior_phone: Optional[str] = "+91 98260 11234"
    family_phone: Optional[str] = "+91 98260 99887"
    family_contact_name: Optional[str] = "Rajesh Sharma (Son)"
    home_hub_status: Optional[str] = "ONLINE"
    home_hub_device_id: Optional[str] = "HUB-IND-003"
    latest_audio_url: Optional[str] = None
    baseline_spo2: float
    baseline_sys_bp: float
    baseline_dia_bp: float
    baseline_sugar: float
    baseline_inactivity_hours: float
    baseline_night_bathroom: float
    baseline_door_events: float
    created_at: datetime
    coordinator_name: Optional[str] = None

    class Config:
        from_attributes = True


class FamilyConsentUpdate(BaseModel):
    family_consent: bool

