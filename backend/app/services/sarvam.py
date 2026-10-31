"""Sarvam AI Indic Speech Services.
Provides Indic Text-to-Speech (Bulbul:v3 with Priya/Aditi voices)
and Indic Speech-to-Text (Saaras:v1).
"""

import os
import json
import base64
import logging
import requests
from typing import Optional, Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

SARVAM_API_KEY = getattr(settings, "SARVAM_API_KEY", "") or os.getenv("SARVAM_API_KEY", "")
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"
SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"


def synthesize_speech_sarvam(
    text: str,
    speaker: str = "priya",
    pace: float = 1.10
) -> Optional[Dict[str, Any]]:
    """
    Synthesize natural, warm Hindi speech using Sarvam Bulbul:v3.
    Uses 'priya' (female caretaker tone representing Priya Didi / Sahara).
    Returns dict with base64 audio and local static URL.
    """
    cleaned = (
        text.replace("?", "।")
        .replace("!", "।")
        .replace("*", "")
        .replace('"', "")
        .strip()
    )
    if not cleaned:
        return None

    try:
        headers = {
            "api-subscription-key": SARVAM_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": [cleaned],
            "target_language_code": "hi-IN",
            "speaker": speaker,
            "pitch": 0.0,
            "pace": pace,
            "loudness": 1.0,
            "speech_sample_rate": 22050,
            "enable_preprocessing": True,
            "model": "bulbul:v3"
        }

        res = requests.post(SARVAM_TTS_URL, headers=headers, json=payload, timeout=12)
        if res.status_code == 200:
            data = res.json()
            audios = data.get("audios", [])
            if audios and len(audios) > 0:
                audio_b64 = audios[0]
                
                # Save as local static audio file for dashboard playback
                try:
                    import uuid
                    import datetime
                    filename = f"sarvam_{int(datetime.datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:6]}.wav"
                    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "audio")
                    os.makedirs(static_dir, exist_ok=True)
                    filepath = os.path.join(static_dir, filename)
                    
                    audio_raw = base64.b64decode(audio_b64)
                    with open(filepath, "wb") as f:
                        f.write(audio_raw)
                        
                    static_url = f"http://localhost:8000/static/audio/{filename}"
                except Exception as file_err:
                    logger.warning(f"Failed to persist Sarvam audio to disk: {file_err}")
                    static_url = None

                return {
                    "source": "sarvam-bulbul-v3",
                    "speaker": speaker,
                    "audio_base64": f"data:audio/wav;base64,{audio_b64}",
                    "audio_url": static_url,
                    "text": cleaned
                }
        else:
            logger.warning(f"Sarvam TTS failed with {res.status_code}: {res.text[:200]}")
    except Exception as e:
        logger.error(f"Sarvam TTS error: {e}")

    return None


def transcribe_speech_sarvam(
    audio_bytes: bytes,
    mime_type: str = "audio/webm",
    prompt: Optional[str] = None
) -> Optional[str]:
    """
    Transcribe senior speech in Hindi / Hinglish using Sarvam Saaras:v1 STT.
    """
    if not audio_bytes or len(audio_bytes) < 200:
        return None

    try:
        headers = {
            "api-subscription-key": SARVAM_API_KEY
        }
        files = {
            "file": ("audio.wav", audio_bytes, mime_type)
        }
        data = {
            "language_code": "hi-IN",
            "model": "saaras:v1"
        }
        if prompt:
            data["prompt"] = prompt

        res = requests.post(SARVAM_STT_URL, headers=headers, files=files, data=data, timeout=15)
        if res.status_code == 200:
            result = res.json()
            transcript = result.get("transcript", "").strip()
            if transcript:
                return transcript
        else:
            logger.warning(f"Sarvam STT failed with {res.status_code}: {res.text[:200]}")
    except Exception as e:
        logger.error(f"Sarvam STT error: {e}")

    return None

