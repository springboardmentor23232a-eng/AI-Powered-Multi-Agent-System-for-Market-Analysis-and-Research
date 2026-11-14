import yfinance as yf

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
    interval = "1wk" if period_code == "5Y" else "1d"  # keeps 5Y small
    hist = yf.Ticker(ticker).history(period=PERIODS[period_code], interval=interval)
    if hist.empty:
        raise ValueError("No price data returned")
    return [
        {"date": idx.strftime("%Y-%m-%d"), "close": round(float(row["Close"]), 2)}
        for idx, row in hist.iterrows()
    ]
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