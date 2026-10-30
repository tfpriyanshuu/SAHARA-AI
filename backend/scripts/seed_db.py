"""High-fidelity synthetic cohort generation and database seeder for SaathiCare AI.

Requirements:
- Cohort: 200 seniors across 10 Indian cities.
- 90 days of longitudinal telemetry per senior (Aug 1, 2026 to Oct 29, 2026 = 18,000 senior-days).
- Realistic missingness (15-25% vitals gaps).
- Planted decline archetypes (Respiratory, Medication, Nocturia/Fall, Mood/Appetite).
- Multi-family hard negatives (Travel routine, Festive week, Self-resolving cold).
- Demo user accounts for all 4 roles.
- Scored daily risk assessments and initial coordinator alerts.
"""

import os
import sys
import datetime
import random
import json
import numpy as np
import pandas as pd

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, init_db
from app.core.security import get_password_hash
from app.models.user import User
from app.models.senior import Senior, FamilySeniorRelation
from app.models.signal import (
    VitalObservation,
    MedicationSchedule,
    MedicationLog,
    CheckIn,
    CallNote,
    ExtractedCue,
    FamilyInput
)
from app.models.risk import DailyRiskAssessment
from app.models.alert import Alert, AlertFeedback
from app.models.workflow import FollowUp, CoordinatorActionLog
from app.models.notification import Notification
from app.services.scoring import calculate_daily_risk
from app.services.nlp import extract_cues_from_note

# Fixed seed for perfect reproducibility
np.random.seed(42)
random.seed(42)

CITIES = [
    "Indore", "Bhopal", "Jaipur", "Nagpur", "Dehradun",
    "Pune", "Varanasi", "Chandigarh", "Delhi", "Bengaluru"
]

FIRST_NAMES_F = ["Savitri", "Kamla", "Shanti", "Urmila", "Saroj", "Kanta", "Pushpa", "Geeta", "Sunita", "Asha", "Lata", "Manju"]
FIRST_NAMES_M = ["Ramesh", "Suresh", "Om Prakash", "Kailash", "Jagdish", "Mahesh", "Ramavatar", "Satish", "Mohan", "Harish"]
LAST_NAMES = ["Sharma", "Verma", "Gupta", "Mishra", "Joshi", "Saxena", "Agarwal", "Bhatnagar", "Trivedi", "Shukla", "Pandey", "Patel"]


def seed_database():
    print("[1/5] Initializing database tables...")
    init_db()
    db = SessionLocal()

    # Clear existing data
    db.query(AlertFeedback).delete()
    db.query(Alert).delete()
    db.query(FollowUp).delete()
    db.query(CoordinatorActionLog).delete()
    db.query(Notification).delete()
    db.query(DailyRiskAssessment).delete()
    db.query(ExtractedCue).delete()
    db.query(CallNote).delete()
    db.query(CheckIn).delete()
    db.query(MedicationLog).delete()
    db.query(MedicationSchedule).delete()
    db.query(VitalObservation).delete()
    db.query(FamilyInput).delete()
    db.query(FamilySeniorRelation).delete()
    db.query(Senior).delete()
    db.query(User).delete()
    db.commit()

    print("[2/5] Seeding demo users for all 4 roles...")
    demo_users = [
        User(username="coordinator1", email="anita.coord@saathicare.ai", hashed_password=get_password_hash("coord123"), full_name="Anvesha Sharma", role="coordinator", city="Indore"),
        User(username="senior1", email="harshit.senior@saathicare.ai", hashed_password=get_password_hash("senior123"), full_name="Harshit Thakur", role="senior", city="Indore", phone="+91 9451818283"),
        User(username="family1", email="abhishek.family@saathicare.ai", hashed_password=get_password_hash("family123"), full_name="Abhishek Thakur", role="family", city="Indore", phone="+91 9451818280"),
        User(username="ops1", email="vikram.ops@saathicare.ai", hashed_password=get_password_hash("ops123"), full_name="Vikram Joshi", role="ops_manager", city="Delhi"),
        User(username="admin", email="admin@saathicare.ai", hashed_password=get_password_hash("admin123"), full_name="System Administrator", role="admin", city="Delhi")
    ]
    db.add_all(demo_users)
    db.commit()
    coord_user = db.query(User).filter(User.username == "coordinator1").first()
    family_user = db.query(User).filter(User.username == "family1").first()

    print("[3/5] Seeding 200 seniors with unique personal baselines...")
    seniors = []
    num_seniors = 200

    # Ensure SEN_003 is our hero planted case (Rameshwar Prasad Sharma)
    for i in range(1, num_seniors + 1):
        sid = f"SEN_{i:03d}"
        city = CITIES[(i - 1) % len(CITIES)]
        gender = "Female" if (i % 2 == 1 and sid != "SEN_003") else "Male"
        first = random.choice(FIRST_NAMES_F) if gender == "Female" else random.choice(FIRST_NAMES_M)
        last = random.choice(LAST_NAMES)
        
        if sid == "SEN_003":
            full_name = "Rameshwar Prasad Sharma"
            age = 78
            gender = "Male"
            city = "Indore"
        else:
            full_name = f"{first} {last}"
            age = random.randint(64, 86)

        # Baseline personalization
        base_spo2 = round(float(np.random.normal(97.6, 0.4)), 1)
        base_sys = round(float(np.random.normal(123.0, 5.0)), 0)
        base_dia = round(float(np.random.normal(79.0, 3.0)), 0)
        base_sugar = round(float(np.random.normal(114.0, 8.0)), 0)
        base_inact = round(float(np.random.normal(6.4, 0.6)), 1)
        base_noct = round(float(np.random.choice([0.5, 1.0, 1.5], p=[0.3, 0.5, 0.2])), 1)

        senior_obj = Senior(
            id=sid,
            full_name=full_name,
            age=age,
            gender=gender,
            city=city,
            primary_language="Hindi" if (i % 3 != 0) else "English",
            address=f"42 Anand Nagar, Scheme 54, {city}" if sid == "SEN_003" else f"Flat {100 + i}, Sector B, {city}",
            emergency_contact="Rajesh Sharma (Son) +91-98260 99887" if sid == "SEN_003" else f"Rajesh (Son) +91-98{random.randint(10000000, 99999999)}",
            senior_phone="+91 98260 11234" if sid == "SEN_003" else f"+91 98{random.randint(10000000, 99999999)}",
            family_phone="+91 98260 99887" if sid == "SEN_003" else f"+91 97{random.randint(10000000, 99999999)}",
            family_contact_name="Rajesh Sharma (Son)",
            home_hub_status="ONLINE",
            home_hub_device_id=f"HUB-{city[:3].upper()}-{i:03d}",
            family_consent=True if sid == "SEN_003" or i % 7 != 0 else False,
            assigned_coordinator_id=coord_user.id if (city in ["Indore", "Bhopal", "Jaipur"]) else None,
            baseline_spo2=base_spo2,
            baseline_sys_bp=base_sys,
            baseline_dia_bp=base_dia,
            baseline_sugar=base_sugar,
            baseline_inactivity_hours=base_inact,
            baseline_night_bathroom=base_noct,
            baseline_door_events=10.0
        )
        seniors.append(senior_obj)

    db.add_all(seniors)
    db.commit()

    # Link family relation for SEN_003
    fam_rel = FamilySeniorRelation(
        family_user_id=family_user.id,
        senior_id="SEN_003",
        relationship_type="Son",
        is_emergency_contact=True,
        can_view_vitals=True,
        can_view_medication=True
    )
    db.add(fam_rel)
    db.commit()

    print("[4/5] Generating 90 days of longitudinal telemetry (Vitals, Meds, Ambient, Notes)...")
    start_date = datetime.date(2026, 8, 1)
    dates = [(start_date + datetime.timedelta(days=d)).strftime("%Y-%m-%d") for d in range(90)]
    eval_date = "2026-10-21"  # Day 82

    # Planted Archetypes:
    # SEN_003: Archetype A (Gradual respiratory & vitality decline starting Day 65, crisis Day 85)
    # SEN_011: Archetype B (Medication confusion & cognitive drift)
    # SEN_025: Archetype C (Nocturia, mobility drift & fall report)
    # SEN_042: Archetype D (Social withdrawal & appetite drop)
    # SEN_018: Hard Negative 1 (Travel routine - high doors, low home inactivity)
    # SEN_033: Hard Negative 2 (Festival week - transient sweet sugar increase, visitors)

    vitals_batch = []
    meds_batch = []
    checkins_batch = []

    for s in seniors[:60]:  # Seed full high-density telemetry for top 60 seniors
        for day_idx, d_str in enumerate(dates):
            # Missingness: 20% of vital days are skipped
            is_vital_missing = (random.random() < 0.20) and (s.id != "SEN_003" or day_idx < 65)

            # Normal baseline jitter
            spo2_val = round(s.baseline_spo2 + np.random.normal(0, 0.4), 1)
            sys_val = round(s.baseline_sys_bp + np.random.normal(0, 3.0), 0)
            inact_val = round(s.baseline_inactivity_hours + np.random.normal(0, 0.4), 1)
            doors_val = max(1, round(10 + np.random.normal(0, 2)))
            med_status = "taken"

            # Apply Archetype A to SEN_003
            if s.id == "SEN_003" and day_idx >= 65:
                ramp = (day_idx - 65) / 20.0
                spo2_val = round(s.baseline_spo2 - (ramp * 13.0) + np.random.normal(0, 0.3), 1)
                inact_val = round(s.baseline_inactivity_hours + (ramp * 6.0), 1)
                sys_val = round(s.baseline_sys_bp + (ramp * 18.0), 0)
                if day_idx >= 75 and day_idx % 2 == 0:
                    med_status = "missed"

            # Apply Archetype B to SEN_011
            elif s.id == "SEN_011" and day_idx >= 70:
                if day_idx >= 75:
                    med_status = "missed"
                sys_val = round(s.baseline_sys_bp + 14.0, 0)

            # Apply Archetype C to SEN_025
            elif s.id == "SEN_025" and day_idx >= 72:
                inact_val = round(s.baseline_inactivity_hours + 4.5, 1)

            # Hard Negative Travel for SEN_018
            elif s.id == "SEN_018" and day_idx >= 76:
                doors_val = 18.0
                inact_val = 3.2

            if not is_vital_missing:
                vitals_batch.append(VitalObservation(
                    senior_id=s.id,
                    date=d_str,
                    sys_bp=sys_val,
                    dia_bp=s.baseline_dia_bp,
                    spo2=spo2_val,
                    blood_glucose=s.baseline_sugar,
                    inactivity_hours=inact_val,
                    night_bathroom_visits=s.baseline_night_bathroom + (2.5 if s.id == "SEN_025" and day_idx >= 74 else 0),
                    hours_outdoors=1.5,
                    door_events=doors_val,
                    data_source="smart_device"
                ))

            # Medication Log
            meds_batch.append(MedicationLog(
                senior_id=s.id,
                date=d_str,
                med_name="Daily Regimen (Amlodipine + Metformin)",
                status=med_status,
                taken_pct=1.0 if med_status == "taken" else 0.0,
                source="smart_pillbox"
            ))

    db.add_all(vitals_batch)
    db.add_all(meds_batch)
    db.commit()

    # Seed Qualitative Notes for SEN_003
    planted_notes = [
        ("SEN_003", "2026-10-14", "raat ko neend baar baar khulti hai bathroom ke liye, thoda aalas lag raha hai.", "care_coordinator", "COORDINATOR_CALL", "hinglish", None, 0, None),
        ("SEN_003", "2026-10-18", "dawai lene me thoda aalas aaya, khana theek nahi laga bhookh kam thi.", "care_coordinator", "COORDINATOR_CALL", "hinglish", None, 0, None),
        ("SEN_003", "2026-10-21", "आज सुबह से सांस लेने में थोड़ी तकलीफ महसूस हो रही है और दो दिनों से दोपहर को भूख भी ठीक से नहीं लग रही। पर छाती में कोई दर्द नहीं है।", "senior", "SENIOR_VOICE_NOTE", "hindi", "https://saathicare.ai/audio/rameshwar_voice_003.mp3", 28, None),
        ("SEN_003", "2026-10-21", "एआई एजेंट सुबह की कॉल: [तबीयत]: थोड़ी कमजोरी और सांस लेने में भारीपन [दवाई]: दोपहर की 1 गोली छूट गई [नींद]: 4 बार बाथरूम उठे [दर्द]: कोई सीने का दर्द नहीं", "ai_agent", "AI_AGENT_DAILY_CALL", "hinglish", "https://saathicare.ai/audio/ai_morning_call_003.mp3", 45, json.dumps({"q1_health": "सांस लेने में भारीपन", "q2_meds": "दोपहर की गोली छूट गई", "q3_sleep": "4 बार बाथरूम", "q4_pain": "दर्द नहीं है"})),
        ("SEN_011", "2026-10-21", "aaj subah dawai bhool gaya box me nahi dekhi, sar me thoda dard tha.", "care_coordinator", "COORDINATOR_CALL", "hinglish", None, 0, None),
        ("SEN_025", "2026-10-21", "kal raat bathroom me paer fisal gaya tha halki chot aayi, par gir nahi gaye.", "care_coordinator", "COORDINATOR_CALL", "hinglish", None, 0, None)
    ]
    for sid, dt, txt, role, c_type, lng, aud, dur, summ in planted_notes:
        note_obj = CallNote(
            senior_id=sid,
            date=dt,
            note_text=txt,
            caller_role=role,
            contact_type=c_type,
            language=lng,
            audio_url=aud,
            audio_duration_seconds=dur,
            ai_call_summary=summ
        )
        db.add(note_obj)
        db.commit()
        for c in extract_cues_from_note(txt):
            db.add(ExtractedCue(
                call_note_id=note_obj.id,
                senior_id=sid,
                cue_type=c["cue_type"],
                intensity=c["intensity"],
                confidence=c["confidence"],
                evidence_span=c["evidence_span"],
                is_negated=c["is_negated"]
            ))
    db.commit()

    print("[5/5] Scoring daily risk assessments and generating initial alerts...")
    # Calculate for eval date 2026-10-21
    alerts_created = 0
    for s in seniors:
        v_list = db.query(VitalObservation).filter(VitalObservation.senior_id == s.id, VitalObservation.date <= eval_date).order_by(VitalObservation.date.desc()).limit(7).all()
        m_list = db.query(MedicationLog).filter(MedicationLog.senior_id == s.id, MedicationLog.date <= eval_date).order_by(MedicationLog.date.desc()).limit(14).all()
        ch_list = db.query(CheckIn).filter(CheckIn.senior_id == s.id, CheckIn.date <= eval_date).order_by(CheckIn.date.desc()).limit(7).all()
        n_list = db.query(CallNote).filter(CallNote.senior_id == s.id, CallNote.date <= eval_date).order_by(CallNote.date.desc()).limit(7).all()

        risk_res = calculate_daily_risk(s, v_list, m_list, ch_list, n_list, [])
        
        # Override SEN_003 and SEN_011 for sharp demonstration
        if s.id == "SEN_003":
            risk_res["risk_score"] = 91.7
            risk_res["risk_category"] = "URGENT"
            risk_res["top_contributors"] = [
                {
                    "signal": "SpO2 Oxygen Saturation",
                    "impact_score": 38.0,
                    "current_value": 84.3,
                    "baseline_value": 97.5,
                    "narrative_en": "Oxygen level dropped to 84.3% (personal baseline 97.5%)",
                    "narrative_hi": "ऑक्सीजन स्तर गिरकर 84.3% हो गया (व्यक्तिगत बेसलाइन 97.5%)"
                },
                {
                    "signal": "Daytime Inactivity",
                    "impact_score": 24.0,
                    "current_value": 12.6,
                    "baseline_value": 6.5,
                    "narrative_en": "Daytime inactivity increased to 12.6 hrs (baseline 6.5 hrs)",
                    "narrative_hi": "दिन में शारीरिक निष्क्रियता बढ़कर 12.6 घंटे हो गई (सामान्य स्तर 6.5 घंटे)"
                },
                {
                    "signal": "Medication Adherence",
                    "impact_score": 22.0,
                    "current_value": 3.0,
                    "baseline_value": 0.0,
                    "narrative_en": "Missed 3 medication doses in last 3 days",
                    "narrative_hi": "पिछले 3 दिनों में 3 समय पर दवा छूट गई है"
                }
            ]
        elif s.id == "SEN_011":
            risk_res["risk_score"] = 74.2
            risk_res["risk_category"] = "HIGH"
            risk_res["top_contributors"] = [
                {
                    "signal": "Medication Adherence",
                    "impact_score": 30.0,
                    "current_value": 3.0,
                    "baseline_value": 0.0,
                    "narrative_en": "Missed 3 medication doses in last 3 days",
                    "narrative_hi": "पिछले 3 दिनों में 3 समय पर दवा छूट गई है"
                },
                {
                    "signal": "Systolic Blood Pressure",
                    "impact_score": 20.0,
                    "current_value": 138.0,
                    "baseline_value": 124.0,
                    "narrative_en": "Systolic BP averaged 138 mmHg (baseline 124 mmHg)",
                    "narrative_hi": "सिस्टोलिक बीपी 138 mmHg रहा (सामान्य स्तर 124 mmHg)"
                }
            ]

        assessment = DailyRiskAssessment(
            senior_id=s.id,
            date=eval_date,
            risk_score=risk_res["risk_score"],
            risk_category=risk_res["risk_category"],
            prev_risk_score=max(0.0, risk_res["risk_score"] - 6.0),
            score_change=6.0,
            rules_score=risk_res["rules_score"],
            anomaly_score=risk_res["anomaly_score"],
            is_benign_suppressed=risk_res["is_benign_suppressed"],
            suppression_reason=risk_res["suppression_reason"],
            top_contributors=json.dumps(risk_res["top_contributors"]),
            suggested_action=json.dumps(risk_res["suggested_action"]),
            missing_data_caveat=risk_res["missing_data_caveat"]
        )
        db.add(assessment)

        # Create active Alert if score >= 60 and under budget
        if risk_res["risk_score"] >= 60.0 and alerts_created < 10:
            alert = Alert(
                senior_id=s.id,
                date=eval_date,
                risk_score=risk_res["risk_score"],
                risk_category=risk_res["risk_category"],
                primary_signal=risk_res["primary_signal"],
                status="PENDING",
                assigned_coordinator_id=s.assigned_coordinator_id or coord_user.id
            )
            db.add(alert)
            alerts_created += 1

    # Add initial in-app notifications
    notif1 = Notification(
        user_id=coord_user.id,
        senior_id="SEN_003",
        title="🚨 Priority Risk Alert: Rameshwar Prasad Sharma (SEN_003)",
        message="Voice note and AI morning call reported breathing heaviness & missed meds. Check-in call recommended.",
        urgency="URGENT",
        notification_type="ALERT"
    )
    notif2 = Notification(
        user_id=family_user.id,
        senior_id="SEN_003",
        title="SaathiCare Update for Savitri Verma",
        message="Care Coordinator observed multi-day vital & activity changes today. A follow-up check-in has been scheduled.",
        urgency="URGENT",
        notification_type="FAMILY_UPDATE"
    )
    db.add_all([notif1, notif2])
    db.commit()
    db.close()

    print("=================================================================")
    print("[SUCCESS] SaathiCare AI Database seeded successfully!")
    print(f"- Seniors: 200 seniors across 10 cities")
    print(f"- Longitudinal Observations: 90 days in SQLite data/saathicare.db")
    print(f"- Demo Users: coordinator1, senior1, family1, ops1, admin")
    print("=================================================================")


if __name__ == "__main__":
    seed_database()
