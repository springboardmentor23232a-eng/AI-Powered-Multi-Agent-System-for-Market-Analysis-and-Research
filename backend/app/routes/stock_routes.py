from datetime import datetime
import yfinance as yf
from fastapi import APIRouter, Query, HTTPException, status
from typing import List, Optional
from app.schemas import (
    StockSearchResponse,
    StockSearchResult,
    HistoricalDataResponse,
    CompanyProfileResponse,
    FinancialStatementsResponse,
    OHLCVRecord
)
from app.utils.time_series_analysis import compute_time_series_analysis

router = APIRouter(prefix="/api/stocks", tags=["Stock Search"])

# Curated reference cache of verified tickers across NSE, BSE, NASDAQ, NYSE
VERIFIED_TICKERS = [
    {
        "ticker": "TCS.NS",
        "name": "Tata Consultancy Services Limited",
        "market": "NSE",
        "exchange": "NSE (India)",
        "currency": "INR",
        "currency_symbol": "₹",
        "is_us_market": False,
    },
    {
        "ticker": "INFY.NS",
        "name": "Infosys Limited",
        "market": "NSE",
        "exchange": "NSE (India)",
        "currency": "INR",
        "currency_symbol": "₹",
        "is_us_market": False,
    },
    {
        "ticker": "RELIANCE.NS",
        "name": "Reliance Industries Limited",
        "market": "NSE",
        "exchange": "NSE (India)",
        "currency": "INR",
        "currency_symbol": "₹",
        "is_us_market": False,
    },
    {
        "ticker": "HDFCBANK.NS",
        "name": "HDFC Bank Limited",
        "market": "NSE",
        "exchange": "NSE (India)",
        "currency": "INR",
        "currency_symbol": "₹",
        "is_us_market": False,
    },
    {
        "ticker": "AAPL",
        "name": "Apple Inc.",
        "market": "NASDAQ",
        "exchange": "NASDAQ (US)",
        "currency": "USD",
        "currency_symbol": "$",
        "is_us_market": True,
    },
    {
        "ticker": "MSFT",
        "name": "Microsoft Corporation",
        "market": "NASDAQ",
        "exchange": "NASDAQ (US)",
        "currency": "USD",
        "currency_symbol": "$",
        "is_us_market": True,
    },
    {
        "ticker": "TSLA",
        "name": "Tesla, Inc.",
        "market": "NASDAQ",
        "exchange": "NASDAQ (US)",
        "currency": "USD",
        "currency_symbol": "$",
        "is_us_market": True,
    },
    {
        "ticker": "NVDA",
        "name": "NVIDIA Corporation",
        "market": "NASDAQ",
        "exchange": "NASDAQ (US)",
        "currency": "USD",
        "currency_symbol": "$",
        "is_us_market": True,
    },
    {
        "ticker": "GOOGL",
        "name": "Alphabet Inc.",
        "market": "NASDAQ",
        "exchange": "NASDAQ (US)",
        "currency": "USD",
        "currency_symbol": "$",
        "is_us_market": True,
    },
    {
        "ticker": "AMZN",
        "name": "Amazon.com Inc.",
        "market": "NASDAQ",
        "exchange": "NASDAQ (US)",
        "currency": "USD",
        "currency_symbol": "$",
        "is_us_market": True,
    },
]


def resolve_market_and_currency(ticker_symbol: str, raw_exchange: str = ""):
    """Classifies exchange, currency, and US market status for yfinance tickers."""
    sym = ticker_symbol.upper()
    ex = raw_exchange.upper()

    if sym.endswith(".NS") or "NSI" in ex or "NSE" in ex:
        return "NSE", "NSE (India)", "INR", "₹", False
    elif sym.endswith(".BO") or "BSE" in ex:
        return "BSE", "BSE (India)", "INR", "₹", False
    elif "NYQ" in ex or "NYSE" in ex:
        return "NYSE", "NYSE (US)", "USD", "$", True
    elif "NMS" in ex or "NGM" in ex or "NCM" in ex or "NASDAQ" in ex:
        return "NASDAQ", "NASDAQ (US)", "USD", "$", True
    else:
        # Default fallback: if single token ticker without dot, assume US Market
        if "." not in sym:
            return "NASDAQ", "US Exchange", "USD", "$", True
        return "Global", "International", "USD", "$", True


@router.get("/search", response_model=StockSearchResponse)
def search_stocks(q: str = Query(..., min_length=1, max_length=50, description="Company name or ticker")):
    """
    Searches stocks powered by yfinance live dataset.
    Validates company symbols, retrieves real-time pricing, currency, and flags US market equities.
    """
    search_term = q.strip().upper()
    if not search_term:
        return StockSearchResponse(query=q, count=0, results=[])

    matched_results: List[StockSearchResult] = []
    seen_tickers = set()

    # 1. Fast lookup from verified reference list
    for item in VERIFIED_TICKERS:
        t_clean = item["ticker"].split(".")[0]
        if (search_term in item["ticker"]) or (search_term in t_clean) or (search_term in item["name"].upper()):
            try:
                # Fetch fast real-time price from yfinance
                yf_ticker = yf.Ticker(item["ticker"])
                fast_price = yf_ticker.fast_info.get("lastPrice")
                prev_close = yf_ticker.fast_info.get("previousClose")
                change_pct = None
                if fast_price and prev_close:
                    change_pct = round(((fast_price - prev_close) / prev_close) * 100, 2)
            except Exception:
                fast_price = None
                change_pct = None

            res = StockSearchResult(
                ticker=item["ticker"],
                name=item["name"],
                market=item["market"],
                exchange=item["exchange"],
                currency=item["currency"],
                currency_symbol=item["currency_symbol"],
                current_price=round(fast_price, 2) if fast_price else None,
                change_percent=change_pct,
                is_us_market=item["is_us_market"],
            )
            matched_results.append(res)
            seen_tickers.add(item["ticker"])

    # 2. Dynamic live search via yfinance API
    try:
        yf_search = yf.Search(q.strip(), max_results=6)
        if hasattr(yf_search, "quotes") and yf_search.quotes:
            for quote in yf_search.quotes:
                sym = quote.get("symbol")
                if not sym or sym in seen_tickers:
                    continue

                quote_type = quote.get("quoteType", "")
                if quote_type not in ["EQUITY", "ETF", ""]:
                    continue

                short_name = quote.get("shortname") or quote.get("longname") or f"{sym} Equity"
                raw_ex = quote.get("exchange", "")
                market, exchange, currency, curr_sym, is_us = resolve_market_and_currency(sym, raw_ex)

                # Fetch real-time price
                try:
                    t_obj = yf.Ticker(sym)
                    price = t_obj.fast_info.get("lastPrice")
                    p_close = t_obj.fast_info.get("previousClose")
                    chg = None
                    if price and p_close:
                        chg = round(((price - p_close) / p_close) * 100, 2)
                except Exception:
                    price = None
                    chg = None

                matched_results.append(StockSearchResult(
                    ticker=sym,
                    name=short_name,
                    market=market,
                    exchange=exchange,
                    currency=currency,
                    currency_symbol=curr_sym,
                    current_price=round(price, 2) if price else None,
                    change_percent=chg,
                    is_us_market=is_us,
                ))
                seen_tickers.add(sym)
    except Exception as e:
        # Graceful fallback if external search encounters network or rate limits
        pass

    # 3. Direct ticker fallback: if user typed a specific ticker like 'AAPL' or 'TCS'
    if not matched_results and len(search_term) <= 10:
        for candidate_ticker in [search_term, f"{search_term}.NS"]:
            try:
                candidate = yf.Ticker(candidate_ticker)
                fast_p = candidate.fast_info.get("lastPrice")
                if fast_p:
                    short_n = candidate.info.get("shortName") or f"{candidate_ticker} Equity"
                    market, exchange, currency, curr_sym, is_us = resolve_market_and_currency(candidate_ticker)
                    matched_results.append(StockSearchResult(
                        ticker=candidate_ticker,
                        name=short_n,
                        market=market,
                        exchange=exchange,
                        currency=currency,
                        currency_symbol=curr_sym,
                        current_price=round(fast_p, 2),
                        change_percent=None,
                        is_us_market=is_us,
                    ))
                    break
            except Exception:
                continue

    return StockSearchResponse(
        query=q,
        count=len(matched_results),
        results=matched_results
    )


# ============================================================================
# MODULE 2 ENDPOINTS: Historical OHLCV, TSA, Profile & Financials
# ============================================================================

def normalize_period(period_str: str) -> str:
    cleaned = (period_str or "1y").strip().lower()
    mapping = {
        "1 month": "1mo",
        "1month": "1mo",
        "1m": "1mo",
        "1mo": "1mo",
        "3 months": "3mo",
        "3months": "3mo",
        "3m": "3mo",
        "3mo": "3mo",
        "6 months": "6mo",
        "6months": "6mo",
        "6m": "6mo",
        "6mo": "6mo",
        "1 year": "1y",
        "1year": "1y",
        "1y": "1y",
        "5 years": "5y",
        "5years": "5y",
        "5y": "5y",
    }
    return mapping.get(cleaned, "1y")


def format_market_cap(val: Optional[float], currency: str) -> Optional[str]:
    if not val or val <= 0:
        return None
    if currency == "INR":
        if val >= 1e7:
            return f"₹{val / 1e7:,.2f} Cr"
        elif val >= 1e5:
            return f"₹{val / 1e5:,.2f} Lakh"
        return f"₹{val:,.2f}"
    else:
        if val >= 1e12:
            return f"${val / 1e12:,.2f} T"
        elif val >= 1e9:
            return f"${val / 1e9:,.2f} B"
        elif val >= 1e6:
            return f"${val / 1e6:,.2f} M"
        return f"${val:,.2f}"


@router.get("/{ticker}/historical", response_model=HistoricalDataResponse)
def get_historical_stock_prices(
    ticker: str,
    period: str = Query("1y", description="Time window: 1mo, 3mo, 6mo, 1y, 5y"),
    interval: str = Query("1d", description="Bar interval: 1d, 1wk")
):
    """
    Module 2 Core Feature:
    - Retrieves historical stock prices and OHLCV data from yfinance.
    - Performs Time Series Analysis (SMA 20, SMA 50, Volatility, Bullish/Bearish Trend).
    - Computes price return distribution histogram.
    - Records provenance: Data Source yfinance API and timestamp with HH:mm:ss.
    """
    sym = ticker.strip().upper()
    norm_period = normalize_period(period)
    retrieval_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    t_obj = yf.Ticker(sym)
    try:
        hist = t_obj.history(period=norm_period, interval=interval)
    except Exception:
        hist = None

    # Fallback for Indian tickers without .NS
    if (hist is None or hist.empty) and "." not in sym:
        candidate_sym = f"{sym}.NS"
        candidate_t = yf.Ticker(candidate_sym)
        try:
            candidate_hist = candidate_t.history(period=norm_period, interval=interval)
            if not candidate_hist.empty:
                sym = candidate_sym
                t_obj = candidate_t
                hist = candidate_hist
        except Exception:
            pass

    if hist is None or hist.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No historical price data could be retrieved for ticker '{ticker}' across period '{period}'."
        )

    # 1. Format and align historical DataFrame
    cleaned_df = hist.copy()

    # 2. Time Series Analysis & Histogram Generation
    tsa_report = compute_time_series_analysis(cleaned_df)

    # 3. Extract Metadata
    try:
        raw_name = t_obj.info.get("shortName") or t_obj.info.get("longName") or f"{sym} Equity"
        raw_ex = t_obj.info.get("exchange", "")
    except Exception:
        raw_name = f"{sym} Equity"
        raw_ex = ""

    market, exchange, currency, curr_sym, is_us = resolve_market_and_currency(sym, raw_ex)

    # 4. Format OHLCV records (sorted reverse chronological for table)
    ohlcv_records: List[OHLCVRecord] = []
    reversed_df = cleaned_df.iloc[::-1]
    for idx, row in reversed_df.iterrows():
        d_str = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
        o_val = round(float(row.get("Open", 0)), 2)
        h_val = round(float(row.get("High", 0)), 2)
        l_val = round(float(row.get("Low", 0)), 2)
        c_val = round(float(row.get("Close", 0)), 2)
        v_val = int(row.get("Volume", 0))

        # Daily change % compared to previous day
        chg_pct = None
        if "Close" in cleaned_df.columns:
            pos = cleaned_df.index.get_loc(idx)
            if pos > 0:
                p_val = float(cleaned_df["Close"].iloc[pos - 1])
                if p_val > 0:
                    chg_pct = round(((c_val - p_val) / p_val) * 100.0, 2)

        ohlcv_records.append(OHLCVRecord(
            date=d_str,
            open=o_val,
            high=h_val,
            low=l_val,
            close=c_val,
            volume=v_val,
            change_percent=chg_pct
        ))

    return HistoricalDataResponse(
        ticker=sym,
        company_name=raw_name,
        market=market,
        exchange=exchange,
        currency=currency,
        currency_symbol=curr_sym,
        is_us_market=is_us,
        period=period,
        interval=interval,
        data_source="yfinance API",
        retrieved_at=f"{retrieval_time} IST",
        time_series_analysis=tsa_report,
        ohlcv=ohlcv_records
    )


@router.get("/{ticker}/profile", response_model=CompanyProfileResponse)
def get_company_profile(ticker: str):
    """
    Module 2 Core Feature:
    - Retrieves available company profile, sector, industry, description,
      valuation metrics (Market Cap, P/E, 52-week High/Low, Beta), and executives.
    - Records provenance: Data Source yfinance API and timestamp with HH:mm:ss.
    """
    sym = ticker.strip().upper()
    retrieval_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    t_obj = yf.Ticker(sym)
    try:
        info = t_obj.info or {}
    except Exception:
        info = {}

    # Fallback for Indian tickers without .NS
    if not info and "." not in sym:
        candidate_sym = f"{sym}.NS"
        candidate_t = yf.Ticker(candidate_sym)
        try:
            candidate_info = candidate_t.info or {}
            if candidate_info:
                sym = candidate_sym
                t_obj = candidate_t
                info = candidate_info
        except Exception:
            pass

    raw_name = info.get("shortName") or info.get("longName") or f"{sym} Equity"
    raw_ex = info.get("exchange", "")
    market, exchange, currency, curr_sym, is_us = resolve_market_and_currency(sym, raw_ex)

    # Parse executives
    executives = []
    raw_officers = info.get("companyOfficers", []) or []
    for officer in raw_officers[:5]:
        executives.append({
            "name": officer.get("name", "N/A"),
            "title": officer.get("title", "Executive"),
            "age": officer.get("age", None)
        })

    m_cap = info.get("marketCap")
    formatted_m_cap = format_market_cap(m_cap, currency)

    div_yield = info.get("dividendYield")
    if div_yield is not None:
        div_yield = round(float(div_yield) * 100, 2)

    return CompanyProfileResponse(
        ticker=sym,
        company_name=raw_name,
        market=market,
        exchange=exchange,
        currency=currency,
        currency_symbol=curr_sym,
        is_us_market=is_us,
        sector=info.get("sector") or "General Industry",
        industry=info.get("industry") or "Financial & Commercial Markets",
        country=info.get("country") or ("India" if not is_us else "United States"),
        website=info.get("website"),
        summary=info.get("longBusinessSummary") or info.get("description") or f"{raw_name} is a publicly traded enterprise on the {exchange}.",
        market_cap=m_cap,
        market_cap_formatted=formatted_m_cap,
        trailing_pe=round(float(info["trailingPE"]), 2) if info.get("trailingPE") else None,
        forward_pe=round(float(info["forwardPE"]), 2) if info.get("forwardPE") else None,
        beta=round(float(info["beta"]), 2) if info.get("beta") else None,
        fifty_two_week_high=round(float(info["fiftyTwoWeekHigh"]), 2) if info.get("fiftyTwoWeekHigh") else None,
        fifty_two_week_low=round(float(info["fiftyTwoWeekLow"]), 2) if info.get("fiftyTwoWeekLow") else None,
        dividend_yield=div_yield,
        executives=executives,
        data_source="yfinance API",
        retrieved_at=f"{retrieval_time} IST"
    )


@router.get("/{ticker}/financials", response_model=FinancialStatementsResponse)
def get_company_financial_statements(ticker: str):
    """
    Module 2 Core Feature:
    - Retrieves available financial statements: Income Statement, Balance Sheet, and Cash Flow.
    - Records provenance: Data Source yfinance API and timestamp with HH:mm:ss.
    """
    sym = ticker.strip().upper()
    retrieval_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    t_obj = yf.Ticker(sym)
    try:
        info = t_obj.info or {}
    except Exception:
        info = {}

    if not info and "." not in sym:
        candidate_sym = f"{sym}.NS"
        candidate_t = yf.Ticker(candidate_sym)
        try:
            candidate_info = candidate_t.info or {}
            if candidate_info:
                sym = candidate_sym
                t_obj = candidate_t
                info = candidate_info
        except Exception:
            pass

    raw_name = info.get("shortName") or info.get("longName") or f"{sym} Equity"
    raw_ex = info.get("exchange", "")
    _, _, currency, curr_sym, _ = resolve_market_and_currency(sym, raw_ex)

    def dataframe_to_records(df):
        records = []
        if df is not None and not df.empty:
            for metric_name, row in df.iterrows():
                row_data = {"metric": str(metric_name)}
                for col_date, val in row.items():
                    date_key = col_date.strftime("%Y-%m-%d") if hasattr(col_date, "strftime") else str(col_date)[:10]
                    try:
                        row_data[date_key] = float(val) if val is not None and not (isinstance(val, float) and (val != val)) else None
                    except Exception:
                        row_data[date_key] = None
                records.append(row_data)
        return records

    # 1. Income Statement
    income_records = []
    try:
        inc_df = t_obj.financials
        income_records = dataframe_to_records(inc_df)
    except Exception:
        pass

    # 2. Balance Sheet
    balance_records = []
    try:
        bs_df = t_obj.balance_sheet
        balance_records = dataframe_to_records(bs_df)
    except Exception:
        pass

    # 3. Cash Flow Statement
    cash_records = []
    try:
        cf_df = t_obj.cashflow
        cash_records = dataframe_to_records(cf_df)
    except Exception:
        pass

    # If DataFrames are empty, build a clean fallback summary from info ratios
    if not income_records:
        income_records = [
            {"metric": "Total Revenue", "Latest": info.get("totalRevenue")},
            {"metric": "Gross Profit", "Latest": info.get("grossProfits")},
            {"metric": "Operating Income", "Latest": info.get("operatingIncome")},
            {"metric": "Net Income to Common", "Latest": info.get("netIncomeToCommon")},
            {"metric": "EBITDA", "Latest": info.get("ebitda")},
        ]

    if not balance_records:
        balance_records = [
            {"metric": "Total Cash & Equivalents", "Latest": info.get("totalCash")},
            {"metric": "Total Debt", "Latest": info.get("totalDebt")},
            {"metric": "Current Ratio", "Latest": info.get("currentRatio")},
            {"metric": "Debt to Equity Ratio", "Latest": info.get("debtToEquity")},
            {"metric": "Book Value", "Latest": info.get("bookValue")},
        ]

    if not cash_records:
        cash_records = [
            {"metric": "Operating Cash Flow", "Latest": info.get("operatingCashflow")},
            {"metric": "Free Cash Flow", "Latest": info.get("freeCashflow")},
        ]

    return FinancialStatementsResponse(
        ticker=sym,
        company_name=raw_name,
        currency=currency,
        currency_symbol=curr_sym,
        income_statement=income_records[:10],
        balance_sheet=balance_records[:10],
        cash_flow=cash_records[:10],
        data_source="yfinance API",
        retrieved_at=f"{retrieval_time} IST"
    )

