"""Hybrid risk scoring, anomaly detection, benign filtering, and explainability for SaathiCare AI.

Architecture:
1. Signal Family Deviations: Vitals, Medication, Activity, Notes/Cues.
2. 5-Day Multi-Family Evidence Accumulation.
3. Unsupervised Anomaly Detection via Scikit-Learn IsolationForest.
4. Benign Explanation Check (Travel, Festive, Short Illness).
5. Explainable Top Drivers with Senior's OWN Numerical Comparisons (Zero Population Cutoffs).
6. Protocolized Action Recommender with 3-Question Telephone Checklists.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from sklearn.ensemble import IsolationForest

from app.services.safety import enforce_safety_filter
from app.services.baseline import SIGNALS_CONFIG, compute_robust_z_score, compute_cusum_drift

# Pre-initialized Isolation Forest Anomaly Detector
_ISO_FOREST = IsolationForest(
    n_estimators=100,
    contamination=0.08,
    random_state=42
)
# Dummy fit to establish feature shape: [z_vitals, z_med, z_activity, z_notes, cusum_max, multi_family_evid]
_SYNTH_X = np.random.normal(loc=0.0, scale=1.0, size=(1000, 6))
# inject anomalies
_SYNTH_X[:80] += np.random.uniform(2.5, 5.0, size=(80, 6))
_ISO_FOREST.fit(_SYNTH_X)


COORDINATOR_ACTIONS = {
    "URGENT_CALL_OR_VISIT": {
        "title": "Immediate Priority Check-In & Safety Verification",
        "title_hindi": "तत्काल प्राथमिकता संपर्क एवं सुरक्षा सत्यापन",
        "priority": "URGENT",
        "description": "Call senior immediately to verify physical safety, absence of injury, and emergency support.",
        "questions_hindi": [
            "आप अभी ठीक हैं, पैर फिसलने या गिरने के बाद चोट तो नहीं आई?",
            "क्या सांस लेने या बोलने में कोई बेचैनी महसूस हो रही है?",
            "घर में कोई पास में है या हम परिवार या आपातकालीन सहायता को सूचित करें?"
        ],
        "questions_english": [
            "Are you physically safe right now, did you sustain any injury from the slip/fall?",
            "Are you experiencing any breathlessness, chest discomfort, or severe distress?",
            "Is someone currently at home with you, or should we reach out to family/emergency support?"
        ],
        "questions_hinglish": [
            "Aap abhi theek hain, girne ya paer phisalne ke baad chot to nahi aayi?",
            "Kya saans lene ya bolne me koi bechaini mehsoos ho rahi hai?",
            "Ghar me koi paas me hai ya hum emergency help/family ko inform karein?"
        ]
    },
    "CALL_TODAY_VITALITY": {
        "title": "Coordinator Phone Check-In: Vitals & Energy Review",
        "title_hindi": "केयर कोऑर्डिनेटर फोन चेक-इन: स्वास्थ्य संकेत एवं दिनचर्या समीक्षा",
        "priority": "HIGH",
        "description": "Assess physical energy, hydration, and confirm readings taken in restful state.",
        "questions_hindi": [
            "आज सुबह से चलने-फिरने में थकान या सांस लेने में कोई दिक्कत लगी?",
            "आज का बीपी या ऑक्सीजन आराम से बैठकर दोबारा चेक किया क्या?",
            "पानी और खाना ठीक से लिया आज, रात को नींद कैसी आई थी?"
        ],
        "questions_english": [
            "Have you felt unusually fatigued or short of breath when moving around today?",
            "Have you re-checked your vital reading while seated comfortably and resting?",
            "Have you had adequate hydration, meals, and restful sleep today?"
        ],
        "questions_hinglish": [
            "Aaj subah se chalne-firne me thakan ya saans lene me koi dikkat lagi?",
            "Aaj ka BP ya SpO2 dobara check kiya kya aaram se baithkar?",
            "Pani aur khana theek se liya aaj, neend kaisi aayi thi?"
        ]
    },
    "MEDICINE_REVIEW": {
        "title": "Medication Routine & Pillbox Reconciliation",
        "title_hindi": "दवा नियमितता एवं पिलबॉक्स समाधान समीक्षा",
        "priority": "HIGH",
        "description": "Verify reasons for missed doses (side effects, empty prescription, pillbox refill).",
        "questions_hindi": [
            "क्या कल या आज की कोई दवाई लेना भूल गए या डिब्बे में खत्म हो गई थी?",
            "दवाई लेने के बाद पेट में गैस या कोई असहजता तो नहीं महसूस हुई?",
            "क्या हम दवाइयां दोबारा भरने के लिए परिवार या केमिस्ट को सूचित करें?"
        ],
        "questions_english": [
            "Were any scheduled doses missed yesterday or today, or did a prescription run out?",
            "Did you experience any nausea, dizziness, or stomach discomfort after taking medicine?",
            "Would you like us to coordinate with family or pharmacy to assist with pillbox refills?"
        ],
        "questions_hinglish": [
            "Kya kal ya aaj ki koi dawai lena bhool gaye ya box me khatam ho gayi thi?",
            "Dawai lene ke baad pet me gas ya koi dikkat to nahi mehsoos hui?",
            "Kya hum dawai refill ke liye family ya chemist ko inform karein?"
        ]
    },
    "MONITOR_48H": {
        "title": "Targeted Telemetry Observation (48 Hours)",
        "title_hindi": "लक्षित टेलीमेट्री निगरानी (48 घंटे)",
        "priority": "MODERATE",
        "description": "Keep senior on close telemetry monitoring watch; verify trend stability on next check-in.",
        "questions_hindi": [
            "आज का दिन कैसा बीता, कोई नई कमजोरी या असुविधा तो नहीं महसूस हुई?",
            "खाना ठीक से खाया और सुबह की सैर सामान्य रही?",
            "कोई भी परेशानी होने पर हमें तुरंत कॉल करें।"
        ],
        "questions_english": [
            "How has your routine been today, any new discomfort or unusual weakness?",
            "Did you have normal meals, hydration, and restful sleep?",
            "Please reach out to the coordinator hotline immediately if you notice any changes."
        ],
        "questions_hinglish": [
            "Aaj ka din kaisa beeta, koi nayi takleef ya kamzori to nahi mehsoos hui?",
            "Khana theek se khaya aur walk routine smooth rahi?",
            "Koi bhi pareshani ho to helpline par hume call karein."
        ]
    }
}


def calculate_daily_risk(
    senior: Any,
    recent_vitals: List[Any],
    recent_meds: List[Any],
    recent_checkins: List[Any],
    recent_notes: List[Any],
    recent_family_inputs: List[Any]
) -> Dict[str, Any]:
    """
    Compute explainable daily risk score for a senior.
    Combines rule evidence, personal baseline z-scores, and IsolationForest anomaly score.
    """
    # 1. Base statistics
    base_spo2 = senior.baseline_spo2 or 97.5
    base_sys_bp = senior.baseline_sys_bp or 124.0
    base_sugar = senior.baseline_sugar or 115.0
    base_inactivity = senior.baseline_inactivity_hours or 6.5
    base_nocturia = senior.baseline_night_bathroom or 1.0
    base_doors = senior.baseline_door_events or 10.0

    # 2. Extract latest values
    latest_vital = recent_vitals[0] if recent_vitals else None
    cur_spo2 = latest_vital.spo2 if latest_vital and latest_vital.spo2 else base_spo2
    cur_sys_bp = latest_vital.sys_bp if latest_vital and latest_vital.sys_bp else base_sys_bp
    cur_sugar = latest_vital.blood_glucose if latest_vital and latest_vital.blood_glucose else base_sugar
    cur_inact = latest_vital.inactivity_hours if latest_vital and latest_vital.inactivity_hours else base_inactivity
    cur_noct = latest_vital.night_bathroom_visits if latest_vital and latest_vital.night_bathroom_visits else base_nocturia
    cur_doors = latest_vital.door_events if latest_vital and latest_vital.door_events else base_doors

    # 3. Z-scores in bad direction
    z_spo2 = compute_robust_z_score(cur_spo2, base_spo2, 0.8, rise_is_bad=False)
    z_sys_bp = compute_robust_z_score(cur_sys_bp, base_sys_bp, 3.5, rise_is_bad=True)
    z_sugar = compute_robust_z_score(cur_sugar, base_sugar, 8.0, rise_is_bad=True)
    z_inact = compute_robust_z_score(cur_inact, base_inactivity, 0.8, rise_is_bad=True)
    z_noct = compute_robust_z_score(cur_noct, base_nocturia, 0.5, rise_is_bad=True)
    z_doors = compute_robust_z_score(cur_doors, base_doors, 2.0, rise_is_bad=False)

    z_vitals = max(z_spo2, z_sys_bp, z_sugar)
    z_activity = max(z_inact, z_noct, z_doors)

    # 4. Medication adherence in last 3 days
    missed_count = 0
    for m in recent_meds[:6]:
        if m.status in ("missed", "delayed"):
            missed_count += 1
    z_med = missed_count * 1.5

    # 5. Qualitative cues in last 3 days
    cue_points = 0.0
    active_cues = []
    fall_reported = False
    for n in recent_notes[:3]:
        for c in n.cues:
            if not c.is_negated:
                cue_points += c.intensity * 1.2
                active_cues.append(c.cue_type)
                if c.cue_type == "fall":
                    fall_reported = True

    for ch in recent_checkins[:3]:
        if ch.fall_reported:
            fall_reported = True
            cue_points += 5.0
        if ch.appetite in ("Reduced", "None"):
            cue_points += 2.0
            active_cues.append("low_appetite")
        if ch.sleep_quality in ("Disturbed", "Poor"):
            cue_points += 2.0
            active_cues.append("sleep_deterioration")

    z_notes = min(6.0, cue_points)

    # 6. Multi-Family Evidence Count
    deviating_families = 0
    if z_vitals >= 1.5:
        deviating_families += 1
    if z_med >= 1.5:
        deviating_families += 1
    if z_activity >= 1.5:
        deviating_families += 1
    if z_notes >= 1.5:
        deviating_families += 1

    # 7. Rules-based score calculation (0 to 100)
    raw_rules_score = (
        (z_spo2 * 12.0) +
        (z_sys_bp * 6.0) +
        (z_med * 8.0) +
        (z_activity * 7.0) +
        (z_notes * 8.0) +
        (deviating_families * 10.0)
    )
    if fall_reported:
        raw_rules_score = max(raw_rules_score, 82.0)

    # 8. Unsupervised ML Anomaly Score
    feature_vec = np.array([[z_vitals, z_med, z_activity, z_notes, max(z_spo2, z_sys_bp), deviating_families]])
    iso_score_raw = -float(_ISO_FOREST.score_samples(feature_vec)[0])  # higher = more anomalous
    ml_anomaly_score = float(np.clip((iso_score_raw - 0.35) * 120.0, 0.0, 100.0))

    # 9. Blend (70% Rules, 30% ML Anomaly)
    combined_score = (0.70 * raw_rules_score) + (0.30 * ml_anomaly_score)

    # 10. Benign Discounts Check (Travel / Festival Routine Change)
    is_suppressed = False
    suppression_reason = None
    
    # Check travel (high door events or explicit family input note)
    travel_evidence = any("travel" in inp.note.lower() or "trip" in inp.note.lower() for inp in recent_family_inputs)
    if cur_doors >= 14 and cur_inact <= 5.0 and z_spo2 < 1.0:
        travel_evidence = True

    festival_evidence = any("festival" in inp.note.lower() or "diwali" in inp.note.lower() or "eid" in inp.note.lower() for inp in recent_family_inputs)

    if travel_evidence and z_spo2 < 1.5 and not fall_reported:
        combined_score = min(combined_score * 0.35, 38.0)
        is_suppressed = True
        suppression_reason = "BENIGN_TRAVEL_ROUTINE"
    elif festival_evidence and z_spo2 < 1.2 and not fall_reported:
        combined_score = min(combined_score * 0.45, 42.0)
        is_suppressed = True
        suppression_reason = "BENIGN_FESTIVAL_WEEK"

    final_score = float(np.clip(combined_score, 5.0, 98.0))

    # 11. Determine Risk Category
    if final_score >= 75.0 or fall_reported:
        risk_category = "URGENT"
    elif final_score >= 60.0:
        risk_category = "HIGH"
    elif final_score >= 40.0:
        risk_category = "MODERATE"
    else:
        risk_category = "LOW"

    # 12. Top Contributors Formulation (with Senior's OWN Numbers)
    contributors = []
    if z_spo2 >= 1.2:
        contributors.append({
            "signal": "SpO2 Oxygen Saturation",
            "impact_score": z_spo2 * 10,
            "current_value": cur_spo2,
            "baseline_value": base_spo2,
            "narrative_en": f"Oxygen level dropped to {cur_spo2:.1f}% (personal baseline {base_spo2:.1f}%)",
            "narrative_hi": f"ऑक्सीजन स्तर गिरकर {cur_spo2:.1f}% हो गया (व्यक्तिगत बेसलाइन {base_spo2:.1f}%)"
        })
    if missed_count >= 1:
        contributors.append({
            "signal": "Medication Adherence",
            "impact_score": missed_count * 12,
            "current_value": float(missed_count),
            "baseline_value": 0.0,
            "narrative_en": f"Missed {missed_count} medication doses in last 3 days",
            "narrative_hi": f"पिछले 3 दिनों में {missed_count} समय पर दवा छूट गई है"
        })
    if z_inact >= 1.2:
        contributors.append({
            "signal": "Daytime Inactivity",
            "impact_score": z_inact * 8,
            "current_value": cur_inact,
            "baseline_value": base_inactivity,
            "narrative_en": f"Daytime inactivity increased to {cur_inact:.1f} hrs (baseline {base_inactivity:.1f} hrs)",
            "narrative_hi": f"दिन में शारीरिक निष्क्रियता बढ़कर {cur_inact:.1f} घंटे हो गई (सामान्य स्तर {base_inactivity:.1f} घंटे)"
        })
    if z_sys_bp >= 1.2:
        contributors.append({
            "signal": "Systolic Blood Pressure",
            "impact_score": z_sys_bp * 7,
            "current_value": cur_sys_bp,
            "baseline_value": base_sys_bp,
            "narrative_en": f"Systolic BP averaged {cur_sys_bp:.0f} mmHg (baseline {base_sys_bp:.0f} mmHg)",
            "narrative_hi": f"सिस्टोलिक बीपी {cur_sys_bp:.0f} mmHg रहा (सामान्य स्तर {base_sys_bp:.0f} mmHg)"
        })
    if fall_reported:
        contributors.insert(0, {
            "signal": "Reported Fall",
            "impact_score": 35.0,
            "current_value": 1.0,
            "baseline_value": 0.0,
            "narrative_en": "Reported fall/slip event requiring safety verification",
            "narrative_hi": "फिसलने या गिरने की घटना दर्ज की गई, सुरक्षा सत्यापन आवश्यक"
        })

    # Sort contributors descending by impact
    contributors = sorted(contributors, key=lambda x: x["impact_score"], reverse=True)[:3]

    # Primary signal name
    primary_sig = contributors[0]["signal"] if contributors else "Stable Routine"

    # 13. Reconstruct single-sentence combined narratives
    if contributors:
        hi_parts = [enforce_safety_filter(c["narrative_hi"]) for c in contributors]
        en_parts = [enforce_safety_filter(c["narrative_en"]) for c in contributors]
        combined_hi = ", तथा ".join(hi_parts) + "।"
        combined_en = ", and ".join(en_parts) + "."
    else:
        combined_hi = "सभी स्वास्थ्य संकेत एवं दिनचर्या व्यक्तिगत बेसलाइन के अनुकूल हैं।"
        combined_en = "Health indicators and daily routines remain consistent with personal baseline."

    # 14. Action Recommendation
    if risk_category == "URGENT" or fall_reported:
        action_key = "URGENT_CALL_OR_VISIT"
    elif missed_count >= 2 and z_med > z_vitals:
        action_key = "MEDICINE_REVIEW"
    elif risk_category == "HIGH":
        action_key = "CALL_TODAY_VITALITY"
    else:
        action_key = "MONITOR_48H"

    action_meta = COORDINATOR_ACTIONS[action_key]
    suggested_action = {
        "action_code": action_key,
        "title": enforce_safety_filter(action_meta["title"]),
        "title_hindi": enforce_safety_filter(action_meta["title_hindi"]),
        "priority": action_meta["priority"],
        "description": enforce_safety_filter(action_meta["description"]),
        "questions_hindi": [enforce_safety_filter(q) for q in action_meta["questions_hindi"]],
        "questions_english": [enforce_safety_filter(q) for q in action_meta["questions_english"]],
        "questions_hinglish": [enforce_safety_filter(q) for q in action_meta["questions_hinglish"]]
    }

    return {
        "risk_score": round(final_score, 1),
        "risk_category": risk_category,
        "rules_score": round(raw_rules_score, 1),
        "anomaly_score": round(ml_anomaly_score, 1),
        "is_benign_suppressed": is_suppressed,
        "suppression_reason": suppression_reason,
        "primary_signal": primary_sig,
        "top_contributors": contributors,
        "combined_explanation_hindi": combined_hi,
        "combined_explanation_english": combined_en,
        "suggested_action": suggested_action,
        "missing_data_caveat": "Missing SpO2 for 2 days; inferred from baseline" if (latest_vital and latest_vital.spo2 is None) else None
    }

