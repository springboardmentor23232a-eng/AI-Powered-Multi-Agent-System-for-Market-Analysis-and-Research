import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.marketdata.providers.sample import DATA_DIR

MANIFEST = json.loads((DATA_DIR / "defects.json").read_text())
HDR = {"X-Requested-With": "XMLHttpRequest"}


def make_client(email):
    c = TestClient(app)
    c.headers.update(HDR)
    pw = {"full_name": "Test User", "email": email, "password": "abcd1234", "confirm_password": "abcd1234"}
    assert c.post("/api/auth/register", json=pw).status_code == 201
    assert c.post("/api/auth/login", json={"email": email, "password": "abcd1234"}).status_code == 200
    return c


@pytest.fixture(scope="module")
def client():
    with TestClient(app):  # runs startup, which creates the tables
        yield make_client("one@example.com")


def test_requires_login():
    c = TestClient(app)
    c.headers.update(HDR)
    assert c.get("/api/market-data").status_code == 401
    assert c.post("/api/market-data/collect", json={"ticker": "AAPL", "market": "NASDAQ"}).status_code == 401


def test_collect_requires_csrf_header(client):
    r = client.post("/api/market-data/collect", json={"ticker": "AAPL", "market": "NASDAQ"}, headers={"X-Requested-With": ""})
    assert r.status_code == 403


def test_source_reports_the_sample_dataset(client):
    r = client.get("/api/market-data/source").json()
    assert r["kind"] == "sample" and len(r["symbols"]) == 15


def test_collect_records_source_timestamp_and_validation(client):
    r = client.post("/api/market-data/collect", json={"ticker": "TCS.BO", "market": "BSE"})
    assert r.status_code == 201
    col = r.json()
    assert col["source"] == "Sample dataset (synthetic)" and col["retrieved_at"]
    assert col["status"] == "Cleaned" and col["rows_clean"] < col["rows_raw"]
    detail = client.get(f"/api/market-data/{col['collection_id']}").json()
    found = {i["check"]: i["count"] for i in detail["report"]["issues"]}
    expected = {k: v for k, v in MANIFEST["TCS.BO"].items()}
    # the default period is 1Y, and every planted defect falls inside it
    assert found == expected
    assert detail["profile"]["name"] == "Tata Consultancy Services Limited"
    assert set(detail["financials"]) == {"income_statement", "balance_sheet", "cash_flow"}
    prices = client.get(f"/api/market-data/{col['collection_id']}/prices").json()
    assert len(prices) == col["rows_clean"]
    assert [p["date"] for p in prices] == sorted(p["date"] for p in prices)


def test_clean_symbol_is_marked_clean(client):
    r = client.post("/api/market-data/collect", json={"ticker": "MSFT", "market": "NASDAQ"}).json()
    assert r["status"] == "Clean" and r["rows_raw"] == r["rows_clean"]


def test_bare_indian_ticker_gets_its_exchange_suffix(client):
    r = client.post("/api/market-data/collect", json={"ticker": "infy", "market": "NSE"}).json()
    assert r["ticker"] == "INFY.NS"


def test_unknown_symbol_returns_404_with_a_hint(client):
    r = client.post("/api/market-data/collect", json={"ticker": "ZZZZ", "market": "NYSE"})
    assert r.status_code == 404 and "sample dataset" in r.json()["detail"]


def test_wrong_market_suffix_is_rejected(client):
    assert client.post("/api/market-data/collect", json={"ticker": "TCS.NS", "market": "NASDAQ"}).status_code == 422


def test_users_cannot_see_each_others_collections(client):
    cid = client.get("/api/market-data").json()[0]["collection_id"]
    other = make_client("two@example.com")
    assert other.get("/api/market-data").json() == []
    assert other.get(f"/api/market-data/{cid}").status_code == 404
    assert other.get(f"/api/market-data/{cid}/prices").status_code == 404
