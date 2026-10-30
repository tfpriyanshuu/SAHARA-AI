"""Gemini AI Clinical Doctor Triage and Conversational Voice Agent.
Powered by Google Gemini (gemini-3.5-flash-lite) with deep geriatric clinical reasoning.
"""

import os
import json
import logging
import requests
import base64
from typing import Dict, Any, List, Optional

from app.core.config import settings
from app.services.nlp import extract_cues_from_note, normalize_text

logger = logging.getLogger(__name__)

GEMINI_API_KEY = getattr(settings, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = getattr(settings, "GEMINI_MODEL", "gemini-3.5-flash-lite")
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"


def call_gemini_api(prompt: str, response_json: bool = True, timeout: int = 15, audio_parts: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
    """Call Gemini REST API reliably with structured JSON or natural dialogue."""
    try:
        parts: List[Dict[str, Any]] = []
        if audio_parts:
            parts.extend(audio_parts)
        parts.append({"text": prompt})

        payload: Dict[str, Any] = {
            "contents": [{"parts": parts}]
        }
        if response_json:
            payload["generationConfig"] = {"responseMimeType": "application/json", "temperature": 0.2}
        else:
            payload["generationConfig"] = {"temperature": 0.5}

        res = requests.post(GEMINI_ENDPOINT, json=payload, timeout=timeout)
        if res.status_code == 200:
            data = res.json()
            candidates = data.get("candidates", [])
            if candidates:
                cand_parts = candidates[0].get("content", {}).get("parts", [])
                if cand_parts:
                    return cand_parts[0].get("text", "").strip()
        else:
            logger.warning(f"Gemini API returned status {res.status_code}: {res.text[:200]}")
    except Exception as e:
        logger.error(f"Gemini API request failed: {e}")
    return None


def clean_hindi_speech_text(text: str) -> str:
    """Clean text so speech synthesizers don't speak 'question mark question mark'."""
    if not text:
        return ""
    cleaned = (
        text.replace("?", "। ")
        .replace("???", "। ")
        .replace("??", "। ")
        .replace("!", "। ")
        .replace("*", "")
        .replace('"', "")
        .replace("'", "")
    )
    # Collapse duplicate spaces and purna virams
    while "।।" in cleaned:
        cleaned = cleaned.replace("।।", "।")
    return " ".join(cleaned.split())


def doctor_triage_analysis(
    transcript: str,
    senior_name: str = "Senior Citizen",
    audio_duration: int = 15
) -> Dict[str, Any]:
    """
    Expert clinical doctor triage using Gemini API.
    Evaluates acute distress, severe chest pain, breathlessness, missed medicine, or normal routine,
    and returns an exact dynamic risk score (0-100) and clinical cues.
    """
    cleaned_text = (transcript or "").strip()
    if not cleaned_text:
        cleaned_text = "वरिष्ठ नागरिक ने स्वास्थ्य जांच रिकॉर्ड की।"

    prompt = f"""
You are an expert Geriatric Triage Doctor and Clinical Risk Assessor evaluating an elderly Indian citizen living at home alone.
Senior Name: {senior_name}
Spoken Voice Transcript: "{cleaned_text}"

Evaluate the clinical risk honestly and accurately:
1. Is there acute cardiovascular / respiratory distress?
   - "seene me dard" / "chest pain" / "heart ache" -> CRITICAL EMERGENCY (Risk Score 96.0 - 99.0).
   - "saans phoolna" / "breathlessness" / "saans lene me dikkat" -> URGENT RISK (Risk Score 90.0 - 95.0).
   - "chakkar" / "dizziness" / "dawai bhool gaye" / "missed BP or diabetes medicine" -> HIGH RISK (Risk Score 75.0 - 89.0).
   - "neend kam aayi" / "bhookh nahi lag rahi" / "poor sleep/appetite" -> MODERATE-HIGH (Risk Score 65.0 - 75.0).
   - "pehle tha ab nahi hai" / "dard nahi hai" -> NEGATED symptom (do NOT panic; suppress alert).
   - "sab theek hai" / "normal stroll" / "dawai le li hai" -> HEALTHY (Risk Score 10.0 - 25.0).

2. Calculate a precise numerical calculated_risk_score from 0.0 to 100.0. Higher distress = higher priority.
3. Extract cues: pain, chest_pain, breathing_difficulty, dizziness, low_appetite, sleep_deterioration, missed_medication, fall.
   For each cue, mark is_negated: true if the senior denied it (e.g. "dard nahi hai").
4. Provide a warm, empathetic Doctor Spoken Reply in respectful spoken Hindi (using आप, जी) that reassures the senior and tells them what is being done. IMPORTANT: Do NOT include any question marks '?' in doctor_reply_hindi, use '।' instead so voice synthesis doesn't say 'question mark'.

Return STRICT JSON matching this schema:
{{
  "urgency_level": "CRITICAL" | "URGENT" | "HIGH" | "MODERATE" | "LOW",
  "calculated_risk_score": 98.5,
  "clinical_summary_en": "Acute chest pain reported with insomnia. High suspicion of ischemic event.",
  "clinical_summary_hi": "सीने में दर्द और अनिद्रा की शिकायत। तत्काल चिकित्सकीय ध्यान आवश्यक।",
  "cues": [
    {{"cue_type": "chest_pain", "confidence": 0.98, "is_negated": false, "evidence_span": "seene me dard"}},
    {{"cue_type": "sleep_deterioration", "confidence": 0.92, "is_negated": false, "evidence_span": "neend kam aayi"}}
  ],
  "doctor_reply_hindi": "नमस्ते जी, आपके सीने में दर्द की बात हमने नोट कर ली है। कृपया बिल्कुल घबराएं नहीं और आराम से बैठें। केयर कोऑर्डिनेटर अनिता जी को इमरजेंसी अलर्ट भेजा जा चुका है।"
}}
"""

    gemini_raw = call_gemini_api(prompt, response_json=True)
    if gemini_raw:
        try:
            parsed = json.loads(gemini_raw)
            risk = float(parsed.get("calculated_risk_score", 85.0))
            category = "URGENT" if risk >= 75.0 else ("HIGH" if risk >= 50.0 else "LOW")
            reply = clean_hindi_speech_text(parsed.get("doctor_reply_hindi", "आपकी स्वास्थ्य रिपोर्ट दर्ज हो गई है।"))
            return {
                "source": "gemini-doctor-agent",
                "transcript": cleaned_text,
                "urgency_level": parsed.get("urgency_level", "URGENT"),
                "calculated_risk_score": risk,
                "risk_category": category,
                "summary_en": parsed.get("clinical_summary_en", cleaned_text),
                "summary_hi": parsed.get("clinical_summary_hi", cleaned_text),
                "cues": parsed.get("cues", []),
                "doctor_reply_hindi": reply
            }
        except Exception as e:
            logger.warning(f"Failed to parse Gemini doctor triage response: {e}")

    # Fallback to local clinical NLP
    lower_text = cleaned_text.lower()
    local_cues = extract_cues_from_note(cleaned_text)

    has_negated_pain = "dard nahi" in lower_text or "dard nhi" in lower_text or "pain nahi" in lower_text
    has_chest_pain = ("seene me dard" in lower_text or "chest pain" in lower_text or "chhati" in lower_text or "seena" in lower_text) and not has_negated_pain
    has_breathlessness = ("saans" in lower_text or "sans" in lower_text or "breathing" in lower_text) and not ("saans theek" in lower_text)
    has_insomnia = "neend kam" in lower_text or "neend nahi" in lower_text or "sleep" in lower_text
    has_dizziness = "chakkar" in lower_text or "dizzy" in lower_text
    has_healthy = "sab theek" in lower_text or "badhiya" in lower_text or "dawai le li" in lower_text or "koi dikkat nahi" in lower_text

    if has_chest_pain:
        fallback_score = 98.5
        fallback_cat = "URGENT"
        reply_hi = f"नमस्ते {senior_name} जी, आपके सीने में दर्द की जानकारी तुरंत आपकी केयर कोऑर्डिनेटर अनिता जी को भेज दी गई है। कृपया शांत बैठकर आराम करें, हम आपसे तुरंत संपर्क कर रहे हैं।"
        cues_list = [
            {"cue_type": "chest_pain", "confidence": 0.99, "is_negated": False, "evidence_span": "seene me dard"},
        ]
        if has_insomnia:
            cues_list.append({"cue_type": "sleep_deterioration", "confidence": 0.94, "is_negated": False, "evidence_span": "neend kam aayi"})
        summary_en = "CRITICAL: Acute chest pain reported with insomnia. Emergency alert fired."
        summary_hi = "अति-गंभीर: सीने में दर्द और अनिद्रा की शिकायत। इमरजेंसी अलर्ट जारी।"
    elif has_breathlessness:
        fallback_score = 92.5
        fallback_cat = "URGENT"
        reply_hi = f"नमस्ते {senior_name} जी, सांस लेने में तकलीफ की सूचना दर्ज कर ली गई है। अनिता जी आपकी सहायता के लिए तैयार हैं।"
        cues_list = [{"cue_type": "breathing_difficulty", "confidence": 0.96, "is_negated": False, "evidence_span": "saans me takleef"}]
        summary_en = "URGENT: Shortness of breath reported."
        summary_hi = "तत्काल: सांस लेने में तकलीफ दर्ज।"
    elif has_dizziness:
        fallback_score = 78.0
        fallback_cat = "URGENT"
        reply_hi = f"नमस्ते {senior_name} जी, चक्कर आने की बात हमने नोट की है। कृपया बैठ जाएं और पानी पिएं।"
        cues_list = [{"cue_type": "dizziness", "confidence": 0.91, "is_negated": False, "evidence_span": "chakkar"}]
        summary_en = "HIGH RISK: Dizziness / postural instability reported."
        summary_hi = "उच्च जोखिम: चक्कर आने की रिपोर्ट।"
    elif has_healthy:
        fallback_score = 15.0
        fallback_cat = "LOW"
        reply_hi = f"नमस्ते {senior_name} जी, यह जानकर बहुत खुशी हुई कि आप स्वस्थ हैं और दवा समय पर ले ली है।"
        cues_list = []
        summary_en = "Normal healthy routine reported. Medication confirmed."
        summary_hi = "सामान्य स्वास्थ्य दिनचर्या। दवा समय पर ली।"
    else:
        fallback_score = 55.0
        fallback_cat = "HIGH"
        reply_hi = f"नमस्ते {senior_name} जी, आपकी जानकारी दर्ज हो गई है।"
        cues_list = local_cues
        summary_en = f"Check-in noted: {cleaned_text}"
        summary_hi = f"जांच दर्ज: {cleaned_text}"

    return {
        "source": "local-doctor-nlp",
        "transcript": cleaned_text,
        "urgency_level": "CRITICAL" if fallback_score >= 95.0 else ("URGENT" if fallback_score >= 75.0 else "LOW"),
        "calculated_risk_score": fallback_score,
        "risk_category": fallback_cat,
        "summary_en": summary_en,
        "summary_hi": summary_hi,
        "cues": cues_list,
        "doctor_reply_hindi": clean_hindi_speech_text(reply_hi)
    }


def transcribe_and_analyze_audio(
    audio_bytes: Optional[bytes] = None,
    mime_type: str = "audio/webm",
    client_transcript: Optional[str] = None,
    senior_name: str = "Senior Citizen",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transcribes and clinically analyzes senior voice audio.
    If audio_bytes are provided, attempts Gemini multimodal transcription,
    otherwise uses the client_transcript from Web Speech API and performs clinical doctor triage.
    """
    final_text = (client_transcript or "").strip()

    # Try Gemini Multimodal STT if audio bytes available
    if audio_bytes and len(audio_bytes) > 200:
        try:
            b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
            stt_prompt = """
Listen to this audio recording of an elderly Indian senior speaking in Hindi or English.
1. Transcribe the spoken words accurately into Hindi (Devanagari script) or English.
2. Return JSON: {"transcript_hindi": "..."}
"""
            audio_part = {
                "inline_data": {
                    "mime_type": mime_type,
                    "data": b64_audio
                }
            }
            res = call_gemini_api(stt_prompt, response_json=True, audio_parts=[audio_part])
            if res:
                parsed = json.loads(res)
                if parsed.get("transcript_hindi"):
                    final_text = parsed["transcript_hindi"].strip()
        except Exception as err:
            logger.warning(f"Gemini audio transcription fallback to client STT: {err}")

    if not final_text:
        final_text = "आज स्वास्थ्य दिनचर्या की जांच की गई।"

    # Perform Doctor Triage on the transcript
    triage = doctor_triage_analysis(final_text, senior_name)
    triage["transcript_hindi"] = final_text
    return triage


def continuous_conversational_agent_turn(
    senior_name: str,
    conversation_history: List[Dict[str, str]],
    senior_input: str,
    turn_index: int = 0
) -> Dict[str, Any]:
    """
    Continuous, natural Speech-to-Speech doctor & care companion.
    Keeps conversing naturally turn after turn without stopping at 3 questions.
    Cleans text of any '?' so Web Speech API never says 'question mark'.
    """
    cleaned_input = (senior_input or "").strip()
    
    # Analyze the input medically
    triage = doctor_triage_analysis(cleaned_input, senior_name)

    # If first turn (initial greeting)
    if turn_index == 0 and not cleaned_input:
        greeting = f"नमस्ते {senior_name} जी! मैं साथी केयर से आपका एआई स्वास्थ्य साथी बोल रहा हूँ। आज आपकी तबीयत कैसी महसूस हो रही है?"
        return {
            "turn_index": 0,
            "agent_speech_hi": clean_hindi_speech_text(greeting),
            "next_turn_index": 1,
            "is_complete": False,
            "triage": triage
        }

    # Prompt Gemini for dynamic conversational response
    history_snippet = "\n".join([f"{m.get('sender')}: {m.get('text')}" for m in conversation_history[-4:]])
    prompt = f"""
You are Saathi, a caring, respectful, conversational AI Geriatric Care Companion & Family Doctor speaking with an elderly Indian citizen named {senior_name} Ji.
Tone: Warm, comforting, patient, respectful (pure spoken Hindi with 'आप', 'जी', 'दादाजी').
Recent Conversation History:
{history_snippet}
Senior's Latest Words: "{cleaned_input}"

Instructions:
1. Address what the senior just said directly and compassionately in 1-2 short sentences.
2. If the senior reports severe pain (like chest pain / seene me dard) or breathlessness, show sincere medical concern, tell them not to exert, reassure them that coordinator Anvesha Sharma is alerted right now, and ask a gentle clarifying question in natural Hindi.
3. If they took their medicine or feel okay, express happiness and ask naturally about their meals, hydration, or sleep.
4. Keep the conversation going! Do NOT say goodbye unless the senior explicitly says "bye" or "alvida".
5. CRITICAL: Do NOT use any question mark '?' characters anywhere in your response. End sentences with '।' or commas so the voice speech synthesizer sounds natural and does NOT say "question mark" aloud.

Return ONLY the Hindi text to be spoken out loud by Text-to-Speech. No English, no markdown asterisks, no quotes, no question marks.
"""

    gemini_reply = call_gemini_api(prompt, response_json=False)
    if gemini_reply:
        spoken_reply = clean_hindi_speech_text(gemini_reply)
    else:
        spoken_reply = clean_hindi_speech_text(triage.get("doctor_reply_hindi", f"जी {senior_name} जी, मैंने नोट कर लिया है। क्या आपने दोपहर का खाना खाया।"))

    return {
        "turn_index": turn_index,
        "agent_speech_hi": spoken_reply,
        "next_turn_index": turn_index + 1,
        "is_complete": False,
        "triage": triage
    }


def generate_conversational_voice_turn(
    senior_name: str,
    turn_index: int = 0,
    user_speech_text: Optional[str] = None,
    api_key: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """Compatibility wrapper for conversational turns."""
    return continuous_conversational_agent_turn(
        senior_name=senior_name,
        conversation_history=conversation_history or [],
        senior_input=user_speech_text or "",
        turn_index=turn_index
    )
