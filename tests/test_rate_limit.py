"""
Tests for the RateLimitMiddleware
"""
import time
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.rate_limiter import RateLimitMiddleware


def create_test_app(max_requests: int, window_seconds: int):
    app = FastAPI()

    @app.get("/ping")
    def ping():
        return {"msg": "pong"}

    app.add_middleware(RateLimitMiddleware, max_requests=max_requests, window_seconds=window_seconds)
    return app


def test_rate_limit_exceeded():
    # Very small window for test speed
    app = create_test_app(max_requests=3, window_seconds=2)
    client = TestClient(app)

    # First 3 requests should pass
    for i in range(3):
        r = client.get("/ping")
        assert r.status_code == 200
        assert r.json() == {"msg": "pong"}

    # 4th request should be rate limited
    r = client.get("/ping")
    assert r.status_code == 429
    assert r.json().get("detail") == "Rate limit exceeded"

    # Wait for the window to expire and ensure requests are accepted again
    time.sleep(2)
    r = client.get("/ping")
    assert r.status_code == 200
    assert r.json() == {"msg": "pong"}
