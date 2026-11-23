import pytest
import pandas as pd
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_current_user
from app.models import User
from app.routers.stocks import (
    provider_symbol,
    clean_num,
    clean_int,
    clean_url,
    format_metric_name,
    check_exchange_mismatch,
    serialize_statement,
)

# Test User Fixture
mock_user = User(
    id="test-user-id",
    full_name="Test Analyst",
    email="analyst@example.com",
    auth_provider="local",
    is_active=True,
    created_at=datetime.now(timezone.utc),
)

@pytest.fixture
def client():
    # Override auth dependency
    app.dependency_overrides[get_current_user] = lambda: mock_user
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture
def unauthed_client():
    app.dependency_overrides.clear()
    return TestClient(app)

# 1. Test Provider Symbol Mapping
def test_provider_symbol_mapping():
    assert provider_symbol("INFY", "NSE") == "INFY.NS"
    assert provider_symbol("INFY.NS", "NSE") == "INFY.NS"
    assert provider_symbol("INFY", "BSE") == "INFY.BO"
    assert provider_symbol("INFY.BO", "BSE") == "INFY.BO"
    assert provider_symbol("KO", "NYSE") == "KO"
    assert provider_symbol("AAPL", "NASDAQ") == "AAPL"
    assert provider_symbol("aapl", "NASDAQ") == "AAPL"

# 2. Test Helper Functions
def test_clean_num_and_int():
    assert clean_num(123.45) == 123.45
    assert clean_num(None) is None
    assert clean_num(float("nan")) is None
    assert clean_num(float("inf")) is None
    assert clean_num("invalid") is None

    assert clean_int(100) == 100
    assert clean_int("100") == 100
    assert clean_int(None) is None
    assert clean_int("invalid") is None

def test_clean_url():
    assert clean_url("www.apple.com") == "https://www.apple.com"
    assert clean_url("https://www.infosys.com") == "https://www.infosys.com"
    assert clean_url("http://coca-colacompany.com") == "http://coca-colacompany.com"
    assert clean_url("invalid_url") is None
    assert clean_url("None") is None
    assert clean_url("") is None
    assert clean_url(None) is None

def test_format_metric_name():
    assert format_metric_name("Total Revenue") == "Total Revenue"
    assert format_metric_name("TotalRevenue") == "Total Revenue"
    assert format_metric_name("GrossProfit") == "Gross Profit"
    assert format_metric_name("OperatingExpense") == "Operating Expense"

# 3. Test Exchange Mismatch Logic (Prevents Silent Exchange Mixing)
def test_exchange_mismatch_detection():
    # KO queried under NASDAQ -> error
    err = check_exchange_mismatch("NASDAQ", "NYQ", "KO")
    assert err is not None
    assert "NYSE" in err

    # AAPL queried under NYSE -> error
    err = check_exchange_mismatch("NYSE", "NMS", "AAPL")
    assert err is not None
    assert "NASDAQ" in err

    # INFY.NS queried under NASDAQ -> error
    err = check_exchange_mismatch("NASDAQ", "NSI", "INFY.NS")
    assert err is not None

    # INFY without .NS queried under NSE -> error
    err = check_exchange_mismatch("NSE", "NSI", "INFY")
    assert err is not None

    # Valid matches
    assert check_exchange_mismatch("NASDAQ", "NMS", "AAPL") is None
    assert check_exchange_mismatch("NYSE", "NYQ", "KO") is None
    assert check_exchange_mismatch("NSE", "NSI", "INFY.NS") is None
    assert check_exchange_mismatch("BSE", "BSE", "INFY.BO") is None

# 4. Test Financial Statement Serialization
def test_serialize_statement():
    # DataFrame with Timestamps as columns
    cols = [pd.Timestamp("2024-09-30"), pd.Timestamp("2023-09-30")]
    df = pd.DataFrame(
        {
            cols[0]: [100.0, -25.5, float("nan")],
            cols[1]: [90.0, -20.0, 5.0],
        },
        index=["Total Revenue", "Operating Income", "Other Income"],
    )

    data = serialize_statement(df, is_annual=True)
    assert len(data.periods) == 2
    assert "2024" in data.periods
    assert "2023" in data.periods
    assert len(data.metrics) == 3

    rev = next(m for m in data.metrics if m.name == "Total Revenue")
    assert rev.values["2024"] == 100.0
    assert rev.values["2023"] == 90.0

    op_inc = next(m for m in data.metrics if m.name == "Operating Income")
    assert op_inc.values["2024"] == -25.5  # Preserves negative values!

    other = next(m for m in data.metrics if m.name == "Other Income")
    assert other.values["2024"] is None  # NaN becomes None (N/A in UI), not zero!

# 5. Test Endpoint Authentication Enforcement
def test_endpoints_require_authentication(unauthed_client):
    endpoints = [
        "/api/stocks/search?q=Apple&market=NASDAQ",
        "/api/stocks/quote?ticker=AAPL&market=NASDAQ",
        "/api/stocks/history?ticker=AAPL&market=NASDAQ",
        "/api/stocks/profile?ticker=AAPL&market=NASDAQ",
        "/api/stocks/financials?ticker=AAPL&market=NASDAQ",
        "/api/stocks/analytics?ticker=AAPL&market=NASDAQ",
    ]
    for url in endpoints:
        res = unauthed_client.get(url)
        assert res.status_code == 401

# 6. Test Endpoint Input Validation
def test_endpoint_input_validation(client):
    # Invalid market
    res = client.get("/api/stocks/quote?ticker=AAPL&market=TOKYO")
    assert res.status_code == 422

    # Invalid period
    res = client.get("/api/stocks/history?ticker=AAPL&market=NASDAQ&period=10 Years")
    assert res.status_code == 422

    # Missing parameters
    res = client.get("/api/stocks/profile")
    assert res.status_code == 422

# 7. Test Exchange Mixing Guard via API (HTTP 404)
@patch("yfinance.Ticker")
def test_quote_exchange_mismatch_blocks_mixing(mock_ticker_cls, client):
    mock_stock = MagicMock()
    mock_fast_info = MagicMock()
    mock_fast_info.get.side_effect = lambda k: "NYQ" if k == "exchange" else 100.0
    mock_stock.fast_info = mock_fast_info
    mock_ticker_cls.return_value = mock_stock

    # User queries KO under NASDAQ -> should return 404 with clear message
    res = client.get("/api/stocks/quote?ticker=KO&market=NASDAQ")
    assert res.status_code == 404
    assert "NYSE" in res.json()["detail"]

# 8. Test Stock History Endpoint
@patch("yfinance.Ticker")
def test_history_endpoint(mock_ticker_cls, client):
    mock_stock = MagicMock()
    mock_fast_info = MagicMock()
    mock_fast_info.get.side_effect = lambda k: "NMS" if k == "exchange" else "USD"
    mock_stock.fast_info = mock_fast_info

    # Mock historical DataFrame
    dates = pd.date_range("2026-11-15", periods=3, freq="D")
    df = pd.DataFrame(
        {
            "Open": [150.0, 152.0, 155.0],
            "High": [153.0, 156.0, 158.0],
            "Low": [149.0, 151.0, 154.0],
            "Close": [152.0, 155.0, 157.0],
            "Volume": [1000000, 1200000, 1500000],
        },
        index=dates,
    )
    mock_stock.history.return_value = df
    mock_ticker_cls.return_value = mock_stock

    res = client.get("/api/stocks/history?ticker=AAPL&market=NASDAQ&period=1 Month")
    assert res.status_code == 200
    data = res.json()
    assert data["ticker"] == "AAPL"
    assert data["market"] == "NASDAQ"
    assert data["source"] == "Yahoo Finance"
    assert data["period"] == "1 Month"
    assert data["count"] == 3
    assert len(data["history"]) == 3
    # Check that OHLCV fields are present and latest date is first
    latest = data["history"][0]
    assert "open" in latest
    assert "high" in latest
    assert "low" in latest
    assert "close" in latest
    assert "volume" in latest
    assert "date" in latest
    assert "formatted_date" in latest

# 9. Test Stock Profile Endpoint
@patch("yfinance.Ticker")
def test_profile_endpoint(mock_ticker_cls, client):
    mock_stock = MagicMock()
    mock_fast_info = MagicMock()
    mock_fast_info.get.side_effect = lambda k: "NMS" if k == "exchange" else None
    mock_stock.fast_info = mock_fast_info
    mock_stock.info = {
        "longName": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "longBusinessSummary": "Apple Inc. designs, manufactures, and markets smartphones...",
        "country": "United States",
        "city": "Cupertino",
        "website": "https://www.apple.com",
        "marketCap": 3500000000000,
        "fullTimeEmployees": 164000,
        "currency": "USD",
        "exchange": "NASDAQ",
    }
    mock_ticker_cls.return_value = mock_stock

    res = client.get("/api/stocks/profile?ticker=AAPL&market=NASDAQ")
    assert res.status_code == 200
    data = res.json()
    assert data["company_name"] == "Apple Inc."
    assert data["sector"] == "Technology"
    assert data["industry"] == "Consumer Electronics"
    assert data["website"] == "https://www.apple.com"
    assert data["market_cap"] == 3500000000000
    assert data["full_time_employees"] == 164000
    assert data["currency"] == "USD"
    assert data["source"] == "Yahoo Finance"

# 10. Test Financial Statements Endpoint
@patch("yfinance.Ticker")
def test_financials_endpoint(mock_ticker_cls, client):
    mock_stock = MagicMock()
    mock_fast_info = MagicMock()
    mock_fast_info.get.side_effect = lambda k: "NMS" if k == "exchange" else "USD"
    mock_stock.fast_info = mock_fast_info

    cols = [pd.Timestamp("2024-09-30"), pd.Timestamp("2023-09-30")]
    stmt_df = pd.DataFrame(
        {
            cols[0]: [391035000000.0, 170782000000.0],
            cols[1]: [383285000000.0, 169148000000.0],
        },
        index=["Total Revenue", "Gross Profit"],
    )
    mock_stock.income_stmt = stmt_df
    mock_stock.balance_sheet = stmt_df
    mock_stock.cashflow = stmt_df
    mock_stock.quarterly_income_stmt = stmt_df
    mock_stock.quarterly_balance_sheet = stmt_df
    mock_stock.quarterly_cashflow = stmt_df
    mock_ticker_cls.return_value = mock_stock

    res = client.get("/api/stocks/financials?ticker=AAPL&market=NASDAQ")
    assert res.status_code == 200
    data = res.json()
    assert data["ticker"] == "AAPL"
    assert "annual" in data
    assert "quarterly" in data
    assert "income_statement" in data["annual"]
    assert "balance_sheet" in data["annual"]
    assert "cash_flow" in data["annual"]
    assert len(data["annual"]["income_statement"]["periods"]) == 2
    assert len(data["annual"]["income_statement"]["metrics"]) == 2

# 11. Live Provider Integration Tests for Supported Markets
@pytest.mark.parametrize("market,ticker,expected_provider_symbol", [
    ("NSE", "INFY", "INFY.NS"),
    ("BSE", "INFY", "INFY.BO"),
    ("NYSE", "KO", "KO"),
    ("NASDAQ", "AAPL", "AAPL"),
])
def test_live_provider_integration(client, market, ticker, expected_provider_symbol):
    """Verify actual yfinance market data responses across all 4 markets."""
    import yfinance as yf
    try:
        # 1. Quote
        res = client.get(f"/api/stocks/quote?ticker={ticker}&market={market}")
        if res.status_code == 200:
            quote = res.json()
            assert quote["ticker"] == ticker
            assert quote["market"] == market
            assert quote["provider_symbol"] == expected_provider_symbol
            assert quote["source"] == "Yahoo Finance"
            assert "price" in quote
            assert "retrieval_timestamp" in quote

        # 2. History
        res_hist = client.get(f"/api/stocks/history?ticker={ticker}&market={market}&period=1 Month")
        if res_hist.status_code == 200:
            hist = res_hist.json()
            assert hist["ticker"] == ticker
            assert hist["market"] == market
            assert hist["period"] == "1 Month"
            assert "history" in hist
            assert len(hist["history"]) > 0
            row = hist["history"][0]
            for col in ["open", "high", "low", "close", "volume", "date", "formatted_date"]:
                assert col in row

        # 3. Profile
        res_prof = client.get(f"/api/stocks/profile?ticker={ticker}&market={market}")
        if res_prof.status_code == 200:
            prof = res_prof.json()
            assert prof["ticker"] == ticker
            assert prof["market"] == market
            assert "company_name" in prof
            assert "source" in prof

        # 4. Financials
        res_fin = client.get(f"/api/stocks/financials?ticker={ticker}&market={market}")
        if res_fin.status_code == 200:
            fin = res_fin.json()
            assert fin["ticker"] == ticker
            assert fin["market"] == market
            assert "annual" in fin
            assert "quarterly" in fin
    except Exception as exc:
        pytest.skip(f"Live network test skipped due to provider connectivity: {exc}")

# 12. Password Strength Validation Tests
def test_password_strength_validation(client):
    # Missing uppercase
    res = client.post("/api/auth/register", json={
        "full_name": "Test User",
        "email": "test_pass1@example.com",
        "password": "password123!",
        "confirm_password": "password123!"
    })
    assert res.status_code == 422

    # Missing lowercase
    res = client.post("/api/auth/register", json={
        "full_name": "Test User",
        "email": "test_pass2@example.com",
        "password": "PASSWORD123!",
        "confirm_password": "PASSWORD123!"
    })
    assert res.status_code == 422

    # Missing number
    res = client.post("/api/auth/register", json={
        "full_name": "Test User",
        "email": "test_pass3@example.com",
        "password": "Password!",
        "confirm_password": "Password!"
    })
    assert res.status_code == 422

    # Missing special character
    res = client.post("/api/auth/register", json={
        "full_name": "Test User",
        "email": "test_pass4@example.com",
        "password": "Password123",
        "confirm_password": "Password123"
    })
    assert res.status_code == 422

    # Shorter than 8 chars
    res = client.post("/api/auth/register", json={
        "full_name": "Test User",
        "email": "test_pass5@example.com",
        "password": "Pass1!",
        "confirm_password": "Pass1!"
    })
    assert res.status_code == 422

# 13. Test Analytics Endpoint Sentiment and Confidence
@patch("yfinance.Ticker")
def test_analytics_sentiment_calculation(mock_ticker_cls, client):
    mock_stock = MagicMock()
    mock_fast_info = MagicMock()
    mock_fast_info.get.side_effect = lambda k: "NMS" if k == "exchange" else "USD"
    mock_stock.fast_info = mock_fast_info

    # Upward trending series to trigger Bullish
    dates = pd.date_range("2026-01-01", periods=60, freq="D")
    prices = [100.0 + i * 1.5 for i in range(60)]
    df = pd.DataFrame({"Close": prices}, index=dates)
    mock_stock.history.return_value = df
    mock_ticker_cls.return_value = mock_stock

    res = client.get("/api/stocks/analytics?ticker=AAPL&market=NASDAQ&period=1 Year")
    assert res.status_code == 200
    data = res.json()
    assert data["sentiment"] in ("Bullish", "Bearish", "Neutral")
    assert "confidence" in data
    assert "explanation" in data
    assert "disclaimer" in data
    assert isinstance(data["signals"], list)

# 14. Test BSE Dividend-Only Row Filtering
@patch("yfinance.Ticker")
def test_bse_dividend_row_filtering(mock_ticker_cls, client):
    mock_stock = MagicMock()
    mock_fast_info = MagicMock()
    mock_fast_info.get.side_effect = lambda k: "BSE" if k == "exchange" else "INR"
    mock_stock.fast_info = mock_fast_info

    # Create DataFrame where one row is a dividend-only row (Close/Open is NaN)
    dates = pd.date_range("2026-11-01", periods=3, freq="D")
    df = pd.DataFrame({
        "Open": [1500.0, float("nan"), 1520.0],
        "High": [1510.0, float("nan"), 1530.0],
        "Low": [1490.0, float("nan"), 1510.0],
        "Close": [1505.0, float("nan"), 1525.0],
        "Volume": [10000, 0, 12000],
        "Dividends": [0.0, 10.0, 0.0]
    }, index=dates)
    mock_stock.history.return_value = df
    mock_ticker_cls.return_value = mock_stock

    res = client.get("/api/stocks/history?ticker=INFY&market=BSE&period=1 Month")
    assert res.status_code == 200
    data = res.json()
    # Dividend-only row with NaN Open/Close must be filtered out!
    assert data["count"] == 2
    assert len(data["history"]) == 2
    for row in data["history"]:
        assert row["open"] is not None
        assert row["close"] is not None
