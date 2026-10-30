import pytest
from app.services.nlp import extract_cues_from_note, normalize_text
from app.services.safety import enforce_safety_filter, validate_text_safety


def test_nlp_cue_extraction_basic():
    text = "aaj subah se chalne par saans phool rahi hai, seene me bhaari lagta hai"
    cues = extract_cues_from_note(text)
    active_types = [c["cue_type"] for c in cues if not c["is_negated"]]
    assert "breathing_difficulty" in active_types


def test_nlp_negation_handling_hinglish():
    # "gir nahi gaye" must NOT be marked as an active fall
    text = "kal raat bathroom me paer fisal gaya tha halki chot aayi, par gir nahi gaye"
    cues = extract_cues_from_note(text)
    fall_cues = [c for c in cues if c["cue_type"] == "fall"]
    assert len(fall_cues) >= 1
    assert fall_cues[0]["is_negated"] is True, "'gir nahi gaye' must be marked as negated"


def test_nlp_negation_handling_pain():
    # "dard nahi hai" must be negated
    text = "dawai subah le li thi, koi sar dard nahi hai abhi"
    cues = extract_cues_from_note(text)
    pain_cues = [c for c in cues if c["cue_type"] == "pain"]
    assert len(pain_cues) >= 1
    assert pain_cues[0]["is_negated"] is True, "'dard nahi hai' must be negated"


def test_nlp_multiple_cues():
    text = "aaj dawai bhool gaya lena, bhookh bahut kam lagi hai, ghar me akelapan lagta hai"
    cues = extract_cues_from_note(text)
    active = [c["cue_type"] for c in cues if not c["is_negated"]]
    assert "missed_medication" in active
    assert "low_appetite" in active
    assert "loneliness" in active


def test_safety_filter_removes_diagnostic_names():
    unsafe_text = "Senior exhibits symptoms consistent with diabetes and depression."
    safe_text = enforce_safety_filter(unsafe_text)
    assert "diabetes" not in safe_text.lower()
    assert "depression" not in safe_text.lower()
    assert validate_text_safety(safe_text) is True

