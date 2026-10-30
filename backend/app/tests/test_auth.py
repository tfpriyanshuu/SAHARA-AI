import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "SaathiCare AI"
    assert data["status"] == "ONLINE"


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "HEALTHY"


def test_demo_users_endpoint():
    response = client.get("/api/v1/auth/demo-users")
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 4
    usernames = [u["username"] for u in users]
    assert "coordinator1" in usernames
    assert "family1" in usernames
    assert "ops1" in usernames


def test_successful_login_and_me():
    # Login as coordinator
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "coordinator1", "password": "coord123"}
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]
    assert token_data["user"]["role"] == "coordinator"

    # Get /me with token
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "coordinator1"


def test_invalid_login():
    res = client.post(
        "/api/v1/auth/login",
        json={"username": "coordinator1", "password": "wrongpassword"}
    )
    assert res.status_code == 401

