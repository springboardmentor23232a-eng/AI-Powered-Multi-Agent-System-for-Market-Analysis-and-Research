import logging
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.saved_stock import SavedStock
from app.models.user import User
from app.schemas.watchlist import SavedStockCreate, SavedStockResponse
from app.services.validation_service import validate_ticker_symbol
from app.services.stock_service import PREDEFINED_UNIVERSE

logger = logging.getLogger("uvicorn.error")

# Fast cache/lookup dictionary from predefined universe
PREDEFINED_MAP = {
    item["ticker"].upper(): (item["company_name"], item["exchange"])
    for item in PREDEFINED_UNIVERSE
}


def resolve_stock_display_metadata(ticker: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolves company name and exchange for a given ticker.
    Checks predefined stock universe first, with graceful fallback to exchange inference.
    """
    clean_ticker = ticker.upper()
    if clean_ticker in PREDEFINED_MAP:
        return PREDEFINED_MAP[clean_ticker]

    # Dynamic lookup via yfinance if not predefined
    try:
        import yfinance as yf
        t = yf.Ticker(clean_ticker)
        info = t.info or {}
        company_name = info.get("shortName") or info.get("longName")
        exchange = info.get("exchange")
        if company_name:
            return company_name, exchange
    except Exception:
        pass

    # Fallback exchange inference from ticker suffix
    exchange = "NASDAQ/NYSE"
    if clean_ticker.endswith(".NS"):
        exchange = "NSE"
    elif clean_ticker.endswith(".BO"):
        exchange = "BSE"
    elif clean_ticker.endswith(".L"):
        exchange = "LSE"

    return clean_ticker, exchange


def add_stock_to_watchlist(
    db: Session,
    user: User,
    payload: SavedStockCreate,
) -> SavedStockResponse:
    """
    Adds a normalized stock ticker to the authenticated user's watchlist.
    Validates format, checks for duplicates, and handles uniqueness conflicts.
    """
    clean_ticker = validate_ticker_symbol(payload.ticker)

    # Check for existing entry for this user
    existing = (
        db.query(SavedStock)
        .filter(
            SavedStock.user_id == user.user_id,
            SavedStock.ticker == clean_ticker,
        )
        .first()
    )
    if existing:
        logger.warning(f"User #{user.user_id} attempted to add duplicate ticker '{clean_ticker}'")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Stock '{clean_ticker}' is already in your watchlist.",
        )

    # Create new saved stock record
    saved_stock = SavedStock(
        user_id=user.user_id,
        ticker=clean_ticker,
    )
    db.add(saved_stock)

    try:
        db.commit()
        db.refresh(saved_stock)
    except IntegrityError as exc:
        db.rollback()
        logger.warning(f"IntegrityError on adding watchlist item: {exc}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Stock '{clean_ticker}' is already in your watchlist.",
        )

    company_name, exchange = resolve_stock_display_metadata(clean_ticker)

    logger.info(f"User #{user.user_id} added '{clean_ticker}' to watchlist (ID #{saved_stock.saved_stock_id})")

    return SavedStockResponse(
        saved_stock_id=saved_stock.saved_stock_id,
        user_id=saved_stock.user_id,
        ticker=saved_stock.ticker,
        company_name=company_name,
        exchange=exchange,
        created_at=saved_stock.created_at,
    )


def get_user_watchlist(
    db: Session,
    user_id: int,
) -> List[SavedStockResponse]:
    """
    Retrieves all saved stocks belonging strictly to the authenticated user.
    """
    stocks = (
        db.query(SavedStock)
        .filter(SavedStock.user_id == user_id)
        .order_by(SavedStock.created_at.desc())
        .all()
    )

    results: List[SavedStockResponse] = []
    for s in stocks:
        company_name, exchange = resolve_stock_display_metadata(s.ticker)
        results.append(
            SavedStockResponse(
                saved_stock_id=s.saved_stock_id,
                user_id=s.user_id,
                ticker=s.ticker,
                company_name=company_name,
                exchange=exchange,
                created_at=s.created_at,
            )
        )

    return results


def remove_stock_from_watchlist(
    db: Session,
    user_id: int,
    saved_stock_id: int,
) -> dict:
    """
    Removes a saved stock belonging strictly to the authenticated user.
    Returns HTTP 404 if the record does not exist or belongs to another user.
    """
    stock = (
        db.query(SavedStock)
        .filter(SavedStock.saved_stock_id == saved_stock_id)
        .first()
    )

    if not stock or stock.user_id != user_id:
        logger.warning(
            f"User #{user_id} attempted unauthorized deletion of saved_stock_id #{saved_stock_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved stock not found.",
        )

    removed_ticker = stock.ticker
    db.delete(stock)
    db.commit()

    logger.info(f"User #{user_id} removed stock '{removed_ticker}' (ID #{saved_stock_id}) from watchlist")
    return {
        "status": "success",
        "message": f"Stock '{removed_ticker}' successfully removed from watchlist.",
    }

