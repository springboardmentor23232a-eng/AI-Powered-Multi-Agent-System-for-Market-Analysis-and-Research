import pytest


def get_auth_headers(client, email="pref_user@example.com"):
    client.post("/api/auth/register", json={
        "full_name": "Pref User",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    login_res = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_and_update_preferences(client):
    headers = get_auth_headers(client, "pref_user1@example.com")

    # Fetch default preferences
    res = client.get("/api/preferences", headers=headers)
    assert res.status_code == 200
    assert res.json()["preferred_market"] == "NASDAQ"
    assert res.json()["analysis_period"] == "1 Year"

    # Update preferences
    update_res = client.put(
        "/api/preferences",
        headers=headers,
        json={"preferred_market": "NSE", "analysis_period": "6 Months"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["preferred_market"] == "NSE"
    assert update_res.json()["analysis_period"] == "6 Months"

    # Re-fetch
    check_res = client.get("/api/preferences", headers=headers)
    assert check_res.json()["preferred_market"] == "NSE"
    assert check_res.json()["analysis_period"] == "6 Months"


def test_invalid_preference_values(client):
    headers = get_auth_headers(client, "pref_user2@example.com")

    # Invalid market
    res1 = client.put(
        "/api/preferences",
        headers=headers,
        json={"preferred_market": "INVALID_MARKET", "analysis_period": "1 Year"}
    )
    assert res1.status_code == 422

    # Invalid period
    res2 = client.put(
        "/api/preferences",
        headers=headers,
        json={"preferred_market": "NSE", "analysis_period": "100 Years"}
    )
    assert res2.status_code == 422

