import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "SaathiCare AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "saathicare-dev-secret-key-32-chars-long-secure-key!")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/saathicare.db")
    
    # Gemini AI API Key (Protected in backend)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    
    # Sarvam AI API Key (Indic STT Saaras & Indic TTS Bulbul)
    SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")
    
    # Exotel Cloud Telephony API Key
    EXOTEL_API_KEY: str = os.getenv("EXOTEL_API_KEY", "")
    EXOTEL_ACCOUNT_SID: str = os.getenv("EXOTEL_ACCOUNT_SID", "sahara-ai")
    EXOTEL_CALLER_ID: str = os.getenv("EXOTEL_CALLER_ID", "+918047192345")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    
    # Alerting & Scoring Parameters
    ALERT_BUDGET_PER_COORDINATOR: int = 10
    RISK_THRESHOLD_URGENT: float = 75.0
    RISK_THRESHOLD_HIGH: float = 60.0
    RISK_THRESHOLD_MODERATE: float = 40.0
    
    # Baseline Parameters
    BASELINE_MIN_PERIODS: int = 7
    BASELINE_LAG_DAYS: int = 14
    BASELINE_WINDOW_DAYS: int = 28  # [t-42, t-14]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

