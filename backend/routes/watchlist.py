from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, SavedStock
from routes.authentication import get_current_user
from pydantic import BaseModel


router = APIRouter(
    prefix="/watchlist",
    tags=["Watchlist"]
)

class StockCreate(BaseModel):
    ticker: str
    market: str = "NSI"

@router.get("/")
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    saved_stocks = db.query(SavedStock).filter(
        SavedStock.user_id == current_user.id
    ).order_by(
        SavedStock.created_at.desc()
    ).all()

    return saved_stocks

@router.post("/", status_code=status.HTTP_201_CREATED)
def add_stock(
    stock_data: StockCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticker = stock_data.ticker.strip().upper()

    # Validate the stock symbol
    if not ticker or len(ticker) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid stock ticker"
        )

    # Check whether this stock is already saved
    existing_stock = db.query(SavedStock).filter(
        SavedStock.user_id == current_user.id,
        SavedStock.ticker == ticker
    ).first()

    if existing_stock:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Stock is already in your watchlist"
        )

    # Create a new saved stock
    new_stock = SavedStock(
    user_id=current_user.id,
    ticker=ticker,
    market=stock_data.market
)

    db.add(new_stock)
    db.commit()
    db.refresh(new_stock)

    return new_stock

@router.delete("/{ticker}")
def remove_stock(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticker = ticker.strip().upper()

    saved_stock = db.query(SavedStock).filter(
        SavedStock.user_id == current_user.id,
        SavedStock.ticker == ticker
    ).first()

    if not saved_stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found in your watchlist"
        )

    db.delete(saved_stock)
    db.commit()

    return {
        "message": f"{ticker} removed from your watchlist"
    }
