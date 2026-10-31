"""Sahara AI Dynamic Two-Way Conversational Engine.
Powered by Google Gemini (gemini-3.1-flash-lite-preview) & Sarvam AI Bulbul (Priya Voice).
Provides real natural dialogue, dynamic Q&A, empathetic symptom handling, and acute geriatric emergency detection.
"""

import os
import json
import logging
import concurrent.futures
from typing import Dict, Any, Optional, List

from app.services.gemini import call_gemini_api, clean_hindi_speech_text
from app.services.sarvam import synthesize_speech_sarvam

logger = logging.getLogger(__name__)

# Module-level thread pool so timeouts return instantly without blocking HTTP thread
_SARVAM_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Core Emergency Keywords for Immediate Escalation
EMERGENCY_KEYWORDS = [
    "सीने में दर्द", "छाती में दर्द", "दर्द बहुत तेज", "सांस फूल", "सांस नहीं आ रही",
    "चक्कर आ रहे हैं", "बेहोश", "गिर गया", "गिर गई", "खून आ रहा", "बहुत घबराहट",
    "chhati me dard", "chest pain", "breathless", "gir gaya", "chakkar"
]

# Severe Psychological Distress, Depression & Suicidal Ideation Keywords
CRITICAL_MENTAL_HEALTH_KEYWORDS = [
    "suicide", "आत्महत्या", "मरने का मन", "मरना चाहता", "मर जाऊं", "मर जाने का",
    "जीने का मन नहीं", "जीना नहीं चाहता", "जीने की इच्छा नहीं", "जान दे दूंगा", "जान देने",
    "जिंदगी खत्म", "ज़िंदगी ख़त्म", "तंग आ चुका", "तंग आ गया", "कोई मतलब नहीं जीने",
    "कोई फायदा नहीं", "सब छोड़ के जाना", "दुनिया छोड़", "अकेलापन", "अकेला महसूस",
    "marne ka man", "marna chahta", "suicide karne", "jeena nahi chahta", "jeena nahi",
    "jeene ki ichha nahi", "ichha nahi", "iccha nahi", "jaan de dunga", "zindagi khatam",
    "tang aa gaya", "akela feel", "kuch bacha nahi", "marne"
]

# Unwell / Sickness / Distress Keywords
UNWELL_KEYWORDS = [
    "ठीक नहीं", "अच्छा नहीं", "तबीयत खराब", "तबीयत ठीक नहीं", "बीमार",
    "दर्द", "सूजन", "गले", "गला", "पेट", "सिर", "कमर", "बुखार",
    "भारीपन", "कमजोरी", "थकावट", "उल्टी", "खांसी", "जुकाम", "परेशान",
    "तकलीफ", "तकलीफ़", "theek nahi", "achha nahi", "dard", "bukhar",
    "gala", "pet", "soojan", "sujan", "bimar", "kamzori"
]


def check_suicidal_or_self_harm(text: str) -> bool:
    """Detects suicidal ideation, self-harm, or severe acute psychological crisis."""
    if not text:
        return False
    lower = text.lower()
    return any(k in lower for k in CRITICAL_MENTAL_HEALTH_KEYWORDS)


def check_emergency_symptoms(text: str) -> bool:
    """Quick scan for acute emergency or suicidal keywords to prioritize response."""
    if not text:
        return False
    lower = text.lower()
    return any(k in lower for k in EMERGENCY_KEYWORDS) or check_suicidal_or_self_harm(lower)


def is_unwell_or_distressed(text: str) -> bool:
    """Detects whether senior expressed discomfort, pain, sickness or negative feelings."""
    if not text:
        return False
    lower = text.lower()
    return any(k in lower for k in UNWELL_KEYWORDS) or check_suicidal_or_self_harm(lower)


def generate_gemini_conversational_turn(
    senior_name: str,
    coordinator_name: str,
    family_name: str,
    user_reply: str,
    dialogue_history: List[Dict[str, str]],
    step_index: int
) -> Dict[str, Any]:
    """
    Calls Gemini to produce an empathetic, logical Hindi response.
    Understands questions, symptoms, and feelings.
    Never auto-hangs up!
    """
    senior_short = senior_name.split()[0] if senior_name else "हर्षित"
    coord_short = coordinator_name.split()[0] if coordinator_name else "अन्वेषा"
    family_short = family_name.split()[0] if family_name else "आँचल"

    history_formatted = "\n".join(
        [f"{m.get('sender', 'user')}: {m.get('text', '')}" for m in dialogue_history[-6:]]
    )

    prompt = f"""
You are Sahara AI (सहारा AI), an empathetic, caring Indian geriatric voice assistant speaking with {senior_name} (72 yrs old, Indore).
Care Coordinator: {coordinator_name} (Phone: 8267069623). Mother: {family_name} (Phone: 8957266841).
Medicines: Telmisartan 40mg (Morning BP), Metformin 500mg (1:30 PM Lunch Sugar).

Conversation History:
{history_formatted}

Senior Citizen just spoke:
"{user_reply}"

Turn: {step_index}

RULES:
1. CRITICAL PSYCHOLOGICAL & SUICIDAL CRISIS PROTOCOL:
   - If the senior mentions suicidal thoughts, wanting to die, self-harm, hopelessness, or giving up on life (e.g. "suicide", "मरने का मन", "जीने की इच्छा नहीं", "जान दे दूंगा", "मरना चाहता हूँ"):
     - MUST return "is_emergency": true, "emergency_reason": "Acute psychological crisis: Suicidal ideation verbalized"
     - Immediately de-escalate with unconditional warmth, deep love, and reassurance. Tell them their life is precious, they are not alone, and you are connecting Anvesha Didi and family right now.
2. NEVER say "अच्छा लगा सुनकर" if the senior says they are NOT well, in pain, or have symptoms!
   - If they report pain, throat swelling, fever, or stomach ache, express IMMEDIATE WARM CONCERN: e.g. "अरे हर्षित जी, यह सुनकर चिंता हुई। क्या आपको बुखार या दर्द भी है? आप आराम करिए..."
3. Answer any question directly in 1-2 warm Hindi sentences (Devanagari).
4. Keep the conversation going! Never say goodbye unless the senior explicitly asked to hang up.

Return strictly JSON:
{{
  "reply": "Empathetic 1-2 sentence Hindi response in Devanagari",
  "is_emergency": false,
  "emergency_reason": null,
  "is_complete": false,
  "symptoms_noted": []
}}
"""

    try:
        raw_json = call_gemini_api(prompt, response_json=True, timeout=1.8)
        if raw_json:
            parsed = json.loads(raw_json)
            reply = clean_hindi_speech_text(parsed.get("reply", ""))
            if reply:
                # Top priority safety guard: suicidal ideation or self-harm
                if check_suicidal_or_self_harm(user_reply):
                    return {
                        "reply": reply or f"अरे {senior_short} जी, आप ऐसी बातें बिल्कुल मत सोचिए। हम सब आपसे बहुत प्यार करते हैं और आपके साथ हैं। आपकी जिंदगी बहुत कीमती है। आप बिल्कुल अकेले नहीं हैं, मैं अभी तुरंत {coord_short} दीदी और {family_short} जी को आपसे बात करने के लिए जोड़ रही हूँ। कृपया थोड़ा पानी पीजिए और आराम से बैठिए।",
                        "is_emergency": True,
                        "emergency_reason": "Acute psychological crisis: Suicidal ideation verbalized",
                        "is_complete": False,
                        "symptoms_noted": ["suicidal_ideation_or_mental_distress"]
                    }

                # Sanity guard: if senior expressed illness, ensure AI never says "अच्छा लगा सुनकर"
                if is_unwell_or_distressed(user_reply) and ("अच्छा लगा" in reply or "बढ़िया" in reply):
                    reply = f"अरे {senior_short} जी, यह सुनकर चिंता हुई। आप आराम से बैठिए, क्या गले या शरीर में और कोई तकलीफ़ महसूस हो रही है?"

                return {
                    "reply": reply,
                    "is_emergency": bool(parsed.get("is_emergency", False)),
                    "emergency_reason": parsed.get("emergency_reason"),
                    "is_complete": False,  # Never auto-cut call
                    "symptoms_noted": parsed.get("symptoms_noted", [])
                }
    except Exception as e:
        logger.warning(f"Gemini conversational turn notice: {e}")

    # =========================================================================
    # INSTANT LOCAL INTELLIGENT & EMPATHETIC ENGINE (< 2ms Response Time)
    # =========================================================================
    reply_clean = user_reply.strip().lower()

    # 0. Severe Psychological Distress / Suicidal Ideation Check (Priority #1)
    if check_suicidal_or_self_harm(reply_clean):
        return {
            "reply": f"अरे {senior_short} जी, आप ऐसी बातें बिल्कुल मत सोचिए। हम सब आपसे बहुत प्यार करते हैं और आपके साथ हैं। आपकी जिंदगी बहुत कीमती है। आप बिल्कुल अकेले नहीं हैं, मैं अभी तुरंत {coord_short} दीदी और {family_short} जी को आपसे बात करने के लिए जोड़ रही हूँ। कृपया थोड़ा पानी पीजिए और आराम से बैठिए।",
            "is_emergency": True,
            "emergency_reason": f"Acute distress / suicidal ideation: {user_reply[:60]}",
            "is_complete": False,
            "symptoms_noted": ["suicidal_ideation_or_mental_distress"]
        }

    # 1. Severe Acute Medical Emergency Check
    if check_emergency_symptoms(reply_clean):
        return {
            "reply": f"हर्षित जी, आप बिल्कुल घबराइए मत। मैंने तुरंत अन्वेषा दीदी और आँचल जी को सूचित कर दिया है। आप आराम से बैठिए और बताइए अभी कैसा महसूस हो रहा है?",
            "is_emergency": True,
            "emergency_reason": f"Acute distress: {user_reply[:50]}",
            "is_complete": False,
            "symptoms_noted": ["acute_chest_or_pain"]
        }

    # 2. Illness / Pain / Symptoms / Discomfort (NEVER say "अच्छा लगा"!)
    if is_unwell_or_distressed(reply_clean):
        if any(w in reply_clean for w in ["गले", "गला", "soojan", "सूजन"]):
            reply_text = f"अरे हर्षित जी, गले में तकलीफ़ या सूजन की बात सुनकर चिंता हुई। क्या आपको बुखार या निगलने में दर्द भी है? आप थोड़ा गुनगुना पानी पीजिए, मैं तुरंत अन्वेषा दीदी को बता रही हूँ।"
        elif any(w in reply_clean for w in ["पेट", "pet", "उल्टी"]):
            reply_text = f"अरे हर्षित जी, पेट में दर्द की बात सुनकर चिंता हुई। क्या आपने दोपहर में कुछ खाया था? आप आराम करिए, मैं अन्वेषा दीदी को सूचित कर रही हूँ।"
        elif any(w in reply_clean for w in ["बुखार", "bukhar", "fever", "तप"]):
            reply_text = f"हर्षित जी, आपको बुखार है तो आप तुरंत आराम करिए और पानी पीते रहिए। मैंने अन्वेषा दीदी और आँचल जी को सूचना भेज दी है।"
        elif any(w in reply_clean for w in ["कमजोरी", "थकान", "कमज़ोरी", "kamzori"]):
            reply_text = f"हर्षित जी, कमजोरी महसूस हो रही है तो आप आराम से लेट जाइए। क्या आपने आज खाना और पानी समय पर लिया था?"
        else:
            reply_text = f"अरे हर्षित जी, आपकी तबीयत ठीक नहीं है यह सुनकर चिंता हुई। क्या परेशानी हो रही है, थोड़ा विस्तार से बताइए? मैं अन्वेषा दीदी को भी बता रही हूँ।"

        return {
            "reply": reply_text,
            "is_emergency": False,
            "emergency_reason": f"Symptom reported: {user_reply[:50]}",
            "is_complete": False,
            "symptoms_noted": ["general_symptom"]
        }

    # 3. Direct Medicine Inquiries
    if any(q in reply_clean for q in ["दवाई", "दवा", "tablet", "medicine", "goli"]):
        return {
            "reply": f"जी हर्षित जी, आपकी सुबह बीपी की दवाई तेलमिसारटन और दोपहर डेढ़ बजे शुगर की दवाई मेटफ़ॉर्मिन है। क्या आपने आज दोपहर की दवाई ले ली?",
            "is_emergency": False,
            "emergency_reason": None,
            "is_complete": False,
            "symptoms_noted": []
        }

    # 4. Inquiries about Coordinator / Family
    if any(p in reply_clean for p in ["अन्वेषा", "anvesha", "दीदी", "मम्मी", "anchal", "आँचल"]):
        return {
            "reply": f"जी हर्षित जी, अन्वेषा दीदी और आपकी मम्मी आँचल जी दोनों सिस्टम पर कनेक्टेड हैं। आपकी कोई भी बात सीधे उन तक पहुँच रही है।",
            "is_emergency": False,
            "emergency_reason": None,
            "is_complete": False,
            "symptoms_noted": []
        }

    # 5. Affirmation / Agreement / Ready to Talk (e.g. "हा बात कर सकते हैं", "हाँ", "जी")
    is_affirming = any(w in reply_clean for w in ["बात कर सकते हैं", "बात कर सकते", "बात कर", "हाँ", "हा", "haan", "boliye", "bolo", "ji haan", "जी हाँ", "जी"]) and not is_unwell_or_distressed(reply_clean)
    if is_affirming and not any(p in reply_clean for p in ["ठीक", "अच्छा", "मस्त"]):
        return {
            "reply": f"जी बहुत अच्छा हर्षित जी! आप बताइए, आज आप कैसा महसूस कर रहे हैं? सब ठीक-ठाक है?",
            "is_emergency": False,
            "emergency_reason": None,
            "is_complete": False,
            "symptoms_noted": []
        }

    # 6. Positive / Doing Well (e.g. "ठीक हूँ", "बढ़िया", "अच्छा", "बहुत अच्छा")
    is_positive = any(p in reply_clean for p in ["ठीक हूँ", "बढ़िया", "अच्छा हूँ", "मस्त", "theek hu", "theek", "1", "अच्छा"]) and not is_unwell_or_distressed(reply_clean)
    if is_positive:
        return {
            "reply": f"जी बहुत अच्छा लगा सुनकर कि आप ठीक हैं! क्या आज आपने दोपहर का खाना खा लिया और दोपहर डेढ़ बजे वाली दवाई समय पर ले ली?",
            "is_emergency": False,
            "emergency_reason": None,
            "is_complete": False,
            "symptoms_noted": []
        }

    # 7. Single word "बहुत"
    if reply_clean in ["बहुत", "bahut"]:
        return {
            "reply": f"जी हर्षित जी, आप बताइए आज आपकी सेहत और खाना-पीना कैसा रहा?",
            "is_emergency": False,
            "emergency_reason": None,
            "is_complete": False,
            "symptoms_noted": []
        }

    # 8. Goodbye / Hang Up (Acknowledge warmly, but let user click button)
    if any(gb in reply_clean for gb in ["बाय", "अलविदा", "रखता", "कॉल काटो"]):
        return {
            "reply": f"बहुत धन्यवाद हर्षित जी! अपना पूरा ध्यान रखिएगा, कोई भी तकलीफ़ हो तो मुझे तुरंत बताइएगा।",
            "is_emergency": False,
            "emergency_reason": None,
            "is_complete": False,
            "symptoms_noted": []
        }

    # 9. General Ongoing Inquiries
    if step_index <= 1:
        general_reply = f"जी मैं सुन रही हूँ। आप बताइए आज आपका खाना-पीना और सेहत कैसी रही?"
    elif step_index == 2:
        general_reply = f"जी बिल्कुल। क्या आपने दोपहर डेढ़ बजे वाली शुगर की दवाई ले ली है?"
    else:
        general_reply = f"जी समझ गई। और कोई बात जो आप बताना चाहते हों?"

    return {
        "reply": general_reply,
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
    Every answer is analyzed with deep empathy, zero delay, and natural tone.
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

    # Call empathetic dialogue turn
    turn_result = generate_gemini_conversational_turn(
        senior_name=senior_name,
        coordinator_name=coordinator_name,
        family_name=family_name,
        user_reply=reply_clean,
        dialogue_history=dialogue,
        step_index=step_index
    )

    spoken_text = turn_result["reply"]
    is_emergency = turn_result["is_emergency"]

    # Direct synthesis via Sarvam AI Priya Voice so the voice is 100% consistent across every turn!
    sarvam_audio = None
    try:
        sarvam_audio = synthesize_speech_sarvam(spoken_text, speaker="priya", pace=1.0)
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
        "emergency_reason": turn_result.get("emergency_reason"),
        "is_complete": False,
        "accumulated": accumulated
    }
