import pytest
from app.models.user_preference import UserPreference
from app.models.research_task import ResearchTask


def register_and_login(client, email: str, name: str = "Test User"):
    reg_payload = {
        "fullName": name,
        "email": email,
        "password": "Password123!",
        "confirmPassword": "Password123!",
    }
    client.post("/api/auth/register", json=reg_payload)

    login_payload = {
        "email": email,
        "password": "Password123!",
    }
    res = client.post("/api/auth/login", json=login_payload)
    assert res.status_code == 200
    return res.json()["data"]


def test_authenticated_user_can_retrieve_preferences(client):
    user = register_and_login(client, "pref_user1@example.com", "Preference User 1")

    res = client.get("/api/preferences")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["user_id"] == user["user_id"]
    assert "market" in data
    assert "analysis_period" in data
    assert "updated_at" in data


def test_new_user_receives_default_nse_and_1mo(client):
    user = register_and_login(client, "new_pref_user@example.com", "New User Defaults")

    res = client.get("/api/preferences")
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == user["user_id"]
    assert data["market"] == "NSE"
    assert data["analysis_period"] == "1mo"


def test_authenticated_user_can_update_market(client):
    register_and_login(client, "pref_market_user@example.com", "Market Updater")

    update_res = client.put("/api/preferences", json={"market": "NASDAQ", "analysis_period": "1mo"})
    assert update_res.status_code == 200
    assert update_res.json()["market"] == "NASDAQ"

    get_res = client.get("/api/preferences")
    assert get_res.status_code == 200
    assert get_res.json()["market"] == "NASDAQ"
    assert get_res.json()["analysis_period"] == "1mo"


def test_authenticated_user_can_update_analysis_period(client):
    register_and_login(client, "pref_period_user@example.com", "Period Updater")

    update_res = client.put("/api/preferences", json={"market": "NSE", "analysis_period": "6mo"})
    assert update_res.status_code == 200
    assert update_res.json()["analysis_period"] == "6mo"

    get_res = client.get("/api/preferences")
    assert get_res.status_code == 200
    assert get_res.json()["analysis_period"] == "6mo"


def test_authenticated_user_can_update_both_preferences(client):
    register_and_login(client, "pref_both_user@example.com", "Both Updater")

    update_res = client.put("/api/preferences", json={"market": "NYSE", "analysis_period": "5y"})
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["market"] == "NYSE"
    assert data["analysis_period"] == "5y"

    get_res = client.get("/api/preferences")
    assert get_res.status_code == 200
    assert get_res.json()["market"] == "NYSE"
    assert get_res.json()["analysis_period"] == "5y"


def test_invalid_market_is_rejected(client):
    register_and_login(client, "invalid_mkt@example.com", "Invalid Market User")

    res = client.put("/api/preferences", json={"market": "FOREX_GLOBAL", "analysis_period": "1mo"})
    assert res.status_code == 422
    assert "invalid market" in res.json()["detail"].lower()


def test_invalid_analysis_period_is_rejected(client):
    register_and_login(client, "invalid_prd@example.com", "Invalid Period User")

    res = client.put("/api/preferences", json={"market": "NSE", "analysis_period": "99y"})
    assert res.status_code == 422
    assert "invalid analysis period" in res.json()["detail"].lower()


def test_unauthenticated_requests_are_rejected(client):
    client.cookies.clear()

    get_res = client.get("/api/preferences")
    assert get_res.status_code == 401

    put_res = client.put("/api/preferences", json={"market": "NSE", "analysis_period": "1mo"})
    assert put_res.status_code == 401


def test_user_a_cannot_access_user_b_preferences(client):
    user_a = register_and_login(client, "isolation_a@example.com", "Isolation Alpha")
    client.put("/api/preferences", json={"market": "BSE", "analysis_period": "3mo"})

    client.cookies.clear()
    user_b = register_and_login(client, "isolation_b@example.com", "Isolation Beta")

    res_b = client.get("/api/preferences")
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["user_id"] == user_b["user_id"]
    assert data_b["user_id"] != user_a["user_id"]
    assert data_b["market"] == "NSE"  # Default for B, not A's BSE!
    assert data_b["analysis_period"] == "1mo"  # Default for B, not A's 3mo!


def test_user_a_cannot_modify_user_b_preferences(client, db_session):
    user_a = register_and_login(client, "isolation_mod_a@example.com", "Mod Alpha")
    client.put("/api/preferences", json={"market": "NASDAQ", "analysis_period": "1y"})

    client.cookies.clear()
    user_b = register_and_login(client, "isolation_mod_b@example.com", "Mod Beta")
    client.put("/api/preferences", json={"market": "BSE", "analysis_period": "5y"})

    # Verify directly in DB that User A's and User B's records are completely isolated
    pref_a = db_session.query(UserPreference).filter(UserPreference.user_id == user_a["user_id"]).first()
    pref_b = db_session.query(UserPreference).filter(UserPreference.user_id == user_b["user_id"]).first()

    assert pref_a is not None
    assert pref_b is not None
    assert pref_a.market == "NASDAQ"
    assert pref_a.analysis_period == "1y"
    assert pref_b.market == "BSE"
    assert pref_b.analysis_period == "5y"


def test_repeated_get_requests_do_not_create_duplicate_preference_records(client, db_session):
    user = register_and_login(client, "idempotent_pref@example.com", "Idempotent User")

    # Issue 5 consecutive GET requests
    for _ in range(5):
        res = client.get("/api/preferences")
        assert res.status_code == 200

    records = db_session.query(UserPreference).filter(UserPreference.user_id == user["user_id"]).all()
    assert len(records) == 1


def test_existing_research_workflow_accepts_valid_requests(client):
    register_and_login(client, "research_workflow_pref@example.com", "Workflow Analyst")

    # 1. Valid NSE stock research with explicit market
    res_nse = client.post(
        "/api/research/tasks",
        json={"ticker": "INFY.NS", "market": "NSE", "period": "1mo"}
    )
    assert res_nse.status_code == 201
    task_nse = res_nse.json()["task"]
    assert task_nse["market"] == "NSE"
    assert task_nse["requested_period"] == "1mo"

    # 2. Incompatible combination (US stock under NSE) rejected with 400
    res_bad = client.post(
        "/api/research/tasks",
        json={"ticker": "AAPL", "market": "NSE", "period": "1mo"}
    )
    assert res_bad.status_code == 400
    assert "incompatible" in res_bad.json()["detail"].lower() or "cannot be researched" in res_bad.json()["detail"].lower()
