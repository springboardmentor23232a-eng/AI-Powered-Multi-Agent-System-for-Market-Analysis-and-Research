import pytest
from app.models.saved_stock import SavedStock


def register_and_login(client, email: str, name: str = "Watchlist User"):
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


def test_authenticated_user_can_add_stock(client, db_session):
    user = register_and_login(client, "wl_tester_1@example.com", "Tester One")

    res = client.post("/api/watchlist", json={"ticker": "INFY.NS"})
    assert res.status_code == 201
    data = res.json()

    assert data["ticker"] == "INFY.NS"
    assert data["user_id"] == user["user_id"]
    assert data["company_name"] == "Infosys Limited"
    assert data["exchange"] == "NSE"
    assert "saved_stock_id" in data

    # Verify persistence in database
    db_item = db_session.query(SavedStock).filter(SavedStock.saved_stock_id == data["saved_stock_id"]).first()
    assert db_item is not None
    assert db_item.ticker == "INFY.NS"
    assert db_item.user_id == user["user_id"]


def test_duplicate_ticker_rejected_409(client):
    register_and_login(client, "wl_duplicate@example.com", "Duplicate Tester")

    # First addition succeeds
    res1 = client.post("/api/watchlist", json={"ticker": "AAPL"})
    assert res1.status_code == 201

    # Second addition for the same user fails with 409 Conflict
    res2 = client.post("/api/watchlist", json={"ticker": "AAPL"})
    assert res2.status_code == 409
    assert "already in your watchlist" in res2.json()["detail"]


def test_ticker_normalization(client):
    register_and_login(client, "wl_normalize@example.com", "Normalize Tester")

    # Add with lowercase and whitespace
    res = client.post("/api/watchlist", json={"ticker": "  msft  "})
    assert res.status_code == 201
    data = res.json()
    assert data["ticker"] == "MSFT"

    # Attempting to add normalized uppercase returns 409
    res_dup = client.post("/api/watchlist", json={"ticker": "MSFT"})
    assert res_dup.status_code == 409


def test_different_users_can_save_same_ticker(client):
    # User A saves RELIANCE.NS
    user_a = register_and_login(client, "wl_user_a@example.com", "User Alpha")
    res_a = client.post("/api/watchlist", json={"ticker": "RELIANCE.NS"})
    assert res_a.status_code == 201
    assert res_a.json()["user_id"] == user_a["user_id"]

    # User B also saves RELIANCE.NS -> Must succeed!
    client.cookies.clear()
    user_b = register_and_login(client, "wl_user_b@example.com", "User Beta")
    res_b = client.post("/api/watchlist", json={"ticker": "RELIANCE.NS"})
    assert res_b.status_code == 201
    assert res_b.json()["user_id"] == user_b["user_id"]
    assert res_b.json()["saved_stock_id"] != res_a.json()["saved_stock_id"]


def test_user_can_retrieve_own_watchlist_and_isolation(client):
    # User A adds 2 stocks
    client.cookies.clear()
    register_and_login(client, "wl_owner_a@example.com", "Owner A")
    res_a1 = client.post("/api/watchlist", json={"ticker": "TCS.NS"})
    res_a2 = client.post("/api/watchlist", json={"ticker": "NVDA"})
    assert res_a1.status_code == 201
    assert res_a2.status_code == 201

    list_a = client.get("/api/watchlist")
    assert list_a.status_code == 200
    data_a = list_a.json()
    assert data_a["status"] == "success"
    tickers_a = [s["ticker"] for s in data_a["data"]]
    assert "TCS.NS" in tickers_a
    assert "NVDA" in tickers_a

    # User B adds 1 stock
    client.cookies.clear()
    register_and_login(client, "wl_owner_b@example.com", "Owner B")
    res_b = client.post("/api/watchlist", json={"ticker": "TSLA"})
    assert res_b.status_code == 201

    list_b = client.get("/api/watchlist")
    assert list_b.status_code == 200
    data_b = list_b.json()
    tickers_b = [s["ticker"] for s in data_b["data"]]
    assert "TSLA" in tickers_b
    # Strict isolation: User B must NOT see User A's stocks
    assert "TCS.NS" not in tickers_b
    assert "NVDA" not in tickers_b


def test_user_can_remove_own_stock(client, db_session):
    client.cookies.clear()
    register_and_login(client, "wl_remover@example.com", "Remover Tester")

    res = client.post("/api/watchlist", json={"ticker": "HDFCBANK.NS"})
    assert res.status_code == 201
    item_id = res.json()["saved_stock_id"]

    # Delete the stock
    del_res = client.delete(f"/api/watchlist/{item_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # Verify deleted from DB
    db_item = db_session.query(SavedStock).filter(SavedStock.saved_stock_id == item_id).first()
    assert db_item is None

    # Watchlist is now empty
    list_res = client.get("/api/watchlist")
    assert list_res.json()["count"] == 0


def test_user_a_cannot_remove_user_b_stock(client):
    # User A creates a saved stock
    client.cookies.clear()
    register_and_login(client, "wl_victim@example.com", "Victim User")
    res_a = client.post("/api/watchlist", json={"ticker": "INFY.NS"})
    assert res_a.status_code == 201
    item_id = res_a.json()["saved_stock_id"]

    # User B attempts to delete User A's stock -> 404 Not Found
    client.cookies.clear()
    register_and_login(client, "wl_attacker@example.com", "Attacker User")
    del_res = client.delete(f"/api/watchlist/{item_id}")
    assert del_res.status_code == 404
    assert "not found" in del_res.json()["detail"].lower()


def test_missing_saved_stock_id_returns_404(client):
    client.cookies.clear()
    register_and_login(client, "wl_notfound@example.com", "NotFound Tester")
    res = client.delete("/api/watchlist/999999")
    assert res.status_code == 404


def test_unauthenticated_requests_rejected(client):
    client.cookies.clear()

    # POST /api/watchlist
    res_post = client.post("/api/watchlist", json={"ticker": "AAPL"})
    assert res_post.status_code == 401

    # GET /api/watchlist
    res_get = client.get("/api/watchlist")
    assert res_get.status_code == 401

    # DELETE /api/watchlist/1
    res_del = client.delete("/api/watchlist/1")
    assert res_del.status_code == 401


def test_invalid_ticker_rejected(client):
    client.cookies.clear()
    register_and_login(client, "wl_invalid@example.com", "Invalid Tester")

    # Empty ticker rejected by schema validation
    res_empty = client.post("/api/watchlist", json={"ticker": ""})
    assert res_empty.status_code in (400, 422)

    # Malformed symbol with invalid characters
    res_bad = client.post("/api/watchlist", json={"ticker": "INVALID$$$SYMBOL"})
    assert res_bad.status_code in (400, 422)

