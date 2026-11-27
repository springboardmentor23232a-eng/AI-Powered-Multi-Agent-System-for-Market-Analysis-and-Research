import pytest
from datetime import datetime
from unittest.mock import MagicMock
import pandas as pd
import numpy as np
from fastapi import HTTPException

from app.schemas.stock import (
    StockSearchResult,
    StockOverviewResponse,
    HistoricalDataResponse,
    FinancialStatementsResponse,
)
from app.services.validation_service import (
    validate_ticker_symbol,
    check_missing_values,
    check_duplicate_dates,
    check_invalid_prices,
    check_chronological_order,
    validate_and_clean_market_data,
)
from app.services.stock_service import (
    search_stocks,
    get_company_overview,
    get_historical_ohlcv,
    get_financial_statements,
    _dataframe_to_statement_data,
)
from app.services.research_service import (
    determine_market_from_ticker,
    validate_market_and_ticker,
    execute_research_workflow,
)
from app.schemas.research import ResearchTaskCreate
from app.models.research_task import ResearchTask, ResearchReport
from app.models.user import User


def register_and_login_market_user(client, email: str = "market_tester@example.com"):
    reg_payload = {
        "fullName": "Market Data Tester",
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


# ── 1. Ticker Symbol Validation Tests ──────────────────────────────────────────

def test_validate_ticker_symbol_valid():
    assert validate_ticker_symbol("aapl") == "AAPL"
    assert validate_ticker_symbol("  infy.ns  ") == "INFY.NS"
    assert validate_ticker_symbol("500209.bo") == "500209.BO"
    assert validate_ticker_symbol("brk.a") == "BRK.A"


def test_validate_ticker_symbol_invalid():
    with pytest.raises(HTTPException) as exc1:
        validate_ticker_symbol("")
    assert exc1.value.status_code == 400

    with pytest.raises(HTTPException) as exc2:
        validate_ticker_symbol("   ")
    assert exc2.value.status_code == 400

    with pytest.raises(HTTPException) as exc3:
        validate_ticker_symbol("AAPL@123")
    assert exc3.value.status_code == 400

    with pytest.raises(HTTPException) as exc4:
        validate_ticker_symbol("A" * 25)
    assert exc4.value.status_code == 400


# ── 2. Data Cleaning & Validation Function Tests ───────────────────────────────

def test_check_missing_values():
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    df = pd.DataFrame(
        {
            "Open": [100.0, np.nan, 102.0, 103.0, 104.0],
            "High": [105.0, 106.0, np.nan, 108.0, 109.0],
            "Low": [95.0, 96.0, 97.0, np.nan, 99.0],
            "Close": [102.0, 101.0, 103.0, 105.0, np.nan],
            "Volume": [1000, 1100, np.nan, 1300, 1400],
        },
        index=dates,
    )
    clean_df, missing_count = check_missing_values(df)
    assert missing_count == 4
    assert clean_df.isna().sum().sum() == 0


def test_check_duplicate_dates():
    dates = [
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2024-01-02"),
        pd.Timestamp("2024-01-02"),  # Duplicate
        pd.Timestamp("2024-01-03"),
    ]
    df = pd.DataFrame(
        {
            "Open": [100.0, 101.0, 101.5, 102.0],
            "High": [105.0, 106.0, 106.5, 107.0],
            "Low": [95.0, 96.0, 96.5, 97.0],
            "Close": [102.0, 103.0, 103.5, 104.0],
            "Volume": [1000, 1100, 1150, 1200],
        },
        index=dates,
    )
    clean_df, dup_count = check_duplicate_dates(df)
    assert dup_count == 1
    assert len(clean_df) == 3
    assert clean_df.loc[pd.Timestamp("2024-01-02")]["Open"] == 101.5  # Keeps last


def test_check_invalid_prices_and_inverted_ohlc():
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    df = pd.DataFrame(
        {
            "Open": [100.0, -5.0, 102.0, 103.0],  # row 1: negative price
            "High": [105.0, 106.0, 90.0, 108.0],   # row 2: High < Low (inverted)
            "Low": [95.0, 96.0, 98.0, 99.0],
            "Close": [102.0, 101.0, 95.0, 105.0],
            "Volume": [1000, 1100, 1200, 1300],
        },
        index=dates,
    )
    clean_df, invalid_count, inverted_count = check_invalid_prices(df)
    assert invalid_count == 1
    assert inverted_count == 1
    assert len(clean_df) == 2


def test_check_chronological_order():
    dates = [
        pd.Timestamp("2024-01-03"),
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2024-01-02"),
    ]
    df = pd.DataFrame(
        {
            "Open": [103.0, 100.0, 101.0],
            "High": [108.0, 105.0, 106.0],
            "Low": [98.0, 95.0, 96.0],
            "Close": [104.0, 102.0, 103.0],
            "Volume": [1300, 1000, 1100],
        },
        index=dates,
    )
    sorted_df, was_chronological = check_chronological_order(df)
    assert was_chronological is False
    assert list(sorted_df.index) == sorted(dates)


def test_validate_and_clean_market_data_telemetry():
    dates = [
        pd.Timestamp("2024-01-02"),
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2024-01-02"),  # Duplicate
    ]
    df = pd.DataFrame(
        {
            "Open": [100.0, np.nan, 102.0],
            "High": [105.0, 104.0, 106.0],
            "Low": [95.0, 94.0, 96.0],
            "Close": [102.0, 101.0, 103.0],
            "Volume": [1000, 1100, 1200],
        },
        index=dates,
    )
    clean_df, telemetry = validate_and_clean_market_data(df, "TEST")
    assert telemetry["ticker"] == "TEST"
    assert telemetry["total_input_rows"] == 3
    assert telemetry["total_raw_records"] == 3
    assert telemetry["duplicate_date_count"] == 1
    assert "warnings" in telemetry
    assert "validation_status" in telemetry
    assert isinstance(clean_df, pd.DataFrame)


# ── 3. Stock Search Tests ──────────────────────────────────────────────────────

def test_search_stocks_predefined_universe():
    # Indian NSE
    res_nse = search_stocks("Infosys")
    assert res_nse.count > 0
    assert any("INFY.NS" in r.ticker for r in res_nse.results)

    # Indian BSE
    res_bse = search_stocks("500209")
    assert res_bse.count > 0
    assert any("500209.BO" in r.ticker for r in res_bse.results)

    # US NASDAQ
    res_nasdaq = search_stocks("Apple")
    assert res_nasdaq.count > 0
    assert any("AAPL" == r.ticker for r in res_nasdaq.results)

    # US NYSE
    res_nyse = search_stocks("IBM")
    assert res_nyse.count > 0
    assert any("IBM" == r.ticker for r in res_nyse.results)


def test_search_stocks_empty():
    res = search_stocks("")
    assert res.count == 0
    assert res.results == []


# ── 4. Financial Statements Service Tests ──────────────────────────────────────

def test_dataframe_to_statement_data_conversion():
    # Null input returns empty StatementData
    res_none = _dataframe_to_statement_data("income_statement", None)
    assert res_none.raw_available is False
    assert res_none.periods == []
    assert res_none.items == []

    # Valid DataFrame conversion
    dates = [pd.Timestamp("2023-12-31"), pd.Timestamp("2022-12-31")]
    df = pd.DataFrame(
        {
            dates[0]: [1000000.0, 200000.0, np.nan],
            dates[1]: [900000.0, 180000.0, 50000.0],
        },
        index=["Total Revenue", "Operating Income", "Net Income"],
    )
    res = _dataframe_to_statement_data("income_statement_annual", df)
    assert res.raw_available is True
    assert len(res.periods) == 2
    assert "2023-12-31" in res.periods
    assert len(res.items) == 3
    revenue_item = next(i for i in res.items if i.metric == "Total Revenue")
    assert revenue_item.values["2023-12-31"] == 1000000.0


def test_get_financial_statements_mocked(monkeypatch):
    dates = [pd.Timestamp("2023-12-31"), pd.Timestamp("2022-12-31")]
    sample_df = pd.DataFrame(
        {
            dates[0]: [500000.0, 100000.0],
            dates[1]: [450000.0, 90000.0],
        },
        index=["Metric A", "Metric B"],
    )

    class MockTicker:
        def __init__(self, ticker):
            self.ticker = ticker
            self.info = {"longName": "Test Company", "currency": "USD"}
            self.income_stmt = sample_df
            self.quarterly_income_stmt = sample_df
            self.balance_sheet = sample_df
            self.quarterly_balance_sheet = sample_df
            self.cashflow = sample_df
            self.quarterly_cashflow = sample_df

    monkeypatch.setattr("app.services.stock_service.yf.Ticker", MockTicker)

    fin_res = get_financial_statements("AAPL")
    assert isinstance(fin_res, FinancialStatementsResponse)
    assert fin_res.ticker == "AAPL"
    assert fin_res.currency == "USD"
    assert fin_res.data_source == "yfinance"
    assert fin_res.income_statement.annual.raw_available is True
    assert fin_res.balance_sheet.annual.raw_available is True
    assert fin_res.cash_flow.annual.raw_available is True
    assert len(fin_res.income_statement.annual.items) == 2


# ── 5. Market Determinations and Inferences ────────────────────────────────────

def test_determine_market_from_ticker():
    assert determine_market_from_ticker("INFY.NS") == "NSE"
    assert determine_market_from_ticker("TCS.NS") == "NSE"
    assert determine_market_from_ticker("INFY.BO") == "BSE"
    assert determine_market_from_ticker("500209.BO") == "BSE"
    assert determine_market_from_ticker("IBM") == "NYSE"
    assert determine_market_from_ticker("JPM") == "NYSE"
    assert determine_market_from_ticker("AAPL") == "NASDAQ"
    assert determine_market_from_ticker("MSFT") == "NASDAQ"

    # Explicit market overrides
    assert determine_market_from_ticker("AAPL", explicit_market="NASDAQ") == "NASDAQ"
    assert determine_market_from_ticker("INFY", explicit_market="NSE") == "NSE"

    # Invalid market raises 400
    with pytest.raises(HTTPException) as exc:
        determine_market_from_ticker("AAPL", explicit_market="FOREX")
    assert exc.value.status_code == 400


def test_validate_market_and_ticker_incompatibilities():
    # US ticker on Indian market
    with pytest.raises(HTTPException):
        validate_market_and_ticker("NSE", "AAPL")

    with pytest.raises(HTTPException):
        validate_market_and_ticker("BSE", "MSFT")

    # Indian ticker on US market
    with pytest.raises(HTTPException):
        validate_market_and_ticker("NASDAQ", "INFY.NS")

    with pytest.raises(HTTPException):
        validate_market_and_ticker("NYSE", "INFY.BO")

    # Cross-Indian exchange suffix mismatch
    with pytest.raises(HTTPException):
        validate_market_and_ticker("NSE", "INFY.BO")

    with pytest.raises(HTTPException):
        validate_market_and_ticker("BSE", "INFY.NS")


# ── 6. Full API Endpoints & Research Workflow Verification ────────────────────

def test_api_stocks_search_authenticated(client):
    user = register_and_login_market_user(client, "search_user@example.com")
    res = client.get("/api/stocks/search?q=Infosys")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] > 0
    assert "results" in data
    first = data["results"][0]
    assert "ticker" in first
    assert "company_name" in first
    assert "market" in first


def test_api_stocks_financials_endpoint_mocked(client, monkeypatch):
    register_and_login_market_user(client, "financials_user@example.com")

    dates = [pd.Timestamp("2023-12-31")]
    df = pd.DataFrame({dates[0]: [1000000.0]}, index=["Revenue"])

    class MockTicker:
        def __init__(self, ticker):
            self.ticker = ticker
            self.info = {"longName": "Apple Inc.", "currency": "USD"}
            self.income_stmt = df
            self.quarterly_income_stmt = df
            self.balance_sheet = df
            self.quarterly_balance_sheet = df
            self.cashflow = df
            self.quarterly_cashflow = df

    monkeypatch.setattr("app.services.stock_service.yf.Ticker", MockTicker)

    res = client.get("/api/stocks/AAPL/financials")
    assert res.status_code == 200
    data = res.json()
    assert data["ticker"] == "AAPL"
    assert data["currency"] == "USD"
    assert data["data_source"] == "yfinance"
    assert "income_statement" in data
    assert "balance_sheet" in data
    assert "cash_flow" in data


def test_api_stocks_financials_endpoint_unauthenticated(client):
    # Unauthenticated client (no cookies)
    from fastapi.testclient import TestClient
    from app.main import app
    unauth_client = TestClient(app)

    res = unauth_client.get("/api/stocks/AAPL/financials")
    assert res.status_code == 401


def test_research_workflow_persists_financial_statements(client, db_session, monkeypatch):
    user_data = register_and_login_market_user(client, "workflow_user@example.com")
    user_id = user_data["user_id"]

    # Mock market data dependencies
    mock_overview = StockOverviewResponse(
        ticker="AAPL",
        company_name="Apple Inc.",
        exchange="NASDAQ",
        currency="USD",
        sector="Technology",
        industry="Consumer Electronics",
        current_price=180.50,
        previous_close=179.00,
        day_high=181.00,
        day_low=178.50,
        fifty_two_week_high=199.62,
        fifty_two_week_low=164.08,
        market_cap=2800000000000,
        pe_ratio=28.5,
        volume=50000000,
        average_volume=48000000,
        dividend_yield=0.55,
        business_summary="Apple designs consumer electronics.",
        data_source="yfinance",
        retrieved_at=datetime.utcnow().isoformat() + "Z",
    )

    from app.schemas.stock import StockSummaryStats, ValidationReport, OHLCVCandle
    mock_history = HistoricalDataResponse(
        ticker="AAPL",
        period="1mo",
        interval="1d",
        count=2,
        data_source="yfinance",
        retrieved_at=datetime.utcnow().isoformat() + "Z",
        stats=StockSummaryStats(
            start_date="2024-01-01",
            end_date="2024-01-02",
            highest_price=181.00,
            lowest_price=178.50,
            average_volume=50000000.0,
            total_trading_days=2,
            period_change_pct=1.0,
        ),
        validation=ValidationReport(
            ticker="AAPL",
            total_raw_records=2,
            cleaned_records=2,
            duplicates_removed=0,
            invalid_records_removed=0,
            is_chronological=True,
            total_input_rows=2,
            valid_rows=2,
            removed_rows=0,
            missing_value_count=0,
            duplicate_date_count=0,
            invalid_price_count=0,
            invalid_ohlc_count=0,
            warnings=[],
            validation_status="PASSED",
        ),
        candles=[
            OHLCVCandle(date="2024-01-01", open=179.0, high=180.5, low=178.5, close=180.0, volume=49000000),
            OHLCVCandle(date="2024-01-02", open=180.0, high=181.0, low=179.0, close=180.5, volume=51000000),
        ],
    )

    dates = [pd.Timestamp("2023-12-31")]
    fin_df = pd.DataFrame({dates[0]: [383285000000.0]}, index=["Total Revenue"])

    class MockTicker:
        def __init__(self, ticker):
            self.ticker = ticker
            self.info = {"longName": "Apple Inc.", "currency": "USD"}
            self.income_stmt = fin_df
            self.quarterly_income_stmt = fin_df
            self.balance_sheet = fin_df
            self.quarterly_balance_sheet = fin_df
            self.cashflow = fin_df
            self.quarterly_cashflow = fin_df

    monkeypatch.setattr("app.services.research_service.get_company_overview", lambda ticker: mock_overview)
    monkeypatch.setattr("app.services.research_service.get_historical_ohlcv", lambda ticker, period: mock_history)
    monkeypatch.setattr("app.services.stock_service.yf.Ticker", MockTicker)

    # Post research task
    res = client.post(
        "/api/research/tasks",
        json={"ticker": "AAPL", "period": "1mo", "market": "NASDAQ"},
    )
    assert res.status_code in {200, 201}
    resp_data = res.json()
    assert resp_data["task"]["status"] == "Completed"

    # Verify report persistence in PostgreSQL/SQLite
    report_in_db = (
        db_session.query(ResearchReport)
        .filter(ResearchReport.task_id == resp_data["task"]["task_id"])
        .first()
    )
    assert report_in_db is not None
    assert "financial_statements" in report_in_db.report_content
    fin_content = report_in_db.report_content["financial_statements"]
    assert fin_content is not None
    assert fin_content["ticker"] == "AAPL"
    assert "income_statement" in fin_content
    assert fin_content["income_statement"]["annual"]["raw_available"] is True
