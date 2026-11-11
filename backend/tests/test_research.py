import pytest


def get_auth_token(client, email):
    client.post("/api/auth/register", json={
        "full_name": "Research User",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    res = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    return res.json()["access_token"]


def test_research_task_creation_and_isolation(client):
    token1 = get_auth_token(client, "res_user1@example.com")
    token2 = get_auth_token(client, "res_user2@example.com")

    h1 = {"Authorization": f"Bearer {token1}"}
    h2 = {"Authorization": f"Bearer {token2}"}

    # 1. User 1 creates research task
    create_res = client.post(
        "/api/research",
        headers=h1,
        json={"ticker": "MSFT", "market": "NASDAQ", "analysis_period": "1 Year"}
    )
    assert create_res.status_code == 201
    task_id = create_res.json()["task_id"]
    assert create_res.json()["status"] == "Pending"

    # 2. User 1 can view task details
    detail_res = client.get(f"/api/research/{task_id}", headers=h1)
    assert detail_res.status_code == 200
    assert detail_res.json()["ticker"] == "MSFT"

    # 3. User 2 is forbidden from accessing task
    u2_view = client.get(f"/api/research/{task_id}", headers=h2)
    assert u2_view.status_code == 403

    # 4. History filtering
    hist_res = client.get("/api/research/history?search=MSFT", headers=h1)
    assert hist_res.status_code == 200
    assert len(hist_res.json()) >= 1

    # 5. Dashboard overview
    dash_res = client.get("/api/research/dashboard/overview", headers=h1)
    assert dash_res.status_code == 200
    assert dash_res.json()["total_research"] >= 1

