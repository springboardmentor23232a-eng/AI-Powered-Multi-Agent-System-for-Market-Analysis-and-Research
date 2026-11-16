from datetime import datetime
from typing import List
import yfinance as yf
import pandas as pd
from fastapi import HTTPException, status

from app.schemas.stock import (
    StockSearchResult,
    StockSearchResponse,
    OHLCVCandle,
    StockSummaryStats,
    ValidationReport,
    StockOverviewResponse,
    HistoricalDataResponse,
)
from app.services.validation_service import (
    validate_ticker_symbol,
    validate_and_clean_market_data,
)

PREDEFINED_UNIVERSE = [
    {"ticker": "INFY.NS", "company_name": "Infosys Limited", "exchange": "NSE", "sector": "Information Technology", "country": "India"},
    {"ticker": "TCS.NS", "company_name": "Tata Consultancy Services Ltd", "exchange": "NSE", "sector": "Information Technology", "country": "India"},
    {"ticker": "RELIANCE.NS", "company_name": "Reliance Industries Limited", "exchange": "NSE", "sector": "Energy & Conglomerate", "country": "India"},
    {"ticker": "HDFCBANK.NS", "company_name": "HDFC Bank Limited", "exchange": "NSE", "sector": "Financial Services", "country": "India"},
    {"ticker": "AAPL", "company_name": "Apple Inc.", "exchange": "NASDAQ", "sector": "Consumer Electronics", "country": "United States"},
    {"ticker": "MSFT", "company_name": "Microsoft Corporation", "exchange": "NASDAQ", "sector": "Software & Cloud", "country": "United States"},
    {"ticker": "NVDA", "company_name": "NVIDIA Corporation", "exchange": "NASDAQ", "sector": "Semiconductors", "country": "United States"},
    {"ticker": "TSLA", "company_name": "Tesla, Inc.", "exchange": "NASDAQ", "sector": "Automotive & Energy", "country": "United States"},
]


def search_stocks(query: str) -> StockSearchResponse:
    clean_query = query.strip().lower()
    if not clean_query:
        return StockSearchResponse(query=query, count=0, results=[])

    matches: List[StockSearchResult] = []
    for item in PREDEFINED_UNIVERSE:
        if (clean_query in item["ticker"].lower()) or (clean_query in item["company_name"].lower()):
            matches.append(StockSearchResult(**item))

    if not matches:
        upper_query = query.strip().upper()
        try:
            t = yf.Ticker(upper_query)
            info = t.info or {}
            short_name = info.get("shortName") or info.get("longName")
            if short_name:
                matches.append(
                    StockSearchResult(
                        ticker=upper_query,
                        company_name=short_name,
                        exchange=info.get("exchange", "Unknown"),
                        sector=info.get("sector"),
                        country=info.get("country"),
                    )
                )
        except Exception:
            pass

    return StockSearchResponse(query=query, count=len(matches), results=matches)


def get_company_overview(ticker: str) -> StockOverviewResponse:
    clean_ticker = validate_ticker_symbol(ticker)

    try:
        t = yf.Ticker(clean_ticker)
        info = t.info or {}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch market data for '{clean_ticker}': {str(exc)}"
        )

    company_name = info.get("longName") or info.get("shortName")
    current_price = info.get("currentPrice") or info.get("regularMarketPrice")
    prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose")

    # Fast info fallback if standard info is incomplete
    if not current_price:
        try:
            fast = t.fast_info
            current_price = getattr(fast, "last_price", None)
            prev_close = getattr(fast, "previous_close", None)
        except Exception:
            pass

    if not current_price and not company_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock ticker '{clean_ticker}' could not be located."
        )

    day_high = info.get("dayHigh") or info.get("regularMarketDayHigh")
    day_low = info.get("dayLow") or info.get("regularMarketDayLow")
    fifty_two_high = info.get("fiftyTwoWeekHigh")
    fifty_two_low = info.get("fiftyTwoWeekLow")
    pe_ratio = info.get("trailingPE") or info.get("forwardPE")
    volume = info.get("regularMarketVolume") or info.get("volume")
    avg_volume = info.get("averageVolume")
    div_yield = info.get("dividendYield")
    if div_yield:
        div_yield = round(div_yield * 100, 2)

    return StockOverviewResponse(
        ticker=clean_ticker,
        company_name=company_name or clean_ticker,
        exchange=info.get("exchange", "Unknown"),
        currency=info.get("currency", "USD"),
        sector=info.get("sector"),
        industry=info.get("industry"),
        current_price=round(float(current_price), 2) if current_price else None,
        previous_close=round(float(prev_close), 2) if prev_close else None,
        day_high=round(float(day_high), 2) if day_high else None,
        day_low=round(float(day_low), 2) if day_low else None,
        fifty_two_week_high=round(float(fifty_two_high), 2) if fifty_two_high else None,
        fifty_two_week_low=round(float(fifty_two_low), 2) if fifty_two_low else None,
        market_cap=int(info.get("marketCap")) if info.get("marketCap") else None,
        pe_ratio=round(float(pe_ratio), 2) if pe_ratio else None,
        volume=int(volume) if volume else None,
        average_volume=int(avg_volume) if avg_volume else None,
        dividend_yield=div_yield,
        business_summary=info.get("longBusinessSummary"),
        data_source="yfinance",
        retrieved_at=datetime.utcnow().isoformat() + "Z",
    )


def get_historical_ohlcv(ticker: str, period: str = "1mo") -> HistoricalDataResponse:
    clean_ticker = validate_ticker_symbol(ticker)
    
    valid_periods = ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"]
    if period not in valid_periods:
        period = "1mo"

    try:
        t = yf.Ticker(clean_ticker)
        raw_df = t.history(period=period, interval="1d")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Market data provider error for '{clean_ticker}': {str(exc)}"
        )

    clean_df, telemetry = validate_and_clean_market_data(raw_df, clean_ticker)

    candles: List[OHLCVCandle] = []
    for idx, row in clean_df.iterrows():
        date_str = idx.strftime("%Y-%m-%d") if isinstance(idx, pd.Timestamp) else str(idx).split(" ")[0]
        candles.append(
            OHLCVCandle(
                date=date_str,
                open=round(float(row["Open"]), 2),
                high=round(float(row["High"]), 2),
                low=round(float(row["Low"]), 2),
                close=round(float(row["Close"]), 2),
                volume=int(row["Volume"]),
            )
        )

    first_close = clean_df["Close"].iloc[0]
    last_close = clean_df["Close"].iloc[-1]
    pct_change = round(((last_close - first_close) / first_close) * 100, 2)

    summary_stats = StockSummaryStats(
        start_date=candles[0].date,
        end_date=candles[-1].date,
        highest_price=round(float(clean_df["High"].max()), 2),
        lowest_price=round(float(clean_df["Low"].min()), 2),
        average_volume=round(float(clean_df["Volume"].mean()), 2),
        total_trading_days=len(candles),
        period_change_pct=pct_change,
    )

    return HistoricalDataResponse(
        ticker=clean_ticker,
        period=period,
        interval="1d",
        count=len(candles),
        data_source="yfinance",
        retrieved_at=datetime.utcnow().isoformat() + "Z",
        stats=summary_stats,
        validation=ValidationReport(**telemetry),
        candles=candles,
    )

