from unittest.mock import MagicMock, patch
import numpy as np
import pandas as pd
import pytest
from app.schemas.market_data import StockMarketData
from app.services.market_data import (
    calculate_rsi,
    compute_technical_indicators,
    extract_news_articles,
    fetch_stock_market_data,
    validate_ticker,
)


def test_validate_ticker_valid():
    """Verify ticker validation standardizes and accepts valid symbols."""
    assert validate_ticker("AAPL") == "AAPL"
    assert validate_ticker("  msft  ") == "MSFT"
    assert validate_ticker("brk.b") == "BRK.B"
    assert validate_ticker("bf-b") == "BF-B"
    assert validate_ticker("NVDA") == "NVDA"


def test_validate_ticker_invalid():
    """Verify ticker validation rejects invalid formats."""
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_ticker("")

    with pytest.raises(ValueError, match="cannot be empty"):
        validate_ticker(None)

    with pytest.raises(ValueError, match="Invalid ticker symbol format"):
        validate_ticker("TOOLONGTICKERNAME")

    with pytest.raises(ValueError, match="Invalid ticker symbol format"):
        validate_ticker("AAPL$123")


def test_calculate_rsi():
    """Verify RSI calculation logic with normal and edge cases."""
    # Insufficient elements
    short_series = pd.Series([100.0, 102.0, 101.0])
    assert calculate_rsi(short_series, period=14) is None

    # Empty series
    assert calculate_rsi(pd.Series([], dtype=float), period=14) is None

    # Steady upward momentum
    up_prices = pd.Series([100.0 + i * 2.0 for i in range(25)])
    rsi_up = calculate_rsi(up_prices, period=14)
    assert rsi_up is not None
    assert rsi_up > 70.0  # Overbought/strong uptrend

    # Steady downward momentum
    down_prices = pd.Series([200.0 - i * 2.5 for i in range(25)])
    rsi_down = calculate_rsi(down_prices, period=14)
    assert rsi_down is not None
    assert rsi_down < 30.0  # Oversold/strong downtrend


def test_extract_news_articles():
    """Verify news parser handles multiple yfinance payload structures."""
    sample_raw_news = [
        # Modern v2 yfinance structure
        {
            "id": "item-1",
            "content": {
                "title": "Tech Giant Expands AI Services",
                "summary": "Revenue grew significantly this quarter.",
                "provider": {"displayName": "Financial Times"},
                "canonicalUrl": {"url": "https://example.com/article1"},
                "pubDate": "2026-11-14T10:00:00Z",
            },
        },
        # Legacy top-level structure
        {
            "title": "Market Rally Continues",
            "summary": "Indices closed at record highs.",
            "publisher": "Bloomberg",
            "link": "https://example.com/article2",
            "providerPublishTime": 1794685200,
        },
    ]

    articles = extract_news_articles(sample_raw_news)
    assert len(articles) == 2
    assert articles[0].title == "Tech Giant Expands AI Services"
    assert articles[0].publisher == "Financial Times"
    assert articles[0].link == "https://example.com/article1"
    assert articles[1].title == "Market Rally Continues"
    assert articles[1].publisher == "Bloomberg"

    # Edge cases
    assert extract_news_articles(None) == []
    assert extract_news_articles([]) == []


@patch("app.services.market_data.yf.Ticker")
def test_fetch_stock_market_data_with_mock(mock_ticker_class):
    """Verify complete market data fetching using mocked yfinance objects without live network calls."""
    # Build mocked Ticker instance
    mock_instance = MagicMock()

    # Mock .info
    mock_instance.info = {
        "symbol": "MOCK",
        "shortName": "Mock Technologies Inc.",
        "currentPrice": 150.25,
        "previousClose": 148.00,
        "dayHigh": 152.00,
        "dayLow": 147.50,
        "fiftyTwoWeekHigh": 175.00,
        "fiftyTwoWeekLow": 110.00,
        "marketCap": 250000000000,
        "currency": "USD",
        "trailingPE": 28.5,
        "forwardPE": 24.2,
        "priceToBook": 8.4,
        "enterpriseToEbitda": 18.2,
        "profitMargins": 0.22,
        "operatingMargins": 0.26,
        "grossMargins": 0.45,
        "revenueGrowth": 0.12,
        "earningsGrowth": 0.15,
        "totalRevenue": 45000000000,
        "ebitda": 12000000000,
        "totalDebt": 10000000000,
        "totalCash": 15000000000,
        "debtToEquity": 45.2,
        "freeCashflow": 8500000000,
        "dividendYield": 0.015,
        "fiftyDayAverage": 145.00,
        "twoHundredDayAverage": 138.00,
        "sector": "Technology",
        "industry": "Software",
        "country": "United States",
        "beta": 1.15,
        "longBusinessSummary": "Mock Technologies builds advanced AI and cloud infrastructure.",
    }

    # Mock .history
    dates = pd.date_range(end="2026-11-14", periods=120)
    mock_hist = pd.DataFrame(
        {
            "Open": [130.0 + i * 0.2 for i in range(120)],
            "High": [132.0 + i * 0.2 for i in range(120)],
            "Low": [129.0 + i * 0.2 for i in range(120)],
            "Close": [131.0 + i * 0.2 for i in range(120)],
            "Volume": [1000000 + i * 5000 for i in range(120)],
        },
        index=dates,
    )
    mock_instance.history.return_value = mock_hist

    # Mock .news
    mock_instance.news = [
        {
            "content": {
                "title": "Mock Tech Launches Next-Gen Platform",
                "summary": "Platform enhances developer efficiency.",
                "provider": {"displayName": "TechWire"},
                "canonicalUrl": {"url": "https://example.com/mock-news"},
                "pubDate": "2026-11-14T08:00:00Z",
            }
        }
    ]

    mock_ticker_class.return_value = mock_instance

    # Execute service function
    result = fetch_stock_market_data("MOCK")

    assert isinstance(result, StockMarketData)
    assert result.ticker == "MOCK"
    assert result.company_name == "Mock Technologies Inc."
    assert result.price.current_price == 150.25
    assert result.price.previous_close == 148.00
    assert result.price.day_change == 2.25
    assert result.fundamentals.pe_ratio == 28.5
    assert result.fundamentals.free_cash_flow == 8500000000.0
    assert result.technicals.trend_signal == "BULLISH"
    assert result.technicals.rsi_14 is not None
    assert len(result.news) == 1
    assert result.news[0].publisher == "TechWire"
    assert result.profile.sector == "Technology"


@patch("app.services.market_data.yf.Ticker")
def test_fetch_stock_market_data_invalid_symbol(mock_ticker_class):
    """Verify service raises ValueError when ticker is unlisted or has no data."""
    mock_instance = MagicMock()
    mock_instance.info = {}  # Empty response from Yahoo Finance for invalid ticker
    mock_ticker_class.return_value = mock_instance

    with pytest.raises(ValueError, match="was not found or has no active market data available"):
        fetch_stock_market_data("XYZ999")


@patch("app.services.market_data.yf.Ticker")
def test_fetch_stock_market_data_network_error(mock_ticker_class):
    """Verify service raises RuntimeError when provider network call fails."""
    mock_ticker_class.side_effect = ConnectionError("Connection refused by provider")

    with pytest.raises(RuntimeError, match="Market data provider query failed"):
        fetch_stock_market_data("AAPL")


@patch("app.services.market_data.yf.Ticker")
def test_fetch_stock_market_data_handles_missing_fields_without_fabrication(mock_ticker_class):
    """Verify service leaves missing financial figures as None and never fabricates numbers."""
    mock_instance = MagicMock()
    mock_instance.info = {
        "symbol": "GROWTH",
        "shortName": "Unprofitable Growth Co.",
        "currentPrice": 45.00,
        "previousClose": 46.00,
        "trailingPE": None,  # No P/E because company is unprofitable
        "dividendYield": None,  # Pays no dividend
        "freeCashflow": None,  # Negative or not reported
    }
    mock_instance.history.return_value = pd.DataFrame()
    mock_instance.news = []
    mock_ticker_class.return_value = mock_instance

    result = fetch_stock_market_data("GROWTH")

    assert result.ticker == "GROWTH"
    assert result.price.current_price == 45.00
    # Crucial assertion: metrics must remain None, never fabricated!
    assert result.fundamentals.pe_ratio is None
    assert result.fundamentals.dividend_yield is None
    assert result.fundamentals.free_cash_flow is None
    assert result.technicals.rsi_14 is None
    assert result.news == []
