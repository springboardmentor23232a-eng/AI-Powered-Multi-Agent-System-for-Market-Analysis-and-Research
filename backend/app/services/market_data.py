import hashlib
import json
import re
from datetime import date, datetime, timedelta, timezone
from typing import Callable, Protocol

import pandas as pd
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import MarketSnapshot, SourceDocument
from app.services.validation import Issue, ValidationReport, validate_financials, validate_ohlcv

DEFAULT_TTL = timedelta(hours=12)
SUFFIX = {"NSE": ".NS", "BSE": ".BO"}


class ProviderError(Exception):
    pass


class MarketDataProvider(Protocol):
    name: str

    def get_ohlcv(self, symbol: str, period: str) -> pd.DataFrame: ...

    def get_financials(self, symbol: str) -> dict: ...


class YahooProvider:
    """yfinance adapter. Live behaviour is unverified in CI; tests use a fake provider."""

    name = "yfinance"

    def get_ohlcv(self, symbol: str, period: str) -> pd.DataFrame:
        import yfinance as yf

        try:
            df = yf.Ticker(symbol).history(period=period, auto_adjust=False)
        except Exception as exc:  # network, rate limit, delisted
            raise ProviderError(str(exc)) from exc
        if df is None or df.empty:
            raise ProviderError(f"No price data returned for {symbol}")
        df = df.reset_index().rename(columns=str.lower)
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
        return df[["date", "open", "high", "low", "close", "volume"]]

    def get_financials(self, symbol: str) -> dict:
        import yfinance as yf

        try:
            t = yf.Ticker(symbol)
            info, fin, bs = t.info or {}, t.financials, t.balance_sheet
        except Exception as exc:
            raise ProviderError(str(exc)) from exc

        def row(df, labels, col):
            for label in labels:
                if df is not None and label in df.index:
                    v = df.loc[label, col]
                    return None if pd.isna(v) else float(v)
            return None

        annual = []
        if fin is not None and not fin.empty:
            for col in fin.columns:
                annual.append({
                    "year": int(pd.Timestamp(col).year),
                    "revenue": row(fin, ["Total Revenue"], col),
                    "operating_income": row(fin, ["Operating Income"], col),
                    "net_income": row(fin, ["Net Income"], col),
                    "total_debt": row(bs, ["Total Debt"], col) if bs is not None and col in bs.columns else None,
                    "total_equity": row(bs, ["Stockholders Equity", "Total Equity Gross Minority Interest"], col)
                    if bs is not None and col in bs.columns else None,
                })
        profile = {k: info.get(k) for k in (
            "longName", "sector", "industry", "marketCap", "currency", "sharesOutstanding",
            "trailingPE", "priceToBook", "returnOnEquity")}
        if not annual and not profile.get("longName"):
            raise ProviderError(f"No financial data returned for {symbol}")
        return {"profile": profile, "annual": annual}


def normalize_ticker(ticker: str) -> str:
    t = ticker.strip().upper()
    return re.sub(r"\.(NS|BO)$", "", t)


def provider_symbol(ticker: str, market: str) -> str:
    return normalize_ticker(ticker) + SUFFIX.get(market.upper(), "")


def content_hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _period_days(period: str) -> int | None:
    m = re.fullmatch(r"(\d+)(d|mo|y)", period)
    if not m:
        return None
    return int(m.group(1)) * {"d": 1, "mo": 30, "y": 365}[m.group(2)]


def fact_line(year: int, field: str, value: float) -> str:
    """Canonical text line for one financial figure; FACT claims quote it verbatim."""
    return f"FY{year} {field}={value!r}"


def financials_excerpt(annual: list[dict]) -> str:
    fields = ("revenue", "operating_income", "net_income", "total_debt", "total_equity")
    return "\n".join(fact_line(y["year"], f, y[f]) for y in annual for f in fields if y.get(f) is not None)


def last_close_line(date_str: str, close: float) -> str:
    return f"last_close={date_str}:{close!r}"


class Source(BaseModel):
    provider: str
    retrieved_at: datetime
    content_hash: str
    from_cache: bool
    stale_cache: bool = False


def _cached(db: Session, provider, symbol: str, kind: str, period: str,
            fetch: Callable[[], dict], now: datetime, ttl: timedelta) -> tuple[dict, Source]:
    snap = db.scalar(select(MarketSnapshot).where(
        MarketSnapshot.symbol == symbol, MarketSnapshot.kind == kind, MarketSnapshot.period == period))
    if snap and now - _aware(snap.retrieved_at) < ttl:
        return snap.payload, Source(provider=snap.provider, retrieved_at=_aware(snap.retrieved_at),
                                    content_hash=snap.content_hash, from_cache=True)
    try:
        payload = fetch()
    except ProviderError:
        if snap:  # fall back to the old snapshot, flagged as stale
            return snap.payload, Source(provider=snap.provider, retrieved_at=_aware(snap.retrieved_at),
                                        content_hash=snap.content_hash, from_cache=True, stale_cache=True)
        raise
    h = content_hash(payload)
    if snap:
        snap.payload, snap.content_hash, snap.retrieved_at, snap.provider = payload, h, now, provider.name
    else:
        db.add(MarketSnapshot(symbol=symbol, kind=kind, period=period, provider=provider.name,
                              payload=payload, content_hash=h, retrieved_at=now))
    try:
        db.commit()
    except IntegrityError:  # another worker stored the same snapshot first; use theirs
        db.rollback()
        snap = db.scalar(select(MarketSnapshot).where(
            MarketSnapshot.symbol == symbol, MarketSnapshot.kind == kind, MarketSnapshot.period == period))
        if snap is None:
            raise
        return snap.payload, Source(provider=snap.provider, retrieved_at=_aware(snap.retrieved_at),
                                    content_hash=snap.content_hash, from_cache=True)
    return payload, Source(provider=provider.name, retrieved_at=now, content_hash=h, from_cache=False)


def _log_source(db: Session, task_id, source_type: str, title: str, src: Source, excerpt: str):
    if task_id is None:
        return
    exists = db.scalar(select(SourceDocument.source_id).where(
        SourceDocument.task_id == task_id, SourceDocument.content_hash == src.content_hash,
        SourceDocument.source_type == source_type))
    if exists:
        return
    db.add(SourceDocument(task_id=task_id, source_type=source_type, title=title, source_url=None,
                          retrieved_at=src.retrieved_at, content_hash=src.content_hash, content_excerpt=excerpt))
    db.commit()


class PriceResult(BaseModel):
    ticker: str
    market: str
    symbol: str
    period: str
    as_of: date | None
    rows: list[dict]
    validation: ValidationReport
    source: Source


class FinancialsResult(BaseModel):
    ticker: str
    market: str
    symbol: str
    data: dict
    issues: list[Issue]
    source: Source


def get_prices(db: Session, provider: MarketDataProvider, ticker: str, market: str = "NSE",
               period: str = "2y", as_of: date | None = None, task_id=None,
               now: datetime | None = None, ttl: timedelta = DEFAULT_TTL) -> PriceResult:
    now = now or datetime.now(timezone.utc)
    symbol = provider_symbol(ticker, market)
    fetch_period = "max" if as_of else period

    def fetch() -> dict:
        df = provider.get_ohlcv(symbol, fetch_period)
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        df = df.astype(object).where(df.notna(), None)  # NaN is not valid JSON (Postgres rejects it)
        return {"rows": df.to_dict("records")}

    payload, src = _cached(db, provider, symbol, "prices", fetch_period, fetch, now, ttl)
    df = pd.DataFrame(payload["rows"])
    ref = as_of or now.date()
    if as_of:  # replay: drop everything after as_of, then trim to requested lookback
        df = df[pd.to_datetime(df["date"]) <= pd.Timestamp(as_of)]
        days = _period_days(period)
        if days:
            df = df[pd.to_datetime(df["date"]) >= pd.Timestamp(as_of) - pd.Timedelta(days=days)]
    clean, report = validate_ohlcv(df, reference_date=ref)
    if src.stale_cache:
        report.issues.append(Issue(code="provider_unavailable", severity="warning",
                                   message="Live fetch failed; serving cached snapshot"))
    rows = clean.assign(date=clean["date"].dt.strftime("%Y-%m-%d")).to_dict("records")
    if rows:
        _log_source(db, task_id, "price", f"{symbol} OHLCV {period} via {src.provider}", src,
                    f"rows={len(rows)} range={rows[0]['date']}..{rows[-1]['date']} "
                    + last_close_line(rows[-1]["date"], rows[-1]["close"]))
    return PriceResult(ticker=normalize_ticker(ticker), market=market.upper(), symbol=symbol, period=period,
                       as_of=as_of, rows=rows, validation=report, source=src)


def get_financials(db: Session, provider: MarketDataProvider, ticker: str, market: str = "NSE",
                   task_id=None, now: datetime | None = None, ttl: timedelta = DEFAULT_TTL) -> FinancialsResult:
    now = now or datetime.now(timezone.utc)
    symbol = provider_symbol(ticker, market)
    payload, src = _cached(db, provider, symbol, "financials", "", lambda: provider.get_financials(symbol), now, ttl)
    issues = validate_financials(payload)
    if src.stale_cache:
        issues.append(Issue(code="provider_unavailable", severity="warning",
                            message="Live fetch failed; serving cached snapshot"))
    _log_source(db, task_id, "financials", f"{symbol} financial statements via {src.provider}", src,
                financials_excerpt(payload.get("annual", [])))
    return FinancialsResult(ticker=normalize_ticker(ticker), market=market.upper(), symbol=symbol,
                            data=payload, issues=issues, source=src)
