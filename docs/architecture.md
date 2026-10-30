# SaathiCare AI — System Architecture & Data Flow

**Tagline:** Every Signal Matters. Every Senior Matters.  
**Core Mission:** AI-Powered Early Warning Decision Support for Seniors Living at Home.

---

## 1. High-Level System Architecture

SaathiCare AI is a full-stack, human-in-the-loop healthcare decision-support system. It answers three core operational questions every morning:
1. **WHO needs attention today?** (Triage priority queue strictly capped at $N=10$ seniors/coordinator)
2. **WHY is this senior's risk increasing?** (SHAP and personal baseline deviation narratives in English, Hindi, and Hinglish)
3. **WHAT should the Care Coordinator do next?** (Protocolized 3-question telephone scripts and action routing)

```mermaid
flowchart TD
    subgraph Multi_Signal_Ingestion ["Multi-Signal Telemetry Ingestion"]
        V["Vital Observations\n(SpO2, Systolic/Diastolic BP, Glucose)"]
        M["Connected Pillbox\n(Dose logs, Timestamps, Misses)"]
        A["Ambient IoT Sensors\n(Inactivity, Bathroom Visits, Door Events)"]
        C["Automated Check-ins\n(Voice recordings, Mood, Self-reports)"]
        N["Coordinator Call Notes\n(Free-text Hindi/English/Hinglish)"]
    end

    subgraph Data_Processing_Pipeline ["Telemetry & NLP Pipeline"]
        NLP["Negation-Aware Clinical Cue Engine\n(±3 Token Window, 10 Adverse Cues)"]
        LaggedBase["Lagged Baseline Engine\nWindow [t-42, t-14], Median, 1.4826×MAD"]
    end

    subgraph Decision_Support_Engine ["AI Risk & Gating Engine"]
        IF["Isolation Forest Anomaly Model\n(Unsupervised Normalized Features)"]
        Rules["Clinical Rules Engine\n(Multi-family drift, Fall, SOS)"]
        Benign["Benign Explanation Filter\n(Travel verification, Festival calibration)"]
        Budget["Alert Budget Gating\n(Max N=10 per coordinator shift)"]
    end

    subgraph Safe_Presentation_Layer ["Safety Filter & Role Portals"]
        Safety["100% Non-Diagnostic Safety Filter\n(Regex Blocklist: EN, HI, Hinglish)"]
        CoordUI["Care Coordinator Command Center\n(/coordinator/dashboard)"]
        SeniorUI["Accessible Senior Portal\n(/senior/dashboard, /senior/check-in)"]
        FamilyUI["Family Member Circle\n(/family/dashboard, /family/consent)"]
        OpsUI["Operations & SLA Dashboard\n(/operations/dashboard)"]
    end

    V & M & A & C --> LaggedBase
    N --> NLP
    LaggedBase & NLP --> IF & Rules
    IF & Rules --> Benign --> Budget --> Safety
    Safety --> CoordUI & SeniorUI & FamilyUI & OpsUI
```

---

## 2. Telemetry Ingestion Contracts

All signals arrive through standardized REST endpoints at `/api/v1/signals/{senior_id}`:

| Signal Family | Schema / Model | Key Fields | Source Hardware / Input |
| :--- | :--- | :--- | :--- |
| **Vital Signs** | `VitalObservation` | `spo2`, `sys_bp`, `dia_bp`, `blood_glucose` | Bluetooth Pulse Oximeter, Smart BP Cuff |
| **Medication Logs** | `MedicationLog` | `status` (taken/missed), `taken_pct`, `schedule_id` | Connected Smart Pill Dispenser |
| **Ambient IoT Activity** | `VitalObservation` | `inactivity_hours`, `night_bathroom_visits`, `door_events` | Fall radar, Sleep sensor mat, PIR door sensor |
| **Daily Voice Check-in** | `CheckIn` | `wellbeing_status`, `voice_note_url`, `fatigue_reported` | Senior Web Portal, Automated IVR phone check-in |
| **Coordinator Notes** | `CallNote` | `raw_text`, `call_duration_seconds`, `contact_type` | Care Coordinator CRM entry (Hindi/English) |

---

## 3. Database Entity Relationship (ER) Model

The relational persistence layer is implemented in SQLite/PostgreSQL with SQLAlchemy 2.0:

```mermaid
erDiagram
    USERS ||--o{ SENIORS : "coordinates"
    USERS ||--o{ FAMILY_SENIOR_RELATION : "linked_to"
    USERS ||--o{ ALERTS : "assigned_to"
    USERS ||--o{ AUDIT_LOGS : "performed_by"
    SENIORS ||--o{ VITALS : "records"
    SENIORS ||--o{ MEDICATION_LOGS : "logs"
    SENIORS ||--o{ CHECK_INS : "submits"
    SENIORS ||--o{ CALL_NOTES : "logged_for"
    SENIORS ||--o{ DAILY_RISK : "evaluates"
    SENIORS ||--o{ ALERTS : "triggers"
    ALERTS ||--o{ ALERT_FEEDBACK : "receives"
    ALERTS ||--o{ FOLLOW_UPS : "schedules"

    USERS {
        int id PK
        string email
        string hashed_password
        string role "coordinator | senior | family | ops | admin"
        string full_name
        string phone_number
    }

    SENIORS {
        string id PK
        string full_name
        int age
        string gender
        string city
        string primary_language
        boolean family_consent
        float baseline_spo2
        float baseline_sys_bp
        float baseline_dia_bp
        float baseline_night_bathroom
        float baseline_inactivity_hours
    }

    DAILY_RISK {
        int id PK
        string senior_id FK
        string date
        float risk_score "0 to 100"
        string risk_category "LOW | MODERATE | HIGH | URGENT"
        float rules_score
        float anomaly_score
        json top_contributors
        json suggested_action
    }

    ALERTS {
        int id PK
        string senior_id FK
        string date
        float risk_score
        string risk_category
        string status "PENDING | ACKNOWLEDGED | RESOLVED | ESCALATED"
        int assigned_coordinator_id FK
        string resolution_notes
    }
```

---

## 4. Role-Based Access Control (RBAC) & Boundary Enforcements

Data access permissions are enforced directly in the database query layer:

1. **Care Coordinator (`coordinator`)**:
   - Access restricted to seniors where `senior.assigned_coordinator_id == current_user.id`.
   - Accessing another coordinator's senior immediately raises `HTTP 403 Forbidden`.
2. **Family Member (`family`)**:
   - Access restricted to the explicitly linked senior in `family_senior_relation`.
   - Reassuring, non-alarming aggregated weekly wellbeing summaries.
   - Acute notifications dispatched **only** when `family_consent == True`.
3. **Operations Manager (`ops`)**:
   - Macro-level operational views: alert velocity, response time SLA distributions, coordinator workloads.
   - **Confidential Notes Redacted**: Personal call notes and raw audio are excluded.
4. **Senior Citizen (`senior`)**:
   - High-contrast, large touch targets, English/Hindi toggles, routine check-offs, voice check-in, and emergency SOS button.

---

## 5. Non-Diagnostic Safety Charter

SaathiCare AI does not provide clinical diagnoses. Every outgoing string generated for coordinators or families passes through `backend/app/services/safety.py`:
- Blocklist scrubs medical disease terms across English, Hindi, and Hinglish (`pneumonia`, `heart attack`, `stroke`, `diabetes`, `copd`, `dementia`, etc.).
- Replaces clinical diagnostic assumptions with neutral behavioral and biomarker trajectory descriptions (`respiratory variation`, `adherence gap`, `nighttime restlessness`).
- Clearly emphasizes that doctor appointments are human coordinator recommendations, not system prescriptions.

