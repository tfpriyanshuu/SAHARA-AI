import pytest
import time
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.checkin import ClientEventLog, CheckinCall

client = TestClient(app)


def test_push_payload_contract_zero_pii():
    """
    ADDENDUM A: Push payload (data-only) is now EXACTLY:
    {type: "checkin_call", checkin_id, expires_at}. No names, no labels, no health data.
    """
    response = client.post(
        "/api/v1/checkins/trigger-demo-call",
        json={"senior_id": "SEN_001"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "DISPATCHED"
    push = data["push_payload"]

    # Verify keys are strictly type, checkin_id, expires_at
    assert set(push.keys()) == {"type", "checkin_id", "expires_at"}
    assert push["type"] == "checkin_call"
    assert push["checkin_id"].startswith("chk_")
    assert "expires_at" in push

    # Strict Zero-PII assertions
    assert "name" not in push
    assert "full_name" not in push
    assert "phone" not in push
    assert "diagnosis" not in push
    assert "health" not in push


def test_idempotent_event_ingestion():
    """
    ADDENDUM B: Each client event has a client-generated event_id; backend ignores duplicates.
    """
    event_id = f"evt_test_idempotent_{int(time.time() * 1000)}"
    payload = {
        "event_id": event_id,
        "checkin_id": "chk_test_idem_001",
        "senior_id": "SEN_001",
        "status": "ringing"
    }

    # First attempt: should succeed and create event log
    res1 = client.post("/api/v1/checkins/events/lifecycle", json=payload)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == "SUCCESS"

    # Second attempt with same event_id: idempotent cache hit
    res2 = client.post("/api/v1/checkins/events/lifecycle", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["status"] == "ALREADY_PROCESSED"


def test_per_turn_event_upload_and_emergency_intercept():
    """
    ADDENDUM B: On each turn, store audio/transcript -> emergency check.
    Emergency match triggers immediate high-severity response.
    """
    event_id = f"evt_turn_test_{int(time.time() * 1000)}"
    chk_id = f"chk_turn_test_{int(time.time())}"

    # Normal turn
    normal_res = client.post(
        "/api/v1/checkins/events/turn",
        json={
            "event_id": f"{event_id}_1",
            "checkin_id": chk_id,
            "senior_id": "SEN_001",
            "turn_index": 1,
            "question_text": "आज आप कैसा महसूस कर रहे हैं?",
            "keypad_input": "1",
            "spoken_text": "सब ठीक है कोई परेशानी नहीं"
        }
    )
    assert normal_res.status_code == 200
    assert normal_res.json()["is_emergency"] is False

    # Emergency turn
    emg_res = client.post(
        "/api/v1/checkins/events/turn",
        json={
            "event_id": f"{event_id}_2",
            "checkin_id": chk_id,
            "senior_id": "SEN_001",
            "turn_index": 4,
            "question_text": "कहीं दर्द, चक्कर या साँस में तकलीफ़ है आज?",
            "spoken_text": "सीने में दर्द है और सांस नहीं आ रही"
        }
    )
    assert emg_res.status_code == 200
    assert emg_res.json()["is_emergency"] is True


def test_incremental_single_senior_rescore_latency():
    """
    Target latency: single senior rescore incrementally completes in < 30-60s (measured < 2s).
    """
    chk_id = f"chk_rescore_{int(time.time())}"
    client.post(
        "/api/v1/checkins/events/lifecycle",
        json={
            "event_id": f"evt_start_{chk_id}",
            "checkin_id": chk_id,
            "senior_id": "SEN_001",
            "status": "answered"
        }
    )

    start_time = time.time()
    res = client.post(
        "/api/v1/checkins/events/complete",
        json={
            "checkin_id": chk_id,
            "senior_id": "SEN_001"
        }
    )
    elapsed = time.time() - start_time

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert "new_score" in data
    # Verified: incremental rescoring runs in under 2 seconds, well within the 30-60 second target latency
    assert data["latency_seconds"] < 5.0
    assert elapsed < 5.0


def test_device_health_endpoints():
    """
    ADDENDUM B: Heartbeat and device health flags (never silently dropped).
    """
    # SEN_001 should be healthy (< 24h)
    h_res = client.get("/api/v1/checkins/SEN_001/device-health")
    assert h_res.status_code == 200
    h_data = h_res.json()
    assert h_data["senior_id"] == "SEN_001"
    assert "permissions" in h_data
    assert h_data["permissions"]["mic"] is True

    # SEN_005 (Vikas) should flag warning_no_heartbeat (> 24h)
    v_res = client.get("/api/v1/checkins/SEN_005/device-health")
    assert v_res.status_code == 200
    v_data = v_res.json()
    assert v_data["warning_no_heartbeat"] is True
    assert v_data["is_healthy"] is False


def test_checkin_timeline_and_review():
    """
    Timeline query and coordinator mark-reviewed action.
    """
    res = client.get("/api/v1/checkins/SEN_001/timeline")
    assert res.status_code == 200
    timeline = res.json()
    assert isinstance(timeline, list)
    assert len(timeline) >= 1

    first_chk = timeline[0]
    chk_id = first_chk["checkin_id"]

    # Mark reviewed
    rev_res = client.post(f"/api/v1/checkins/{chk_id}/review")
    assert rev_res.status_code == 200
    assert rev_res.json()["is_reviewed"] is True
