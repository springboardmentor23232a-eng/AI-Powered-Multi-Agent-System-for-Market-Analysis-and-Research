from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import catalog
from ..database import get_db
from ..deps import get_current_user
from ..models import SavedStock, User
from ..schemas import Market, ResearchTaskOut, StockOut, WatchlistAdd, WatchlistItemOut
from .preferences import get_or_create_prefs
from .research import create_task

router = APIRouter(prefix="/api", tags=["watchlist"])


@router.get("/stocks/search", response_model=list[StockOut])
def search_stocks(q: str = Query(..., min_length=1, max_length=50), market: Market | None = None,
                  limit: int = Query(10, ge=1, le=25), _: User = Depends(get_current_user)):
    """Search the validated ticker list by company name or ticker symbol."""
    return [StockOut(ticker=s.ticker, name=s.name, market=s.market) for s in catalog.search(q, market, limit)]


@router.get("/watchlist", response_model=list[WatchlistItemOut])
def list_watchlist(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(SavedStock).where(SavedStock.user_id == user.user_id)
                      .order_by(desc(SavedStock.created_at), desc(SavedStock.saved_stock_id))).all()


@router.post("/watchlist", response_model=WatchlistItemOut, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(body: WatchlistAdd, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prefs = get_or_create_prefs(db, user)
    stock = catalog.lookup(body.ticker, body.market, prefer_market=prefs.market)
    if stock is None:
        raise HTTPException(422,
                            f"'{body.ticker}' is not a supported ticker. Use the search box to find one.")
    # user_id comes from the JWT, never from the request body
    if db.scalar(select(SavedStock).where(SavedStock.user_id == user.user_id, SavedStock.ticker == stock.ticker)):
        raise HTTPException(status.HTTP_409_CONFLICT, f"{stock.ticker} is already in your watchlist.")
    item = SavedStock(user_id=user.user_id, ticker=stock.ticker, company_name=stock.name, market=stock.market)
    db.add(item)
    try:
        db.commit()
    except IntegrityError:  # unique constraint (race condition)
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, f"{stock.ticker} is already in your watchlist.")
    db.refresh(item)
    return item


def _own_item(db: Session, user: User, saved_stock_id: int) -> SavedStock:
    item = db.scalar(select(SavedStock).where(SavedStock.saved_stock_id == saved_stock_id, SavedStock.user_id == user.user_id))
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Saved stock not found.")
    return item


@router.delete("/watchlist/{saved_stock_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_watchlist(saved_stock_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(_own_item(db, user, saved_stock_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/watchlist/{saved_stock_id}/research", response_model=ResearchTaskOut, status_code=status.HTTP_201_CREATED)
def research_saved_stock(saved_stock_id: int, background: BackgroundTasks,
                         user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Start a new research task for a saved stock (uses its market + the user's saved analysis period)."""
    item = _own_item(db, user, saved_stock_id)
    return create_task(db, user, item.ticker, item.market, None, background)
