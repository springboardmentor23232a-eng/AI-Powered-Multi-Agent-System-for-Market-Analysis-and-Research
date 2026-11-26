"""Stock search + market data endpoints (Milestone 1).

GET /api/stocks/search?q=&market=                    (in watchlist.py)
GET /api/stocks/{market}/{ticker}/history?period=    OHLCV + validation report + source/timestamp
GET /api/stocks/{market}/{ticker}/profile            company profile (missing fields listed)
GET /api/stocks/{market}/{ticker}/financials         annual statements (income / balance / cash flow)
GET /api/stocks/sources                              my recent data retrievals (source + timestamp log)
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from .. import catalog
from ..database import get_db
from ..deps import get_current_user
from ..market_data import MarketDataError, fetch_financials, fetch_ohlcv, fetch_profile
from ..models import SourceDocument, User
from ..schemas import (FinancialsOut, HistoryOut, Market, OHLCVRow, Period, ProfileOut, SourceDocOut, SourceInfo)
from ..sources import record_source
from ..validation import validate_ohlcv

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stocks", tags=["market data"])


def _stock(market: str, ticker: str, period: str = "1Y") -> catalog.Stock:
    try:
        return catalog.validate_research_request(ticker, market, period)
    except ValueError as exc:
        raise HTTPException(422, str(exc))


def _source(f) -> SourceInfo:
    return SourceInfo(name=f.source, url=f.source_url, retrieved_at=f.retrieved_at, synthetic=f.synthetic)


@router.get("/sources", response_model=list[SourceDocOut])
def my_recent_sources(limit: int = Query(20, ge=1, le=100), user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """Newest first. Only this user's own retrievals (user id from the JWT)."""
    return db.scalars(select(SourceDocument).where(SourceDocument.user_id == user.user_id)
                      .order_by(desc(SourceDocument.retrieved_at), desc(SourceDocument.source_id)).limit(limit)).all()


@router.get("/{market}/{ticker}/history", response_model=HistoryOut)
def price_history(market: Market, ticker: str, period: Period = "1Y",
                  user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stock = _stock(market, ticker, period)
    try:
        fetched = fetch_ohlcv(stock, period)
    except MarketDataError as exc:
        raise HTTPException(502, str(exc))
    bars, report = validate_ohlcv(fetched.data)
    record_source(db, stock, "ohlcv", fetched, user_id=user.user_id, record_count=len(bars), quality=report)
    if not report["usable"]:
        raise HTTPException(502, f"Price data for {stock.ticker} failed validation: only {len(bars)} valid rows.")
    return HistoryOut(
        ticker=stock.ticker, name=stock.name, market=stock.market, currency=catalog.MARKET_INFO[stock.market]["currency"],
        period=period, source=_source(fetched), validation=report,
        rows=[OHLCVRow(date=b.date.isoformat(), open=b.open, high=b.high, low=b.low, close=b.close, volume=b.volume)
              for b in bars],
    )


@router.get("/{market}/{ticker}/profile", response_model=ProfileOut)
def company_profile(market: Market, ticker: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stock = _stock(market, ticker)
    try:
        fetched = fetch_profile(stock)
    except MarketDataError as exc:
        raise HTTPException(502, str(exc))
    profile = fetched.data
    missing = [k for k, v in profile.items() if v is None]
    record_source(db, stock, "profile", fetched, user_id=user.user_id, record_count=1,
                  quality={"missing_fields": missing})
    return ProfileOut(profile=profile, missing_fields=missing, source=_source(fetched),
                      warning=("Some profile details are not available from the data provider." if missing else None))


@router.get("/{market}/{ticker}/financials", response_model=FinancialsOut)
def financial_statements(market: Market, ticker: str, user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    stock = _stock(market, ticker)
    try:
        fetched = fetch_financials(stock)
    except MarketDataError as exc:
        raise HTTPException(502, str(exc))
    fin = fetched.data
    record_source(db, stock, "financials", fetched, user_id=user.user_id, record_count=len(fin["periods"]),
                  quality={"missing_metrics": fin["missing_metrics"]})
    return FinancialsOut(financials=fin, source=_source(fetched))
