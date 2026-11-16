"""Market-data providers used by the research workflow.

demo  : deterministic SYNTHETIC prices, clearly labelled in the report. Works offline.
yahoo : real daily closes from Yahoo Finance's public chart endpoint (needs internet).
"""
import hashlib
import math
import random
from datetime import date, datetime, timedelta, timezone

import httpx

from .catalog import PERIOD_INFO, Stock, provider_symbol
from .config import settings


class MarketDataError(Exception):
    pass


def _demo_history(stock: Stock, period: str) -> tuple[list[tuple[date, float]], str]:
    days = PERIOD_INFO[period]["days"]
    seed = int(hashlib.sha256(f"{stock.market}:{stock.ticker}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    price = rng.uniform(50, 2500)
    end = date.today()
    series, d = [], end - timedelta(days=days)
    while d <= end:
        if d.weekday() < 5:
            price *= math.exp(rng.gauss(0.0004, 0.015))
            series.append((d, round(price, 2)))
        d += timedelta(days=1)
    return series, "Demo provider (SYNTHETIC data - not real prices)"


def _yahoo_history(stock: Stock, period: str) -> tuple[list[tuple[date, float]], str]:
    symbol = provider_symbol(stock)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"range": PERIOD_INFO[period]["yahoo_range"], "interval": "1d"}
    try:
        r = httpx.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        r.raise_for_status()
        result = r.json()["chart"]["result"][0]
        stamps, closes = result["timestamp"], result["indicators"]["quote"][0]["close"]
    except Exception as exc:  # network error, bad symbol, rate limit, unexpected payload
        raise MarketDataError(f"Could not fetch price history for {symbol} from Yahoo Finance: {exc}") from exc
    series = [(datetime.fromtimestamp(t, timezone.utc).date(), round(c, 2)) for t, c in zip(stamps, closes) if c is not None]
    if len(series) < 5:
        raise MarketDataError(f"Yahoo Finance returned too little data for {symbol} ({len(series)} points).")
    return series, "Yahoo Finance (daily closes)"


def fetch_history(stock: Stock, period: str) -> tuple[list[tuple[date, float]], str]:
    """Returns (list of (date, close), human-readable data-source label)."""
    if settings.market_data_provider == "yahoo":
        return _yahoo_history(stock, period)
    return _demo_history(stock, period)
