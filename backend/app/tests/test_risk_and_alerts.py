import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_auth_token(username: str = "coordinator1", password: str = "coord123"):
    res = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    return res.json()["access_token"]


def test_list_seniors_and_detail():
    token = get_auth_token("coordinator1", "coord123")
    res = client.get("/api/v1/seniors", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    seniors = res.json()
    assert len(seniors) > 0
    
    # Detail for SEN_003
    detail_res = client.get("/api/v1/seniors/SEN_003", headers={"Authorization": f"Bearer {token}"})
    assert detail_res.status_code == 200
    s_detail = detail_res.json()
    assert s_detail["id"] == "SEN_003"
    assert s_detail["full_name"] in ["Rameshwar Prasad Sharma", "Anchal"]
    assert s_detail["baseline_spo2"] > 90.0


def test_risk_queue_and_explanation():
    token = get_auth_token("coordinator1", "coord123")
    res = client.get("/api/v1/risk/daily", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    queue = res.json()
    assert len(queue) > 0
    
    # SEN_003 explanation
    expl_res = client.get("/api/v1/risk/SEN_003/risk-explanations", headers={"Authorization": f"Bearer {token}"})
    assert expl_res.status_code == 200
    expl = expl_res.json()
    assert expl["senior_id"] == "SEN_003"
    assert len(expl["top_contributors"]) >= 1
    assert "suggested_action" in expl
    assert "questions_hindi" in expl["suggested_action"]
    assert "questions_english" in expl["suggested_action"]


def test_alert_lifecycle_and_workflow():
    token = get_auth_token("coordinator1", "coord123")
    alerts_res = client.get("/api/v1/alerts", headers={"Authorization": f"Bearer {token}"})
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert len(alerts) > 0
    alert_id = alerts[0]["id"]

    # 1. Acknowledge Alert
    ack_res = client.patch(
        f"/api/v1/alerts/{alert_id}",
        json={"status": "ACKNOWLEDGED"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert ack_res.status_code == 200

    # 2. Schedule Follow-up
    fu_res = client.post(
        f"/api/v1/alerts/{alert_id}/follow-ups",
        json={"senior_id": alerts[0]["senior_id"], "due_date": "2026-10-22", "notes": "Check vital recovery"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert fu_res.status_code == 200
    assert fu_res.json()["status"] == "PENDING"

    # 3. Resolve Alert with Feedback
    res_res = client.post(
        f"/api/v1/alerts/{alert_id}/resolve",
        json={"resolution_notes": "Checked via phone, vitals stabilized after rest.", "outcome_rating": "useful"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_res.status_code == 200


def test_family_portal_consent_gating():
    fam_token = get_auth_token("family1", "family123")
    
    # 1. View summary with consent active
    res = client.get("/api/v1/family/weekly-summary", headers={"Authorization": f"Bearer {fam_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["senior_id"] in ["SEN_001", "SEN_003"]
    assert data["family_consent"] is True
    assert "show_alert_banner" in data

    # 2. Toggle consent to False
    toggle_res = client.patch("/api/v1/family/consent", json={"family_consent": False}, headers={"Authorization": f"Bearer {fam_token}"})
    assert toggle_res.status_code == 200
    assert toggle_res.json()["family_consent"] is False

    # 3. View summary when paused (alert banner must be False)
    res_paused = client.get("/api/v1/family/weekly-summary", headers={"Authorization": f"Bearer {fam_token}"})
    assert res_paused.json()["show_alert_banner"] is False
    assert "PAUSED" in res_paused.json()["consent_notice"]

    # Reset back to True
    client.patch("/api/v1/family/consent", json={"family_consent": True}, headers={"Authorization": f"Bearer {fam_token}"})


def test_demo_scenario_trigger():
    token = get_auth_token("coordinator1", "coord123")
    res = client.post(
        "/api/v1/demo/scenarios/trigger",
        json={"scenario": "fall_emergency", "senior_id": "SEN_003"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["category"] == "URGENT"
    assert data["new_risk_score"] >= 90.0

