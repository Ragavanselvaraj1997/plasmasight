import httpx
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "System Operational"

def test_auth_login():
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "password"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_unauthenticated_access():
    response = client.get("/api/v1/auth/user")
    assert response.status_code == 401
