from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import yfinance as yf
from app.schemas.market_data import (
    CompanyProfile,
    FundamentalMetrics,
    NewsArticle,
    PriceSummary,
    StockMarketData,
    TechnicalIndicators,
)


def validate_ticker(ticker: str) -> str:
    """
    Validates and standardizes a stock ticker symbol.
    - Strips leading/trailing whitespace
    - Converts to uppercase
    - Validates 1-10 alphanumeric characters (allowing '.' and '-' for tickers like BRK.B)
    Raises ValueError on invalid format.
    """
    if not ticker or not isinstance(ticker, str):
        raise ValueError("Ticker symbol cannot be empty.")

    cleaned_ticker = ticker.strip().upper()

    if not re.match(r"^[A-Z0-9.\-]{1,10}$", cleaned_ticker):
        raise ValueError(
            f"Invalid ticker symbol format: '{ticker}'. Ticker must be 1 to 10 alphanumeric characters."
        )

    return cleaned_ticker


def _safe_float(val: Any, round_digits: Optional[int] = 2) -> Optional[float]:
    """Safely converts numerical input to float or returns None; avoids NaN/Inf."""
    if val is None or pd.isna(val):
        return None
    try:
        f = float(val)
        if np.isnan(f) or np.isinf(f):
            return None
        return round(f, round_digits) if round_digits is not None else f
    except (ValueError, TypeError):
        return None


def calculate_rsi(series: pd.Series, period: int = 14) -> Optional[float]:
    """
    Calculates 14-period Relative Strength Index (RSI) from historical closing prices.
    Returns float (0 to 100) or None if insufficient historical data.
    """
    if series is None or len(series) < period + 1:
        return None

    try:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        last_val = rsi.iloc[-1]
        return _safe_float(last_val, round_digits=2)
    except Exception:
        return None


def extract_news_articles(raw_news: Optional[List[Dict[str, Any]]], max_items: int = 10) -> List[NewsArticle]:
    """
    Safely parses financial news articles from yfinance across different API payload versions.
    Never fabricates news content.
    """
    if not raw_news:
        return []

    articles: List[NewsArticle] = []
    for item in raw_news[:max_items]:
        if not isinstance(item, dict):
            continue

        # Extract content (v1 vs v2 structure compatibility)
        content = item.get("content") if isinstance(item.get("content"), dict) else item

        title = content.get("title") or item.get("title")
        if not title:
            continue

        summary = content.get("summary") or item.get("summary") or content.get("description")
        
        # Publisher
        provider = content.get("provider")
        publisher = None
        if isinstance(provider, dict):
            publisher = provider.get("displayName")
        elif isinstance(provider, str):
            publisher = provider
        elif "publisher" in item:
            publisher = item.get("publisher")

        # URL
        canonical = content.get("canonicalUrl")
        link = None
        if isinstance(canonical, dict):
            link = canonical.get("url")
        elif isinstance(canonical, str):
            link = canonical
        elif "link" in item:
            link = item.get("link")

        # Publication time
        pub_time = content.get("pubDate") or content.get("displayTime") or item.get("providerPublishTime")
        if isinstance(pub_time, (int, float)):
            try:
                pub_time = datetime.fromtimestamp(pub_time, tz=timezone.utc).isoformat()
            except Exception:
                pub_time = str(pub_time)

        articles.append(
            NewsArticle(
                title=str(title).strip(),
                summary=str(summary).strip() if summary else None,
                publisher=str(publisher).strip() if publisher else None,
                link=str(link).strip() if link else None,
                published_at=str(pub_time) if pub_time else None,
            )
        )

    return articles


def compute_technical_indicators(hist: pd.DataFrame, info: Dict[str, Any]) -> TechnicalIndicators:
    """
    Computes key quantitative chart and trend indicators from historical price data.
    Never fabricates missing indicator values.
    """
    if hist is None or hist.empty or "Close" not in hist.columns:
        return TechnicalIndicators(
            sma_50=_safe_float(info.get("fiftyDayAverage")),
            sma_200=_safe_float(info.get("twoHundredDayAverage")),
            trend_signal="NEUTRAL",
        )

    close_series = hist["Close"]
    total_candles = len(close_series)

    # Moving Averages
    sma_50 = _safe_float(close_series.rolling(window=min(50, total_candles)).mean().iloc[-1]) if total_candles >= 20 else _safe_float(info.get("fiftyDayAverage"))
    sma_200 = _safe_float(close_series.rolling(window=min(200, total_candles)).mean().iloc[-1]) if total_candles >= 100 else _safe_float(info.get("twoHundredDayAverage"))

    # RSI (14 period)
    rsi_14 = calculate_rsi(close_series, period=14)

    # 30-day and 90-day returns
    pct_30d = None
    if total_candles >= 22:
        start_p = close_series.iloc[-22]
        end_p = close_series.iloc[-1]
        if start_p > 0:
            pct_30d = _safe_float(((end_p - start_p) / start_p) * 100, round_digits=2)

    pct_90d = None
    if total_candles >= 65:
        start_p90 = close_series.iloc[-65]
        end_p90 = close_series.iloc[-1]
        if start_p90 > 0:
            pct_90d = _safe_float(((end_p90 - start_p90) / start_p90) * 100, round_digits=2)

    # Support & Resistance (6-month min & max)
    support_level = _safe_float(close_series.min())
    resistance_level = _safe_float(close_series.max())

    # Trend Determination
    latest_close = close_series.iloc[-1]
    trend = "NEUTRAL"
    if sma_50 and sma_200:
        if latest_close > sma_50 > sma_200:
            trend = "BULLISH"
        elif latest_close < sma_50 < sma_200:
            trend = "BEARISH"
    elif sma_50:
        if latest_close > sma_50:
            trend = "BULLISH"
        elif latest_close < sma_50:
            trend = "BEARISH"

    # Recent 30 daily price bars
    recent_bars = []
    tail_hist = hist.tail(30)
    for index, row in tail_hist.iterrows():
        date_str = index.strftime("%Y-%m-%d") if hasattr(index, "strftime") else str(index)
        recent_bars.append({
            "date": date_str,
            "close": _safe_float(row.get("Close")),
            "high": _safe_float(row.get("High")),
            "low": _safe_float(row.get("Low")),
            "volume": int(row.get("Volume", 0)) if not pd.isna(row.get("Volume")) else 0,
        })

    return TechnicalIndicators(
        sma_50=sma_50,
        sma_200=sma_200,
        rsi_14=rsi_14,
        trend_signal=trend,
        price_change_30d_pct=pct_30d,
        price_change_90d_pct=pct_90d,
        support_level=support_level,
        resistance_level=resistance_level,
        recent_history=recent_bars,
    )


def fetch_stock_market_data(ticker_symbol: str) -> StockMarketData:
    """
    Fetches real-time and historical financial market data for a given ticker symbol using yfinance.
    Validates the ticker, handles network/API errors, and returns a verified Pydantic StockMarketData object.
    Never fabricates figures.
    """
    # 1. Validate ticker syntax
    ticker = validate_ticker(ticker_symbol)

    # 2. Query market data provider
    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info or {}
    except Exception as exc:
        raise RuntimeError(f"Market data provider query failed for '{ticker}': {exc}") from exc

    # 3. Verify ticker validity from response
    # Valid tickers return non-null price, symbol, or quoteType
    current_price = _safe_float(info.get("currentPrice") or info.get("regularMarketPrice"))
    prev_close = _safe_float(info.get("previousClose") or info.get("regularMarketPreviousClose"))
    company_name = info.get("shortName") or info.get("longName") or info.get("name")

    if not current_price and not prev_close and not company_name:
        raise ValueError(
            f"Ticker symbol '{ticker}' was not found or has no active market data available."
        )

    # 4. Fetch 6-month historical price data
    try:
        hist_df = ticker_obj.history(period="6mo", interval="1d")
    except Exception:
        hist_df = pd.DataFrame()

    # 5. Extract News
    try:
        raw_news = ticker_obj.news
        news_articles = extract_news_articles(raw_news)
    except Exception:
        news_articles = []

    # 6. Build Price Summary
    day_change = None
    day_change_pct = None
    if current_price and prev_close and prev_close > 0:
        day_change = _safe_float(current_price - prev_close)
        day_change_pct = _safe_float(((current_price - prev_close) / prev_close) * 100)

    price_summary = PriceSummary(
        current_price=current_price,
        previous_close=prev_close,
        day_change=day_change,
        day_change_percent=day_change_pct,
        day_high=_safe_float(info.get("dayHigh") or info.get("regularMarketDayHigh")),
        day_low=_safe_float(info.get("dayLow") or info.get("regularMarketDayLow")),
        fifty_two_week_high=_safe_float(info.get("fiftyTwoWeekHigh")),
        fifty_two_week_low=_safe_float(info.get("fiftyTwoWeekLow")),
        market_cap=_safe_float(info.get("marketCap")),
        currency=info.get("currency") or "USD",
    )

    # 7. Build Fundamental Metrics
    fundamentals = FundamentalMetrics(
        pe_ratio=_safe_float(info.get("trailingPE")),
        forward_pe=_safe_float(info.get("forwardPE")),
        price_to_book=_safe_float(info.get("priceToBook")),
        enterprise_to_ebitda=_safe_float(info.get("enterpriseToEbitda")),
        profit_margins=_safe_float(info.get("profitMargins")),
        operating_margins=_safe_float(info.get("operatingMargins")),
        gross_margins=_safe_float(info.get("grossMargins")),
        revenue_growth=_safe_float(info.get("revenueGrowth")),
        earnings_growth=_safe_float(info.get("earningsGrowth")),
        total_revenue=_safe_float(info.get("totalRevenue")),
        ebitda=_safe_float(info.get("ebitda")),
        total_debt=_safe_float(info.get("totalDebt")),
        total_cash=_safe_float(info.get("totalCash")),
        debt_to_equity=_safe_float(info.get("debtToEquity")),
        free_cash_flow=_safe_float(info.get("freeCashflow")),
        dividend_yield=_safe_float(info.get("dividendYield")),
    )

    # 8. Build Technical Indicators
    technicals = compute_technical_indicators(hist_df, info)

    # 9. Build Company Profile
    profile = CompanyProfile(
        ticker=ticker,
        company_name=company_name or ticker,
        sector=info.get("sector"),
        industry=info.get("industry"),
        country=info.get("country"),
        website=info.get("website"),
        beta=_safe_float(info.get("beta")),
        business_summary=info.get("longBusinessSummary") or info.get("shortBusinessSummary"),
    )

    return StockMarketData(
        ticker=ticker,
        company_name=company_name or ticker,
        fetched_at=datetime.now(timezone.utc).isoformat(),
        profile=profile,
        price=price_summary,
        fundamentals=fundamentals,
        technicals=technicals,
        news=news_articles,
        has_full_data=(current_price is not None and fundamentals.pe_ratio is not None),
    )

