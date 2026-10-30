"""Setup 6 Priority Demo Seniors for Care Coordinator Anvesha Sharma:
1. Harshit Thakur - +91 9451818283 (Score: 98.5 - CRITICAL EMERGENCY)
2. Anvesha - +91 8267069623 (Score: 94.0 - URGENT)
3. Anchal - +91 8957266841 (Score: 88.5 - HIGH)
4. Priyanshu - +91 6307120421 (Score: 84.0 - HIGH)
5. Vikas - +91 8445168405 (Score: 79.5 - HIGH)
6. Sejal - +91 7017464158 (Score: 72.0 - HIGH)
"""

import os
import sys
import json
import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.senior import Senior
from app.models.risk import DailyRiskAssessment
from app.models.alert import Alert
from app.models.signal import CallNote, ExtractedCue, VitalObservation

DEMO_SENIORS = [
    {
        "id": "SEN_001",
        "full_name": "Harshit Thakur",
        "age": 76,
        "gender": "Male",
        "city": "Indore",
        "senior_phone": "+91 9451818283",
        "family_phone": "+91 9451818280",
        "family_contact_name": "Abhishek Thakur (Son)",
        "home_hub_device_id": "HUB-IND-001",
        "home_hub_status": "ONLINE",
        "score": 98.5,
        "category": "URGENT",
        "alert_title": "🚨 Real Voice Note & IoT Alert: Acute Chest Pain & Insomnia",
        "transcript": "1. सेहत/मूड: अच्छा नहीं (3) | 2. खाना: भूख नहीं लगी | 3. दवा: ली थी | 4. लक्षण: सीने में भारीपन और दर्द है, बाईं तरफ जा रहा है | 5. टिप्पणी: रात को नींद नहीं आई",
        "summary_en": "CRITICAL EMERGENCY: Acute chest pain radiating leftward reported with severe insomnia. Priority #1 medical intervention.",
        "summary_hi": "अति-गंभीर आपातकाल: सीने में दर्द और अनिद्रा। तत्काल प्राथमिक चिकित्सा हस्तक्षेप आवश्यक।",
        "cues": [
            {"cue_type": "chest_pain", "confidence": 0.99, "is_negated": False, "evidence_span": "सीने में भारीपन और दर्द"},
            {"cue_type": "sleep_deterioration", "confidence": 0.95, "is_negated": False, "evidence_span": "रात को नींद नहीं आई"}
        ],
        "pill_mismatch": False
    },
    {
        "id": "SEN_002",
        "full_name": "Anvesha",
        "age": 74,
        "gender": "Female",
        "city": "Indore",
        "senior_phone": "+91 8267069623",
        "family_phone": "+91 8267069620",
        "family_contact_name": "Ritu Sharma (Daughter)",
        "home_hub_device_id": "HUB-IND-002",
        "home_hub_status": "ONLINE",
        "score": 94.0,
        "category": "URGENT",
        "alert_title": "⚠️ Respiratory Distress & Low Appetite",
        "transcript": "1. सेहत/मूड: अच्छा नहीं (3) | 2. खाना: दोपहर को थोड़ा खाया, भूख नहीं है | 3. दवा: ली है | 4. लक्षण: सांस लेने में तकलीफ हो रही है, सीने में दर्द नहीं है | 5. टिप्पणी: कमजोरी महसूस हो रही है",
        "summary_en": "URGENT: Shortness of breath with poor appetite and daytime fatigue. Respiratory check scheduled.",
        "summary_hi": "तत्काल: सांस लेने में तकलीफ और भूख में कमी। श्वसन जांच आवश्यक।",
        "cues": [
            {"cue_type": "breathing_difficulty", "confidence": 0.96, "is_negated": False, "evidence_span": "सांस लेने में तकलीफ"},
            {"cue_type": "low_appetite", "confidence": 0.91, "is_negated": False, "evidence_span": "भूख नहीं है"}
        ],
        "pill_mismatch": False
    },
    {
        "id": "SEN_003",
        "full_name": "Anchal",
        "age": 72,
        "gender": "Female",
        "city": "Indore",
        "senior_phone": "+91 8957266841",
        "family_phone": "+91 8957266840",
        "family_contact_name": "Saurabh Verma (Son)",
        "home_hub_device_id": "HUB-IND-003",
        "home_hub_status": "ONLINE",
        "score": 88.5,
        "category": "HIGH",
        "alert_title": "💊 Missed BP Medication & Dizziness (Pill Mismatch)",
        "transcript": "1. सेहत/मूड: ठीक-ठाक (2) | 2. खाना: सामान्य खाया | 3. दवा: दोपहर की गोली भूल गए, डिब्बी में खत्म हो गई है | 4. लक्षण: हल्का चक्कर आ रहा है | 5. टिप्पणी: दवा का रीफिल चाहिए",
        "summary_en": "HIGH RISK: Missed BP dose with postural dizziness and pillbox mismatch. Medication refill required.",
        "summary_hi": "उच्च जोखिम: बीपी की छूटी दवा, चक्कर और पिल बॉक्स में मिसमैच। रीफिल आवश्यक।",
        "cues": [
            {"cue_type": "missed_medication", "confidence": 0.98, "is_negated": False, "evidence_span": "दवा भूल गए / खत्म हो गई"},
            {"cue_type": "dizziness", "confidence": 0.92, "is_negated": False, "evidence_span": "हल्का चक्कर आ रहा है"},
            {"cue_type": "pill_box_mismatch", "confidence": 0.96, "is_negated": False, "evidence_span": "Self-reported medicine mismatch with sensor"}
        ],
        "pill_mismatch": True
    },
    {
        "id": "SEN_004",
        "full_name": "Priyanshu",
        "age": 77,
        "gender": "Male",
        "city": "Bhopal",
        "senior_phone": "+91 6307120421",
        "family_phone": "+91 6307120420",
        "family_contact_name": "Aditya Singh (Son)",
        "home_hub_device_id": "HUB-BHO-004",
        "home_hub_status": "ONLINE",
        "score": 84.0,
        "category": "HIGH",
        "alert_title": "🚶 Mobility Drift & Postural Instability",
        "transcript": "1. सेहत/मूड: ठीक-ठाक (2) | 2. खाना: थोड़ा खाया | 3. दवा: ली है | 4. लक्षण: सुबह उठते वक्त पैर लड़खड़ाया, कमजोरी लग रही है | 5. टिप्पणी: बाहर टहलने नहीं जा पाए",
        "summary_en": "HIGH RISK: Balance disturbance and leg stumble reported upon rising. Fall hazard assessment recommended.",
        "summary_hi": "उच्च जोखिम: बिस्तर से उठने पर संतुलन बिगड़ा। फॉल रिस्क का मूल्यांकन आवश्यक।",
        "cues": [
            {"cue_type": "mobility_issue", "confidence": 0.94, "is_negated": False, "evidence_span": "पैर लड़खड़ाया"},
            {"cue_type": "weakness", "confidence": 0.90, "is_negated": False, "evidence_span": "कमजोरी लग रही है"}
        ],
        "pill_mismatch": False
    },
    {
        "id": "SEN_005",
        "full_name": "Vikas",
        "age": 75,
        "gender": "Male",
        "city": "Jaipur",
        "senior_phone": "+91 8445168405",
        "family_phone": "+91 8445168400",
        "family_contact_name": "Neha Gupta (Daughter)",
        "home_hub_device_id": "HUB-JAI-005",
        "home_hub_status": "ONLINE",
        "score": 79.5,
        "category": "HIGH",
        "alert_title": "🌙 Nocturia & Severe Sleep Fragmentation",
        "transcript": "1. सेहत/मूड: ठीक-ठाक (2) | 2. खाना: आधी रोटी खाई | 3. दवा: ली थी | 4. लक्षण: रात को 4 बार बाथरूम उठे, नींद बार-बार टूटी | 5. टिप्पणी: दिन में सुस्ती लग रही है",
        "summary_en": "HIGH RISK: Multiple nocturnal bathroom visits with fragmented sleep and low appetite.",
        "summary_hi": "उच्च जोखिम: रात में 4 बार बाथरूम की हलचल और नींद टूटना। सुस्ती और भूख कम।",
        "cues": [
            {"cue_type": "sleep_deterioration", "confidence": 0.92, "is_negated": False, "evidence_span": "नींद बार-बार टूटी"},
            {"cue_type": "low_appetite", "confidence": 0.88, "is_negated": False, "evidence_span": "आधी रोटी खाई"}
        ],
        "pill_mismatch": False
    },
    {
        "id": "SEN_006",
        "full_name": "Sejal",
        "age": 73,
        "gender": "Female",
        "city": "Jaipur",
        "senior_phone": "+91 7017464158",
        "family_phone": "+91 7017464150",
        "family_contact_name": "Rohan Patel (Grandson)",
        "home_hub_device_id": "HUB-JAI-006",
        "home_hub_status": "ONLINE",
        "score": 72.0,
        "category": "HIGH",
        "alert_title": "💧 Hydration Deficit & Mild Dizziness",
        "transcript": "1. सेहत/मूड: ठीक-ठाक (2) | 2. खाना: खा लिया | 3. दवा: ली है | 4. लक्षण: सिर भारी लग रहा है और हल्का चक्कर आया | 5. टिप्पणी: पानी कम पिया था आज",
        "summary_en": "ELEVATED RISK: Dehydration indicators and lightheadedness. Hydration reminder queued.",
        "summary_hi": "सजगता: पानी की कमी और हल्का सिर घूमना। हाइड्रेशन फॉलो-अप कतार में।",
        "cues": [
            {"cue_type": "dizziness", "confidence": 0.85, "is_negated": False, "evidence_span": "हल्का चक्कर आया"},
            {"cue_type": "hydration_deficit", "confidence": 0.88, "is_negated": False, "evidence_span": "पानी कम पिया था"}
        ],
        "pill_mismatch": False
    }
]


def seed_priority_seniors():
    db = SessionLocal()
    today_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    # Lower any other seniors so these 6 are strictly #1 to #6
    db.query(DailyRiskAssessment).filter(
        ~DailyRiskAssessment.senior_id.in_(["SEN_001", "SEN_002", "SEN_003", "SEN_004", "SEN_005", "SEN_006"])
    ).update({"risk_score": 25.0, "risk_category": "LOW"}, synchronize_session=False)

    for item in DEMO_SENIORS:
        sid = item["id"]
        senior = db.query(Senior).filter(Senior.id == sid).first()
        if not senior:
            senior = Senior(
                id=sid,
                full_name=item["full_name"],
                age=item["age"],
                gender=item["gender"],
                city=item["city"],
                primary_language="Hindi",
                senior_phone=item["senior_phone"],
                family_phone=item["family_phone"],
                family_contact_name=item["family_contact_name"],
                home_hub_status=item["home_hub_status"],
                home_hub_device_id=item["home_hub_device_id"],
                assigned_coordinator_id=1,
                family_consent=True
            )
            db.add(senior)
        else:
            senior.full_name = item["full_name"]
            senior.age = item["age"]
            senior.gender = item["gender"]
            senior.city = item["city"]
            senior.senior_phone = item["senior_phone"]
            senior.family_phone = item["family_phone"]
            senior.family_contact_name = item["family_contact_name"]
            senior.assigned_coordinator_id = 1
            senior.family_consent = True

        db.commit()

        # Update or Create DailyRiskAssessment
        risk = db.query(DailyRiskAssessment).filter(DailyRiskAssessment.senior_id == sid).order_by(DailyRiskAssessment.id.desc()).first()
        top_contrib = [
            {
                "signal": item["alert_title"],
                "impact_score": round(item["score"] * 0.65, 1),
                "current_value": len(item["cues"]),
                "baseline_value": 0,
                "narrative_en": item["summary_en"],
                "narrative_hi": item["summary_hi"]
            }
        ]
        suggested_action = {
            "action": "Immediate Phone Call Verification" if item["category"] == "URGENT" else "Routine Health & Medication Touchpoint",
            "urgency": item["category"],
            "questions_hindi": ["दादाजी क्या आप ठीक हैं?", "दवा और सेहत की स्थिति कैसी है?"],
            "questions_en": ["Are you alright?", "How are your symptoms right now?"]
        }

        if not risk:
            risk = DailyRiskAssessment(
                senior_id=sid,
                date=today_str,
                risk_score=item["score"],
                risk_category=item["category"],
                top_contributors=json.dumps(top_contrib),
                suggested_action=json.dumps(suggested_action)
            )
            db.add(risk)
        else:
            risk.risk_score = item["score"]
            risk.risk_category = item["category"]
            risk.top_contributors = json.dumps(top_contrib)
            risk.suggested_action = json.dumps(suggested_action)

        # Update or Create Alert
        alert = db.query(Alert).filter(Alert.senior_id == sid).first()
        if not alert:
            alert = Alert(
                senior_id=sid,
                date=today_str,
                risk_score=item["score"],
                risk_category=item["category"],
                primary_signal=item["alert_title"],
                status="PENDING",
                assigned_coordinator_id=1
            )
            db.add(alert)
        else:
            alert.risk_score = item["score"]
            alert.risk_category = item["category"]
            alert.primary_signal = item["alert_title"]
            alert.status = "PENDING"
            alert.assigned_coordinator_id = 1

        # Add CallNote with recording and cues
        call_note = CallNote(
            senior_id=sid,
            date=today_str,
            note_text=item["transcript"],
            caller_role="senior",
            contact_type="SENIOR_VOICE_NOTE",
            audio_url="http://localhost:8000/static/audio/sarvam_1793319413_998c75.wav" if sid == "SEN_001" else "http://localhost:8000/static/audio/sarvam_1793319398_c6a1a3.wav",
            audio_duration_seconds=65,
            ai_call_summary=item["summary_en"],
            language="hi"
        )
        db.add(call_note)
        db.commit()
        db.refresh(call_note)

        # Add cues
        for c in item["cues"]:
            cue_obj = ExtractedCue(
                call_note_id=call_note.id,
                senior_id=sid,
                cue_type=c["cue_type"],
                confidence=c["confidence"],
                is_negated=c["is_negated"],
                evidence_span=c["evidence_span"]
            )
            db.add(cue_obj)

        db.commit()

    db.close()
    print("SUCCESS: 6 Priority demo seniors seeded at the very top of Anvesha Sharma's coordinator queue!")


if __name__ == "__main__":
    seed_priority_seniors()

