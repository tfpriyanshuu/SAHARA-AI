"""Seed realistic check-in timeline calls, device health, and turns for Top 6 Seniors."""

import os
import sys
import json
import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.checkin import SeniorDevice, CheckinCall, CheckinTurn
from app.models.senior import Senior

def seed():
    db = SessionLocal()
    now = datetime.datetime.utcnow()
    
    top_seniors = ["SEN_001", "SEN_002", "SEN_003", "SEN_004", "SEN_005", "SEN_006"]
    
    # 1. Seed Senior Devices
    for sid in top_seniors:
        senior = db.query(Senior).filter(Senior.id == sid).first()
        if not senior:
            continue
        dev = db.query(SeniorDevice).filter(SeniorDevice.senior_id == sid).first()
        is_healthy = True if sid != "SEN_005" else False
        if not dev:
            dev = SeniorDevice(
                senior_id=sid,
                device_id=f"PWA-DEV-{sid}",
                app_version="1.2.0-pwa",
                paired_at=now - datetime.timedelta(days=12),
                last_seen=now - datetime.timedelta(minutes=5 if sid != "SEN_005" else 1500),
                notifications_enabled=True,
                mic_permission=True,
                fullscreen_permission=True,
                battery_optimisation_disabled=True,
                is_healthy=is_healthy
            )
            db.add(dev)
        else:
            dev.is_healthy = is_healthy
            dev.last_seen = now - datetime.timedelta(minutes=5 if sid != "SEN_005" else 1500)

    # 2. Seed Rich Call for Harshit Thakur (SEN_001)
    call_001 = db.query(CheckinCall).filter(CheckinCall.checkin_id == "chk_today_sen_001").first()
    if not call_001:
        call_001 = CheckinCall(
            checkin_id="chk_today_sen_001",
            event_id="evt_001_today",
            senior_id="SEN_001",
            coordinator_id=1,
            coordinator_name="Anvesha Sharma",
            caller_name="Sahara AI",
            caller_label="सहारा AI",
            status="completed",
            rang_at=now - datetime.timedelta(hours=2, minutes=30),
            answered_at=now - datetime.timedelta(hours=2, minutes=29, seconds=45),
            ended_at=now - datetime.timedelta(hours=2, minutes=27),
            duration_seconds=165,
            risk_score_before=84.0,
            risk_score_after=98.5,
            summary_en="CRITICAL EMERGENCY: Acute chest pain radiating leftward reported with severe insomnia. Priority #1 medical intervention.",
            summary_hi="अति-गंभीर आपातकाल: सीने में भारीपन और दर्द बाईं तरफ जा रहा है, रात को नींद नहीं आई। तत्काल सहायता आवश्यक।",
            stt_confidence=0.98,
            needs_review=True,
            is_emergency=True,
            is_reviewed=False
        )
        db.add(call_001)
        db.commit()

        turns = [
            CheckinTurn(
                checkin_id="chk_today_sen_001",
                event_id="evt_turn_001_1",
                turn_index=1,
                question_text="आज आप कैसा महसूस कर रहे हैं? अच्छा हो तो 1, ठीक-ठाक हो तो 2, अच्छा नहीं हो तो 3 दबाइए, या बोल दीजिए।",
                audio_url="http://localhost:8000/static/audio/sarvam_1793319413_998c75.wav",
                keypad_input="3",
                transcript="आज बिल्कुल अच्छा नहीं लग रहा, बहुत भारीपन है।",
                confidence=0.97,
                cues_extracted=json.dumps([{"cue_type": "poor_health", "confidence": 0.95, "is_negated": False}]),
                is_emergency=False,
                timestamp=now - datetime.timedelta(hours=2, minutes=29)
            ),
            CheckinTurn(
                checkin_id="chk_today_sen_001",
                event_id="evt_turn_001_2",
                turn_index=4,
                question_text="कहीं दर्द, चक्कर या साँस में तकलीफ़ है आज?",
                audio_url="http://localhost:8000/static/audio/sarvam_1793319413_998c75.wav",
                keypad_input="haan",
                transcript="सीने में भारीपन और तेज दर्द है, बाईं तरफ जा रहा है। रात भर नींद नहीं आई।",
                confidence=0.99,
                cues_extracted=json.dumps([
                    {"cue_type": "chest_pain", "confidence": 0.99, "is_negated": False, "evidence_span": "सीने में भारीपन और तेज दर्द"},
                    {"cue_type": "sleep_deterioration", "confidence": 0.95, "is_negated": False, "evidence_span": "रात भर नींद नहीं आई"}
                ]),
                is_emergency=True,
                timestamp=now - datetime.timedelta(hours=2, minutes=28)
            )
        ]
        db.add_all(turns)

    # 3. Seed Call for Anchal (SEN_003) - Pill Mismatch
    call_003 = db.query(CheckinCall).filter(CheckinCall.checkin_id == "chk_today_sen_003").first()
    if not call_003:
        call_003 = CheckinCall(
            checkin_id="chk_today_sen_003",
            event_id="evt_003_today",
            senior_id="SEN_003",
            coordinator_id=1,
            coordinator_name="Anvesha Sharma",
            caller_name="Sahara AI",
            caller_label="सहारा AI",
            status="completed",
            rang_at=now - datetime.timedelta(hours=1, minutes=45),
            answered_at=now - datetime.timedelta(hours=1, minutes=44, seconds=50),
            ended_at=now - datetime.timedelta(hours=1, minutes=42),
            duration_seconds=170,
            risk_score_before=72.0,
            risk_score_after=94.5,
            summary_en="HIGH RISK: Missed BP dose with postural dizziness and pillbox mismatch. Medication refill required.",
            summary_hi="उच्च जोखिम: बीपी की दवा छूटी, चक्कर आ रहा है, पिल बॉक्स मिसमैच। रीफिल की आवश्यकता।",
            stt_confidence=0.97,
            needs_review=True,
            is_emergency=False,
            is_reviewed=False
        )
        db.add(call_003)
        db.commit()

        turns_003 = [
            CheckinTurn(
                checkin_id="chk_today_sen_003",
                event_id="evt_turn_003_1",
                turn_index=3,
                question_text="आज की दवाई ली?",
                audio_url="http://localhost:8000/static/audio/sarvam_1793319398_c6a1a3.wav",
                keypad_input="nahi",
                transcript="दोपहर की गोली भूल गए, डिब्बी में खत्म हो गई है।",
                confidence=0.98,
                cues_extracted=json.dumps([{"cue_type": "missed_medication", "confidence": 0.98, "is_negated": False}]),
                is_emergency=False,
                timestamp=now - datetime.timedelta(hours=1, minutes=43)
            ),
            CheckinTurn(
                checkin_id="chk_today_sen_003",
                event_id="evt_turn_003_2",
                turn_index=4,
                question_text="कहीं दर्द, चक्कर या साँस में तकलीफ़ है आज?",
                audio_url="http://localhost:8000/static/audio/sarvam_1793319398_c6a1a3.wav",
                keypad_input="haan",
                transcript="हल्का चक्कर आ रहा है, सीने में दर्द नहीं है।",
                confidence=0.96,
                cues_extracted=json.dumps([
                    {"cue_type": "dizziness", "confidence": 0.94, "is_negated": False},
                    {"cue_type": "chest_pain", "confidence": 0.91, "is_negated": True}
                ]),
                is_emergency=False,
                timestamp=now - datetime.timedelta(hours=1, minutes=42)
            )
        ]
        db.add_all(turns_003)

    # 4. Seed Call for Vikas (SEN_005) - Missed Call
    call_005 = db.query(CheckinCall).filter(CheckinCall.checkin_id == "chk_today_sen_005").first()
    if not call_005:
        call_005 = CheckinCall(
            checkin_id="chk_today_sen_005",
            event_id="evt_005_today",
            senior_id="SEN_005",
            coordinator_id=1,
            coordinator_name="Anvesha Sharma",
            caller_name="Sahara AI",
            caller_label="सहारा AI",
            status="missed",
            rang_at=now - datetime.timedelta(hours=1, minutes=15),
            answered_at=None,
            ended_at=now - datetime.timedelta(hours=1, minutes=14),
            duration_seconds=0,
            risk_score_before=75.0,
            risk_score_after=79.5,
            summary_en="MISSED CALL: Routine check-in unanswered (Retry 2/3 scheduled). Device heartbeat delayed.",
            summary_hi="छूटी हुई कॉल: रूटीन चेक-इन कॉल नहीं उठी (पुनः प्रयास 2/3)। डिवाइस हार्टबीट में देरी।",
            stt_confidence=1.0,
            needs_review=True,
            is_emergency=False,
            is_reviewed=False
        )
        db.add(call_005)

    db.commit()
    print("Successfully seeded realistic check-in calls and device health for top seniors.")

if __name__ == "__main__":
    seed()

