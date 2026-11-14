from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, SavedStock, UserPreference
from app.schemas import SavedStockCreate, SavedStockOut
from app.auth import get_current_user
from app.mock_data import search_stocks, resolve_stock_info

router = APIRouter(prefix="/watchlist", tags=["Saved Stocks & Watchlists"])

@router.get("/search")
def search_tickers(
    q: str = Query(..., min_length=1, description="Ticker or company name query"),
    market: Optional[str] = Query(None, description="Optional market filter"),
    current_user: User = Depends(get_current_user)
):
    """Search known stock tickers by symbol or company name."""
    results = search_stocks(query=q, market=market)
    return {"results": results}


@router.get("", response_model=List[SavedStockOut])
def get_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all saved stocks belonging exclusively to the authenticated user."""
    stocks = (
        db.query(SavedStock)
        .filter(SavedStock.user_id == current_user.user_id)
        .order_by(SavedStock.created_at.desc())
        .all()
    )
    return stocks


@router.post("", response_model=SavedStockOut, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    stock_in: SavedStockCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a stock to user's personal watchlist.
    Prevents duplicate entries for the same user and ticker.
    """
    clean_ticker = stock_in.ticker.strip().upper()

    # Check for existing duplicate
    existing = (
        db.query(SavedStock)
        .filter(SavedStock.user_id == current_user.user_id, SavedStock.ticker == clean_ticker)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock {clean_ticker} is already in your watchlist."
        )

    # Determine user preference default market if not provided
    default_market = "NASDAQ"
    user_pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.user_id).first()
    if user_pref and user_pref.market:
        default_market = user_pref.market

    resolved = resolve_stock_info(clean_ticker, preferred_market=default_market)
    company_name = stock_in.company_name or resolved["company_name"]
    market = stock_in.market or resolved["market"]

    saved_stock = SavedStock(
        user_id=current_user.user_id,
        ticker=clean_ticker,
        company_name=company_name,
        market=market
    )
    db.add(saved_stock)
    db.commit()
    db.refresh(saved_stock)
    return saved_stock


@router.delete("/{saved_stock_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_watchlist(
    saved_stock_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a stock from the authenticated user's watchlist."""
    stock = (
        db.query(SavedStock)
        .filter(SavedStock.saved_stock_id == saved_stock_id, SavedStock.user_id == current_user.user_id)
        .first()
    )
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found in your watchlist."
        )

    db.delete(stock)
    db.commit()
    return None
