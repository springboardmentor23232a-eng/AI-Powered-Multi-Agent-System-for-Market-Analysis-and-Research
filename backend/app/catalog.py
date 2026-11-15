"""Validated ticker list + per-market rules (market, ticker format, supported periods).

Swap `CATALOG` for a live market-data search API later; the rest of the code only uses the functions below.
Yahoo Finance symbol format: NSE -> RELIANCE.NS, BSE -> RELIANCE.BO, NASDAQ/NYSE -> plain (AAPL).
"""
import re
from dataclasses import dataclass

MARKET_INFO = {
    "NSE": {"name": "National Stock Exchange of India", "example": "RELIANCE, TCS", "suffix": ".NS", "currency": "INR",
            "pattern": r"^[A-Z0-9&\-]{1,20}$"},
    "BSE": {"name": "BSE Ltd., India", "example": "RELIANCE, TCS", "suffix": ".BO", "currency": "INR",
            "pattern": r"^[A-Z0-9&\-]{1,20}$"},
    "NASDAQ": {"name": "NASDAQ (US)", "example": "AAPL, MSFT", "suffix": "", "currency": "USD",
               "pattern": r"^[A-Z]{1,5}$"},
    "NYSE": {"name": "New York Stock Exchange", "example": "JPM, KO", "suffix": "", "currency": "USD",
             "pattern": r"^[A-Z]{1,5}(\.[A-Z])?$"},
}

PERIOD_INFO = {
    "1M": {"label": "1 Month", "yahoo_range": "1mo", "days": 30},
    "3M": {"label": "3 Months", "yahoo_range": "3mo", "days": 91},
    "6M": {"label": "6 Months", "yahoo_range": "6mo", "days": 182},
    "1Y": {"label": "1 Year", "yahoo_range": "1y", "days": 365},
    "5Y": {"label": "5 Years", "yahoo_range": "5y", "days": 1826},
}


@dataclass(frozen=True)
class Stock:
    ticker: str
    name: str
    market: str


_NSE = {
    "RELIANCE": "Reliance Industries", "TCS": "Tata Consultancy Services", "INFY": "Infosys",
    "HDFCBANK": "HDFC Bank", "ICICIBANK": "ICICI Bank", "SBIN": "State Bank of India", "ITC": "ITC Ltd",
    "LT": "Larsen & Toubro", "WIPRO": "Wipro", "BHARTIARTL": "Bharti Airtel", "HINDUNILVR": "Hindustan Unilever",
    "AXISBANK": "Axis Bank", "KOTAKBANK": "Kotak Mahindra Bank", "MARUTI": "Maruti Suzuki India",
    "TATAMOTORS": "Tata Motors", "SUNPHARMA": "Sun Pharmaceutical", "ASIANPAINT": "Asian Paints",
    "BAJFINANCE": "Bajaj Finance", "HCLTECH": "HCL Technologies", "TITAN": "Titan Company",
}
_NASDAQ = {
    "AAPL": "Apple Inc.", "MSFT": "Microsoft Corporation", "GOOGL": "Alphabet Inc. (Class A)", "AMZN": "Amazon.com, Inc.",
    "TSLA": "Tesla, Inc.", "NVDA": "NVIDIA Corporation", "META": "Meta Platforms, Inc.", "NFLX": "Netflix, Inc.",
    "AMD": "Advanced Micro Devices", "INTC": "Intel Corporation", "ADBE": "Adobe Inc.", "CSCO": "Cisco Systems",
    "PEP": "PepsiCo, Inc.", "COST": "Costco Wholesale", "QCOM": "QUALCOMM Incorporated",
}
_NYSE = {
    "JPM": "JPMorgan Chase & Co.", "V": "Visa Inc.", "WMT": "Walmart Inc.", "DIS": "The Walt Disney Company",
    "KO": "The Coca-Cola Company", "BA": "The Boeing Company", "XOM": "Exxon Mobil Corporation",
    "JNJ": "Johnson & Johnson", "PG": "Procter & Gamble", "MA": "Mastercard Incorporated", "NKE": "NIKE, Inc.",
    "IBM": "International Business Machines", "ORCL": "Oracle Corporation", "GS": "The Goldman Sachs Group",
    "T": "AT&T Inc.",
}

CATALOG: list[Stock] = (
    [Stock(t, n, "NSE") for t, n in _NSE.items()]
    + [Stock(t, n, "BSE") for t, n in _NSE.items()]
    + [Stock(t, n, "NASDAQ") for t, n in _NASDAQ.items()]
    + [Stock(t, n, "NYSE") for t, n in _NYSE.items()]
)


def ticker_format_ok(market: str, ticker: str) -> bool:
    return bool(re.match(MARKET_INFO[market]["pattern"], ticker))


def search(q: str, market: str | None = None, limit: int = 10) -> list[Stock]:
    q = q.strip().upper()
    if not q:
        return []
    hits = []
    for s in CATALOG:
        if market and s.market != market:
            continue
        if s.ticker == q:
            rank = 0
        elif s.ticker.startswith(q):
            rank = 1
        elif q in s.name.upper():
            rank = 2
        else:
            continue
        hits.append((rank, s.ticker, s.market, s))
    hits.sort(key=lambda h: h[:3])
    return [h[3] for h in hits[:limit]]


def lookup(ticker: str, market: str | None = None, prefer_market: str | None = None) -> Stock | None:
    """Find a validated stock. If market is omitted and the ticker is listed on several markets,
    prefer `prefer_market` (the user's saved market), otherwise the first match."""
    ticker = ticker.strip().upper()
    matches = [s for s in CATALOG if s.ticker == ticker and (market is None or s.market == market)]
    if not matches:
        return None
    for s in matches:
        if s.market == prefer_market:
            return s
    return matches[0]


def provider_symbol(stock: Stock) -> str:
    return stock.ticker + MARKET_INFO[stock.market]["suffix"]


def validate_research_request(ticker: str, market: str, period: str) -> Stock:
    """Checks the data provider supports this market, ticker format and historical period.
    Raises ValueError with a human-readable message."""
    if market not in MARKET_INFO:
        raise ValueError(f"Unsupported market '{market}'.")
    if period not in PERIOD_INFO:
        raise ValueError(f"Unsupported analysis period '{period}'.")
    ticker = ticker.strip().upper()
    if not ticker_format_ok(market, ticker):
        raise ValueError(f"'{ticker}' is not a valid {market} ticker format (examples: {MARKET_INFO[market]['example']}).")
    stock = lookup(ticker, market)
    if stock is None:
        raise ValueError(f"'{ticker}' is not a supported {market} symbol. Use the search box to find supported stocks.")
    return stock
