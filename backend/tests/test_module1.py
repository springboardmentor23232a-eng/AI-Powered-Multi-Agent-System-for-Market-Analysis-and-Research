import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# Use isolated in-memory SQLite database for testing with StaticPool
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_user_registration_and_login():
    # 1. Register valid user
    reg_payload = {
        "full_name": "Deepika Pulluri",
        "email": "deepika@test.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!"
    }
    res = client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "deepika@test.com"
    assert data["full_name"] == "Deepika Pulluri"
    assert "user_id" in data
    assert "password" not in data  # Never expose passwords

    # 2. Reject duplicate email
    dup_res = client.post("/api/auth/register", json=reg_payload)
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]

    # 3. Reject password mismatch
    mismatch_payload = {
        "full_name": "Test User",
        "email": "mismatch@test.com",
        "password": "Password123",
        "confirm_password": "DifferentPassword"
    }
    mis_res = client.post("/api/auth/register", json=mismatch_payload)
    assert mis_res.status_code == 422

    # 4. Successful Login
    login_res = client.post("/api/auth/login", json={
        "email": "deepika@test.com",
        "password": "SecurePassword123!"
    })
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    token = token_data["access_token"]

    # 5. Access protected /me route
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "deepika@test.com"


def test_user_preferences():
    # Register and login
    client.post("/api/auth/register", json={
        "full_name": "User Pref Test",
        "email": "pref@test.com",
        "password": "Password123",
        "confirm_password": "Password123"
    })
    token = client.post("/api/auth/login", json={"email": "pref@test.com", "password": "Password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch default preferences (NASDAQ, 1 Year)
    pref_res = client.get("/api/preferences", headers=headers)
    assert pref_res.status_code == 200
    assert pref_res.json()["market"] == "NASDAQ"
    assert pref_res.json()["analysis_period"] == "1 Year"

    # Update preferences to NSE and 6 Months
    update_res = client.put("/api/preferences", json={"market": "NSE", "analysis_period": "6 Months"}, headers=headers)
    assert update_res.status_code == 200
    assert update_res.json()["market"] == "NSE"
    assert update_res.json()["analysis_period"] == "6 Months"


def test_watchlist_management():
    client.post("/api/auth/register", json={
        "full_name": "Watchlist User",
        "email": "watch@test.com",
        "password": "Password123",
        "confirm_password": "Password123"
    })
    token = client.post("/api/auth/login", json={"email": "watch@test.com", "password": "Password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Add stock AAPL
    add_res = client.post("/api/watchlist", json={"ticker": "AAPL"}, headers=headers)
    assert add_res.status_code == 201
    stock_id = add_res.json()["saved_stock_id"]
    assert add_res.json()["ticker"] == "AAPL"

    # Duplicate stock should be rejected
    dup_res = client.post("/api/watchlist", json={"ticker": "AAPL"}, headers=headers)
    assert dup_res.status_code == 400
    assert "already in your watchlist" in dup_res.json()["detail"]

    # View saved stocks
    list_res = client.get("/api/watchlist", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # Remove stock
    del_res = client.delete(f"/api/watchlist/{stock_id}", headers=headers)
    assert del_res.status_code == 204

    # Confirm empty watchlist
    empty_res = client.get("/api/watchlist", headers=headers)
    assert len(empty_res.json()) == 0


def test_research_tasks_and_multiagent_report():
    client.post("/api/auth/register", json={
        "full_name": "Analyst User",
        "email": "analyst@test.com",
        "password": "Password123",
        "confirm_password": "Password123"
    })
    token = client.post("/api/auth/login", json={"email": "analyst@test.com", "password": "Password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Start research task on TSLA
    task_res = client.post("/api/research/tasks", json={
        "ticker": "TSLA",
        "market": "NASDAQ",
        "analysis_period": "1 Year"
    }, headers=headers)
    assert task_res.status_code == 201
    data = task_res.json()
    assert data["ticker"] == "TSLA"
    assert data["status"] == "Completed"
    assert data["report_data"] is not None
    assert "agents" in data["report_data"]
    assert "fundamental_agent" in data["report_data"]["agents"]
    assert "technical_agent" in data["report_data"]["agents"]
    assert "sentiment_agent" in data["report_data"]["agents"]

    task_id = data["task_id"]

    # Retrieve history
    history_res = client.get("/api/research/tasks", headers=headers)
    assert history_res.status_code == 200
    assert len(history_res.json()) == 1

    # Retrieve single task report
    single_res = client.get(f"/api/research/tasks/{task_id}", headers=headers)
    assert single_res.status_code == 200
    assert single_res.json()["task_id"] == task_id


def test_unauthorized_access():
    # Attempting to access protected endpoints without token must return 401
    res1 = client.get("/api/auth/me")
    assert res1.status_code == 401

    res2 = client.get("/api/watchlist")
    assert res2.status_code == 401

    res3 = client.get("/api/research/tasks")
    assert res3.status_code == 401
