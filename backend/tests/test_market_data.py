import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import pandas as pd

from app.main import app
from app.services.yahoo_finance import (
    yahoo_finance_service,
    StockNotFoundError,
    NoHistoricalDataError,
    MarketDataProviderError,
    RateLimitError,
)
from app.models import User
import uuid


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def dummy_user():
    return User(
        user_id=uuid.uuid4(),
        full_name="Test Analyst",
        email="analyst@example.com",
    )


# =========================================================================
# 1. Tests for Specific Required Symbols (Live Provider)
# =========================================================================

def test_nse_symbols():
    """Test required NSE symbols: TCS.NS, RELIANCE.NS, INFY.NS"""
    for sym in ["TCS.NS", "RELIANCE.NS", "INFY.NS"]:
        hist = yahoo_finance_service.get_historical_ohlcv(sym, market="NSE", period="1mo", interval="1d")
        assert hist["ticker"] == sym
        assert hist["market"] == "NSE"
        assert hist["currency"] == "INR"
        assert hist["data_source"] == "Yahoo Finance via yfinance"
        assert hist["current_price"] is not None and hist["current_price"] > 0
        assert len(hist["ohlcv"]) > 0

        bar = hist["ohlcv"][-1]
        assert bar["high"] >= bar["low"]
        assert bar["volume"] >= 0


def test_nasdaq_symbols():
    """Test required NASDAQ symbols: AAPL, NVDA, MSFT"""
    for sym in ["AAPL", "NVDA", "MSFT"]:
        hist = yahoo_finance_service.get_historical_ohlcv(sym, market="NASDAQ", period="1mo", interval="1d")
        assert hist["ticker"] == sym
        assert hist["market"] == "NASDAQ"
        assert hist["currency"] == "USD"
        assert hist["data_source"] == "Yahoo Finance via yfinance"
        assert hist["current_price"] is not None and hist["current_price"] > 0
        assert len(hist["ohlcv"]) > 0


def test_nyse_symbol():
    """Test required NYSE symbol: JPM"""
    hist = yahoo_finance_service.get_historical_ohlcv("JPM", market="NYSE", period="1mo", interval="1d")
    assert hist["ticker"] == "JPM"
    assert hist["market"] == "NYSE"
    assert hist["currency"] == "USD"
    assert hist["data_source"] == "Yahoo Finance via yfinance"
    assert hist["current_price"] is not None and hist["current_price"] > 0
    assert len(hist["ohlcv"]) > 0


# =========================================================================
# 2. Ticker Normalization Rules
# =========================================================================

def test_ticker_normalization():
    """
    Test ticker normalization:
    NSE: TCS -> TCS.NS, RELIANCE -> RELIANCE.NS, INFY -> INFY.NS
    BSE: TCS -> TCS.BO
    NASDAQ: AAPL, MSFT, NVDA
    NYSE: JPM, V, WMT
    Do not blindly append exchange suffixes to US stocks.
    """
    # NSE
    assert yahoo_finance_service.normalize_ticker("TCS", "NSE") == "TCS.NS"
    assert yahoo_finance_service.normalize_ticker("RELIANCE", "NSE") == "RELIANCE.NS"
    assert yahoo_finance_service.normalize_ticker("INFY", "NSE") == "INFY.NS"
    assert yahoo_finance_service.normalize_ticker("TCS.NS", "NSE") == "TCS.NS"
    assert yahoo_finance_service.normalize_ticker("TCS.BO", "NSE") == "TCS.NS"

    # BSE
    assert yahoo_finance_service.normalize_ticker("TCS", "BSE") == "TCS.BO"
    assert yahoo_finance_service.normalize_ticker("TCS.BO", "BSE") == "TCS.BO"
    assert yahoo_finance_service.normalize_ticker("TCS.NS", "BSE") == "TCS.BO"

    # NASDAQ (US) - must not have suffix appended
    assert yahoo_finance_service.normalize_ticker("AAPL", "NASDAQ") == "AAPL"
    assert yahoo_finance_service.normalize_ticker("MSFT", "NASDAQ") == "MSFT"
    assert yahoo_finance_service.normalize_ticker("NVDA", "NASDAQ") == "NVDA"
    assert yahoo_finance_service.normalize_ticker("AAPL.NS", "NASDAQ") == "AAPL"

    # NYSE (US) - must not have suffix appended
    assert yahoo_finance_service.normalize_ticker("JPM", "NYSE") == "JPM"
    assert yahoo_finance_service.normalize_ticker("V", "NYSE") == "V"
    assert yahoo_finance_service.normalize_ticker("WMT", "NYSE") == "WMT"
    assert yahoo_finance_service.normalize_ticker("JPM.BO", "NYSE") == "JPM"


# =========================================================================
# 3. Verification That All Artificial Data Generators Are Removed
# =========================================================================

def test_strictly_no_artificial_data_generators():
    """Verify that all artificial data generators and fallback catalogs are completely removed."""
    assert not hasattr(yahoo_finance_service, "_generate_ohlcv_fallback")
    assert not hasattr(yahoo_finance_service, "_generate_profile_fallback")
    assert not hasattr(yahoo_finance_service, "_generate_financials_fallback")
    assert not hasattr(yahoo_finance_service, "_search_fallback_catalog")
    assert not hasattr(yahoo_finance_service, "_offline_until")
    assert not hasattr(yahoo_finance_service, "_is_online")


# =========================================================================
# 4. Error Handling Tests (Invalid Ticker, Empty Response, Rate Limit, etc.)
# =========================================================================

def test_invalid_ticker_raises_stock_not_found():
    """Invalid ticker must raise StockNotFoundError, NEVER fake data."""
    with pytest.raises(StockNotFoundError):
        yahoo_finance_service.get_historical_ohlcv("INVALIDXYZ99999", market="NASDAQ")

    with pytest.raises(StockNotFoundError):
        yahoo_finance_service.get_company_profile("INVALIDXYZ99999", market="NASDAQ")

    with pytest.raises(StockNotFoundError):
        yahoo_finance_service.get_financial_statements("INVALIDXYZ99999", market="NASDAQ")


def test_empty_historical_response_handling():
    """Empty historical DataFrame must raise NoHistoricalDataError."""
    with patch("yfinance.Ticker") as mock_ticker_cls:
        mock_inst = MagicMock()
        mock_inst.history.return_value = pd.DataFrame()
        mock_inst.fast_info.last_price = 150.0  # ticker exists
        mock_ticker_cls.return_value = mock_inst

        with pytest.raises(NoHistoricalDataError):
            yahoo_finance_service.get_historical_ohlcv("AAPL", market="NASDAQ", period="1mo", interval="1d")


def test_network_connection_failure():
    """Network connection failure must raise MarketDataProviderError, never synthetic fallback."""
    with patch("yfinance.Ticker") as mock_ticker_cls:
        mock_inst = MagicMock()
        mock_inst.history.side_effect = Exception("Connection refused / Network unreachable")
        mock_ticker_cls.return_value = mock_inst

        with pytest.raises(MarketDataProviderError) as exc_info:
            yahoo_finance_service.get_historical_ohlcv("AAPL", market="NASDAQ")
        assert "Market data provider unavailable" in str(exc_info.value)


def test_rate_limiting_handling():
    """Rate limit 429 must raise RateLimitError with a helpful message."""
    with patch("yfinance.Ticker") as mock_ticker_cls:
        mock_inst = MagicMock()
        mock_inst.history.side_effect = Exception("HTTP 429 Too Many Requests")
        mock_ticker_cls.return_value = mock_inst

        with pytest.raises(RateLimitError) as exc_info:
            yahoo_finance_service.get_historical_ohlcv("AAPL", market="NASDAQ")
        assert "Request limit reached" in str(exc_info.value)


def test_missing_financial_information_returns_na():
    """Missing financial items must return 'N/A' or empty lists, never fabricated values."""
    with patch("yfinance.Ticker") as mock_ticker_cls:
        mock_inst = MagicMock()
        mock_inst.fast_info.last_price = 100.0
        mock_inst.info = {"symbol": "TEST"}
        mock_inst.income_stmt = pd.DataFrame()  # empty statements
        mock_inst.balance_sheet = pd.DataFrame()
        mock_inst.cashflow = pd.DataFrame()
        mock_ticker_cls.return_value = mock_inst

        fin = yahoo_finance_service.get_financial_statements("TEST", market="NASDAQ")
        assert fin["income_statement"] == []
        assert fin["balance_sheet"] == []
        assert fin["cash_flow"] == []
        assert fin["key_ratios"]["gross_margin"] == "N/A"
        assert fin["key_ratios"]["profit_margin"] == "N/A"
        assert fin["key_ratios"]["return_on_equity"] == "N/A"


# =========================================================================
# 5. Search, Profile, Financials, and Router Tests
# =========================================================================

def test_search_verified_results():
    """Search returns only verified actual provider results."""
    res_tcs = yahoo_finance_service.search("TCS", market="NSE")
    assert len(res_tcs) > 0
    assert any("TCS" in r["ticker"] for r in res_tcs)
    assert res_tcs[0]["data_source"] == "Yahoo Finance via yfinance"

    res_aapl = yahoo_finance_service.search("Apple", market="NASDAQ")
    assert len(res_aapl) > 0
    assert any("AAPL" in r["ticker"] for r in res_aapl)


def test_company_profile_data():
    """Company profile returns actual fields without fictional values."""
    prof = yahoo_finance_service.get_company_profile("AAPL", market="NASDAQ")
    assert prof["ticker"] == "AAPL"
    assert prof["company_name"] == "Apple Inc."
    assert prof["sector"] != "N/A"
    assert prof["data_source"] == "Yahoo Finance via yfinance"
    assert isinstance(prof["officers"], list)


def test_financial_statements_data():
    """Financial statements return actual statements and metrics."""
    fin = yahoo_finance_service.get_financial_statements("AAPL", market="NASDAQ")
    assert fin["ticker"] == "AAPL"
    assert len(fin["income_statement"]) > 0
    assert len(fin["balance_sheet"]) > 0
    assert len(fin["cash_flow"]) > 0
    assert fin["key_ratios"]["gross_margin"] != "N/A"


def test_router_endpoints(dummy_user):
    """Test API router endpoints with yfinance integration."""
    from app.routers.market_data import (
        get_market_api_config,
        search_stocks,
        get_historical_prices,
        get_company_profile,
        get_financial_statements,
    )

    # 1. Config endpoint
    cfg = get_market_api_config(current_user=dummy_user)
    assert cfg["provider"] == "Yahoo Finance (via yfinance)"
    assert cfg["has_api_key"] is False
    assert cfg["requires_api_key"] is False

    # 2. Search endpoint
    search_res = search_stocks(q="AAPL", market="NASDAQ", current_user=dummy_user)
    assert len(search_res) > 0
    assert search_res[0]["data_source"] == "Yahoo Finance via yfinance"

    # 3. Historical endpoint
    hist_res = get_historical_prices(ticker="AAPL", market="NASDAQ", period="1mo", interval="1d", current_user=dummy_user)
    assert hist_res["ticker"] == "AAPL"
    assert len(hist_res["ohlcv"]) > 0
    assert hist_res["data_source"] == "Yahoo Finance via yfinance"

    # 4. Invalid ticker raises 404
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        get_historical_prices(ticker="INVALIDXYZ99999", market="NASDAQ", current_user=dummy_user)
    assert exc_info.value.status_code == 404

