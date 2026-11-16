from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.watchlist import (
    SavedStockCreate,
    SavedStockResponse,
    WatchlistResponse,
)
from app.services.watchlist_service import (
    add_stock_to_watchlist,
    get_user_watchlist,
    remove_stock_from_watchlist,
)

router = APIRouter(
    prefix="/watchlist",
    tags=["Watchlist & Saved Stocks"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "",
    response_model=SavedStockResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a stock ticker to authenticated user's watchlist",
    description="Saves a normalized ticker to the current user's watchlist. Enforces uniqueness per user.",
)
def add_to_watchlist(
    payload: SavedStockCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavedStockResponse:
    """
    Saves a stock ticker under the authenticated user's identity.
    Returns HTTP 409 if the stock is already in the user's watchlist.
    """
    return add_stock_to_watchlist(db=db, user=current_user, payload=payload)


@router.get(
    "",
    response_model=WatchlistResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve authenticated user's saved stocks",
    description="Returns all stocks saved in the current user's watchlist.",
)
def get_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WatchlistResponse:
    """
    Retrieves the user's watchlist. User ID is extracted directly from the verified JWT.
    """
    stocks = get_user_watchlist(db=db, user_id=current_user.user_id)
    return WatchlistResponse(
        status="success",
        count=len(stocks),
        data=stocks,
    )


@router.delete(
    "/{saved_stock_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove a stock from authenticated user's watchlist",
    description="Removes a saved stock record. Returns 404 if the record does not exist or belongs to another user.",
)
def remove_from_watchlist(
    saved_stock_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Removes a stock from the watchlist with strict ownership enforcement.
    """
    return remove_stock_from_watchlist(
        db=db,
        user_id=current_user.user_id,
        saved_stock_id=saved_stock_id,
    )

