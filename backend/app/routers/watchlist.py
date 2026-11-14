from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import market as mkt
from ..database import get_db
from ..deps import get_current_user
from ..models import SavedStock, User
from ..schemas import Market, SavedStockOut, StockResult

router = APIRouter(tags=["watchlist"])


@router.get("/stocks/search", response_model=list[StockResult])
def search(q: str = Query(min_length=1, max_length=50), market: Market = "NASDAQ", _: User = Depends(get_current_user)):
    try:
        return mkt.search_stocks(q.strip(), market)
    except Exception:
        raise HTTPException(502, "Market data provider is unavailable right now")


@router.get("/watchlist", response_model=list[SavedStockOut])
def list_saved(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(SavedStock).where(SavedStock.user_id == user.user_id).order_by(SavedStock.created_at.desc())
    return db.scalars(stmt).all()


@router.post("/watchlist", response_model=SavedStockOut, status_code=201)
def add_saved(data: StockResult, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        ticker = mkt.normalize_symbol(data.ticker, data.market)
    except ValueError as e:
        raise HTTPException(422, str(e))
    exists = db.scalar(select(SavedStock).where(SavedStock.user_id == user.user_id, SavedStock.ticker == ticker))
    if exists:
        raise HTTPException(409, f"{ticker} is already in your watchlist")
    try:
        valid = mkt.has_price_data(ticker, "1M")
    except Exception:
        raise HTTPException(502, "Market data provider is unavailable right now")
    if not valid:
        raise HTTPException(422, f"No market data found for {ticker}")
    stock = SavedStock(user_id=user.user_id, ticker=ticker, company_name=data.company_name[:200], market=data.market)
    db.add(stock)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, f"{ticker} is already in your watchlist")
    db.refresh(stock)
    return stock


@router.delete("/watchlist/{saved_stock_id}", status_code=204)
def remove_saved(saved_stock_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stock = db.scalar(select(SavedStock).where(SavedStock.saved_stock_id == saved_stock_id, SavedStock.user_id == user.user_id))
    if not stock:
        raise HTTPException(404, "Saved stock not found")
    db.delete(stock)
    db.commit()
