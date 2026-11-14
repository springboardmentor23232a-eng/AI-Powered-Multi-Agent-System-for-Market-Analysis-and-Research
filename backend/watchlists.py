from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from market_data import has_price_data, resolve_ticker
from models import SavedStock, User, UserPreference, Watchlist
from schemas import (
    SavedStockMove,
    SavedStockOut,
    StockAdd,
    WatchlistCreate,
    WatchlistOut,
)

router = APIRouter(tags=["watchlists"])

DEFAULT_LISTS = ["Long Term", "Short Term"]


def _load_lists(db: Session, user_id: int):
    return db.scalars(
        select(Watchlist)
        .where(Watchlist.user_id == user_id)
        .order_by(Watchlist.created_at, Watchlist.watchlist_id)
    ).all()


def _to_out(db: Session, wl: Watchlist) -> dict:
    stocks = db.scalars(
        select(SavedStock)
        .where(SavedStock.watchlist_id == wl.watchlist_id)
        .order_by(SavedStock.created_at.desc())
    ).all()
    return {
        "watchlist_id": wl.watchlist_id,
        "name": wl.name,
        "created_at": wl.created_at,
        "stocks": [SavedStockOut.model_validate(s) for s in stocks],
    }


def _owned_list(db: Session, watchlist_id: int, user_id: int) -> Watchlist:
    wl = db.scalar(
        select(Watchlist).where(
            Watchlist.watchlist_id == watchlist_id, Watchlist.user_id == user_id
        )
    )
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return wl


def _owned_stock(db: Session, saved_stock_id: int, user_id: int) -> SavedStock:
    row = db.scalar(
        select(SavedStock).where(
            SavedStock.saved_stock_id == saved_stock_id, SavedStock.user_id == user_id
        )
    )
    if not row:
        raise HTTPException(status_code=404, detail="Saved stock not found")
    return row


# ---------- Watchlists ----------
@router.get("/watchlists", response_model=list[WatchlistOut])
def list_watchlists(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    lists = _load_lists(db, current_user.user_id)
    if not lists:  # first visit: create the two default lists
        try:
            for name in DEFAULT_LISTS:
                db.add(Watchlist(user_id=current_user.user_id, name=name))
            db.commit()
        except IntegrityError:  # two requests raced; the other one created them
            db.rollback()
        lists = _load_lists(db, current_user.user_id)
    return [_to_out(db, wl) for wl in lists]


@router.post("/watchlists", response_model=WatchlistOut, status_code=status.HTTP_201_CREATED)
def create_watchlist(
    data: WatchlistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Watchlist name cannot be empty")

    exists = db.scalar(
        select(Watchlist).where(
            Watchlist.user_id == current_user.user_id,
            func.lower(Watchlist.name) == name.lower(),
        )
    )
    if exists:
        raise HTTPException(status_code=409, detail="You already have a watchlist with that name")

    wl = Watchlist(user_id=current_user.user_id, name=name)
    db.add(wl)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="You already have a watchlist with that name")
    db.refresh(wl)
    return _to_out(db, wl)


@router.delete("/watchlists/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watchlist(
    watchlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wl = _owned_list(db, watchlist_id, current_user.user_id)
    db.delete(wl)  # the stocks inside are removed by the database (ON DELETE CASCADE)
    db.commit()


# ---------- Stocks inside a watchlist ----------
@router.post(
    "/watchlists/{watchlist_id}/stocks",
    response_model=SavedStockOut,
    status_code=status.HTTP_201_CREATED,
)
def add_stock(
    watchlist_id: int,
    data: StockAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wl = _owned_list(db, watchlist_id, current_user.user_id)

    pref = db.get(UserPreference, current_user.user_id)
    stock = resolve_ticker(data.ticker, pref.market if pref else None)
    if not stock:
        raise HTTPException(
            status_code=400,
            detail="Unknown or unsupported ticker. Only equities on NSE, BSE, NASDAQ and NYSE are supported.",
        )

    exists = db.scalar(
        select(SavedStock).where(
            SavedStock.watchlist_id == wl.watchlist_id,
            SavedStock.ticker == stock["ticker"],
        )
    )
    if exists:
        raise HTTPException(status_code=409, detail=f"{stock['name']} is already in {wl.name}")

    # Companies Yahoo has no recent prices for (delisted, merged, suspended) can't be analysed
    if has_price_data(stock["ticker"]) is False:
        raise HTTPException(
            status_code=400,
            detail=(
                f"No recent market data from Yahoo Finance for {stock['ticker']}. "
                "It may be delisted, merged, suspended or not supported, "
                "or Yahoo may be temporarily unavailable. It was not added."
            ),
        )

    row = SavedStock(
        user_id=current_user.user_id,
        watchlist_id=wl.watchlist_id,
        ticker=stock["ticker"],
        company_name=stock["name"],
        market=stock["market"],
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"{stock['name']} is already in {wl.name}")
    db.refresh(row)
    return row


@router.patch("/saved-stocks/{saved_stock_id}", response_model=SavedStockOut)
def move_stock(
    saved_stock_id: int,
    data: SavedStockMove,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = _owned_stock(db, saved_stock_id, current_user.user_id)
    target = _owned_list(db, data.watchlist_id, current_user.user_id)

    duplicate = db.scalar(
        select(SavedStock).where(
            SavedStock.watchlist_id == target.watchlist_id,
            SavedStock.ticker == row.ticker,
        )
    )
    if duplicate:
        raise HTTPException(status_code=409, detail=f"{row.company_name} is already in {target.name}")

    row.watchlist_id = target.watchlist_id
    db.commit()
    db.refresh(row)
    return row


@router.delete("/saved-stocks/{saved_stock_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_stock(
    saved_stock_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = _owned_stock(db, saved_stock_id, current_user.user_id)
    db.delete(row)
    db.commit()