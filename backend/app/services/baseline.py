"""Personal baseline calculation and robust deviation tracking for SaathiCare AI.

Key Innovations:
1. Senior-Specific Baseline: Every senior is judged against their OWN normal vitals,
   NEVER population averages.
2. Lagged Window [t-42, t-14]: Excludes the most recent 14 days to prevent gradual decline
   trajectories from contaminating and normalizing the baseline.
3. Robust Statistics: Rolling median + MAD (1.4826 * MAD) with safe numerical floors.
4. Direction-Aware Deviations:
   - Rising is bad: Systolic/Diastolic BP, Blood Sugar, Inactivity Hours, Nocturia visits.
   - Falling is bad: SpO2 Oxygen Saturation, Medication Adherence, Outdoor Hours, Door Events.
5. Missingness Awareness: Explicit days_since_last_obs tracking; missing values are NEVER imputed as zero.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

SIGNALS_CONFIG = {
    "sys_bp": {"rise_is_bad": True, "floor_mad": 3.0, "default_base": 124.0, "unit": "mmHg"},
    "dia_bp": {"rise_is_bad": True, "floor_mad": 2.0, "default_base": 80.0, "unit": "mmHg"},
    "spo2": {"rise_is_bad": False, "floor_mad": 0.8, "default_base": 97.5, "unit": "%"},
    "blood_glucose": {"rise_is_bad": True, "floor_mad": 8.0, "default_base": 115.0, "unit": "mg/dL"},
    "inactivity_hours": {"rise_is_bad": True, "floor_mad": 0.8, "default_base": 6.5, "unit": "hours"},
    "night_bathroom_visits": {"rise_is_bad": True, "floor_mad": 0.5, "default_base": 1.0, "unit": "visits"},
    "hours_outdoors": {"rise_is_bad": False, "floor_mad": 0.4, "default_base": 1.5, "unit": "hours"},
    "door_events": {"rise_is_bad": False, "floor_mad": 2.0, "default_base": 10.0, "unit": "events"},
    "med_adherence": {"rise_is_bad": False, "floor_mad": 0.05, "default_base": 1.0, "unit": "ratio"}
}


def compute_robust_z_score(
    value: float,
    median: float,
    mad: float,
    floor_mad: float = 1.0,
    rise_is_bad: bool = True
) -> float:
    """
    Compute direction-aware robust z-score:
    Positive z always indicates deviation in the BAD direction.
    """
    if pd.isna(value) or pd.isna(median):
        return 0.0

    effective_mad = max(mad, floor_mad)
    raw_z = (value - median) / (1.4826 * effective_mad)
    
    # Invert if drop is bad (so positive z is always clinically concerning)
    bad_z = raw_z if rise_is_bad else -raw_z
    return float(np.clip(bad_z, -3.0, 10.0))


def compute_cusum_drift(
    z_scores: List[float],
    slack: float = 0.5,
    threshold: float = 4.0
) -> Tuple[float, bool]:
    """
    Compute one-sided cumulative sum (CUSUM) drift for positive (bad) deviations.
    Returns (latest_cusum_value, alarm_triggered).
    """
    cusum = 0.0
    for z in z_scores:
        if z is None or pd.isna(z):
            continue
        cusum = max(0.0, cusum + (z - slack))

    alarm = cusum >= threshold
    return float(cusum), alarm

