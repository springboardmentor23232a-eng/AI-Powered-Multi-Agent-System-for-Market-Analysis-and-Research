SUFFIX = {"NSE": ".NS", "BSE": ".BO", "NASDAQ": "", "NYSE": ""}
EXCHANGE_TO_MARKET = {
    "NSI": "NSE", "BSE": "BSE",
    "NMS": "NASDAQ", "NGM": "NASDAQ", "NCM": "NASDAQ",
    "NYQ": "NYSE",
}

def normalize_ticker(ticker: str, market: str) -> str:
    """yfinance format: NSE -> TCS.NS, BSE -> TCS.BO, US -> AAPL"""
    t = ticker.strip().upper()
    if market in ("NSE", "BSE") and not t.endswith((".NS", ".BO")):
        t += SUFFIX[market]
    return t