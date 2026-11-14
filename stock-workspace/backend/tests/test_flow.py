import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

H = {"X-Requested-With": "XMLHttpRequest"}
REG = {"full_name": "Test User", "email": "t@example.com", "password": "secret123", "confirm_password": "secret123"}


def test_full_flow():
    c = TestClient(app)
    assert c.post("/api/auth/register", json=REG, headers=H).status_code == 201
    assert c.post("/api/auth/register", json=REG, headers=H).status_code == 409          # duplicate email
    assert c.get("/api/research").status_code == 401                                      # protected
    assert c.post("/api/auth/login", json={"email": "t@example.com", "password": "bad"}, headers=H).status_code == 401
    assert c.post("/api/auth/login", json={"email": "t@example.com", "password": "secret123"}, headers=H).status_code == 200
    assert c.put("/api/preferences", json={"market": "NASDAQ", "analysis_period": "6M"}, headers=H).json()["market"] == "NASDAQ"
    assert c.post("/api/watchlist", json={"ticker": "aapl", "market": "NASDAQ"}, headers=H).status_code == 201
    assert c.post("/api/watchlist", json={"ticker": "AAPL", "market": "NASDAQ"}, headers=H).status_code == 409
    t = c.post("/api/research", json={"ticker": "AAPL"}, headers=H).json()
    assert t["market"] == "NASDAQ" and t["analysis_period"] == "6M"
    assert len(c.get("/api/research").json()) == 1
    assert c.post("/api/watchlist", json={"ticker": "AAPL", "market": "NASDAQ"}).status_code == 403  # CSRF header

    other = TestClient(app)  # a second user must not see the first user's data
    other.post("/api/auth/register", json={**REG, "email": "o@example.com"}, headers=H)
    other.post("/api/auth/login", json={"email": "o@example.com", "password": "secret123"}, headers=H)
    assert other.get("/api/research").json() == []
    assert other.get(f"/api/research/{t['task_id']}").status_code == 404
