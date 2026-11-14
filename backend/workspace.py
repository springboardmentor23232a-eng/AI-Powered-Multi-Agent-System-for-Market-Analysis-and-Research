from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from market_data import get_price_history, get_stock_info, search_stocks_live
from models import ResearchTask, User, UserPreference
from schemas import (
    Period,
    PreferencesIn,
    PreferencesOut,
    PriceHistory,
    ResearchStart,
    ResearchTaskOut,
    StockOut,
)

router = APIRouter(tags=["workspace"])


# ---------- Preferences ----------
@router.get("/preferences", response_model=PreferencesOut)
def get_preferences(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    pref = db.get(UserPreference, current_user.user_id)
    if not pref:
        return {"market": "NSE", "analysis_period": "1Y"}
    return pref


@router.put("/preferences", response_model=PreferencesOut)
def save_preferences(
    data: PreferencesIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pref = db.get(UserPreference, current_user.user_id)
    if pref:
        pref.market = data.market
        pref.analysis_period = data.analysis_period
    else:
        pref = UserPreference(
            user_id=current_user.user_id,
            market=data.market,
            analysis_period=data.analysis_period,
        )
        db.add(pref)
    db.commit()
    db.refresh(pref)
    return pref


# ---------- Stock search and price history ----------
@router.get("/stocks/search", response_model=list[StockOut])
def stock_search(
    q: str = "",
    market: str | None = None,
    current_user: User = Depends(get_current_user),
):
    return search_stocks_live(q, market)


@router.get("/stocks/{ticker}/history", response_model=PriceHistory)
def stock_history(
    ticker: str,
    period: Period | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stock = get_stock_info(ticker)
    if not stock:
        raise HTTPException(status_code=400, detail="Unknown or unverifiable ticker")

    if period is None:
        pref = db.get(UserPreference, current_user.user_id)
        period = pref.analysis_period if pref else "1Y"

    try:
        points = get_price_history(stock["ticker"], period)
    except Exception:
        raise HTTPException(status_code=502, detail="Market data provider unavailable")

    return {
        "ticker": stock["ticker"],
        "name": stock["name"],
        "market": stock["market"],
        "period": period,
        "points": points,
    }


# ---------- Research history ----------
@router.post("/research", response_model=ResearchTaskOut, status_code=status.HTTP_201_CREATED)
def start_research(
    data: ResearchStart,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stock = get_stock_info(data.ticker)
    if not stock:
        raise HTTPException(status_code=400, detail="Unknown or unverifiable ticker")

    pref = db.get(UserPreference, current_user.user_id)
    period = pref.analysis_period if pref else "1Y"

    task = ResearchTask(
        user_id=current_user.user_id,
        company_name=stock["name"],
        ticker=stock["ticker"],
        market=stock["market"],
        analysis_period=period,
        status="Pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/research", response_model=list[ResearchTaskOut])
def research_history(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return db.scalars(
        select(ResearchTask)
        .where(ResearchTask.user_id == current_user.user_id)
        .order_by(ResearchTask.created_at.desc())
    ).all()