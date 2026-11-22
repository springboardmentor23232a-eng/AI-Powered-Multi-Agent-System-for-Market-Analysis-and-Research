import yfinance as yf
import math
import pandas as pd

from stocks import find_stock, search_stocks as search_static  # built-in fallback list

# App period codes -> Yahoo periods
PERIODS = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "5Y": "5y"}

# Yahoo exchange codes for US markets (India is detected by ticker suffix)
US_EXCHANGES = {"NMS": "NASDAQ", "NGM": "NASDAQ", "NCM": "NASDAQ", "NYQ": "NYSE"}

_INFO: dict[str, dict] = {}  # in-memory cache: ticker -> {name, ticker, market}


def _market_for(symbol: str, exchange: str | None) -> str | None:
    if symbol.endswith(".NS"):
        return "NSE"
    if symbol.endswith(".BO"):
        return "BSE"
    return US_EXCHANGES.get(exchange or "")


def _clean(quote: dict) -> dict | None:
    """Keeps only equities on the four supported markets."""
    if quote.get("quoteType") != "EQUITY":
        return None
    symbol = (quote.get("symbol") or "").upper()
    market = _market_for(symbol, quote.get("exchange"))
    if not symbol or not market:
        return None
    name = quote.get("shortname") or quote.get("longname") or symbol
    return {"name": name, "ticker": symbol, "market": market}


def _search_yahoo(q: str, market: str | None, limit: int):
    try:
        quotes = yf.Search(q, max_results=20, news_count=0).quotes
    except Exception:
        return None  # Yahoo unreachable or rate-limited
    results = []
    for quote in quotes:
        stock = _clean(quote)
        if not stock:
            continue
        _INFO[stock["ticker"]] = stock
        if not market or stock["market"] == market.upper():
            results.append(stock)
    return results[:limit]


def search_stocks_live(q: str, market: str | None = None, limit: int = 10):
    q = q.strip()
    if not q:
        return []
    live = _search_yahoo(q, market, limit)
    if live is None:
        return search_static(q, market, limit)  # fallback
    return live


def get_stock_info(ticker: str) -> dict | None:
    """Validates a ticker and returns its name and market (or None)."""
    ticker = ticker.strip().upper()
    if ticker in _INFO:
        return _INFO[ticker]
    info = find_stock(ticker)  # built-in list first, no network call
    if not info:
        try:
            quotes = yf.Search(ticker, max_results=10, news_count=0).quotes
        except Exception:
            return None
        for quote in quotes:
            stock = _clean(quote)
            if stock and stock["ticker"] == ticker:
                info = stock
                break
    if info:
        _INFO[ticker] = info
    return info


def get_price_history(ticker: str, period_code: str) -> list[dict]:
    """Returns one OHLCV row per trading day (per week for the 5Y period)."""
    interval = "1wk" if period_code == "5Y" else "1d"
    hist = yf.Ticker(ticker).history(period=PERIODS[period_code], interval=interval)

    # Rows with a missing price can't be drawn or sent as JSON, so drop them.
    # (Proper data validation is bullet 6, which we are skipping for now.)
    hist = hist.dropna(subset=["Open", "High", "Low", "Close"])
    if hist.empty:
        raise ValueError("No price data returned")

    rows = []
    for idx, row in hist.iterrows():
        volume = row["Volume"]
        rows.append(
            {
                "date": idx.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": 0 if math.isnan(volume) else int(volume),
            }
        )
    return rows
def resolve_ticker(raw: str, preferred_market: str | None = None) -> dict | None:
    """Accepts RELIANCE or TCS for NSE/BSE users by adding .NS / .BO."""
    raw = raw.strip().upper()
    suffix = {"NSE": ".NS", "BSE": ".BO"}.get(preferred_market or "")
    if suffix and "." not in raw:
        info = get_stock_info(raw + suffix)
        if info:
            return info
    return get_stock_info(raw)
def has_price_data(ticker: str) -> bool | None:
    """True if Yahoo returns recent prices, False if not, None if the check itself failed."""
    try:
        return not yf.Ticker(ticker).history(period="1mo").empty
    except Exception:
        return None

def get_company_profile(ticker: str) -> dict:
    """Company facts from Yahoo. Missing fields come back as None."""
    info = yf.Ticker(ticker).info or {}
    return {
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "country": info.get("country"),
        "description": info.get("longBusinessSummary"),
        "website": info.get("website"),
        "employees": info.get("fullTimeEmployees"),
        "market_cap": info.get("marketCap"),
        "currency": info.get("currency"),  # currency the stock trades in
        "financial_currency": info.get("financialCurrency"),  # currency the company reports in
    }


def _empty_statement() -> dict:
    return {"available": False, "periods": [], "rows": []}


def _statement(df) -> dict:
    """Turns a Yahoo statement table into {periods, rows}. Line items with no data at all are dropped."""
    if df is None or df.empty:
        return _empty_statement()
    df = df.dropna(how="all")
    if df.empty:
        return _empty_statement()
    periods = [str(col)[:10] for col in df.columns]  # period-end dates, newest first
    rows = []
    for item, series in df.iterrows():
        values = [None if pd.isna(v) else float(v) for v in series]
        rows.append({"item": str(item), "values": values})
    return {"available": True, "periods": periods, "rows": rows}


def _safe_statement(getter) -> dict:
    try:
        return _statement(getter())
    except Exception:
        return _empty_statement()


def get_financials(ticker: str, frequency: str) -> dict:
    """Income statement, balance sheet and cash flow, annual or quarterly."""
    t = yf.Ticker(ticker)
    quarterly = frequency == "quarterly"
    try:
        currency = t.info.get("financialCurrency")
    except Exception:
        currency = None
    return {
        "currency": currency,
        "income_statement": _safe_statement(
            lambda: t.quarterly_income_stmt if quarterly else t.income_stmt
        ),
        "balance_sheet": _safe_statement(
            lambda: t.quarterly_balance_sheet if quarterly else t.balance_sheet
        ),
        "cash_flow": _safe_statement(
            lambda: t.quarterly_cashflow if quarterly else t.cashflow
        ),
    }