"""Market-data providers (Milestone 1: historical OHLCV, company profile, financial statements).

demo  : deterministic SYNTHETIC data, clearly labelled everywhere it is shown. Works offline - the default.
yahoo : real data from Yahoo Finance's public endpoints (needs internet; failures raise MarketDataError).

Every fetch returns a `Fetched` bundle: the data + where it came from + when it was retrieved. Nothing here
cleans or "fixes" data - raw bars go to `validation.validate_ohlcv`, which reports what it found.
"""
import hashlib
import math
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx

from .catalog import MARKET_INFO, PERIOD_INFO, Stock, provider_symbol
from .config import settings
from .validation import Bar

YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
YAHOO_SEARCH = "https://query2.finance.yahoo.com/v1/finance/search"
YAHOO_FUNDAMENTALS = "https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/{symbol}"
_HEADERS = {"User-Agent": "Mozilla/5.0"}


class MarketDataError(Exception):
    pass


@dataclass(frozen=True)
class Fetched:
    data: Any
    source: str
    source_url: str | None
    synthetic: bool
    retrieved_at: datetime


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _seed(stock: Stock, salt: str = "") -> random.Random:
    digest = hashlib.sha256(f"{stock.market}:{stock.ticker}:{salt}".encode()).hexdigest()[:8]
    return random.Random(int(digest, 16))


_DEMO_LABEL = "Demo provider (SYNTHETIC data - not real prices)"


# ----------------------------------------------------------------------------------------------- OHLCV
def _demo_ohlcv(stock: Stock, period: str) -> Fetched:
    days = PERIOD_INFO[period]["days"]
    rng = _seed(stock)
    price = rng.uniform(50, 2500)
    base_volume = rng.uniform(2e5, 5e6)
    end = date.today()
    bars: list[Bar] = []
    d = end - timedelta(days=days)
    while d <= end:
        if d.weekday() < 5:
            open_ = price
            close = open_ * math.exp(rng.gauss(0.0004, 0.015))
            high = max(open_, close) * (1 + abs(rng.gauss(0, 0.006)))
            low = min(open_, close) * (1 - abs(rng.gauss(0, 0.006)))
            volume = round(base_volume * rng.uniform(0.6, 1.5))
            bars.append(Bar(d, round(open_, 2), round(high, 2), round(low, 2), round(close, 2), volume))
            price = close
        d += timedelta(days=1)
    return Fetched(bars, _DEMO_LABEL, None, True, _now())


def _yahoo_ohlcv(stock: Stock, period: str) -> Fetched:
    symbol = provider_symbol(stock)
    url = YAHOO_CHART.format(symbol=symbol)
    try:
        r = httpx.get(url, params={"range": PERIOD_INFO[period]["yahoo_range"], "interval": "1d"},
                      headers=_HEADERS, timeout=10)
        r.raise_for_status()
        result = r.json()["chart"]["result"][0]
        stamps, q = result["timestamp"], result["indicators"]["quote"][0]
        o, h, l, c, v = (q.get(k) or [None] * len(stamps) for k in ("open", "high", "low", "close", "volume"))
    except Exception as exc:  # network error, bad symbol, rate limit, unexpected payload
        raise MarketDataError(f"Could not fetch price history for {symbol} from Yahoo Finance: {exc}") from exc
    bars = [Bar(datetime.fromtimestamp(t, timezone.utc).date(), *(None if x is None else round(x, 4) for x in row[:4]), row[4])
            for t, row in zip(stamps, zip(o, h, l, c, v))]
    return Fetched(bars, "Yahoo Finance (daily OHLCV)", f"https://finance.yahoo.com/quote/{symbol}/history", False, _now())


def fetch_ohlcv(stock: Stock, period: str) -> Fetched:
    """Raw (unvalidated) daily Open/High/Low/Close/Volume bars as a list[Bar]."""
    return _yahoo_ohlcv(stock, period) if settings.market_data_provider == "yahoo" else _demo_ohlcv(stock, period)


# ------------------------------------------------------------------------------------------- profile
PROFILE_FIELDS = ("name", "symbol", "exchange", "currency", "sector", "industry", "latest_price",
                  "week52_high", "week52_low", "market_cap", "website", "description")


def _demo_profile(stock: Stock) -> Fetched:
    rng = _seed(stock, "profile")
    sectors = [("Technology", "Software"), ("Financial Services", "Banks"), ("Energy", "Oil & Gas"),
               ("Healthcare", "Pharmaceuticals"), ("Consumer Defensive", "Beverages"), ("Industrials", "Machinery")]
    sector, industry = rng.choice(sectors)
    price = round(rng.uniform(50, 2500), 2)
    profile = {
        "name": stock.name, "symbol": provider_symbol(stock), "exchange": stock.market,
        "currency": MARKET_INFO[stock.market]["currency"], "sector": sector, "industry": industry,
        "latest_price": price, "week52_high": round(price * 1.25, 2), "week52_low": round(price * 0.72, 2),
        "market_cap": None,  # deliberately absent so the "missing field" handling is visible in demo mode
        "website": None, "description": None,
    }
    return Fetched(profile, _DEMO_LABEL, None, True, _now())


def _yahoo_profile(stock: Stock) -> Fetched:
    symbol = provider_symbol(stock)
    try:
        r = httpx.get(YAHOO_CHART.format(symbol=symbol), params={"range": "1y", "interval": "1d"},
                      headers=_HEADERS, timeout=10)
        r.raise_for_status()
        meta = r.json()["chart"]["result"][0]["meta"]
    except Exception as exc:
        raise MarketDataError(f"Could not fetch the company profile for {symbol} from Yahoo Finance: {exc}") from exc
    sector = industry = None
    try:  # best effort: sector/industry come from the search endpoint and may be absent
        s = httpx.get(YAHOO_SEARCH, params={"q": symbol, "quotesCount": 1, "newsCount": 0}, headers=_HEADERS, timeout=10)
        s.raise_for_status()
        quotes = s.json().get("quotes") or []
        hit = next((q for q in quotes if q.get("symbol") == symbol), None)
        if hit:
            sector, industry = hit.get("sectorDisp") or hit.get("sector"), hit.get("industryDisp") or hit.get("industry")
    except Exception:
        pass
    profile = {
        "name": meta.get("longName") or meta.get("shortName") or stock.name, "symbol": symbol,
        "exchange": meta.get("fullExchangeName") or meta.get("exchangeName"), "currency": meta.get("currency"),
        "sector": sector, "industry": industry, "latest_price": meta.get("regularMarketPrice"),
        "week52_high": meta.get("fiftyTwoWeekHigh"), "week52_low": meta.get("fiftyTwoWeekLow"),
        "market_cap": None, "website": None, "description": None,
    }
    return Fetched(profile, "Yahoo Finance (chart metadata + search)", f"https://finance.yahoo.com/quote/{symbol}",
                   False, _now())


def fetch_profile(stock: Stock) -> Fetched:
    return _yahoo_profile(stock) if settings.market_data_provider == "yahoo" else _demo_profile(stock)


# ------------------------------------------------------------------------------------------ financials
STATEMENTS = {
    "income_statement": {"total_revenue": "TotalRevenue", "gross_profit": "GrossProfit",
                         "operating_income": "OperatingIncome", "net_income": "NetIncome"},
    "balance_sheet": {"total_assets": "TotalAssets", "total_debt": "TotalDebt",
                      "stockholders_equity": "StockholdersEquity", "cash": "CashAndCashEquivalents"},
    "cash_flow": {"operating_cash_flow": "OperatingCashFlow", "free_cash_flow": "FreeCashFlow",
                  "capital_expenditure": "CapitalExpenditure"},
    "per_share": {"eps": "BasicEPS", "shares_outstanding": "OrdinarySharesNumber"},
}


def _demo_financials(stock: Stock) -> Fetched:
    rng = _seed(stock, "financials")
    year = date.today().year - 1
    periods = [f"{y}-03-31" for y in range(year - 3, year + 1)]
    revenue = rng.uniform(5e9, 3e11)
    rev, net, ocf = [], [], []
    for _ in periods:
        revenue *= rng.uniform(0.95, 1.18)
        rev.append(round(revenue))
        net.append(round(revenue * rng.uniform(0.05, 0.22)))
        ocf.append(round(revenue * rng.uniform(0.08, 0.25)))
    assets = [round(r * rng.uniform(1.1, 2.0)) for r in rev]
    data = {
        "currency": MARKET_INFO[stock.market]["currency"], "periods": periods,
        "income_statement": {"total_revenue": rev, "gross_profit": [round(r * 0.45) for r in rev],
                             "operating_income": [round(n * 1.35) for n in net], "net_income": net},
        "balance_sheet": {"total_assets": assets, "total_debt": [round(a * rng.uniform(0.1, 0.4)) for a in assets],
                          "stockholders_equity": [round(a * rng.uniform(0.3, 0.6)) for a in assets],
                          "cash": [None] + [round(a * 0.08) for a in assets[1:]]},  # one gap on purpose
        "cash_flow": {"operating_cash_flow": ocf, "free_cash_flow": [round(o * 0.7) for o in ocf],
                      "capital_expenditure": [-round(o * 0.3) for o in ocf]},
        "per_share": {"eps": [round(n / (sh := rng.uniform(5e8, 5e9)), 2) for n in net],
                      "shares_outstanding": [round(n / (round(n / sh, 2) or 1)) for n in net]},
    }
    data["missing_metrics"] = _missing_metrics(data)
    return Fetched(data, _DEMO_LABEL, None, True, _now())


def _missing_metrics(data: dict) -> list[str]:
    out = []
    for stmt, metrics in STATEMENTS.items():
        for m in metrics:
            vals = data[stmt].get(m, [])
            if not vals or any(v is None for v in vals):
                out.append(f"{stmt}.{m}")
    return out


def _yahoo_financials(stock: Stock) -> Fetched:
    symbol = provider_symbol(stock)
    wanted = [f"annual{yname}" for metrics in STATEMENTS.values() for yname in metrics.values()]
    now = int(_now().timestamp())
    try:
        r = httpx.get(YAHOO_FUNDAMENTALS.format(symbol=symbol),
                      params={"type": ",".join(wanted), "period1": now - 5 * 366 * 86400, "period2": now,
                              "merge": "false", "padTimeSeries": "true"},
                      headers=_HEADERS, timeout=15)
        r.raise_for_status()
        results = r.json()["timeseries"]["result"]
    except Exception as exc:
        raise MarketDataError(f"Could not fetch financial statements for {symbol} from Yahoo Finance: {exc}") from exc

    by_type: dict[str, dict[str, float]] = {}
    for item in results:
        key = item["meta"]["type"][0]
        by_type[key] = {p["asOfDate"]: p["reportedValue"]["raw"] for p in (item.get(key) or []) if p}
    periods = sorted({d for series in by_type.values() for d in series})[-4:]
    if not periods:
        raise MarketDataError(f"Yahoo Finance has no annual financial statements for {symbol}.")
    data: dict[str, Any] = {"currency": MARKET_INFO[stock.market]["currency"], "periods": periods}
    for stmt, metrics in STATEMENTS.items():
        data[stmt] = {m: [by_type.get(f"annual{y}", {}).get(p) for p in periods] for m, y in metrics.items()}
    data["missing_metrics"] = _missing_metrics(data)
    return Fetched(data, "Yahoo Finance (annual fundamentals time-series)",
                   f"https://finance.yahoo.com/quote/{symbol}/financials", False, _now())


def fetch_financials(stock: Stock) -> Fetched:
    return _yahoo_financials(stock) if settings.market_data_provider == "yahoo" else _demo_financials(stock)
