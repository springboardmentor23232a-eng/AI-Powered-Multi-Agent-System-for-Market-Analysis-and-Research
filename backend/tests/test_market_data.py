from unittest.mock import patch
import numpy as np
import pandas as pd

from app.services.market_data_service import get_yf_symbol, validate_ohlcv_dataframe


def _get_auth_headers(client, email="mkt_user@example.com"):
    client.post("/api/auth/register", json={
        "full_name": "Market Tester",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!",
    })
    res = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_yf_symbol_mapping():
    assert get_yf_symbol("infy", "NSE") == "INFY.NS"
    assert get_yf_symbol("INFY.NS", "NSE") == "INFY.NS"
    assert get_yf_symbol("500209", "BSE") == "500209.BO"
    assert get_yf_symbol("aapl", "NASDAQ") == "AAPL"
    assert get_yf_symbol("jpm", "NYSE") == "JPM"


def test_validate_ohlcv_clean_data():
    dates = pd.date_range("2026-01-01", periods=5, freq="B")
    df = pd.DataFrame({
        "Open": [100.0, 102.0, 101.0, 103.0, 105.0],
        "High": [103.0, 104.0, 103.5, 106.0, 107.0],
        "Low": [99.0, 101.0, 100.0, 102.0, 104.0],
        "Close": [102.0, 101.5, 103.0, 105.0, 106.0],
        "Volume": [1000, 1200, 1100, 1500, 1600],
    }, index=dates)

    cleaned, report = validate_ohlcv_dataframe(df)
    assert report["quality_status"] == "VALID"
    assert report["total_raw_rows"] == 5
    assert report["valid_rows"] == 5
    assert report["duplicate_dates_removed"] == 0
    assert report["missing_values_count"] == 0
    assert report["inconsistent_rows_count"] == 0
    assert len(cleaned) == 5


def test_validate_ohlcv_detects_duplicates_missing_and_inconsistent():
    dates = pd.to_datetime([
        "2026-01-02",
        "2026-01-02",  # duplicate date
        "2026-01-05",
        "2026-01-06",
        "2026-01-07",
    ])
    df = pd.DataFrame({
        "Open": [100.0, 101.0, np.nan, 104.0, 105.0],
        "High": [105.0, 106.0, 104.0, 102.0, 108.0],  # row 4: High(102) < Low(103) & Open(104)
        "Low": [99.0, 100.0, 100.0, 103.0, 104.0],
        "Close": [102.0, 103.0, 102.0, 101.0, 107.0],
        "Volume": [1000, 1100, 1200, -50, np.nan],  # negative volume + missing volume
    }, index=dates)

    cleaned, report = validate_ohlcv_dataframe(df)
    assert report["quality_status"] == "VALID_WITH_WARNINGS"
    assert report["duplicate_dates_removed"] == 1
    assert report["missing_values_count"] == 2  # Open NaN + Volume NaN
    assert report["inconsistent_rows_count"] >= 1
    assert report["valid_rows"] == 3  # 5 raw - 1 dup - 1 missing Open
    assert (cleaned["High"] >= cleaned["Low"]).all()
    assert (cleaned["Volume"] >= 0).all()


def test_stock_search_with_market_filter(client):
    headers = _get_auth_headers(client, "search_filter@example.com")

    res_nse = client.get("/api/stocks/search?q=Infosys&market=NSE", headers=headers)
    assert res_nse.status_code == 200
    data_nse = res_nse.json()
    assert len(data_nse) >= 1
    assert all(item["market"] == "NSE" for item in data_nse)
    assert any(item["ticker"] == "INFY" for item in data_nse)

    res_nasdaq = client.get("/api/stocks/search?q=Apple&market=NASDAQ", headers=headers)
    assert res_nasdaq.status_code == 200
    data_us = res_nasdaq.json()
    assert any(item["ticker"] == "AAPL" and item["market"] == "NASDAQ" for item in data_us)


def test_market_data_endpoint(client):
    headers = _get_auth_headers(client, "mkt_ep@example.com")
    fake_payload = {
        "ticker": "AAPL",
        "market": "NASDAQ",
        "yf_symbol": "AAPL",
        "period": "1 Month",
        "retrieved_at": "2026-11-26T10:00:00+00:00",
        "profile": {
            "ticker": "AAPL",
            "company_name": "Apple Inc.",
            "market": "NASDAQ",
            "currency": "USD",
            "current_price": 225.0,
        },
        "period_performance": {"period": "1 Month", "change_percent": 4.5, "trading_days": 2},
        "ohlcv": [
            {"date": "2026-11-24", "open": 215.0, "high": 218.0, "low": 214.0, "close": 215.3, "volume": 1000000},
            {"date": "2026-11-25", "open": 216.0, "high": 226.0, "low": 215.5, "close": 225.0, "volume": 1200000},
        ],
        "data_quality": {
            "total_raw_rows": 2,
            "valid_rows": 2,
            "duplicate_dates_removed": 0,
            "duplicate_dates": [],
            "missing_values_count": 0,
            "missing_value_details": [],
            "inconsistent_rows_count": 0,
            "inconsistent_row_details": [],
            "date_gaps": [],
            "quality_status": "VALID",
            "validated_at": "2026-11-26T10:00:00+00:00",
            "notes": ["All OHLCV rows passed completeness, uniqueness, and price consistency checks."],
        },
        "financial_statements": {
            "income_statement": {"statement_type": "Income Statement", "currency": "USD", "periods": [], "rows": {}},
            "balance_sheet": {"statement_type": "Balance Sheet", "currency": "USD", "periods": [], "rows": {}},
            "cash_flow": {"statement_type": "Cash Flow Statement", "currency": "USD", "periods": [], "rows": {}},
        },
        "sources": [
            {
                "source_type": "MARKET_OHLCV",
                "title": "Yahoo Finance Historical OHLCV (AAPL, 1 Month)",
                "source_url": "https://finance.yahoo.com/quote/AAPL/history",
                "published_at": "2026-11-25",
                "retrieved_at": "2026-11-26T10:00:00+00:00",
                "content_hash": "abc123",
            }
        ],
    }

    with patch("app.routers.stocks.MarketDataCollector.collect_market_data", return_value=fake_payload):
        res = client.get("/api/stocks/AAPL/market-data?market=NASDAQ&period=1%20Month", headers=headers)
        assert res.status_code == 200
        body = res.json()
        assert body["ticker"] == "AAPL"
        assert len(body["ohlcv"]) == 2
        assert body["data_quality"]["quality_status"] == "VALID"
        assert len(body["sources"]) == 1

