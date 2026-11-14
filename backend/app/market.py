"""Thin wrapper around yfinance: ticker formats per market and period mapping."""
import re

import yfinance as yf

MARKETS = {
    "NSE": {"suffix": ".NS", "exchanges": {"NSI"}},
    "BSE": {"suffix": ".BO", "exchanges": {"BSE", "BOM"}},
    "NASDAQ": {"suffix": "", "exchanges": {"NMS", "NGM", "NCM"}},
    "NYSE": {"suffix": "", "exchanges": {"NYQ"}},
}
PERIODS = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "5Y": "5y"}
_SYMBOL = re.compile(r"^[A-Z0-9&\-\.]{1,20}$")


def normalize_symbol(symbol: str, market: str) -> str:
    """RELIANCE -> RELIANCE.NS for NSE, TCS -> TCS.BO for BSE, AAPL stays AAPL."""
    symbol = symbol.strip().upper()
    suffix = MARKETS[market]["suffix"]
    if suffix:
        if not symbol.endswith(suffix):
            symbol += suffix
    elif symbol.endswith((".NS", ".BO")):
        raise ValueError(f"{symbol} is not a {market} symbol")
    if not _SYMBOL.match(symbol):
        raise ValueError("Invalid ticker format")
    return symbol


def search_stocks(query: str, market: str) -> list[dict]:
    quotes = yf.Search(query, max_results=20, news_count=0).quotes
    results = []
    for q in quotes:
        if q.get("quoteType") == "EQUITY" and q.get("exchange") in MARKETS[market]["exchanges"]:
            results.append({
                "ticker": q["symbol"],
                "company_name": q.get("shortname") or q.get("longname") or q["symbol"],
                "market": market,
            })
    return results


def has_price_data(symbol: str, period: str) -> bool:
    return not yf.Ticker(symbol).history(period=PERIODS[period]).empty
