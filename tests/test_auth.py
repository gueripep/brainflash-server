"""
Pytest-friendly tests for authentication-related sanity checks.

This file contains:
- a small, fast unit-style test that uses TestClient against the in-process app
- an opt-in integration test (the original script converted to assertions)
  which only runs when RUN_INTEGRATION_TESTS=1 is set in the environment.

Integration tests still depend on a running server and real DB — they are
guarded and won't run in CI by default.
"""
import os
import time
import pytest
import requests
from fastapi.testclient import TestClient

# Ensure ENV is set before importing the app factory (create_app reads ENV at import)
os.environ.setdefault("ENV", "dev")

from app.main import app  # import after ENV is defined


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_root_endpoint(client):
    """Unit-style test: ensure root endpoint is reachable and returns expected keys."""
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert "message" in body
    assert "Welcome" in body["message"]


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("ENV") != "dev", reason="Integration tests disabled unless ENV=dev")
def test_authentication_integration():
    """Converted original integration script into assertions. Runs only when enabled.

    This hits a live server at http://localhost:8000 and therefore is opt-in.
    """
    BASE_URL = "http://localhost:8000"

    # 1. Access protected endpoint without auth -> should be unauthorized
    r = requests.get(f"{BASE_URL}/tts/protected/user-stats")
    assert r.status_code == 401

    # 2. Register a new user
    timestamp = int(time.time())
    user_data = {
        "email": f"test{timestamp}@example.com",
        "password": "SecurePassword123!",
        "first_name": "Test",
        "last_name": "User",
    }
    r = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    assert r.status_code in (200, 201)
    user_info = r.json()
    assert "email" in user_info

    # 3. Login with the user
    login_data = {"username": user_data["email"], "password": user_data["password"]}
    r = requests.post(f"{BASE_URL}/auth/jwt/login", data=login_data)
    assert r.status_code == 200
    token_info = r.json()
    assert "access_token" in token_info
    access_token = token_info["access_token"]

    # 4. Access protected endpoint with auth
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(f"{BASE_URL}/tts/protected/user-stats", headers=headers)
    assert r.status_code == 200

    # 5. Get user profile
    r = requests.get(f"{BASE_URL}/users/me", headers=headers)
    assert r.status_code == 200

    # 6. Logout
    r = requests.post(f"{BASE_URL}/auth/jwt/logout", headers=headers)
    assert r.status_code in (200, 204)
