from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class VitalCreate(BaseModel):
    date: str
    sys_bp: Optional[float] = None
    dia_bp: Optional[float] = None
    spo2: Optional[float] = None
    blood_glucose: Optional[float] = None
    glucose_context: Optional[str] = "random"
    weight_kg: Optional[float] = None
    inactivity_hours: Optional[float] = None
    night_bathroom_visits: Optional[float] = None
    hours_outdoors: Optional[float] = None
    door_events: Optional[float] = None
    data_source: Optional[str] = "coordinator_manual"


class VitalResponse(VitalCreate):
    id: int
    senior_id: str
    timestamp: datetime

    class Config:
        from_attributes = True


class MedicationScheduleCreate(BaseModel):
    med_name: str
    dosage: str
    frequency: Optional[str] = "Daily"
    morning: Optional[bool] = True
    afternoon: Optional[bool] = False
    evening: Optional[bool] = True
    instructions: Optional[str] = "Take after food"


class MedicationScheduleResponse(MedicationScheduleCreate):
    id: int
    senior_id: str
    is_active: bool

    class Config:
        from_attributes = True


class MedicationLogCreate(BaseModel):
    date: str
    med_name: Optional[str] = "Prescribed Daily Regimen"
    status: str = "taken"  # taken, missed, delayed, unknown
    taken_pct: Optional[float] = 1.0
    source: Optional[str] = "smart_pillbox"


class MedicationLogResponse(MedicationLogCreate):
    id: int
    senior_id: str
    timestamp: datetime

    class Config:
        from_attributes = True


class CheckInCreate(BaseModel):
    date: str
    mood: Optional[str] = "Good"
    sleep_quality: Optional[str] = "Normal"
    appetite: Optional[str] = "Normal"
    pain_level: Optional[str] = "None"
    loneliness: Optional[bool] = False
    fall_reported: Optional[bool] = False
    raw_response: Optional[str] = None
    audio_url: Optional[str] = None
    language: Optional[str] = "hi"


class CheckInResponse(CheckInCreate):
    id: int
    senior_id: str
    timestamp: datetime

    class Config:
        from_attributes = True


class ExtractedCueResponse(BaseModel):
    id: int
    cue_type: str
    intensity: int
    confidence: float
    evidence_span: Optional[str] = None
    is_negated: bool

    class Config:
        from_attributes = True


class CallNoteCreate(BaseModel):
    date: str
    note_text: str
    caller_role: Optional[str] = "care_coordinator"
    contact_type: Optional[str] = "COORDINATOR_CALL"
    audio_url: Optional[str] = None
    audio_duration_seconds: Optional[int] = 0
    ai_call_summary: Optional[str] = None
    language: Optional[str] = "hinglish"


class CallNoteResponse(CallNoteCreate):
    id: int
    senior_id: str
    timestamp: datetime
    cues: List[ExtractedCueResponse] = []

    class Config:
        from_attributes = True


class FamilyInputCreate(BaseModel):
    date: str
    category: str
    note: str
    severity: Optional[str] = "LOW"


class FamilyInputResponse(FamilyInputCreate):
    id: int
    senior_id: str
    family_user_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

