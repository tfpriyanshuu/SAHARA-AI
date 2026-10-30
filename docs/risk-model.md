# SaathiCare AI — Risk Model & Anomaly Detection Pipeline

**Philosophy:** Traditional population cutoffs fail elderly homecare because individual physiological normal varies significantly. A vital reading of SpO2 91% might be chronic normal for a patient with stable pulmonary history, but catastrophic acute failure for a senior whose baseline is 97.5%.

SaathiCare AI replaces fixed thresholds with **personalized longitudinal baselines**, **contamination-resistant statistics**, and **multi-signal trajectory fusion**.

---

## 1. Contamination-Free Personal Baseline Mathematics

### The Contamination Problem
In standard 14-day rolling averages, when a senior begins a gradual multi-week decline, the deteriorating values are absorbed into the rolling window itself. By day 10 of decline, the baseline has drifted downwards, blunting the z-score and preventing alerts.

### The Lagged Window Solution
SaathiCare AI computes individual baselines over a lagged historical window:
$$\text{Window}_{\text{baseline}}(t) = [t - 42, \, t - 14]$$
By excluding the most recent 14 days, ongoing early decline cannot contaminate the reference normal.

### Robust Statistics: Median & MAD
Because single noisy readings and sensor dropouts occur in home IoT environments, we avoid the sample mean and sample standard deviation. We instead use robust non-parametric metrics:

$$\tilde{x} = \text{Median}(X_{[t-42 : t-14]})$$

$$\text{MAD} = \text{Median}\Big(\big|x_i - \tilde{x}\big|\Big)$$

To align with standard normal deviations without sensitivity to outliers:
$$\hat{\sigma}_{\text{robust}} = 1.4826 \times \text{MAD}$$

### Direction-Aware Normalized Z-Score
For any biomarker observation $x(t)$, the z-score is calculated relative to the senior's own distribution:
$$z(t) = \frac{x(t) - \tilde{x}}{\hat{\sigma}_{\text{robust}} + \epsilon}$$

Where $\epsilon = 10^{-4}$ prevents division by zero for extraordinarily stable signals.

---

## 2. Multi-Signal Families Evaluated

A daily risk score is composed across 5 distinct signal families:

1. **Vital Biomarkers:** Pulse oximetry (SpO2), Systolic/Diastolic blood pressure, random blood glucose.
2. **Medication Adherence:** Daily taken percentage, consecutive missed doses, dose timing delays.
3. **Ambient Activity & Mobility:** Continuous daytime inactivity hours, hours spent outdoors, magnetic door cycles.
4. **Nocturnal Restlessness:** Frequency of night bathroom visits between 11:00 PM and 05:00 AM.
5. **Call Notes & Check-in Transcripts:** Negation-aware extracted adverse cues from free text.

---

## 3. Negation-Aware Multilingual NLP Pipeline

Call notes and voice check-ins are spoken/written in colloquial Hindi, English, and Hinglish. Keyword matching alone creates excessive false alarms when seniors state:
> *"Dard nahi hai abhi"* (No pain right now)  
> *"Chakkar bilkul nahi aaye"* (Did not feel dizzy at all)

SaathiCare AI uses a regex-based cue extraction engine with a **$\pm 3$ token negation window**:
- Evaluates 10 clinical cues: `breathing_difficulty`, `fall`, `low_appetite`, `missed_medication`, `pain`, `confusion`, `sleep_deterioration`, `loneliness`, `mood_changes`, `reduced_activity`.
- Identifies negation prefixes and suffixes: `nahi`, `nahin`, `bilkul nahi`, `no`, `never`, `denied`, `free of`, `without`.
- Evaluates every match span to mark negated mentions as `negated: true`, effectively suppressing false alarms while logging genuine mentions.

---

## 4. Unsupervised Anomaly Detection + Rules Blend

The daily score ($0 - 100$) blends two independent scoring mechanisms:

```
Daily Score = 0.55 × RulesScore + 0.45 × IsolationForestAnomalyScore
```

### A. Clinical Rules Engine ($0 - 100$)
- **Critical Single-Signal Triggers:** Uncancelled fall event, SOS button push, or severe oxygen collapse ($z_{\text{spo2}} \le -3.0$) automatically yield $\ge 80$.
- **Multi-Family Compounding:** Minor shifts across $\ge 2$ independent families (e.g. slight SpO2 drop + 1 missed dose + nocturnal visits doubled) trigger cumulative point increments.

### B. Isolation Forest Model ($0 - 100$)
- Built with Scikit-learn's `IsolationForest(n_estimators=100, contamination=0.08)`.
- **Trained on Baseline-Normalized Features Only:** Inputs include $z$-scores, EWMA momentum, nocturnal drift ratios, and NLP cue counts.
- **Zero Raw Population Cutoffs:** The model never sees raw physiological measurements, preventing it from memorizing population averages.

---

## 5. Benign Context Filters & Gating

To protect Care Coordinators from alert fatigue:

1. **Benign Travel Filter:**
   - If door sensor telemetry records zero interior motion alongside morning door departures, or if the family scheduled a trip, isolated vital gaps are classified as travel rather than deterioration.
2. **Festival Calibration:**
   - Regional cultural calendars (e.g., Diwali, Eid) account for dietary sugar spikes and disrupted sleep routines.
3. **Strict Alert Budgeting ($N = 10$):**
   - A coordinator's daily queue surfaces at most 10 seniors, ranked strictly by severity and trajectory velocity.
   - Low-priority noise is routed to an expandable watchlist rather than triggering active alarms.

