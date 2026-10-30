"""Multi-lingual non-diagnostic clinical safety filter for SaathiCare AI.

HARD CLINICAL INVARIANT:
SaathiCare AI is an early-warning decision-support platform for care coordination,
NOT a medical diagnosis tool.
Every generated explanation, alert narrative, family summary, and coordinator script
MUST pass through this filter to guarantee ZERO medical condition or disease names.
"""

import re
from typing import List

# Blocklist of diagnostic condition words (English, Hindi Devanagari, and Roman Hinglish)
PROHIBITED_DIAGNOSTIC_TERMS: List[str] = [
    # English
    r"\bdiabet(es|ic)\b",
    r"\bpneumonia\b",
    r"\bdepress(ion|ed|ive)\b",
    r"\bhypertens(ion|ive)\b",
    r"\bheart attack\b",
    r"\bstroke\b",
    r"\bcopd\b",
    r"\basthma(tic)?\b",
    r"\bcovid(-19)?\b",
    r"\btuberculosis\b|\btb\b",
    r"\bcancer\b",
    r"\balzheimer('?s)?\b",
    r"\bdementia\b",
    r"\bkidney failure\b",
    r"\bsepsis\b",
    r"\bargina\b|\bangina\b",
    r"\bcongestive heart failure\b|\bchf\b",
    r"\bbronchitis\b",
    r"\barrhythmia\b",
    r"\bosteoarthritis\b|\barthritis\b",

    # Roman Hinglish
    r"\bmadhumeh\b",
    r"\bukhtaapan\b",
    r"\bfalij\b|\blakwa\b",
    r"\bdil ka daura\b",
    r"\bsans ki bimari\b",

    # Hindi Devanagari
    r"मधुमेह",
    r"डायबिटीज",
    r"निमोनिया",
    r"अवसाद",
    r"डिप्रेशन",
    r"उच्च रक्तचाप",
    r"हाइपरटेंशन",
    r"दिल का दौरा",
    r"हार्ट अटैक",
    r"लकवा",
    r"स्ट्रोक",
    r"दमा",
    r"अस्थमा",
    r"तपेदिक",
    r"कैंसर",
    r"अल्जाइमर",
    r"डिमेंशिया",
    r"गठिया"
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in PROHIBITED_DIAGNOSTIC_TERMS]


def enforce_safety_filter(text: str) -> str:
    """
    Sanitize generated text to ensure zero diagnostic or condition terms appear.
    Replaces any accidental clinical diagnoses with safe care-coordination risk language.
    """
    if not text:
        return ""

    sanitized = text
    for pattern in _COMPILED_PATTERNS:
        sanitized = pattern.sub("health indicator changes", sanitized)

    return sanitized


def validate_text_safety(text: str) -> bool:
    """Check if text contains any prohibited diagnostic terms."""
    if not text:
        return True
    for pattern in _COMPILED_PATTERNS:
        if pattern.search(text):
            return False
    return True

