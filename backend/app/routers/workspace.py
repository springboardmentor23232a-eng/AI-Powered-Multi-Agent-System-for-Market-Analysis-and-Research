import re
from datetime import datetime, timezone
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user, require_csrf_for_cookie_auth
from ..models import (
    ResearchReport,
    ResearchTask,
    SavedStock,
    User,
    UserPreference,
)
from ..services.yahoo_finance import yahoo_finance_service

from ..schemas import (
    MARKETS,
    PERIODS,
    PreferenceResponse,
    PreferenceUpdate,
    ResearchReportResponse,
    ResearchTaskCreate,
    ResearchTaskResponse,
    SavedStockResponse,
    StockCreate,
)

router = APIRouter(
    prefix="/api",
    tags=["research workspace"],
    dependencies=[Depends(require_csrf_for_cookie_auth)],
)

MARKET_EXCHANGES = {
    "NSE": ("NSE",),
    "BSE": ("BSE",),
    "NASDAQ": ("Nasdaq",),
    "NYSE": ("NYSE",),
}


def get_or_create_preferences(db: Session, user_id: UUID) -> UserPreference:
    preferences = db.scalar(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    if preferences is None:
        preferences = UserPreference(user_id=user_id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    return preferences


@router.get("/stocks/search")
def search_stocks(
    q: str = Query(min_length=1, max_length=80),
    market: str = Query(default="NSE"),
    current_user: User = Depends(get_current_user),
):
    market = market.strip().upper()
    if market != "ALL" and market not in MARKETS:
        raise HTTPException(status_code=422, detail="Unsupported stock market.")

    try:
        results = yahoo_finance_service.search(q.strip(), market=market)
        return results[:10]
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Market data provider unavailable: {e}")



@router.get("/watchlist", response_model=list[SavedStockResponse])
def get_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list(
        db.scalars(
            select(SavedStock)
            .where(SavedStock.user_id == current_user.user_id)
            .order_by(SavedStock.created_at.desc())
        ).all()
    )


@router.post(
    "/watchlist",
    response_model=SavedStockResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_to_watchlist(
    payload: StockCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticker = payload.ticker.strip().upper()
    existing = db.scalar(
        select(SavedStock).where(
            SavedStock.user_id == current_user.user_id,
            SavedStock.ticker == ticker,
            SavedStock.market == payload.market,
        )
    )
    if existing:
        raise HTTPException(
            status_code=409, detail="This stock is already in your watchlist."
        )

    saved = SavedStock(
        user_id=current_user.user_id,
        ticker=ticker,
        company_name=payload.company_name.strip(),
        market=payload.market,
    )
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return saved


@router.delete("/watchlist/{saved_stock_id}", response_model=dict)
def remove_from_watchlist(
    saved_stock_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    saved = db.scalar(
        select(SavedStock).where(
            SavedStock.saved_stock_id == saved_stock_id,
            SavedStock.user_id == current_user.user_id,
        )
    )
    if saved is None:
        raise HTTPException(status_code=404, detail="Saved stock not found.")
    db.delete(saved)
    db.commit()
    return {"message": "Stock removed from your watchlist."}


@router.get("/preferences", response_model=PreferenceResponse)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_or_create_preferences(db, current_user.user_id)


@router.put("/preferences", response_model=PreferenceResponse)
def update_preferences(
    payload: PreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    preferences = get_or_create_preferences(db, current_user.user_id)
    preferences.market = payload.market
    preferences.analysis_period = payload.analysis_period
    preferences.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(preferences)
    return preferences


@router.get("/research-tasks", response_model=list[ResearchTaskResponse])
def get_research_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list(
        db.scalars(
            select(ResearchTask)
            .where(ResearchTask.user_id == current_user.user_id)
            .order_by(ResearchTask.created_at.desc())
        ).all()
    )


@router.post(
    "/research-tasks",
    response_model=ResearchTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_research_task(
    payload: ResearchTaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticker = payload.ticker.strip().upper()
    if not re.fullmatch(r"[A-Z0-9.-]{1,30}", ticker):
        raise HTTPException(status_code=422, detail="Please enter a valid stock ticker.")

    preferences = get_or_create_preferences(db, current_user.user_id)
    market = (payload.market or preferences.market).upper()
    period = payload.analysis_period or preferences.analysis_period
    if market not in MARKETS:
        raise HTTPException(status_code=422, detail="Unsupported stock market.")
    if period not in PERIODS:
        raise HTTPException(status_code=422, detail="Unsupported analysis period.")

    task = ResearchTask(
        user_id=current_user.user_id,
        ticker=ticker,
        company_name=payload.company_name.strip(),
        market=market,
        analysis_period=period,
        status="Pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get(
    "/research-tasks/{task_id}/report",
    response_model=ResearchReportResponse,
)
def get_research_report(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.scalar(
        select(ResearchTask).where(
            ResearchTask.task_id == task_id,
            ResearchTask.user_id == current_user.user_id,
        )
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Research task not found.")

    report = db.scalar(
        select(ResearchReport).where(ResearchReport.task_id == task_id)
    )
    if report is None:
        raise HTTPException(
            status_code=404,
            detail="A report has not been generated for this task yet.",
        )
    return report
