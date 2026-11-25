from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import User, SavedStock
from ..schemas import WatchlistAdd, SavedStockOut

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("", response_model=list[SavedStockOut])
def list_saved(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(SavedStock).where(SavedStock.user_id == user.user_id)
                      .order_by(SavedStock.created_at.desc())).all()


@router.post("", response_model=SavedStockOut, status_code=201)
def add_saved(data: WatchlistAdd, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    exists = db.scalar(select(SavedStock).where(
        SavedStock.user_id == user.user_id, SavedStock.ticker == data.ticker))
    if exists:
        raise HTTPException(409, f"{data.ticker} is already in your watchlist.")
    stock = SavedStock(user_id=user.user_id, ticker=data.ticker,
                       company_name=data.company_name, market=data.market)
    db.add(stock)
    try:
        db.commit()
    except IntegrityError:          # do requests ek saath aayein to DB constraint bachayega
        db.rollback()
        raise HTTPException(409, f"{data.ticker} is already in your watchlist.")
    db.refresh(stock)
    return stock


@router.delete("/{saved_stock_id}", status_code=204)
def remove_saved(saved_stock_id: int, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    stock = db.scalar(select(SavedStock).where(
        SavedStock.saved_stock_id == saved_stock_id,
        SavedStock.user_id == user.user_id))      # sirf apna record
    if not stock:
        raise HTTPException(404, "Saved stock not found.")
    db.delete(stock)
    db.commit()
    return Response(status_code=204)