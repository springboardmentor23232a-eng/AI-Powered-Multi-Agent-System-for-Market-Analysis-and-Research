import pytest


def get_auth_token(client, email):
    client.post("/api/auth/register", json={
        "full_name": "Watchlist User",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    res = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    return res.json()["access_token"]


def test_watchlist_crud_and_isolation(client):
    token1 = get_auth_token(client, "user_w1@example.com")
    token2 = get_auth_token(client, "user_w2@example.com")

    h1 = {"Authorization": f"Bearer {token1}"}
    h2 = {"Authorization": f"Bearer {token2}"}

    # 1. User 1 adds stock
    add_res = client.post(
        "/api/watchlist",
        headers=h1,
        json={"ticker": "AAPL", "company_name": "Apple Inc.", "market": "NASDAQ"}
    )
    assert add_res.status_code == 201
    stock_id = add_res.json()["saved_stock_id"]

    # 2. Duplicate prevention for same user
    dup_res = client.post(
        "/api/watchlist",
        headers=h1,
        json={"ticker": "AAPL", "company_name": "Apple Inc.", "market": "NASDAQ"}
    )
    assert dup_res.status_code == 409

    # 3. User 2's watchlist is empty
    u2_res = client.get("/api/watchlist", headers=h2)
    assert u2_res.status_code == 200
    assert len(u2_res.json()) == 0

    # 4. User 2 cannot delete User 1's saved stock
    del_forbidden = client.delete(f"/api/watchlist/{stock_id}", headers=h2)
    assert del_forbidden.status_code == 404

    # 5. User 1 deletes their stock
    del_res = client.delete(f"/api/watchlist/{stock_id}", headers=h1)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # 6. Verify empty for user 1
    u1_after = client.get("/api/watchlist", headers=h1)
    assert len(u1_after.json()) == 0

