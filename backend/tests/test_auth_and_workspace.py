from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

TEST_DB_URL = "sqlite:///./test_stock_research.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def _register_and_login(email="alice@example.com", password="Password123!"):
    reg = client.post(
        "/api/auth/register",
        json={
            "full_name": "Alice Analyst",
            "email": email,
            "password": password,
            "confirm_password": password,
        },
    )
    assert reg.status_code == 201
    login = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_registration_duplicate_email_blocked():
    _register_and_login()
    dup = client.post(
        "/api/auth/register",
        json={
            "full_name": "Alice Two",
            "email": "alice@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert dup.status_code == 400


def test_oauth_google_and_apple_register_and_login():
    g_res = client.post(
        "/api/auth/oauth",
        json={"provider": "google", "email": "guser@gmail.com", "full_name": "Google User"},
    )
    assert g_res.status_code == 200
    assert g_res.json()["user"]["auth_provider"] == "google"
    assert g_res.json()["access_token"]

    a_res = client.post(
        "/api/auth/oauth",
        json={"provider": "apple", "email": "auser@icloud.com", "full_name": "Apple User"},
    )
    assert a_res.status_code == 200
    assert a_res.json()["user"]["auth_provider"] == "apple"

    # Existing Google user signs in again seamlessly
    g_again = client.post(
        "/api/auth/oauth",
        json={"provider": "google", "email": "guser@gmail.com"},
    )
    assert g_again.status_code == 200
    assert g_again.json()["user"]["email"] == "guser@gmail.com"


def test_protected_endpoint_requires_jwt():
    res = client.get("/api/workspace/watchlist")
    assert res.status_code == 401


def test_preferences_watchlist_and_isolation():
    headers_a = _register_and_login("alice@example.com")
    headers_b = _register_and_login("bob@example.com")

    pref = client.put(
        "/api/workspace/preferences",
        json={"market": "NASDAQ", "analysis_period": "6M"},
        headers=headers_a,
    )
    assert pref.status_code == 200
    assert pref.json()["market"] == "NASDAQ"

    added = client.post(
        "/api/workspace/watchlist",
        json={"ticker": "AAPL", "company_name": "Apple Inc.", "market": "NASDAQ"},
        headers=headers_a,
    )
    assert added.status_code == 201

    dup_add = client.post(
        "/api/workspace/watchlist",
        json={"ticker": "AAPL", "company_name": "Apple Inc.", "market": "NASDAQ"},
        headers=headers_a,
    )
    assert dup_add.status_code == 409

    bob_list = client.get("/api/workspace/watchlist", headers=headers_b)
    assert bob_list.status_code == 200
    assert bob_list.json() == []


@patch("app.routers.workspace_router.search_companies")
def test_company_search_records_source_timestamp(mock_search):
    mock_search.return_value = {
        "query": "Tata Consultancy",
        "market": "NSE",
        "results": [
            {
                "ticker": "TCS",
                "yf_symbol": "TCS.NS",
                "company_name": "Tata Consultancy Services Limited",
                "market": "NSE",
                "exchange": "NSI",
                "quote_type": "EQUITY",
            }
        ],
        "data_source": "Yahoo Finance (yfinance)",
        "source_url": "https://finance.yahoo.com/lookup?s=Tata+Consultancy",
        "retrieved_at": "2026-11-18T14:40:00+00:00",
    }
    headers = _register_and_login()
    res = client.get(
        "/api/workspace/stocks/search",
        params={"query": "Tata Consultancy", "market": "NSE"},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["results"][0]["yf_symbol"] == "TCS.NS"

    sources = client.get("/api/workspace/sources", headers=headers)
    assert sources.status_code == 200
    assert len(sources.json()) == 1
    assert sources.json()[0]["data_type"] == "COMPANY_SEARCH"


@patch("app.routers.workspace_router.run_stock_research")
def test_research_task_lifecycle_and_ohlcv(mock_research):
    mock_research.return_value = {
        "market_data": {
            "yf_symbol": "TCS.NS",
            "company_name": "Tata Consultancy Services Limited",
            "currency": "INR",
            "data_source": "Yahoo Finance (yfinance)",
            "source_url": "https://finance.yahoo.com/quote/TCS.NS",
            "retrieved_at": "2026-11-18T14:40:00+00:00",
            "metrics": {"latest_price": 4100.0},
            "series": {
                "dates": ["2026-01-01"],
                "open": [4080.0],
                "high": [4120.0],
                "low": [4070.0],
                "close": [4100.0],
                "volume": [1000],
                "sma_20": [4050.0],
                "sma_50": [3990.0],
            },
            "financial_statements": {"income_statement": [], "balance_sheet": [], "cash_flow": []},
        },
        "quant_summary": "Bullish",
        "analyst_report_md": "## TCS Research Brief",
    }
    headers = _register_and_login()
    res = client.post(
        "/api/workspace/research",
        json={"ticker": "TCS", "market": "NSE", "analysis_period": "1Y"},
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "Completed"
    assert data["report_data"]["series"]["open"] == [4080.0]

    sources = client.get("/api/workspace/sources", headers=headers)
    assert sources.status_code == 200
    assert sources.json()[0]["source_name"] == "Yahoo Finance (yfinance)"
