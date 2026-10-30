from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import (
    auth,
    seniors,
    signals,
    risk,
    alerts,
    family,
    operations,
    notifications,
    demo,
    telephony,
    checkins,
    stream,
    calls,
    hardware
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="SaathiCare AI: AI-Powered Early Warning Decision-Support Platform for Seniors Living at Home.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For hackathon local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files for Real Senior Voice Recordings
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(os.path.join(STATIC_DIR, "audio"), exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Include API Routers under /api/v1
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(seniors.router, prefix=f"{settings.API_V1_STR}/seniors", tags=["Seniors"])
app.include_router(signals.router, prefix=f"{settings.API_V1_STR}/signals", tags=["Signals Ingestion"])
app.include_router(risk.router, prefix=f"{settings.API_V1_STR}/risk", tags=["Risk Scoring & Baselines"])
app.include_router(alerts.router, prefix=f"{settings.API_V1_STR}/alerts", tags=["Alerts & Workflows"])
app.include_router(family.router, prefix=f"{settings.API_V1_STR}/family", tags=["Family Portal"])
app.include_router(operations.router, prefix=f"{settings.API_V1_STR}/operations", tags=["Operations Governance"])
app.include_router(notifications.router, prefix=f"{settings.API_V1_STR}/notifications", tags=["In-App Notifications"])
app.include_router(demo.router, prefix=f"{settings.API_V1_STR}/demo", tags=["Judges Demo Scenarios"])
app.include_router(telephony.router, prefix=f"{settings.API_V1_STR}/telephony", tags=["Exotel Telephony & Sarvam AI"])
app.include_router(checkins.router, prefix=f"{settings.API_V1_STR}/checkins", tags=["Live Voice Check-ins & PWA"])
app.include_router(stream.router, prefix=f"{settings.API_V1_STR}/stream", tags=["Live SSE Event Stream"])
app.include_router(stream.router, prefix="/api/stream", tags=["Live SSE Stream Alias"])
app.include_router(calls.router, prefix=f"{settings.API_V1_STR}/calls", tags=["WebRTC Direct App Calling"])
app.include_router(hardware.router, prefix=f"{settings.API_V1_STR}/hardware", tags=["ESP32 Hardware Integration"])


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "tagline": "Every Signal Matters. Every Senior Matters.",
        "status": "ONLINE",
        "docs_url": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "version": settings.VERSION}

