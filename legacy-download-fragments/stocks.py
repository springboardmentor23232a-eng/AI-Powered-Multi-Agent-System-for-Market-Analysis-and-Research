from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.database import get_db
from app.data.universe import UNIVERSE, search_universe
from app.models import User
from app.services import market_data
from app.services.market_data import ProviderError, YahooProvider

router = APIRouter(prefix="/stocks", tags=["stocks"])


def get_provider():
    return YahooProvider()


def _check(ticker: str) -> str:
    t = market_data.normalize_ticker(ticker)
    if t not in UNIVERSE:
        raise HTTPException(404, f"{t} is not in the supported NSE research universe")
    return t


@router.get("/search")
def search(q: str = Query(min_length=1), _: User = Depends(current_user)):
    return {"results": search_universe(q)}


@router.get("/{ticker}/prices")
def prices(ticker: str, period: str = "2y", as_of: date | None = None, db: Session = Depends(get_db),
           provider=Depends(get_provider), _: User = Depends(current_user)):
    try:
        return market_data.get_prices(db, provider, _check(ticker), "NSE", period, as_of)
    except ProviderError as exc:
        raise HTTPException(502, f"Market data unavailable: {exc}")


@router.get("/{ticker}/financials")
def financials(ticker: str, db: Session = Depends(get_db), provider=Depends(get_provider),
               _: User = Depends(current_user)):
    try:
        return market_data.get_financials(db, provider, _check(ticker), "NSE")
    except ProviderError as exc:
        raise HTTPException(502, f"Financial data unavailable: {exc}")
