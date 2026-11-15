"""Business logic for a user's saved stocks (watchlist).

Module 1 validates the ticker *format* only. Checking that the company really
exists on the chosen market needs market data, which arrives in Module 2.
"""

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import SavedStock, User
from app.schemas import SavedStockCreate

MAX_SAVED_STOCKS_PER_USER = 100


class StockAlreadySavedError(Exception):
    pass


class WatchlistFullError(Exception):
    pass


def list_saved_stocks(db: Session, user: User) -> list[SavedStock]:
    query = (
        select(SavedStock)
        .where(SavedStock.user_id == user.user_id)
        .order_by(SavedStock.created_at.desc(), SavedStock.saved_stock_id.desc())
    )
    return list(db.scalars(query))


def add_saved_stock(db: Session, user: User, data: SavedStockCreate) -> SavedStock:
    existing = db.scalar(
        select(SavedStock).where(
            SavedStock.user_id == user.user_id,
            SavedStock.ticker == data.ticker,
            SavedStock.market == data.market,
        )
    )
    if existing is not None:
        raise StockAlreadySavedError(f"{data.ticker} ({data.market}) is already saved")

    current_count = db.scalar(
        select(func.count()).select_from(SavedStock).where(SavedStock.user_id == user.user_id)
    )
    if current_count >= MAX_SAVED_STOCKS_PER_USER:
        raise WatchlistFullError(f"A watchlist can hold at most {MAX_SAVED_STOCKS_PER_USER} stocks")

    stock = SavedStock(user_id=user.user_id, ticker=data.ticker, market=data.market)
    db.add(stock)
    try:
        db.commit()
    except IntegrityError as exc:  # same stock added twice at the same moment
        db.rollback()
        raise StockAlreadySavedError(f"{data.ticker} ({data.market}) is already saved") from exc
    db.refresh(stock)
    return stock


def remove_saved_stock(db: Session, user: User, saved_stock_id: int) -> bool:
    """Delete one of the user's saved stocks. Returns False if it is not theirs or not found."""
    stock = db.scalar(
        select(SavedStock).where(
            SavedStock.saved_stock_id == saved_stock_id,
            SavedStock.user_id == user.user_id,  # users can never touch each other's data
        )
    )
    if stock is None:
        return False
    db.delete(stock)
    db.commit()
    return True
