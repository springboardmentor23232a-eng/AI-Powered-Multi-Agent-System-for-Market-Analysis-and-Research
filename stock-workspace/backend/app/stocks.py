"""Validated ticker list (swap for a market-data API such as yfinance / Alpha Vantage later)."""

CATALOG = {
    "NSE": {"RELIANCE": "Reliance Industries", "TCS": "Tata Consultancy Services", "INFY": "Infosys",
            "HDFCBANK": "HDFC Bank", "ICICIBANK": "ICICI Bank", "SBIN": "State Bank of India",
            "ITC": "ITC Limited", "WIPRO": "Wipro", "BHARTIARTL": "Bharti Airtel", "LT": "Larsen & Toubro"},
    "BSE": {"RELIANCE": "Reliance Industries", "TCS": "Tata Consultancy Services", "INFY": "Infosys",
            "HDFCBANK": "HDFC Bank", "SBIN": "State Bank of India", "TATAMOTORS": "Tata Motors",
            "MARUTI": "Maruti Suzuki", "SUNPHARMA": "Sun Pharma"},
    "NASDAQ": {"AAPL": "Apple Inc.", "MSFT": "Microsoft Corporation", "GOOGL": "Alphabet Inc.",
               "AMZN": "Amazon.com", "TSLA": "Tesla, Inc.", "NVDA": "NVIDIA Corporation",
               "META": "Meta Platforms", "NFLX": "Netflix"},
    "NYSE": {"JPM": "JPMorgan Chase", "KO": "Coca-Cola", "DIS": "Walt Disney", "WMT": "Walmart",
             "BA": "Boeing", "V": "Visa Inc.", "XOM": "Exxon Mobil", "NKE": "Nike"},
}

SUFFIX = {"NSE": ".NS", "BSE": ".BO", "NASDAQ": "", "NYSE": ""}


def provider_symbol(ticker: str, market: str) -> str:
    """Ticker format a Yahoo-Finance-style provider expects."""
    return f"{ticker}{SUFFIX[market]}"


def lookup(ticker: str, market: str) -> str | None:
    return CATALOG.get(market, {}).get(ticker.strip().upper())


def search(q: str, market: str, limit: int = 8):
    q = q.strip().lower()
    if not q:
        return []
    out = [{"ticker": t, "company_name": n, "market": market}
           for t, n in CATALOG.get(market, {}).items() if q in t.lower() or q in n.lower()]
    return out[:limit]
