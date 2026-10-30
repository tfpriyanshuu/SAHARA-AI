"""Negation-aware NLP cue extraction engine for Hindi, English, and Hinglish.

Extracts 10 clinical wellbeing cues from free-text check-in notes:
1. pain
2. confusion
3. low_appetite
4. sleep_deterioration
5. loneliness
6. mood_changes
7. fall
8. missed_medication
9. reduced_activity
10. breathing_difficulty
"""

import re
from typing import Dict, Any, List, Optional, Tuple

CUE_REGEX_PATTERNS = {
    "breathing_difficulty": {
        "pattern": r"(saans|sans|dum ghut|heavy chest|breathless|shortness of breath|breathing issue|seene me bhari|सांस|दम घुट)",
        "intensifiers": [r"severe", r"bahut", r"kaafi", r"tez", r"तेज", r"काफी"]
    },
    "fall": {
        "pattern": r"(\bgir\b|\bfisal\b|\bfell\b|\bfall\b|\bslipped\b|\btripped\b|chot lag|गिर|फिसल|चोट)",
        "intensifiers": [r"hard fall", r"buritarah", r"zor se", r"काफी जोर से"]
    },
    "low_appetite": {
        "pattern": r"(bhookh|appetite|not eating|khana.*nahi|khana.*chhut|khaya nahi|भूख|खाना नहीं)",
        "intensifiers": [r"barely", r"kuch nahi", r"bilkul nahi", r"काफी कम", r"बिल्कुल नहीं"]
    },
    "missed_medication": {
        "pattern": r"(dawai.*(bhool|miss|chhut|nahi|li)|dawa.*(bhool|miss|chhut)|goli.*(nahi|bhool)|missed.*(med|dose|pill)|forgot.*(med|dose|pill)|दवाई.*भूल|दवा.*छूट|गोली.*नहीं)",
        "intensifiers": [r"multiple", r"2 din", r"3 doses", r"काफी दिनों"]
    },
    "pain": {
        "pattern": r"(dard|pain|ache|takleef|peeda|sore|chot|दर्द|तकलीफ|पीड़ा)",
        "intensifiers": [r"severe", r"bahut", r"tez", r"kaafi", r"unbearable", r"काफी", r"तेज"]
    },
    "confusion": {
        "pattern": r"(bhool|confus|yaad nahi|uljhan|disorient|खोया|उलझन|याद नहीं)",
        "intensifiers": [r"completely", r"bilkul", r"bahut", r"बिल्कुल"]
    },
    "sleep_deterioration": {
        "pattern": r"(neend|sleep|insomnia|so nahi|jaagta|नींद|जागते)",
        "intensifiers": [r"whole night", r"saari raat", r"bilkul nahi", r"पूरी रात"]
    },
    "loneliness": {
        "pattern": r"(akela|akelapan|lonel|isolated|alone|अकेला|अकेलापन)",
        "intensifiers": [r"very lonely", r"bahut", r"kaafi", r"बहुत"]
    },
    "mood_changes": {
        "pattern": r"(udaas|sad|low mood|rone ka|dil ghabra|unhappy|उदास|उदासी|रोने)",
        "intensifiers": [r"extremely", r"bahut", r"kaafi", r"बहुत"]
    },
    "reduced_activity": {
        "pattern": r"(thakan|fatigue|tired|kamzori|inactive|weak|bistar par|hil nahi|sair nahi|थकान|कमजोरी)",
        "intensifiers": [r"extremely", r"bahut", r"hil nahi", r"बहुत"]
    }
}

NEGATION_TERMS = ["nahi", "nahin", "nhi", "na", "no", "not", "never", "none", "without", "नहीं", "ना"]
PAST_RESOLUTION_TERMS = ["pehle tha ab theek", "pehle tha ab nahi", "ab aaram hai", "resolved", "now fine", "पहले था अब ठीक"]


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    devanagari_digits = {"०": "0", "१": "1", "२": "2", "३": "3", "४": "4", "५": "5", "६": "6", "७": "7", "८": "8", "९": "9"}
    for d_hi, d_ar in devanagari_digits.items():
        text = text.replace(d_hi, d_ar)
    text = re.sub(r"\s+", " ", text)
    return text


def extract_cues_from_note(text: str) -> List[Dict[str, Any]]:
    if not text:
        return []

    norm_text = normalize_text(text)
    tokens = norm_text.split()
    results = []

    has_past_res = any(pr in norm_text for pr in PAST_RESOLUTION_TERMS)

    for cue_type, meta in CUE_REGEX_PATTERNS.items():
        pattern = meta["pattern"]
        matches = list(re.finditer(pattern, norm_text))
        if matches:
            # Check negation across all occurrences of this cue
            is_negated = False
            best_match = matches[0]

            for m in matches:
                start_pos, end_pos = m.span()
                matched_text = m.group(0)
                pre_tokens = norm_text[:start_pos].split()
                token_idx = len(pre_tokens)

                w_start = max(0, token_idx - 3)
                w_end = min(len(tokens), token_idx + len(matched_text.split()) + 3)
                neighborhood = tokens[w_start:w_end]

                if any(neg in neighborhood for neg in NEGATION_TERMS) or has_past_res:
                    is_negated = True
                    best_match = m
                    break

            # Special case for "missed_medication":
            if cue_type == "missed_medication":
                if any(x in norm_text for x in ["dawai nahi li", "goli nahi li", "dawa nahi li", "dawai bhool", "missed med"]):
                    is_negated = False

            # Intensity
            intensity = 1
            for intensifier in meta.get("intensifiers", []):
                if re.search(intensifier, norm_text):
                    intensity = 2
                    break

            evidence = norm_text[max(0, best_match.start() - 10):min(len(norm_text), best_match.end() + 15)].strip()

            results.append({
                "cue_type": cue_type,
                "intensity": intensity,
                "confidence": 0.95 if not is_negated else 0.88,
                "evidence_span": evidence,
                "is_negated": is_negated
            })

    return results
