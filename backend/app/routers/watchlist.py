from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, SavedStock
from app.schemas import WatchlistAddRequest, WatchlistItemResponse
from app.auth import get_current_user

router = APIRouter(prefix="/watchlist", tags=["Watchlist (Saved Stocks)"])


@router.get("", response_model=List[WatchlistItemResponse])
def get_user_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the personal watchlist of the currently authenticated user
    from the PostgreSQL saved_stocks table.
    If none exist yet, automatically seeds default top stocks in PostgreSQL.
    """
    saved = db.query(SavedStock).filter(SavedStock.user_id == current_user.user_id).order_by(SavedStock.created_at.desc()).all()
    
    if not saved:
        default_stocks = [
            ("RELIANCE", "Reliance Industries Ltd", "NSE"),
            ("TCS", "Tata Consultancy Services", "NSE"),
            ("INFY", "Infosys Limited", "NSE"),
            ("HDFCBANK", "HDFC Bank Limited", "NSE"),
            ("AAPL", "Apple Inc.", "NASDAQ"),
        ]
        created = []
        for ticker, name, market in default_stocks:
            stock = SavedStock(
                user_id=current_user.user_id,
                ticker=ticker,
                company_name=name,
                market=market
            )
            db.add(stock)
            created.append(stock)
        db.commit()
        for stock in created:
            db.refresh(stock)
        return created

    return saved


@router.post("", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    request: WatchlistAddRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Saves a stock ticker to the user's personal watchlist.
    Enforces uniqueness so duplicate entries are rejected.
    """
    ticker_clean = request.ticker.strip().upper()

    # Check for duplicate
    existing = db.query(SavedStock).filter(
        SavedStock.user_id == current_user.user_id,
        SavedStock.ticker == ticker_clean
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{ticker_clean} is already in your watchlist."
        )

    new_stock = SavedStock(
        user_id=current_user.user_id,
        ticker=ticker_clean,
        company_name=request.company_name or ticker_clean,
        market=request.market or "NSE"
    )

    db.add(new_stock)
    db.commit()
    db.refresh(new_stock)
    return new_stock


@router.delete("/{ticker}", status_code=status.HTTP_200_OK)
def remove_from_watchlist(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Removes a stock from the authenticated user's watchlist in PostgreSQL.
    """
    ticker_clean = ticker.strip().upper()
    stock_record = db.query(SavedStock).filter(
        SavedStock.user_id == current_user.user_id,
        SavedStock.ticker == ticker_clean
    ).first()

    if not stock_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{ticker_clean} was not found in your watchlist."
        )

    db.delete(stock_record)
    db.commit()
    return {"message": f"{ticker_clean} removed from your watchlist successfully."}
