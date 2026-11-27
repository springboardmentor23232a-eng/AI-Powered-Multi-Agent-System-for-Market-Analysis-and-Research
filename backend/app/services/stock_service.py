import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import yfinance as yf
import pandas as pd
import numpy as np
from fastapi import HTTPException, status

logger = logging.getLogger("uvicorn.error")

from app.schemas.stock import (
    StockSearchResult,
    StockSearchResponse,
    OHLCVCandle,
    StockSummaryStats,
    ValidationReport,
    StockOverviewResponse,
    HistoricalDataResponse,
    FinancialStatementItem,
    StatementData,
    FinancialSection,
    FinancialStatementsResponse,
)
from app.services.validation_service import (
    validate_ticker_symbol,
    validate_and_clean_market_data,
)

PREDEFINED_UNIVERSE = [
    # NSE Equities (India)
    {"ticker": "INFY.NS", "company_name": "Infosys Limited", "exchange": "NSE", "market": "NSE", "sector": "Information Technology", "country": "India", "currency": "INR"},
    {"ticker": "TCS.NS", "company_name": "Tata Consultancy Services Ltd", "exchange": "NSE", "market": "NSE", "sector": "Information Technology", "country": "India", "currency": "INR"},
    {"ticker": "WIPRO.NS", "company_name": "Wipro Limited", "exchange": "NSE", "market": "NSE", "sector": "Information Technology", "country": "India", "currency": "INR"},
    {"ticker": "HCLTECH.NS", "company_name": "HCL Technologies Limited", "exchange": "NSE", "market": "NSE", "sector": "Information Technology", "country": "India", "currency": "INR"},
    {"ticker": "RELIANCE.NS", "company_name": "Reliance Industries Limited", "exchange": "NSE", "market": "NSE", "sector": "Energy & Conglomerate", "country": "India", "currency": "INR"},
    {"ticker": "ONGC.NS", "company_name": "Oil and Natural Gas Corporation", "exchange": "NSE", "market": "NSE", "sector": "Energy & Conglomerate", "country": "India", "currency": "INR"},
    {"ticker": "BPCL.NS", "company_name": "Bharat Petroleum Corporation Ltd", "exchange": "NSE", "market": "NSE", "sector": "Energy & Conglomerate", "country": "India", "currency": "INR"},
    {"ticker": "IOC.NS", "company_name": "Indian Oil Corporation Limited", "exchange": "NSE", "market": "NSE", "sector": "Energy & Conglomerate", "country": "India", "currency": "INR"},
    {"ticker": "HDFCBANK.NS", "company_name": "HDFC Bank Limited", "exchange": "NSE", "market": "NSE", "sector": "Financial Services", "country": "India", "currency": "INR"},
    {"ticker": "ICICIBANK.NS", "company_name": "ICICI Bank Limited", "exchange": "NSE", "market": "NSE", "sector": "Financial Services", "country": "India", "currency": "INR"},
    {"ticker": "SBIN.NS", "company_name": "State Bank of India", "exchange": "NSE", "market": "NSE", "sector": "Financial Services", "country": "India", "currency": "INR"},
    {"ticker": "KOTAKBANK.NS", "company_name": "Kotak Mahindra Bank Limited", "exchange": "NSE", "market": "NSE", "sector": "Financial Services", "country": "India", "currency": "INR"},
    {"ticker": "BHARTIARTL.NS", "company_name": "Bharti Airtel Limited", "exchange": "NSE", "market": "NSE", "sector": "Telecommunications", "country": "India", "currency": "INR"},

    # BSE Equities (India)
    {"ticker": "INFY.BO", "company_name": "Infosys Limited (BSE)", "exchange": "BSE", "market": "BSE", "sector": "Information Technology", "country": "India", "currency": "INR"},
    {"ticker": "TCS.BO", "company_name": "Tata Consultancy Services (BSE)", "exchange": "BSE", "market": "BSE", "sector": "Information Technology", "country": "India", "currency": "INR"},
    {"ticker": "500209.BO", "company_name": "Infosys Ltd (BSE Script 500209)", "exchange": "BSE", "market": "BSE", "sector": "Information Technology", "country": "India", "currency": "INR"},
    {"ticker": "500325.BO", "company_name": "Reliance Industries Ltd (BSE Script 500325)", "exchange": "BSE", "market": "BSE", "sector": "Energy & Conglomerate", "country": "India", "currency": "INR"},
    {"ticker": "500180.BO", "company_name": "HDFC Bank Ltd (BSE Script 500180)", "exchange": "BSE", "market": "BSE", "sector": "Financial Services", "country": "India", "currency": "INR"},
    {"ticker": "500112.BO", "company_name": "State Bank of India (BSE Script 500112)", "exchange": "BSE", "market": "BSE", "sector": "Financial Services", "country": "India", "currency": "INR"},

    # NASDAQ Equities (United States)
    {"ticker": "AAPL", "company_name": "Apple Inc.", "exchange": "NASDAQ", "market": "NASDAQ", "sector": "Consumer Electronics", "country": "United States", "currency": "USD"},
    {"ticker": "MSFT", "company_name": "Microsoft Corporation", "exchange": "NASDAQ", "market": "NASDAQ", "sector": "Software & Cloud", "country": "United States", "currency": "USD"},
    {"ticker": "NVDA", "company_name": "NVIDIA Corporation", "exchange": "NASDAQ", "market": "NASDAQ", "sector": "Semiconductors", "country": "United States", "currency": "USD"},
    {"ticker": "AMD", "company_name": "Advanced Micro Devices, Inc.", "exchange": "NASDAQ", "market": "NASDAQ", "sector": "Semiconductors", "country": "United States", "currency": "USD"},
    {"ticker": "INTC", "company_name": "Intel Corporation", "exchange": "NASDAQ", "market": "NASDAQ", "sector": "Semiconductors", "country": "United States", "currency": "USD"},
    {"ticker": "QCOM", "company_name": "QUALCOMM Incorporated", "exchange": "NASDAQ", "market": "NASDAQ", "sector": "Semiconductors", "country": "United States", "currency": "USD"},
    {"ticker": "TSLA", "company_name": "Tesla, Inc.", "exchange": "NASDAQ", "market": "NASDAQ", "sector": "Automotive & Energy", "country": "United States", "currency": "USD"},
    {"ticker": "GOOGL", "company_name": "Alphabet Inc. (Google)", "exchange": "NASDAQ", "market": "NASDAQ", "sector": "Internet & Technology", "country": "United States", "currency": "USD"},
    {"ticker": "AMZN", "company_name": "Amazon.com, Inc.", "exchange": "NASDAQ", "market": "NASDAQ", "sector": "E-Commerce & Cloud", "country": "United States", "currency": "USD"},
    {"ticker": "META", "company_name": "Meta Platforms, Inc.", "exchange": "NASDAQ", "market": "NASDAQ", "sector": "Social Media & VR", "country": "United States", "currency": "USD"},
    {"ticker": "COST", "company_name": "Costco Wholesale Corporation", "exchange": "NASDAQ", "market": "NASDAQ", "sector": "Consumer Defensive", "country": "United States", "currency": "USD"},
    {"ticker": "PEP", "company_name": "PepsiCo, Inc.", "exchange": "NASDAQ", "market": "NASDAQ", "sector": "Consumer Defensive", "country": "United States", "currency": "USD"},

    # NYSE Equities (United States)
    {"ticker": "IBM", "company_name": "International Business Machines Corp", "exchange": "NYSE", "market": "NYSE", "sector": "Information Technology", "country": "United States", "currency": "USD"},
    {"ticker": "ORCL", "company_name": "Oracle Corporation", "exchange": "NYSE", "market": "NYSE", "sector": "Software & Cloud", "country": "United States", "currency": "USD"},
    {"ticker": "DELL", "company_name": "Dell Technologies Inc.", "exchange": "NYSE", "market": "NYSE", "sector": "Consumer Electronics", "country": "United States", "currency": "USD"},
    {"ticker": "HPQ", "company_name": "HP Inc.", "exchange": "NYSE", "market": "NYSE", "sector": "Consumer Electronics", "country": "United States", "currency": "USD"},
    {"ticker": "JPM", "company_name": "JPMorgan Chase & Co.", "exchange": "NYSE", "market": "NYSE", "sector": "Financial Services", "country": "United States", "currency": "USD"},
    {"ticker": "BAC", "company_name": "Bank of America Corporation", "exchange": "NYSE", "market": "NYSE", "sector": "Financial Services", "country": "United States", "currency": "USD"},
    {"ticker": "WFC", "company_name": "Wells Fargo & Company", "exchange": "NYSE", "market": "NYSE", "sector": "Financial Services", "country": "United States", "currency": "USD"},
    {"ticker": "DIS", "company_name": "The Walt Disney Company", "exchange": "NYSE", "market": "NYSE", "sector": "Entertainment", "country": "United States", "currency": "USD"},
    {"ticker": "KO", "company_name": "The Coca-Cola Company", "exchange": "NYSE", "market": "NYSE", "sector": "Consumer Defensive", "country": "United States", "currency": "USD"},
    {"ticker": "WMT", "company_name": "Walmart Inc.", "exchange": "NYSE", "market": "NYSE", "sector": "Consumer Defensive", "country": "United States", "currency": "USD"},
    {"ticker": "TGT", "company_name": "Target Corporation", "exchange": "NYSE", "market": "NYSE", "sector": "Consumer Defensive", "country": "United States", "currency": "USD"},
    {"ticker": "GE", "company_name": "General Electric Company", "exchange": "NYSE", "market": "NYSE", "sector": "Industrials", "country": "United States", "currency": "USD"},
]

# Explicit Curated Comparable Peers for Major Blue-Chip Equities
CURATED_PEERS: Dict[str, List[str]] = {
    # Indian IT Equities
    "INFY.NS": ["TCS.NS", "WIPRO.NS", "HCLTECH.NS"],
    "TCS.NS": ["INFY.NS", "WIPRO.NS", "HCLTECH.NS"],
    "WIPRO.NS": ["INFY.NS", "TCS.NS", "HCLTECH.NS"],
    "HCLTECH.NS": ["INFY.NS", "TCS.NS", "WIPRO.NS"],
    "INFY.BO": ["TCS.BO", "WIPRO.NS", "HCLTECH.NS"],
    "TCS.BO": ["INFY.BO", "WIPRO.NS", "HCLTECH.NS"],
    "500209.BO": ["500112.BO", "TCS.BO", "INFY.NS"],
    # Indian Energy / Conglomerate
    "RELIANCE.NS": ["ONGC.NS", "BPCL.NS", "IOC.NS"],
    "ONGC.NS": ["RELIANCE.NS", "BPCL.NS", "IOC.NS"],
    "BPCL.NS": ["RELIANCE.NS", "ONGC.NS", "IOC.NS"],
    "IOC.NS": ["RELIANCE.NS", "ONGC.NS", "BPCL.NS"],
    # Indian Banking & Financial Services
    "HDFCBANK.NS": ["ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS"],
    "ICICIBANK.NS": ["HDFCBANK.NS", "SBIN.NS", "KOTAKBANK.NS"],
    "SBIN.NS": ["HDFCBANK.NS", "ICICIBANK.NS", "KOTAKBANK.NS"],
    "KOTAKBANK.NS": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS"],
    # Indian Telecom
    "BHARTIARTL.NS": ["IDEA.NS", "TATACOMM.NS", "INDUSTOWER.NS"],
    # US Consumer Electronics / Tech Leaders
    "AAPL": ["MSFT", "GOOGL", "DELL", "HPQ"],
    "MSFT": ["AAPL", "GOOGL", "ORCL", "IBM"],
    "GOOGL": ["MSFT", "META", "AAPL", "AMZN"],
    "AMZN": ["GOOGL", "MSFT", "WMT", "COST"],
    "META": ["GOOGL", "MSFT", "SNAP", "PINS"],
    # US Semiconductors
    "NVDA": ["AMD", "INTC", "QCOM", "AVGO"],
    "AMD": ["NVDA", "INTC", "QCOM", "AVGO"],
    "INTC": ["NVDA", "AMD", "QCOM", "TXN"],
    "QCOM": ["NVDA", "AMD", "AVGO", "INTC"],
    # US Automotive / Clean Tech
    "TSLA": ["F", "GM", "RIVN", "LCID"],
    # US Enterprise Tech / IT
    "IBM": ["ORCL", "MSFT", "DELL", "HPQ"],
    "ORCL": ["MSFT", "IBM", "SAP", "CRM"],
    "DELL": ["HPQ", "AAPL", "IBM", "MSFT"],
    "HPQ": ["DELL", "AAPL", "IBM", "MSFT"],
    # US Financial Services
    "JPM": ["BAC", "WFC", "C", "GS"],
    "BAC": ["JPM", "WFC", "C", "MS"],
    "WFC": ["JPM", "BAC", "C", "USB"],
    # US Retail / Consumer Staples
    "WMT": ["TGT", "COST", "AMZN"],
    "TGT": ["WMT", "COST", "AMZN"],
    "COST": ["WMT", "TGT", "AMZN"],
    "KO": ["PEP", "MNST", "KDP"],
    "PEP": ["KO", "MNST", "KDP"],
    "DIS": ["NFLX", "WBD", "PARA"],
}


def _infer_market_from_exchange_and_symbol(symbol: str, exchange: Optional[str] = None) -> Tuple[str, str]:
    """
    Infers standardized exchange and market code from symbol and provider exchange metadata.
    """
    clean_sym = symbol.strip().upper()
    ex_upper = (exchange or "").strip().upper()

    if clean_sym.endswith(".NS") or ex_upper in {"NSE", "NSI"}:
        return "NSE", "NSE"
    if clean_sym.endswith(".BO") or ex_upper in {"BSE", "BOM", "BOMBAY"}:
        return "BSE", "BSE"
    if ex_upper in {"NYQ", "NYSE", "NEW YORK STOCK EXCHANGE"}:
        return "NYSE", "NYSE"
    if ex_upper in {"NMS", "NGM", "NCM", "NASDAQ", "NASDAQNM"}:
        return "NASDAQ", "NASDAQ"

    # Default inference
    if "." in clean_sym:
        suffix = clean_sym.split(".")[-1]
        if suffix == "NS":
            return "NSE", "NSE"
        if suffix == "BO":
            return "BSE", "BSE"
    return "NASDAQ", "NASDAQ"


def search_stocks(query: str) -> StockSearchResponse:
    clean_query = query.strip().lower()
    if not clean_query:
        return StockSearchResponse(query=query, count=0, results=[])

    matches: List[StockSearchResult] = []
    seen_tickers = set()

    # 1. Search predefined universe
    for item in PREDEFINED_UNIVERSE:
        if (clean_query in item["ticker"].lower()) or (clean_query in item["company_name"].lower()):
            matches.append(StockSearchResult(**item))
            seen_tickers.add(item["ticker"].upper())

    # 2. Use yfinance search provider if available
    try:
        if hasattr(yf, "Search"):
            search_obj = yf.Search(query.strip(), max_results=8)
            quotes = getattr(search_obj, "quotes", []) or []
            for q in quotes:
                symbol = q.get("symbol")
                if not symbol or symbol in seen_tickers:
                    continue
                # Skip futures, options, warrants, currency pairs containing '='
                if "=" in symbol or "^" in symbol:
                    continue

                quote_type = q.get("quoteType", "").upper()
                if quote_type and quote_type not in {"EQUITY", "ETF", "MUTUALFUND"}:
                    continue

                company_name = q.get("shortname") or q.get("longname") or symbol
                exchange_disp = q.get("exchDisp") or q.get("exchange") or "Unknown"
                exch, mkt = _infer_market_from_exchange_and_symbol(symbol, exchange_disp)

                matches.append(
                    StockSearchResult(
                        ticker=symbol,
                        company_name=company_name,
                        exchange=exch,
                        market=mkt,
                        sector=q.get("sector") or q.get("sectorDisp"),
                        industry=q.get("industry") or q.get("industryDisp"),
                        country=q.get("country"),
                    )
                )
                seen_tickers.add(symbol.upper())
    except Exception as exc:
        logger.warning(f"Provider search notice for '{query}': {exc}")

    # 3. Direct ticker fallback if still empty
    if not matches and " " not in query.strip():
        upper_query = query.strip().upper()
        try:
            t = yf.Ticker(upper_query)
            info = getattr(t, "info", None) or {}
            short_name = info.get("shortName") or info.get("longName")
            if short_name:
                exch, mkt = _infer_market_from_exchange_and_symbol(upper_query, info.get("exchange"))
                matches.append(
                    StockSearchResult(
                        ticker=upper_query,
                        company_name=short_name,
                        exchange=exch,
                        market=mkt,
                        sector=info.get("sector"),
                        industry=info.get("industry"),
                        country=info.get("country"),
                        currency=info.get("currency"),
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
    raw_trailing_pe = info.get("trailingPE")
    raw_forward_pe = info.get("forwardPE")
    raw_price_to_book = info.get("priceToBook")
    raw_book_value = info.get("bookValue")
    raw_forward_eps = info.get("forwardEps")
    raw_trailing_eps = info.get("trailingEps")

    trailing_pe = round(float(raw_trailing_pe), 2) if raw_trailing_pe is not None else None
    forward_pe = round(float(raw_forward_pe), 2) if raw_forward_pe is not None else None
    price_to_book = round(float(raw_price_to_book), 2) if raw_price_to_book is not None else None
    book_value = round(float(raw_book_value), 2) if raw_book_value is not None else None
    forward_eps = round(float(raw_forward_eps), 2) if raw_forward_eps is not None else None
    trailing_eps = round(float(raw_trailing_eps), 2) if raw_trailing_eps is not None else None
    pe_ratio = trailing_pe or forward_pe

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
        financial_currency=info.get("financialCurrency") or info.get("currency", "USD"),
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
        trailing_pe=trailing_pe,
        forward_pe=forward_pe,
        price_to_book=price_to_book,
        book_value=book_value,
        forward_eps=forward_eps,
        trailing_eps=trailing_eps,
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


def _dataframe_to_statement_data(statement_type: str, df: Optional[pd.DataFrame]) -> StatementData:
    """
    Transforms yfinance financial statement DataFrame into structured JSON-safe StatementData.
    """
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return StatementData(
            statement_type=statement_type,
            periods=[],
            items=[],
            raw_available=False,
        )

    try:
        periods: List[str] = []
        col_map = {}
        for col in df.columns:
            if isinstance(col, (pd.Timestamp, datetime)):
                date_str = col.strftime("%Y-%m-%d")
            else:
                date_str = str(col).split(" ")[0]
            periods.append(date_str)
            col_map[col] = date_str

        items: List[FinancialStatementItem] = []
        for metric_name, row in df.iterrows():
            clean_metric = str(metric_name).strip()
            values: Dict[str, Optional[float]] = {}
            for col in df.columns:
                val = row[col]
                period_str = col_map[col]
                if pd.isna(val) or val is None:
                    values[period_str] = None
                else:
                    try:
                        float_val = float(val)
                        if np.isnan(float_val) or np.isinf(float_val):
                            values[period_str] = None
                        else:
                            values[period_str] = round(float_val, 2)
                    except (ValueError, TypeError):
                        values[period_str] = None

            items.append(
                FinancialStatementItem(
                    line_item=clean_metric,
                    metric=clean_metric,
                    values=values,
                )
            )

        return StatementData(
            statement_type=statement_type,
            periods=periods,
            line_items=items,
            items=items,
            available=True,
            raw_available=True,
        )
    except Exception as exc:
        logger.warning(f"Error parsing financial statement dataframe for {statement_type}: {exc}")
        return StatementData(
            statement_type=statement_type,
            periods=[],
            line_items=[],
            items=[],
            available=False,
            raw_available=False,
        )


def get_financial_statements(ticker: str) -> FinancialStatementsResponse:
    """
    Fetches Annual and Quarterly Income Statement, Balance Sheet, and Cash Flow statement from yfinance.
    """
    clean_ticker = validate_ticker_symbol(ticker)

    try:
        t = yf.Ticker(clean_ticker)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Market data provider error for '{clean_ticker}': {str(exc)}"
        )

    # 1. Income Statements (Annual & Quarterly)
    income_annual_df = None
    income_quarterly_df = None
    try:
        income_annual_df = getattr(t, "income_stmt", None)
        if income_annual_df is None or income_annual_df.empty:
            income_annual_df = getattr(t, "financials", None)
    except Exception as exc:
        logger.warning(f"Failed to fetch annual income statement for {clean_ticker}: {exc}")

    try:
        income_quarterly_df = getattr(t, "quarterly_income_stmt", None)
        if income_quarterly_df is None or income_quarterly_df.empty:
            income_quarterly_df = getattr(t, "quarterly_financials", None)
    except Exception as exc:
        logger.warning(f"Failed to fetch quarterly income statement for {clean_ticker}: {exc}")

    # 2. Balance Sheet (Annual & Quarterly)
    balance_annual_df = None
    balance_quarterly_df = None
    try:
        balance_annual_df = getattr(t, "balance_sheet", None)
    except Exception as exc:
        logger.warning(f"Failed to fetch annual balance sheet for {clean_ticker}: {exc}")

    try:
        balance_quarterly_df = getattr(t, "quarterly_balance_sheet", None)
    except Exception as exc:
        logger.warning(f"Failed to fetch quarterly balance sheet for {clean_ticker}: {exc}")

    # 3. Cash Flow (Annual & Quarterly)
    cashflow_annual_df = None
    cashflow_quarterly_df = None
    try:
        cashflow_annual_df = getattr(t, "cashflow", None)
    except Exception as exc:
        logger.warning(f"Failed to fetch annual cash flow for {clean_ticker}: {exc}")

    try:
        cashflow_quarterly_df = getattr(t, "quarterly_cashflow", None)
    except Exception as exc:
        logger.warning(f"Failed to fetch quarterly cash flow for {clean_ticker}: {exc}")

    # Company name and currency
    currency = "USD"
    financial_currency = "USD"
    company_name = clean_ticker
    try:
        info = getattr(t, "info", None) or {}
        currency = info.get("currency", "USD")
        financial_currency = info.get("financialCurrency") or currency
        company_name = info.get("longName") or info.get("shortName") or clean_ticker
    except Exception:
        pass

    income_stmt = FinancialSection(
        annual=_dataframe_to_statement_data("income_statement_annual", income_annual_df),
        quarterly=_dataframe_to_statement_data("income_statement_quarterly", income_quarterly_df),
    )

    balance_sheet = FinancialSection(
        annual=_dataframe_to_statement_data("balance_sheet_annual", balance_annual_df),
        quarterly=_dataframe_to_statement_data("balance_sheet_quarterly", balance_quarterly_df),
    )

    cash_flow = FinancialSection(
        annual=_dataframe_to_statement_data("cash_flow_annual", cashflow_annual_df),
        quarterly=_dataframe_to_statement_data("cash_flow_quarterly", cashflow_quarterly_df),
    )

    return FinancialStatementsResponse(
        ticker=clean_ticker,
        company_name=company_name,
        currency=currency,
        financial_currency=financial_currency,
        data_source="yfinance",
        retrieved_at=datetime.utcnow().isoformat() + "Z",
        income_statement=income_stmt,
        balance_sheet=balance_sheet,
        cash_flow_statement=cash_flow,
        cash_flow=cash_flow,
    )
