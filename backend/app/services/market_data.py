import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
import yfinance as yf

PROVIDER = "Yahoo Finance (via yfinance)"
REQUIRED = ["Open", "High", "Low", "Close", "Volume"]
# approx trading days per period, short history detect karne ke liye
EXPECTED_DAYS = {"1mo": 21, "3mo": 63, "6mo": 126, "1y": 252, "5y": 1260}


class MarketDataError(Exception):
    pass


class DataUnavailable(MarketDataError):
    """Ticker galat hai ya provider ke paas data nahi."""


class ProviderError(MarketDataError):
    """Provider fail hua (network / rate limit)."""


@dataclass
class HistoryResult:
    df: pd.DataFrame
    meta: dict
    validation: dict


# ---------- chhota cache (Yahoo ko baar baar hit na karein) ----------
_cache: dict = {}


def _cached(key, ttl, fn):
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < ttl:
        return hit[1]
    val = fn()
    _cache[key] = (time.time(), val)
    return val


def sha256_of(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def df_to_records(df: pd.DataFrame) -> list[dict]:
    return [
        {
            "date": d.strftime("%Y-%m-%d"),
            "open": round(float(r.Open), 4),
            "high": round(float(r.High), 4),
            "low": round(float(r.Low), 4),
            "close": round(float(r.Close), 4),
            "volume": int(r.Volume),
        }
        for d, r in zip(df.index, df.itertuples())
    ]


# ---------- VALIDATION ----------
def validate_ohlcv(df: pd.DataFrame, period: str, today=None):
    """Data clean karta hai aur batata hai kya problem mili. Returns (clean_df, report)."""
    issues = []

    def add(severity, code, message, count=None):
        issues.append({"severity": severity, "code": code, "message": message,
                       "count": None if count is None else int(count)})

    raw_rows = len(df)
    missing_cols = [c for c in REQUIRED if c not in df.columns]
    if missing_cols:
        raise DataUnavailable(f"Provider data is missing columns: {missing_cols}")

    df = df[REQUIRED].copy()
    idx = pd.DatetimeIndex(df.index)
    if idx.tz is not None:
        idx = idx.tz_localize(None)
    df.index = idx.normalize()
    df.index.name = "Date"

    # 1. duplicate dates
    dup = df.index.duplicated(keep="last")
    if dup.sum():
        df = df[~dup]
        add("error", "duplicate_dates", "Duplicate dates removed (kept last).", dup.sum())

    # 2. sorting
    if not df.index.is_monotonic_increasing:
        df = df.sort_index()
        add("warning", "unsorted_dates", "Dates were not in order; sorted ascending.")

    # 3. missing values
    price_cols = ["Open", "High", "Low", "Close"]
    na_rows = df[price_cols].isna().any(axis=1)
    if na_rows.sum():
        df = df[~na_rows]
        add("error", "missing_values", "Rows with missing OHLC values removed.", na_rows.sum())
    vol_na = df["Volume"].isna().sum()
    if vol_na:
        df["Volume"] = df["Volume"].fillna(0)
        add("warning", "missing_volume", "Missing volume values set to 0.", vol_na)

    # 4. inconsistent data (hard errors: row hata dete hain)
    bad = (df[price_cols] <= 0).any(axis=1)
    if bad.sum():
        df = df[~bad]
        add("error", "non_positive_price", "Rows with zero/negative prices removed.", bad.sum())
    bad = df["High"] < df["Low"]
    if bad.sum():
        df = df[~bad]
        add("error", "high_below_low", "Rows where High < Low removed.", bad.sum())
    bad = df["Volume"] < 0
    if bad.sum():
        df = df[~bad]
        add("error", "negative_volume", "Rows with negative volume removed.", bad.sum())

    # 5. soft checks (row rakhte hain, sirf warning)
    if len(df):
        oc_max, oc_min = df[["Open", "Close"]].max(axis=1), df[["Open", "Close"]].min(axis=1)
        out = (df["High"] < oc_max) | (df["Low"] > oc_min)
        if out.sum():
            add("warning", "ohlc_inconsistent", "Open/Close lies outside the High-Low range.", out.sum())

        zero_vol = (df["Volume"] == 0).sum()
        if zero_vol:
            add("warning", "zero_volume", "Days with zero volume (illiquid or no trading).", zero_vol)

        gaps = (df.index.to_series().diff().dt.days > 7).sum()
        if gaps:
            add("warning", "date_gaps", "Gaps longer than 7 calendar days between rows.", gaps)

        jumps = (df["Close"].pct_change().abs() > 0.4).sum()
        if jumps:
            add("warning", "extreme_move", "Daily close moved more than 40% (possible split or bad data).", jumps)

        today = today if today is not None else pd.Timestamp.now().normalize()
        if (today - df.index.max()).days > 7:
            add("warning", "stale_data", f"Latest data is from {df.index.max().date()} (older than 7 days).")

        expected = EXPECTED_DAYS.get(period)
        if expected and len(df) < 0.8 * expected:
            add("warning", "short_history",
                f"Only {len(df)} trading days available for requested period '{period}' "
                f"(expected about {expected}). Stock may be newly listed.")

    report = {"rows_raw": raw_rows, "rows_clean": len(df), "issues": issues,
              "is_usable": len(df) >= 5}
    return df, report


# ---------- PRICE HISTORY ----------
def get_history(ticker: str, period: str) -> HistoryResult:
    def fetch():
        try:
            raw = yf.Ticker(ticker).history(period=period, auto_adjust=False)
        except Exception as e:
            raise ProviderError("Market data provider error. Please try again.") from e
        if raw is None or raw.empty:
            raise DataUnavailable(f"No price data found for '{ticker}'. Check the ticker and market.")
        df, validation = validate_ohlcv(raw, period)
        if not validation["is_usable"]:
            raise DataUnavailable(f"Price data for '{ticker}' failed validation (too few valid rows).")
        meta = {
            "provider": PROVIDER,
            "source_url": f"https://finance.yahoo.com/quote/{ticker}",
            "ticker": ticker,
            "period": period,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "content_hash": sha256_of(df_to_records(df)),
        }
        return HistoryResult(df, meta, validation)

    return _cached(("history", ticker, period), 600, fetch)


# ---------- QUOTE (dashboard cards) ----------
def build_quote(ticker: str, market: str, history: HistoryResult, profile: Optional[dict]) -> dict:
    """Quote cards ke liye numbers. Sab kuch validated daily data se nikalta hai (live tick nahi)."""
    df = history.df
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last
    price, prev_close = float(last["Close"]), float(prev["Close"])
    window = df.tail(252)
    p = profile or {}
    return {
        "ticker": ticker,
        "market": market,
        "company_name": p.get("company_name"),
        "exchange": p.get("exchange"),
        "currency": p.get("currency"),
        "sector": p.get("sector"),
        "price": round(price, 4),
        "prev_close": round(prev_close, 4),
        "change": round(price - prev_close, 4),
        "change_pct": round((price / prev_close - 1) * 100, 2),
        "day_low": round(float(last["Low"]), 4),
        "day_high": round(float(last["High"]), 4),
        "week52_low": round(float(window["Low"].min()), 4),
        "week52_high": round(float(window["High"].max()), 4),
        "volume": int(last["Volume"]),
        "pe_ratio": p.get("trailing_pe"),
        "as_of": df.index[-1].strftime("%Y-%m-%d"),
        "spark": [round(float(x), 4) for x in df["Close"].tail(30)],
        "meta": history.meta,
    }


# ---------- COMPANY PROFILE ----------
PROFILE_FIELDS = {
    "longName": "company_name", "sector": "sector", "industry": "industry",
    "country": "country", "exchange": "exchange", "currency": "currency",
    "marketCap": "market_cap", "fullTimeEmployees": "employees", "website": "website",
    "trailingPE": "trailing_pe", "priceToBook": "price_to_book",
    "returnOnEquity": "return_on_equity", "longBusinessSummary": "business_summary",
}


def get_profile(ticker: str) -> dict:
    def fetch():
        try:
            info = yf.Ticker(ticker).get_info() or {}
        except Exception as e:
            raise ProviderError("Market data provider error. Please try again.") from e
        if not (info.get("longName") or info.get("shortName")):
            raise DataUnavailable(f"No company profile found for '{ticker}'.")
        profile = {new: info.get(old) for old, new in PROFILE_FIELDS.items()}
        profile["company_name"] = profile["company_name"] or info.get("shortName")
        return {
            "profile": profile,
            "missing_fields": [k for k, v in profile.items() if v is None],
            "meta": {
                "provider": PROVIDER,
                "source_url": f"https://finance.yahoo.com/quote/{ticker}/profile",
                "ticker": ticker,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "note": "Ratios here are provider-reported, not our own calculation.",
            },
        }

    return _cached(("profile", ticker), 3600, fetch)


# ---------- FINANCIAL STATEMENTS (key items, for agents later) ----------
KEY_ITEMS = {
    "income_statement": ["Total Revenue", "Gross Profit", "Operating Income", "Net Income", "Basic EPS"],
    "balance_sheet": ["Total Assets", "Total Debt", "Stockholders Equity", "Cash And Cash Equivalents"],
    "cash_flow": ["Operating Cash Flow", "Capital Expenditure", "Free Cash Flow"],
}


def _stmt_to_dict(df, items):
    if df is None or df.empty:
        return {}
    out = {}
    for col in df.columns:
        year = pd.Timestamp(col).strftime("%Y-%m-%d")
        out[year] = {}
        for item in items:
            if item in df.index:
                v = df.loc[item, col]
                out[year][item] = None if pd.isna(v) else float(v)
            else:
                out[year][item] = None
    return out


def get_financials(ticker: str) -> dict:
    def fetch():
        try:
            t = yf.Ticker(ticker)
            raw = {"income_statement": t.income_stmt,
                   "balance_sheet": t.balance_sheet,
                   "cash_flow": t.cash_flow}
        except Exception as e:
            raise ProviderError("Market data provider error. Please try again.") from e

        statements = {name: _stmt_to_dict(raw[name], items) for name, items in KEY_ITEMS.items()}
        if not any(statements.values()):
            raise DataUnavailable(f"No financial statements found for '{ticker}'.")

        # kaunse items kisi bhi saal mein nahi mile
        data_gaps = []
        for name, items in KEY_ITEMS.items():
            for item in items:
                if all(yr.get(item) is None for yr in statements[name].values()):
                    data_gaps.append(f"{name}: {item}")
        return {
            "statements": statements,
            "data_gaps": data_gaps,
            "meta": {
                "provider": PROVIDER,
                "source_url": f"https://finance.yahoo.com/quote/{ticker}/financials",
                "ticker": ticker,
                "frequency": "annual",
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            },
        }

    return _cached(("financials", ticker), 3600, fetch)


# ---------- FULL STATEMENTS (dashboard tables, annual or quarterly) ----------
def _table(df) -> dict:
    """DataFrame -> {columns: [newest..oldest dates], rows: [{item, values}]}."""
    if df is None or getattr(df, "empty", True):
        return {"columns": [], "rows": []}
    cols = sorted(df.columns, reverse=True)
    columns = [pd.Timestamp(c).strftime("%Y-%m-%d") for c in cols]
    rows = []
    for item, row in df[cols].iterrows():
        values = [None if pd.isna(row[c]) else float(row[c]) for c in cols]
        if any(v is not None for v in values):
            rows.append({"item": str(item), "values": values})
    return {"columns": columns, "rows": rows}


def get_statements(ticker: str, frequency: str = "annual") -> dict:
    freq = "quarterly" if frequency == "quarterly" else "yearly"

    def fetch():
        try:
            t = yf.Ticker(ticker)
            raw = {
                "income_statement": t.get_income_stmt(freq=freq),
                "balance_sheet": t.get_balance_sheet(freq=freq),
                "cash_flow": t.get_cash_flow(freq=freq),
            }
        except Exception as e:
            raise ProviderError("Market data provider error. Please try again.") from e

        tables = {name: _table(df) for name, df in raw.items()}
        if not any(tb["rows"] for tb in tables.values()):
            raise DataUnavailable(f"No financial statements found for '{ticker}'.")
        return {
            "frequency": "quarterly" if freq == "quarterly" else "annual",
            "statements": tables,
            "meta": {
                "provider": PROVIDER,
                "source_url": f"https://finance.yahoo.com/quote/{ticker}/financials",
                "ticker": ticker,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            },
        }

    return _cached(("statements", ticker, freq), 3600, fetch)
