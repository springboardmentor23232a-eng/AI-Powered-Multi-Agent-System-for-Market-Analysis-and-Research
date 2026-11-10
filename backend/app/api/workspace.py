import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.database import get_db
from app.data.universe import UNIVERSE
from app.models import SavedStock, User
from app.services.market_data import normalize_ticker

router = APIRouter(tags=["workspace"])


class WatchlistAdd(BaseModel):
    ticker: str = Field(min_length=1, max_length=32)


class Preferences(BaseModel):
    market: str = Field(default="NSE", pattern=r"^(NSE|BSE)$")
    analysis_period: str = Field(default="2y", pattern=r"^\d+(d|mo|y)$")


@router.get("/watchlist")
def get_watchlist(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.scalars(select(SavedStock).where(SavedStock.user_id == user.user_id).order_by(SavedStock.created_at)).all()
    return [{"ticker": r.ticker, "name": UNIVERSE.get(r.ticker), "added_at": r.created_at} for r in rows]


@router.post("/watchlist", status_code=201)
def add_to_watchlist(body: WatchlistAdd, db: Session = Depends(get_db), user: User = Depends(current_user)):
    t = normalize_ticker(body.ticker)
    if t not in UNIVERSE:
        raise HTTPException(404, f"{t} is not in the supported NSE research universe")
    if db.scalar(select(SavedStock).where(SavedStock.user_id == user.user_id, SavedStock.ticker == t)):
        raise HTTPException(409, "Already in watchlist")
    db.add(SavedStock(user_id=user.user_id, ticker=t))
    db.commit()
    return {"ticker": t, "name": UNIVERSE[t]}


@router.delete("/watchlist/{ticker}", status_code=204)
def remove_from_watchlist(ticker: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    row = db.scalar(select(SavedStock).where(SavedStock.user_id == user.user_id,
                                             SavedStock.ticker == normalize_ticker(ticker)))
    if row is None:
        raise HTTPException(404, "Not in watchlist")
    db.delete(row)
    db.commit()


@router.get("/preferences")
def get_preferences(user: User = Depends(current_user)):
    return {"market": "NSE", "analysis_period": "2y", **(user.preferences or {})}


@router.put("/preferences")
def put_preferences(body: Preferences, db: Session = Depends(get_db), user: User = Depends(current_user)):
    market = body.market.upper()
    if market not in ("NSE", "BSE"):
        raise HTTPException(422, "Only the NSE and BSE markets are supported")
    user.preferences = {"market": market, "analysis_period": body.analysis_period}
    db.add(user)
    db.commit()
    return user.preferences
