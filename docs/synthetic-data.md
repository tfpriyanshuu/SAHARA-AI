# SaathiCare AI — Synthetic Longitudinal Cohort (200 Seniors × 90 Days)

To evaluate SaathiCare AI with medical realism before clinical trial deployment, we engineered a longitudinal synthetic telemetry generator simulating **200 seniors over 90 days** (18,000 senior-days of telemetry).

---

## 1. Cohort Demographics & Geographical Distribution

The synthetic population mirrors typical elderly homecare demographics across urban and semi-urban India:

- **Cohort Size:** 200 seniors (Ages 65 to 88, Mean Age: 74.2 years, 52% Female, 48% Male)
- **Care Locations (10 Hubs):** Indore, Delhi NCR, Mumbai, Bengaluru, Pune, Jaipur, Lucknow, Ahmedabad, Chennai, Kolkata
- **Languages:** Hindi, Hinglish, Marathi, Tamil, Bengali, English
- **Living Conditions:** Living independently at home with remote family contact (children working in metro cities or abroad)

---

## 2. Personal Baseline Initialization

Each senior is assigned a persistent, individualized physiological baseline drawn from realistic distributions:

| Biomarker | Baseline Distribution | Typical Range | Daily Noise (&sigma;) |
| :--- | :--- | :--- | :--- |
| **SpO2 Pulse Oximetry** | Normal(&mu;=96.4, &sigma;=1.2) | 93.5% &ndash; 98.5% | &plusmn;0.6% |
| **Systolic BP** | Normal(&mu;=126, &sigma;=9.5) | 110 &ndash; 145 mmHg | &plusmn;4.0 mmHg |
| **Diastolic BP** | Normal(&mu;=80, &sigma;=6.0) | 68 &ndash; 92 mmHg | &plusmn;2.5 mmHg |
| **Fasting Blood Glucose** | Normal(&mu;=118, &sigma;=18) | 92 &ndash; 165 mg/dL | &plusmn;8.0 mg/dL |
| **Daytime Inactivity** | Normal(&mu;=6.5, &sigma;=1.2) | 4.5 &ndash; 8.8 hrs | &plusmn;0.8 hrs |
| **Night Bathroom Visits** | Poisson(&lambda;=1.1) | 0 &ndash; 2 visits/night | Discrete noise |
| **Front Door Events** | Poisson(&lambda;=4.8) | 2 &ndash; 8 events/day | Discrete noise |

---

## 3. Planted Clinical & Behavioral Archetypes

The 90-day dataset contains planted decline trajectories alongside hard negatives:

### Archetype A: Gradual Respiratory & Cardiovascular Decline (Planted Case, e.g. SEN_003)
- **Trajectory:** Days 1&ndash;21 remain at healthy baseline. On Day 22, SpO2 begins dropping gradually (-0.8% to -1.2% per day).
- **Compounding Families:** Daytime inactivity rises from 6.2 hrs to 11.5 hrs; night bathroom visits increase from 1 to 4/night. Senior misses 2 afternoon medication doses due to fatigue.
- **NLP Notes:** Call notes report *"saans lene me thodi dikkat"* and *"bhookh kam lag rahi hai"*, while negating chest pain (*"dard nahi hai"*).
- **Crisis Day:** Day 29 without early intervention.

### Archetype B: Medication Lapsing & Blood Pressure Drift
- **Trajectory:** Smart pillbox records consecutive missed doses of anti-hypertensive medication.
- **Compounding Families:** Systolic blood pressure slowly drifts upward by +20 mmHg over 6 days.
- **Outcome:** Detected within 48 hours of second missed dose before hypertensive urgency occurs.

### Archetype C: Hard Negative 1 — Travel & Out-of-Town Wedding
- **Pattern:** Zero vital readings for 4 consecutive days; door sensor shows morning departure with zero motion inside.
- **Handling:** Benign travel filter identifies departure signature and suppresses acute clinical alerts.

### Archetype D: Hard Negative 2 — Festive Week (Diwali / Family Gathering)
- **Pattern:** Blood glucose spikes temporarily (+35 mg/dL) due to sweets; sleep routine shifts later by 2 hours.
- **Handling:** Isolated single-family deviation without oxygen or mobility collapse is identified as benign festive variation.

---

## 4. Ground Truth Annotations & Reproducibility

- **Database Seed Location:** `backend/data/saathicare.db`
- **Seed Script:** `backend/scripts/seed_db.py`
- **Fixed Random Seed:** `42` ensures bit-for-bit reproducible telemetry across testing environments.

