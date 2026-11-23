import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import (
    PortfolioHolding,
    PortfolioOrder,
    ResearchTask,
    SavedStock,
    SourceDocument,
    User,
    UserPreference,
)
from app.schemas import (
    HoldingResponse,
    MarketType,
    PeriodType,
    PreferenceResponse,
    PreferenceUpdate,
    ResearchRequest,
    ResearchTaskResponse,
    SavedStockCreate,
    SavedStockResponse,
    TradeOrderRequest,
    TradeOrderResponse,
)
from app.services.market_data import (
    fetch_company_fundamentals,
    fetch_stock_history,
    search_companies,
)
from app.services.research_graph import run_stock_research

router = APIRouter(prefix="/api/workspace", tags=["Research Workspace"])


def _serialize_task(task: ResearchTask) -> ResearchTaskResponse:
    report_data = json.loads(task.report_json) if task.report_json else None
    return ResearchTaskResponse(
        task_id=task.task_id,
        ticker=task.ticker,
        company_name=task.company_name,
        market=task.market,
        analysis_period=task.analysis_period,
        status=task.status,
        error_message=task.error_message,
        summary_markdown=task.summary_markdown,
        report_data=report_data,
        created_at=task.created_at,
        completed_at=task.completed_at,
    )


def _record_source(
    db: Session,
    user_id: int,
    ticker: str,
    market: str,
    source_name: str,
    source_url: str,
    data_type: str,
    task_id: int | None = None,
):
    doc = SourceDocument(
        user_id=user_id,
        task_id=task_id,
        ticker=ticker.upper(),
        market=market.upper(),
        source_name=source_name,
        source_url=source_url,
        data_type=data_type,
        retrieved_at=datetime.now(timezone.utc),
    )
    db.add(doc)
    db.commit()


@router.get("/preferences", response_model=PreferenceResponse)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.user_id).first()
    if not pref:
        pref = UserPreference(user_id=current_user.user_id, market="NSE", analysis_period="1Y")
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


@router.put("/preferences", response_model=PreferenceResponse)
def update_preferences(
    payload: PreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.user_id).first()
    if not pref:
        pref = UserPreference(
            user_id=current_user.user_id,
            market=payload.market,
            analysis_period=payload.analysis_period,
        )
        db.add(pref)
    else:
        pref.market = payload.market
        pref.analysis_period = payload.analysis_period
    db.commit()
    db.refresh(pref)
    return pref


@router.get("/stocks/search")
def search_stock(
    query: str = Query(..., min_length=1),
    market: MarketType = Query("NSE"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = search_companies(query=query, market=market)
        _record_source(
            db=db,
            user_id=current_user.user_id,
            ticker=query.upper()[:32],
            market=market,
            source_name=result["data_source"],
            source_url=result["source_url"],
            data_type="COMPANY_SEARCH",
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/stocks/ohlcv")
def get_stock_ohlcv(
    ticker: str = Query(..., min_length=1),
    market: MarketType = Query("NSE"),
    period: PeriodType = Query("1Y"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        data = fetch_stock_history(ticker=ticker, market=market, analysis_period=period)
        _record_source(
            db=db,
            user_id=current_user.user_id,
            ticker=ticker,
            market=market,
            source_name=data["data_source"],
            source_url=data["source_url"],
            data_type="HISTORICAL_OHLCV",
        )
        return data
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/stocks/fundamentals")
def get_stock_fundamentals(
    ticker: str = Query(..., min_length=1),
    market: MarketType = Query("NSE"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        data = fetch_company_fundamentals(ticker=ticker, market=market)
        _record_source(
            db=db,
            user_id=current_user.user_id,
            ticker=ticker,
            market=market,
            source_name=data["data_source"],
            source_url=data["source_url"],
            data_type="PROFILE_AND_FINANCIALS",
        )
        return data
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/watchlist", response_model=list[SavedStockResponse])
def list_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(SavedStock)
        .filter(SavedStock.user_id == current_user.user_id)
        .order_by(SavedStock.created_at.desc())
        .all()
    )


@router.post("/watchlist", response_model=SavedStockResponse, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    payload: SavedStockCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(SavedStock)
        .filter(SavedStock.user_id == current_user.user_id, SavedStock.ticker == payload.ticker)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{payload.ticker} is already in your watchlist.",
        )

    item = SavedStock(
        user_id=current_user.user_id,
        ticker=payload.ticker,
        company_name=payload.company_name or payload.ticker,
        market=payload.market,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/watchlist/{saved_stock_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_watchlist(
    saved_stock_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(SavedStock)
        .filter(
            SavedStock.saved_stock_id == saved_stock_id,
            SavedStock.user_id == current_user.user_id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved stock not found.")
    db.delete(item)
    db.commit()


@router.get("/research", response_model=list[ResearchTaskResponse])
def list_research_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tasks = (
        db.query(ResearchTask)
        .filter(ResearchTask.user_id == current_user.user_id)
        .order_by(ResearchTask.created_at.desc())
        .all()
    )
    return [_serialize_task(t) for t in tasks]


@router.post("/research", response_model=ResearchTaskResponse, status_code=status.HTTP_201_CREATED)
def start_research(
    payload: ResearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.user_id).first()
    market = payload.market or (pref.market if pref else "NSE")
    period = payload.analysis_period or (pref.analysis_period if pref else "1Y")

    task = ResearchTask(
        user_id=current_user.user_id,
        ticker=payload.ticker,
        market=market,
        analysis_period=period,
        status="Processing",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    try:
        output = run_stock_research(ticker=payload.ticker, market=market, analysis_period=period)
        market_data = output["market_data"]
        task.company_name = market_data["company_name"]
        task.report_json = json.dumps(market_data)
        task.summary_markdown = output["analyst_report_md"]
        task.status = "Completed"
        task.completed_at = datetime.now(timezone.utc)
        _record_source(
            db=db,
            user_id=current_user.user_id,
            task_id=task.task_id,
            ticker=payload.ticker,
            market=market,
            source_name=market_data.get("data_source", "Yahoo Finance (yfinance)"),
            source_url=market_data.get("source_url", f"https://finance.yahoo.com/quote/{payload.ticker}"),
            data_type="OHLCV_AND_FINANCIALS",
        )
    except Exception as exc:
        task.status = "Failed"
        task.error_message = str(exc)
        task.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(task)
    return _serialize_task(task)


@router.get("/research/{task_id}", response_model=ResearchTaskResponse)
def get_research_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = (
        db.query(ResearchTask)
        .filter(ResearchTask.task_id == task_id, ResearchTask.user_id == current_user.user_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research task not found.")
    return _serialize_task(task)


@router.get("/portfolio", response_model=list[HoldingResponse])
def list_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(PortfolioHolding)
        .filter(PortfolioHolding.user_id == current_user.user_id, PortfolioHolding.quantity > 0)
        .order_by(PortfolioHolding.updated_at.desc())
        .all()
    )


@router.get("/orders", response_model=list[TradeOrderResponse])
def list_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(PortfolioOrder)
        .filter(PortfolioOrder.user_id == current_user.user_id)
        .order_by(PortfolioOrder.created_at.desc())
        .all()
    )


@router.post("/orders", response_model=TradeOrderResponse, status_code=status.HTTP_201_CREATED)
def place_order(
    payload: TradeOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        quote = fetch_stock_history(ticker=payload.ticker, market=payload.market, analysis_period="1M")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    price = float(quote["metrics"]["latest_price"])
    currency = quote["currency"]
    company_name = quote["company_name"]
    total_amount = round(price * payload.quantity, 2)

    holding = (
        db.query(PortfolioHolding)
        .filter(
            PortfolioHolding.user_id == current_user.user_id,
            PortfolioHolding.ticker == payload.ticker,
            PortfolioHolding.market == payload.market,
        )
        .first()
    )

    if payload.side == "BUY":
        if holding:
            new_qty = holding.quantity + payload.quantity
            holding.average_price = round(
                ((holding.average_price * holding.quantity) + total_amount) / new_qty, 2
            )
            holding.quantity = new_qty
            holding.company_name = company_name
        else:
            holding = PortfolioHolding(
                user_id=current_user.user_id,
                ticker=payload.ticker,
                company_name=company_name,
                market=payload.market,
                quantity=payload.quantity,
                average_price=price,
                currency=currency,
            )
            db.add(holding)
    else:
        if not holding or holding.quantity < payload.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient shares of {payload.ticker} to sell.",
            )
        holding.quantity -= payload.quantity

    order = PortfolioOrder(
        user_id=current_user.user_id,
        ticker=payload.ticker,
        company_name=company_name,
        market=payload.market,
        side=payload.side,
        quantity=payload.quantity,
        price_per_share=price,
        total_amount=total_amount,
        currency=currency,
        status="Executed",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("/sources")
def list_source_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    docs = (
        db.query(SourceDocument)
        .filter(SourceDocument.user_id == current_user.user_id)
        .order_by(SourceDocument.retrieved_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "source_id": d.source_id,
            "task_id": d.task_id,
            "ticker": d.ticker,
            "market": d.market,
            "source_name": d.source_name,
            "source_url": d.source_url,
            "data_type": d.data_type,
            "retrieved_at": d.retrieved_at,
        }
        for d in docs
    ]