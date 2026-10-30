"""Sahara 5-Question Daily Routine Call Engine.
Powered by Sarvam AI (Indic TTS Priya Voice & STT Saaras) + Google Gemini Clinical Triage.

Standard Daily Script:
1. "आज आप कैसा महसूस कर रहे हैं? अच्छा हो तो 1, ठीक-ठाक हो तो 2, अच्छा नहीं हो तो 3 दबाइए, या बोल दीजिए।"
2. "आज खाना खाया आपने? कितना खाया?"
3. "आज की दवाई ली?"
4. "कहीं दर्द, चक्कर या साँस में तकलीफ़ है आज?"
5. "और कुछ बताना चाहते हैं? जो भी मन में हो, बोल दीजिए।" (या rotating neend/akelapan सवाल)
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

from app.services.sarvam import synthesize_speech_sarvam
from app.services.gemini import doctor_triage_analysis, clean_hindi_speech_text, call_gemini_api
from app.services.nlp import extract_cues_from_note

logger = logging.getLogger(__name__)

ROTATING_QUESTIONS = [
    {"cue": "sleep", "question": "रात को नींद कैसी आई?"},
    {"cue": "loneliness", "question": "आज किसी से बात हुई, घर पर या फ़ोन पर?"},
    {"cue": "mobility", "question": "आज थोड़ा चले-फिरे या बाहर टहलने गए थे?"},
    {"cue": "hydration", "question": "पानी ठीक से पी रहे हैं ना दादाजी?"},
    {"cue": "general_change", "question": "कल से आज में तबीयत में कुछ बदला है?"}
]

EMERGENCY_KEYWORDS = [
    "सीने में दर्द", "seene me dard", "chest pain", "chhati me dard",
    "सांस नहीं आ रही", "saans nahi aa rahi", "saans phool", "breathless",
    "गिर गया", "gir gaya", "fall", "behoshi", "बेहोश",
    "बहुत चक्कर", "bahut chakkar", "chakkar aa rahe hain"
]


def check_emergency_symptoms(text: str) -> bool:
    """Checks if senior reported an acute emergency symptom."""
    lower = text.lower()
    for kw in EMERGENCY_KEYWORDS:
        if kw in lower and not ("dard nahi" in lower or "pain nahi" in lower):
            return True
    return False


def get_routine_call_step(
    senior_name: str,
    coordinator_name: str,
    step_index: int,
    user_reply: Optional[str] = None,
    dtmf_digit: Optional[str] = None,
    accumulated_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    State machine for Sahara 5-Question Routine Call.
    Generates exact Hindi question, parses answers (spoken or DTMF 1/2/3),
    applies conditional branching, and synthesizes audio via Sarvam Priya voice.
    """
    accumulated = accumulated_data or {}
    senior_short = senior_name.split()[0] if senior_name else "शर्मा"
    coord_short = coordinator_name.split()[0] if coordinator_name else "प्रिया"

    reply_clean = (user_reply or "").strip()
    dtmf = (dtmf_digit or "").strip()

    # STEP 0: Greeting with mandated AI assistant disclosure
    if step_index == 0:
        agent_text = f"नमस्ते {senior_short} जी, मैं सहारा AI बोल रही हूँ, {coord_short} दीदी की तरफ़ से। मैं एक कंप्यूटर असिस्टेंट हूँ। ये बातचीत रिकॉर्ड होगी और {coord_short} दीदी देखेंगी। आपसे बस दो-तीन छोटे सवाल पूछने हैं। बात कर सकते हैं?"
        sarvam_audio = synthesize_speech_sarvam(agent_text, speaker="priya")
        return {
            "step_index": 0,
            "next_step_index": 1,
            "agent_question": agent_text,
            "audio_url": sarvam_audio.get("audio_url") if sarvam_audio else None,
            "audio_base64": sarvam_audio.get("audio_base64") if sarvam_audio else None,
            "is_emergency": False,
            "is_complete": False,
            "accumulated": accumulated
        }

    # CHECK ACUTE EMERGENCY AT ANY STEP
    if reply_clean and check_emergency_symptoms(reply_clean):
        emergency_speech = f"दादाजी, मैं अभी {coord_short} दीदी को बता रही हूँ, आप कृपया शांत होकर बैठ जाइए और कोई घर में है तो उन्हें आवाज़ दे दीजिए।"
        sarvam_audio = synthesize_speech_sarvam(emergency_speech, speaker="priya")
        accumulated["emergency_flagged"] = True
        accumulated["last_reply"] = reply_clean
        return {
            "step_index": step_index,
            "next_step_index": 999,
            "agent_question": emergency_speech,
            "audio_url": sarvam_audio.get("audio_url") if sarvam_audio else None,
            "audio_base64": sarvam_audio.get("audio_base64") if sarvam_audio else None,
            "is_emergency": True,
            "is_complete": True,
            "accumulated": accumulated
        }

    # Track dialogue history
    dialogue = accumulated.setdefault("dialogue", [])
    if reply_clean:
        dialogue.append({"sender": "senior", "text": reply_clean})

    # Check for natural call conclusion or all 5 questions answered
    is_goodbye = any(gb in reply_clean.lower() for gb in ["बाय", "अलविदा", "रखता हूँ", "रखती हूँ", "बस इतना ही", "ठीक है धन्यवाद", "कॉल काटो"])
    if is_goodbye or step_index >= 6:
        closing = f"बहुत धन्यवाद {senior_short} जी! आपकी सारी बातें मैंने नोट कर ली हैं और {coord_short} दीदी को भेज दी हैं। आप अपना पूरा ध्यान रखिएगा!"
        closing = clean_hindi_speech_text(closing)
        sarvam_audio = synthesize_speech_sarvam(closing, speaker="priya")
        dialogue.append({"sender": "ai", "text": closing})
        return {
            "step_index": step_index,
            "next_step_index": step_index + 1,
            "agent_question": closing,
            "audio_url": sarvam_audio.get("audio_url") if sarvam_audio else None,
            "audio_base64": sarvam_audio.get("audio_base64") if sarvam_audio else None,
            "is_emergency": False,
            "is_complete": True,
            "accumulated": accumulated
        }

    # Deterministic step mapping with Gemini natural conversational Hindi adaptation
    # Step 1: Mood/Sehat scale
    # Step 2: Meal / appetite
    # Step 3: Medicine adherence
    # Step 4: Symptoms (Pain, dizziness, breathlessness)
    # Step 5: Open reflection / Sleep
    step_targets = {
        1: {
            "goal": "Mood and health baseline (1=अच्छा, 2=ठीक-ठाक, 3=अच्छा नहीं)",
            "standard_question": "आज आप कैसा महसूस कर रहे हैं? अच्छा हो तो 1, ठीक-ठाक हो तो 2, अच्छा नहीं हो तो 3 दबाइए, या बोल दीजिए।"
        },
        2: {
            "goal": "Meals and appetite (खाना खाया या नहीं, कितना खाया)",
            "standard_question": "आज खाना खाया आपने? कितना खाया?"
        },
        3: {
            "goal": "Medicine adherence (आज की दवाई ली या नहीं)",
            "standard_question": "आज की दवाई ली आपने?"
        },
        4: {
            "goal": "Symptoms (कहीं दर्द, चक्कर या साँस में तकलीफ़ तो नहीं)",
            "standard_question": "कहीं दर्द, चक्कर या साँस में तकलीफ़ है आज?"
        },
        5: {
            "goal": "Open wellbeing check / sleep (रात को नींद कैसी आई, या मन की कोई बात)",
            "standard_question": "और कुछ बताना चाहते हैं? जो भी मन में हो, बोल दीजिए, या रात को नींद कैसी आई?"
        }
    }

    current_target = step_targets.get(step_index, step_targets[5])

    # Check for conditional branching
    followup_override = None
    if step_index == 2: # Senior just answered Step 1
        if dtmf == "3" or any(w in reply_clean.lower() for w in ["अच्छा नहीं", "तबीयत खराब", "बुरा", "दर्द", "तकलीफ", "3"]):
            followup_override = f"क्या तकलीफ़ है दादाजी? बता दीजिए, मैं {coord_short} दीदी को बता दूँगी।"
            accumulated["mood_scale"] = 3
        elif dtmf == "1" or "अच्छा" in reply_clean.lower():
            accumulated["mood_scale"] = 1
        else:
            accumulated["mood_scale"] = 2
    elif step_index == 4: # Senior just answered Step 3 (medicine)
        if any(w in reply_clean.lower() for w in ["नहीं", "nahi", "भूल", "bhool", "छूट"]):
            followup_override = "कोई वजह थी? भूल गए या दवाई ख़त्म हो गई?"
            accumulated["took_medicine"] = False
        else:
            accumulated["took_medicine"] = True
    elif step_index == 5: # Senior just answered Step 4 (symptoms)
        is_negated = any(neg in reply_clean.lower() for neg in ["नहीं", "nahi", "no", "kuch nahi", "sab theek", "koi nahi", "kuchh nahi"])
        has_symptom = any(w in reply_clean.lower() for w in ["हाँ", "haan", "दर्द", "चक्कर", "तकलीफ", "सांस"])
        if has_symptom and not is_negated:
            followup_override = "कहाँ और कब से तकलीफ़ है? एक बार बता दीजिए।"
            accumulated["symptoms_reported"] = reply_clean
        else:
            accumulated["symptoms_reported"] = "कोई तकलीफ़ नहीं"

    history_lines = [f"{m.get('sender')}: {m.get('text')}" for m in dialogue[-6:]]
    history_context = "\n".join(history_lines)

    spoken_text = None
    if followup_override:
        spoken_text = followup_override
    else:
        # Ask Gemini ONLY for a warm, gentle 3-5 word Hindi acknowledgment of the senior's reply
        ack_prompt = f"""
Senior ({senior_short} Ji) just said: "{reply_clean}" (DTMF: {dtmf or 'none'}).
Care Coordinator: {coord_short} Didi.

Generate a warm, brief Hindi acknowledgment in 3 to 6 words in Devanagari script (e.g. 'जी बहुत अच्छा लगा सुनकर', 'जी दादाजी, बिल्कुल ठीक', 'सुनकर तसल्ली मिली').
Language: Pure Devanagari Hindi only. Do NOT use Urdu script, Nastaliq, or English.
Never ask a question. Never use question marks. Only the short Hindi acknowledgment phrase.
"""
        ack = ""
        try:
            gemini_ack = call_gemini_api(ack_prompt, response_json=False, timeout=5)
            if gemini_ack and len(gemini_ack.strip()) > 2 and "?" not in gemini_ack:
                ack = clean_hindi_speech_text(gemini_ack.strip().split("\n")[0])
        except Exception as e:
            logger.warning(f"Gemini ack fallback: {e}")

        std_q = current_target["standard_question"]
        if ack:
            spoken_text = f"{ack}। {std_q}"
        else:
            spoken_text = std_q

    spoken_text = clean_hindi_speech_text(spoken_text)
    sarvam_audio = synthesize_speech_sarvam(spoken_text, speaker="priya")
    dialogue.append({"sender": "ai", "text": spoken_text})

    return {
        "step_index": step_index,
        "next_step_index": step_index + 1,
        "agent_question": spoken_text,
        "audio_url": sarvam_audio.get("audio_url") if sarvam_audio else None,
        "audio_base64": sarvam_audio.get("audio_base64") if sarvam_audio else None,
        "is_emergency": False,
        "is_complete": False,
        "accumulated": accumulated
    }

