import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..market import normalize_symbol
from ..models import DataCollection, PriceBar
from .providers.base import MarketDataProvider
from .validation import validate_and_clean

log = logging.getLogger(__name__)


class NoUsableData(Exception):
    pass


def _optional(fn, *args, default=None):
    """Profiles and statements are best effort: a failure here does not fail the collection."""
    try:
        return fn(*args) or default
    except Exception as e:
        log.warning("optional data unavailable for %s: %s", args, e)
        return default


def collect(db: Session, provider: MarketDataProvider, user_id: int, ticker: str,
            company_name: str | None, market: str, period: str) -> DataCollection:
    symbol = normalize_symbol(ticker, market)          # ValueError for a bad format
    raw = provider.history(symbol, period)             # SymbolNotFound / ProviderError
    retrieved_at = datetime.now(timezone.utc)
    clean, report = validate_and_clean(raw)
    if clean.empty:
        raise NoUsableData(f"None of the {report['rows_in']} rows for {symbol} passed validation")

    profile = _optional(provider.profile, symbol)
    financials = _optional(provider.financials, symbol, default={})
    name = (profile or {}).get("name") or company_name or symbol

    collection = DataCollection(
        user_id=user_id, ticker=symbol, company_name=name[:200], market=market, analysis_period=period,
        source=provider.name, retrieved_at=retrieved_at, rows_raw=report["rows_in"], rows_clean=report["rows_out"],
        status="Cleaned" if report["issues"] else "Clean", report=report, profile=profile, financials=financials,
    )
    db.add(collection)
    db.flush()
    db.bulk_save_objects([
        PriceBar(collection_id=collection.collection_id, date=r.date, open=r.open, high=r.high,
                 low=r.low, close=r.close, volume=int(r.volume))
        for r in clean.itertuples(index=False)
    ])
    db.commit()
    db.refresh(collection)
    return collection
