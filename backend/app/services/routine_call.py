"""Sahara AI Dynamic Two-Way Conversational Engine.
Powered by Google Gemini 3.5 Flash-Lite & Sarvam AI Bulbul (Priya Voice).
Provides real natural dialogue, dynamic Q&A, and acute geriatric emergency detection.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List

from app.services.gemini import call_gemini_api, clean_hindi_speech_text
from app.services.sarvam import synthesize_speech_sarvam

logger = logging.getLogger(__name__)

# Core Emergency Keywords for Immediate Local Fallback Detection
EMERGENCY_KEYWORDS = [
    "सीने में दर्द", "छाती में दर्द", "दर्द बहुत तेज", "सांस फूल", "सांस नहीं आ रही",
    "चक्कर आ रहे हैं", "बेहोश", "गिर गया", "गिर गई", "खून आ रहा", "बहुत घबराहट",
    "बुखार", "पेट में दर्द", "पेट दर्द", "bukhar", "fever", "pet dard",
    "chhati me dard", "chest pain", "breathless", "gir gaya", "chakkar"
]


def check_emergency_symptoms(text: str) -> bool:
    """Quick scan for acute emergency keywords to prioritize response."""
    if not text:
        return False
    lower = text.lower()
    return any(k in lower for k in EMERGENCY_KEYWORDS)


def generate_gemini_conversational_turn(
    senior_name: str,
    coordinator_name: str,
    family_name: str,
    user_reply: str,
    dialogue_history: List[Dict[str, str]],
    step_index: int
) -> Dict[str, Any]:
    """
    Calls Gemini 3.5 Flash-Lite to produce a natural, empathetic, logical Hindi response.
    Understands questions asked by the senior and answers them accurately.
    Detects severe health emergencies and flags them instantly.
    """
    senior_short = senior_name.split()[0] if senior_name else "हर्षित"
    coord_short = coordinator_name.split()[0] if coordinator_name else "अन्वेषा"
    family_short = family_name.split()[0] if family_name else "आँचल"

    history_formatted = "\n".join(
        [f"{m.get('sender', 'user')}: {m.get('text', '')}" for m in dialogue_history[-6:]]
    )

    prompt = f"""
You are Sahara AI (सहारा AI), an empathetic, intelligent Indian geriatric care voice assistant speaking directly with {senior_name} (72 years old, male, lives in Indore).
You work closely with Care Coordinator {coordinator_name} (Phone: 8267069623) and his mother/family {family_name} (Phone: 8957266841).
Senior's Prescribed Medications: Telmisartan 40mg (Morning for BP), Metformin 500mg (1:30 PM Afternoon after lunch for Sugar).

Recent Conversation History:
{history_formatted}

Senior Citizen just spoke:
"{user_reply}"

Turn/Step Number: {step_index}

INSTRUCTIONS:
1. ALWAYS LOGICALLY ACKNOWLEDGE AND ANSWER whatever the senior just said or asked!
   - If the senior asks a question (e.g. who are you, what medicines I take, when is coordinator coming, what is the weather, why are you calling, etc.), ANSWER IT DIRECTLY and warmly!
   - Never give a canned scripted response or ignore what he said.
2. CONVERSATIONAL TONE:
   - Speak in natural, respectful, warm Hindi (देसी और विनम्र बोलचाल, जैसे "जी हर्षित जी...", "हाँ दादाजी...").
   - Length: Strictly 1 to 2 short sentences (maximum 25-30 words). Keep it brisk for voice playback!
   - Do NOT use technical jargon or English letters in the reply text. Pure Devanagari Hindi.
3. HEALTH CHECKFLOW:
   - If the senior just answered a greeting or general remark, naturally inquire about their health, whether they took their 1:30 PM medicine, had their meal, or slept well.
4. EMERGENCY DETECTION:
   - If the senior reports severe chest pain, shortness of breath, severe fall, paralysis, or acute distress, set "is_emergency": true.
   - For emergencies, immediately comfort them: "हर्षित जी, आप घबराइए मत, मैंने तुरंत अन्वेषा दीदी और आँचल जी को आपातकालीन सूचना भेज दी है। आप आराम से बैठिए।"
5. GOODBYE DETECTION:
   - If the senior says goodbye, thanks, or wants to hang up ("ठीक है", "धन्यवाद", "बाय", "फ़ोन रखता हूँ"), set "is_complete": true and give a warm closing blessing.

Return strictly a valid JSON object matching this schema:
{{
  "reply": "Short, warm Hindi response in Devanagari",
  "is_emergency": false,
  "emergency_reason": null,
  "is_complete": false,
  "symptoms_noted": []
}}
"""

    try:
        raw_json = call_gemini_api(prompt, response_json=True, timeout=2.0)
        if raw_json:
            parsed = json.loads(raw_json)
            reply = clean_hindi_speech_text(parsed.get("reply", ""))
            if reply:
                return {
                    "reply": reply,
                    "is_emergency": bool(parsed.get("is_emergency", False)),
                    "emergency_reason": parsed.get("emergency_reason"),
                    "is_complete": False,  # Never auto-cut call
                    "symptoms_noted": parsed.get("symptoms_noted", [])
                }
    except Exception as e:
        logger.warning(f"Gemini conversational turn notice: {e}")

    # High-quality intelligent local fallback (< 5ms response time)
    reply_clean = user_reply.strip().lower()
    is_emerg = check_emergency_symptoms(reply_clean)
    if is_emerg:
        return {
            "reply": f"हर्षित जी, आप बिल्कुल घबराइए मत। मैंने तुरंत अन्वेषा दीदी और आँचल जी को सूचित कर दिया है। आप आराम से बैठिए और बताइए अभी कैसा लग रहा है?",
            "is_emergency": True,
            "emergency_reason": f"Acute distress verbalized: {user_reply[:50]}",
            "is_complete": False,  # Never auto-cut call
            "symptoms_noted": ["acute_chest_or_pain"]
        }

    if any(q in reply_clean for q in ["दवाई", "दवा", "tablet", "medicine"]):
        return {
            "reply": f"जी हर्षित जी, आपकी दोपहर 1:30 बजे की दवाई मेटफ़ॉर्मिन 500 एमजी है। क्या आपने दोपहर का खाना खाकर दवाई ले ली है?",
            "is_emergency": False,
            "emergency_reason": None,
            "is_complete": False,
            "symptoms_noted": []
        }

    if any(gb in reply_clean for gb in ["बाय", "धन्यवाद", "अलविदा", "रखता", "कॉल काटो", "ठीक है बस"]):
        return {
            "reply": f"बहुत धन्यवाद हर्षित जी! मैंने आपकी सारी बातें नोट करके अन्वेषा दीदी को भेज दी हैं। आप अपना पूरा ध्यान रखिएगा।",
            "is_emergency": False,
            "emergency_reason": None,
            "is_complete": False,  # Never auto-cut call
            "symptoms_noted": []
        }

    # Contextual progression fallback
    if step_index <= 1:
        fallback_reply = f"जी बहुत अच्छा लगा सुनकर। क्या आपने आज दोपहर का खाना और 1:30 बजे वाली दवाई समय पर ले ली?"
    elif step_index == 2:
        fallback_reply = f"जी बिल्कुल। शरीर में कहीं कोई दर्द, चक्कर या कमज़ोरी तो महसूस नहीं हो रही आज?"
    else:
        fallback_reply = f"जी समझ गई। और कोई बात जो आप अन्वेषा दीदी या परिवार को बताना चाहते हों?"

    return {
        "reply": fallback_reply,
        "is_emergency": False,
        "emergency_reason": None,
        "is_complete": False,
        "symptoms_noted": []
    }


def get_routine_call_step(
    senior_name: str,
    coordinator_name: str,
    step_index: int,
    user_reply: Optional[str] = None,
    dtmf_digit: Optional[str] = None,
    accumulated_data: Optional[Dict[str, Any]] = None,
    family_name: str = "आँचल मिश्रा"
) -> Dict[str, Any]:
    """
    Two-way dialogue engine for Sahara AI.
    Every answer is analyzed by Gemini 3.5 Flash-Lite and voiced via Sarvam Priya with pace=1.1.
    """
    accumulated = accumulated_data or {}
    senior_short = senior_name.split()[0] if senior_name else "हर्षित"
    coord_short = coordinator_name.split()[0] if coordinator_name else "अन्वेषा"

    reply_clean = (user_reply or "").strip()
    dtmf = (dtmf_digit or "").strip()

    dialogue = accumulated.setdefault("dialogue", [])

    # STEP 0: Initial Greeting and first question
    if step_index == 0 and not reply_clean:
        greeting_text = f"नमस्ते {senior_short} जी! मैं सहारा AI बोल रही हूँ, {coord_short} दीदी की तरफ़ से। मैं आपकी रोज़ाना सेहत का हालचाल लेने आई हूँ। आज आप कैसा महसूस कर रहे हैं?"
        dialogue.append({"sender": "ai", "text": greeting_text})
        
        # Synthesize with natural, normal warm pace 1.0
        sarvam_audio = synthesize_speech_sarvam(greeting_text, speaker="priya", pace=1.0)
        return {
            "step_index": 0,
            "next_step_index": 1,
            "agent_question": greeting_text,
            "audio_url": sarvam_audio.get("audio_url") if sarvam_audio else None,
            "audio_base64": sarvam_audio.get("audio_base64") if sarvam_audio else None,
            "is_emergency": False,
            "is_complete": False,
            "accumulated": accumulated
        }

    # Record senior's reply into history
    if reply_clean:
        dialogue.append({"sender": "senior", "text": reply_clean})

    # Call Gemini 3.5 Flash-Lite for natural two-way response
    gemini_result = generate_gemini_conversational_turn(
        senior_name=senior_name,
        coordinator_name=coordinator_name,
        family_name=family_name,
        user_reply=reply_clean,
        dialogue_history=dialogue,
        step_index=step_index
    )

    spoken_text = gemini_result["reply"]
    is_emergency = gemini_result["is_emergency"]
    is_complete = gemini_result["is_complete"]

    # Fast synthesis via Sarvam AI at natural pace 1.0 with 1.5s timeout cap to ensure instant response
    sarvam_audio = None
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(synthesize_speech_sarvam, spoken_text, "priya", 1.0)
        try:
            sarvam_audio = future.result(timeout=1.5)
        except concurrent.futures.TimeoutError:
            logger.info("Sarvam TTS exceeded 1.5s cap - browser will speak instantly without delay")
        except Exception as e:
            logger.warning(f"Sarvam audio notice: {e}")

    dialogue.append({"sender": "ai", "text": spoken_text})

    accumulated["last_spoken"] = spoken_text
    accumulated["is_emergency"] = is_emergency

    next_step = step_index + 1
    # Never forcefully cut the call! The senior citizen decides when to end the call.
    is_complete = False

    return {
        "step_index": step_index,
        "next_step_index": next_step,
        "agent_question": spoken_text,
        "audio_url": sarvam_audio.get("audio_url") if sarvam_audio else None,
        "audio_base64": sarvam_audio.get("audio_base64") if sarvam_audio else None,
        "is_emergency": is_emergency,
        "emergency_reason": gemini_result.get("emergency_reason"),
        "is_complete": is_complete,
        "accumulated": accumulated
    }
