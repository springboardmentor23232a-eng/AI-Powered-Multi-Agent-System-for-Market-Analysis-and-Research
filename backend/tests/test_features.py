import pytest

from .conftest import GOOD


# ---------- research history ----------
def test_start_research_creates_task_runs_workflow_and_report(user_client):
    r = user_client.post("/api/research", json={"ticker": "aapl", "market": "NASDAQ", "analysis_period": "1Y"})
    assert r.status_code == 201
    tid = r.json()["task_id"]
    t = user_client.get(f"/api/research/{tid}").json()  # background task already finished in TestClient
    assert t["status"] == "Completed" and t["ticker"] == "AAPL" and t["company_name"] == "Apple Inc."
    assert t["market"] == "NASDAQ" and t["analysis_period"] == "1Y" and t["report_available"] and t["research_date"]
    rep = user_client.get(f"/api/research/{tid}/report").json()
    assert rep["content"]["statistics"]["data_points"] > 100
    assert "SYNTHETIC" in rep["content"]["data_source"]


def test_history_lists_only_my_tasks(user_client, make_client):
    user_client.post("/api/research", json={"ticker": "AAPL", "market": "NASDAQ"})
    user_client.post("/api/research", json={"ticker": "TSLA", "market": "NASDAQ"})
    other = make_client("bob@example.com")
    other.post("/api/research", json={"ticker": "MSFT", "market": "NASDAQ"})
    mine = [t["ticker"] for t in user_client.get("/api/research").json()]
    assert mine == ["TSLA", "AAPL"]  # newest first, no MSFT
    assert [t["ticker"] for t in other.get("/api/research").json()] == ["MSFT"]


def test_cannot_open_other_users_task_or_report(user_client, make_client):
    other = make_client("bob@example.com")
    tid = other.post("/api/research", json={"ticker": "MSFT", "market": "NASDAQ"}).json()["task_id"]
    assert user_client.get(f"/api/research/{tid}").status_code == 404
    assert user_client.get(f"/api/research/{tid}/report").status_code == 404


def test_browser_supplied_user_id_is_ignored(user_client, make_client):
    other = make_client("bob@example.com")
    other_id = other.get("/api/auth/me").json()["user"]["user_id"]
    other.post("/api/research", json={"ticker": "MSFT", "market": "NASDAQ"})
    # attacker passes user_id in query and body: must have no effect
    assert user_client.get(f"/api/research?user_id={other_id}").json() == []
    r = user_client.post("/api/research", json={"ticker": "AAPL", "market": "NASDAQ", "user_id": other_id})
    assert r.status_code == 201
    assert other.get("/api/research").json()[0]["ticker"] == "MSFT" and len(other.get("/api/research").json()) == 1


def test_research_requires_auth(client):
    assert client.get("/api/research").status_code == 401
    assert client.post("/api/research", json={"ticker": "AAPL"}).status_code == 401


@pytest.mark.parametrize("body", [
    {"ticker": "AAPL", "market": "NSE"},        # wrong market for ticker
    {"ticker": "ZZZZZ", "market": "NASDAQ"},    # unsupported symbol
    {"ticker": "AAPL.NS", "market": "NSE"},     # bad ticker format
    {"ticker": "AAPL", "market": "LSE"},        # unsupported market
    {"ticker": "AAPL", "market": "NASDAQ", "analysis_period": "10Y"},
])
def test_research_validation(user_client, body):
    assert user_client.post("/api/research", json=body).status_code == 422


def test_research_uses_saved_preferences_when_not_given(user_client):
    user_client.put("/api/preferences", json={"market": "NSE", "analysis_period": "3M"})
    r = user_client.post("/api/research", json={"ticker": "RELIANCE"}).json()
    assert r["market"] == "NSE" and r["analysis_period"] == "3M"


def test_failed_workflow_is_recorded_clearly(user_client, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "market_data_provider", "yahoo")
    import app.market_data as md
    monkeypatch.setattr(md.httpx, "get", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("network down")))
    tid = user_client.post("/api/research", json={"ticker": "AAPL", "market": "NASDAQ"}).json()["task_id"]
    t = user_client.get(f"/api/research/{tid}").json()
    assert t["status"] == "Failed" and "network down" in t["error_message"] and not t["report_available"]
    assert user_client.get(f"/api/research/{tid}/report").status_code == 409


def test_period_controls_history_length(user_client):
    def n(period):
        tid = user_client.post("/api/research", json={"ticker": "AAPL", "market": "NASDAQ", "analysis_period": period}).json()["task_id"]
        return user_client.get(f"/api/research/{tid}/report").json()["content"]["statistics"]["data_points"]
    assert n("1M") < n("6M") < n("1Y")


# ---------- watchlist ----------
def test_stock_search_by_name_and_ticker(user_client):
    assert user_client.get("/api/stocks/search?q=apple").json()[0]["ticker"] == "AAPL"
    assert user_client.get("/api/stocks/search?q=tcs").json()[0]["ticker"] == "TCS"
    assert {s["market"] for s in user_client.get("/api/stocks/search?q=reliance").json()} == {"NSE", "BSE"}
    assert [s["market"] for s in user_client.get("/api/stocks/search?q=reliance&market=BSE").json()] == ["BSE"]
    assert user_client.get("/api/stocks/search?q=zzzzqq").json() == []


def test_watchlist_add_list_duplicate_remove(user_client):
    a = user_client.post("/api/watchlist", json={"ticker": "aapl"})
    assert a.status_code == 201 and a.json()["ticker"] == "AAPL"
    assert user_client.post("/api/watchlist", json={"ticker": "AAPL"}).status_code == 409  # no duplicates
    user_client.post("/api/watchlist", json={"ticker": "TSLA"})
    assert {s["ticker"] for s in user_client.get("/api/watchlist").json()} == {"AAPL", "TSLA"}
    assert user_client.delete(f"/api/watchlist/{a.json()['saved_stock_id']}").status_code == 204
    assert [s["ticker"] for s in user_client.get("/api/watchlist").json()] == ["TSLA"]
    assert user_client.post("/api/watchlist", json={"ticker": "NOPE"}).status_code == 422


def test_watchlist_is_per_user_and_cannot_be_deleted_by_others(user_client, make_client):
    other = make_client("bob@example.com")
    item = user_client.post("/api/watchlist", json={"ticker": "AAPL"}).json()
    assert other.post("/api/watchlist", json={"ticker": "AAPL"}).status_code == 201  # same ticker, different user OK
    assert len(other.get("/api/watchlist").json()) == 1
    assert other.delete(f"/api/watchlist/{item['saved_stock_id']}").status_code == 404
    assert other.post(f"/api/watchlist/{item['saved_stock_id']}/research").status_code == 404
    assert len(user_client.get("/api/watchlist").json()) == 1


def test_research_from_saved_stock(user_client):
    user_client.put("/api/preferences", json={"market": "NASDAQ", "analysis_period": "6M"})
    item = user_client.post("/api/watchlist", json={"ticker": "TCS", "market": "NSE"}).json()
    t = user_client.post(f"/api/watchlist/{item['saved_stock_id']}/research").json()
    assert (t["ticker"], t["market"], t["analysis_period"]) == ("TCS", "NSE", "6M")


def test_watchlist_requires_auth(client):
    assert client.get("/api/watchlist").status_code == 401
    assert client.get("/api/stocks/search?q=a").status_code == 401


# ---------- preferences ----------
def test_preferences_defaults_save_and_reload(user_client):
    assert user_client.get("/api/preferences").json()["market"] == "NASDAQ"
    r = user_client.put("/api/preferences", json={"market": "NSE", "analysis_period": "5Y"})
    assert r.status_code == 200
    got = user_client.get("/api/preferences").json()
    assert (got["market"], got["analysis_period"]) == ("NSE", "5Y")


@pytest.mark.parametrize("body", [{"market": "LSE", "analysis_period": "1Y"}, {"market": "NSE", "analysis_period": "2Y"}, {"market": "NSE"}])
def test_preferences_validation(user_client, body):
    assert user_client.put("/api/preferences", json=body).status_code == 422


def test_preferences_are_per_user(user_client, make_client):
    other = make_client("bob@example.com")
    user_client.put("/api/preferences", json={"market": "BSE", "analysis_period": "1M"})
    assert other.get("/api/preferences").json()["market"] == "NASDAQ"


def test_options_endpoint(user_client):
    o = user_client.get("/api/options").json()
    assert [m["code"] for m in o["markets"]] == ["NSE", "BSE", "NASDAQ", "NYSE"]
    assert [p["label"] for p in o["periods"]] == ["1 Month", "3 Months", "6 Months", "1 Year", "5 Years"]


# ---------- full workflow ----------
def test_registration_to_dashboard_workflow(client):
    assert client.post("/api/auth/register", json=GOOD).status_code == 201
    assert client.get("/api/preferences").status_code == 401           # not signed in yet
    d = client.post("/api/auth/login", json={"email": GOOD["email"], "password": GOOD["password"]}).json()
    h = {"X-CSRF-Token": d["csrf_token"]}
    assert client.get("/api/auth/me").json()["user"]["full_name"] == "Asha Verma"
    client.post("/api/watchlist", json={"ticker": "MSFT"}, headers=h)
    client.post("/api/research", json={"ticker": "MSFT"}, headers=h)
    assert len(client.get("/api/research").json()) == 1
    client.post("/api/auth/logout")
    client.cookies.clear()
    assert client.get("/api/research").status_code == 401
