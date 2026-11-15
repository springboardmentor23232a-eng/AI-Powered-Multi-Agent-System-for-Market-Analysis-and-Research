"""Saved stocks (watchlist) endpoints."""

from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import CurrentUser, DbSession
from app.schemas import SavedStockCreate, SavedStockOut
from app.services import watchlist_service

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("", response_model=list[SavedStockOut])
def list_watchlist(current_user: CurrentUser, db: DbSession):
    return watchlist_service.list_saved_stocks(db, current_user)


@router.post("", response_model=SavedStockOut, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(data: SavedStockCreate, current_user: CurrentUser, db: DbSession):
    try:
        return watchlist_service.add_saved_stock(db, current_user, data)
    except watchlist_service.StockAlreadySavedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from None
    except watchlist_service.WatchlistFullError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from None


@router.delete("/{saved_stock_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_watchlist(saved_stock_id: int, current_user: CurrentUser, db: DbSession):
    # 404 both when the item does not exist and when it belongs to someone else,
    # so a user cannot discover other users' saved stock IDs.
    if not watchlist_service.remove_saved_stock(db, current_user, saved_stock_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved stock not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
