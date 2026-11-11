from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.saved_stock import SavedStock
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.saved_stock import SavedStockCreate, SavedStockResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])


@router.get("", response_model=List[SavedStockResponse])
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all saved stocks belonging exclusively to the authenticated user."""
    stocks = (
        db.query(SavedStock)
        .filter(SavedStock.user_id == current_user.user_id)
        .order_by(SavedStock.created_at.desc())
        .all()
    )
    return stocks


@router.post("", response_model=SavedStockResponse, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    stock_in: SavedStockCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a stock to user's watchlist, preventing duplicate records."""
    existing = (
        db.query(SavedStock)
        .filter(
            SavedStock.user_id == current_user.user_id,
            SavedStock.ticker == stock_in.ticker,
            SavedStock.market == stock_in.market
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Stock '{stock_in.ticker}' ({stock_in.market}) is already in your watchlist."
        )

    saved_stock = SavedStock(
        user_id=current_user.user_id,
        company_name=stock_in.company_name.strip(),
        ticker=stock_in.ticker,
        market=stock_in.market
    )
    db.add(saved_stock)
    db.commit()
    db.refresh(saved_stock)
    return saved_stock


@router.delete("/{saved_stock_id}", response_model=MessageResponse)
def remove_from_watchlist(
    saved_stock_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a stock from the watchlist, strictly verifying ownership."""
    stock = (
        db.query(SavedStock)
        .filter(
            SavedStock.saved_stock_id == saved_stock_id,
            SavedStock.user_id == current_user.user_id
        )
        .first()
    )
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found in your watchlist."
        )

    db.delete(stock)
    db.commit()
    return MessageResponse(success=True, message=f"Stock '{stock.ticker}' removed from watchlist.")

