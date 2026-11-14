# Validated ticker list. Tickers use Yahoo Finance style (RELIANCE.NS / RELIANCE.BO).
# If your data provider uses another format, change it here only.

INDIAN = [
    ("Reliance Industries", "RELIANCE"),
    ("Tata Consultancy Services", "TCS"),
    ("Infosys", "INFY"),
    ("HDFC Bank", "HDFCBANK"),
    ("ICICI Bank", "ICICIBANK"),
    ("State Bank of India", "SBIN"),
    ("ITC", "ITC"),
    ("Wipro", "WIPRO"),
    ("Bharti Airtel", "BHARTIARTL"),
    ("Larsen & Toubro", "LT"),
]

US = [
    ("Apple Inc.", "AAPL", "NASDAQ"),
    ("Microsoft Corporation", "MSFT", "NASDAQ"),
    ("Alphabet Inc.", "GOOGL", "NASDAQ"),
    ("Amazon.com Inc.", "AMZN", "NASDAQ"),
    ("Tesla Inc.", "TSLA", "NASDAQ"),
    ("NVIDIA Corporation", "NVDA", "NASDAQ"),
    ("Meta Platforms", "META", "NASDAQ"),
    ("Netflix Inc.", "NFLX", "NASDAQ"),
    ("JPMorgan Chase", "JPM", "NYSE"),
    ("Walmart Inc.", "WMT", "NYSE"),
    ("Coca-Cola Company", "KO", "NYSE"),
    ("Walt Disney Company", "DIS", "NYSE"),
    ("Visa Inc.", "V", "NYSE"),
    ("Exxon Mobil", "XOM", "NYSE"),
    ("Johnson & Johnson", "JNJ", "NYSE"),
]

STOCKS = []
for name, symbol in INDIAN:
    STOCKS.append({"name": name, "ticker": f"{symbol}.NS", "market": "NSE"})
    STOCKS.append({"name": name, "ticker": f"{symbol}.BO", "market": "BSE"})
for name, ticker, market in US:
    STOCKS.append({"name": name, "ticker": ticker, "market": market})


def find_stock(ticker: str):
    ticker = ticker.strip().upper()
    return next((s for s in STOCKS if s["ticker"] == ticker), None)


def search_stocks(q: str, market: str | None = None, limit: int = 10):
    q = q.strip().lower()
    if not q:
        return []
    results = [
        s for s in STOCKS
        if (q in s["name"].lower() or q in s["ticker"].lower())
        and (not market or s["market"] == market.upper())
    ]
    return results[:limit]