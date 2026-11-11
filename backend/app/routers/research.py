import json
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models.preference import UserPreference
from app.models.research_report import ResearchReport
from app.models.research_task import ResearchTask
from app.models.saved_stock import SavedStock
from app.models.user import User
from app.schemas.research import (
    DashboardOverviewResponse,
    ResearchCreateRequest,
    ResearchReportResponse,
    ResearchTaskResponse,
)
from app.schemas.saved_stock import SavedStockResponse
from app.services.auth_service import get_current_user
from app.services.research_engine import execute_research_task_background
from app.services.stock_data_service import StockDataService

router = APIRouter(prefix="/research", tags=["Research"])


@router.post("", response_model=ResearchTaskResponse, status_code=status.HTTP_201_CREATED)
def start_research_task(
    req: ResearchCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Initiate a new stock research task for the authenticated user.
    Falls back to user preferences for market and analysis period if not provided.
    Enqueues the research coordinator pipeline as an asynchronous background worker.
    """
    # 1. Fetch user preferences for defaults
    user_pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.user_id).first()
    preferred_market = user_pref.preferred_market if user_pref else "NASDAQ"
    preferred_period = user_pref.analysis_period if user_pref else "1 Year"

    market = req.market or preferred_market
    analysis_period = req.analysis_period or preferred_period

    # 2. Resolve company name if not provided
    company_name = req.company_name
    if not company_name:
        profile = StockDataService.get_stock_profile(req.ticker, market)
        company_name = profile.get("company_name", req.ticker)

    # 3. Create task in Pending state
    task = ResearchTask(
        user_id=current_user.user_id,
        company_name=company_name,
        ticker=req.ticker,
        market=market,
        analysis_period=analysis_period,
        status="Pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 4. Trigger asynchronous engine pipeline
    background_tasks.add_task(execute_research_task_background, task.task_id)

    task_dict = {
        "task_id": task.task_id,
        "user_id": task.user_id,
        "company_name": task.company_name,
        "ticker": task.ticker,
        "market": task.market,
        "analysis_period": task.analysis_period,
        "status": task.status,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "error_message": task.error_message,
        "has_report": False
    }
    return task_dict


@router.get("/history", response_model=List[ResearchTaskResponse])
def get_research_history(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    sort: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch research records belonging exclusively to the authenticated user.
    Supports filtering by status, search by ticker or company name, and date sorting.
    """
    query = db.query(ResearchTask).filter(ResearchTask.user_id == current_user.user_id)

    if status_filter:
        query = query.filter(ResearchTask.status.ilike(status_filter.strip()))

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(or_(ResearchTask.ticker.ilike(s), ResearchTask.company_name.ilike(s)))

    if sort == "asc":
        query = query.order_by(ResearchTask.created_at.asc())
    else:
        query = query.order_by(ResearchTask.created_at.desc())

    tasks = query.all()

    # Determine which tasks have a generated report
    result = []
    for t in tasks:
        result.append(ResearchTaskResponse(
            task_id=t.task_id,
            user_id=t.user_id,
            company_name=t.company_name,
            ticker=t.ticker,
            market=t.market,
            analysis_period=t.analysis_period,
            status=t.status,
            created_at=t.created_at,
            updated_at=t.updated_at,
            error_message=t.error_message,
            has_report=t.report is not None
        ))
    return result


@router.get("/dashboard/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Aggregate all dashboard statistics, recent research activities,
    and watchlist preview strictly for the authenticated user from PostgreSQL.
    """
    # Research counts
    user_tasks_q = db.query(ResearchTask).filter(ResearchTask.user_id == current_user.user_id)
    total_research = user_tasks_q.count()
    completed_research = user_tasks_q.filter(ResearchTask.status == "Completed").count()
    pending_research = user_tasks_q.filter(ResearchTask.status.in_(["Pending", "Processing"])).count()
    failed_research = user_tasks_q.filter(ResearchTask.status == "Failed").count()

    # Saved stocks count
    saved_stocks_q = db.query(SavedStock).filter(SavedStock.user_id == current_user.user_id)
    total_saved_stocks = saved_stocks_q.count()

    # Recent activities (last 5)
    recent_tasks = user_tasks_q.order_by(ResearchTask.created_at.desc()).limit(5).all()
    recent_list = [
        ResearchTaskResponse(
            task_id=t.task_id,
            user_id=t.user_id,
            company_name=t.company_name,
            ticker=t.ticker,
            market=t.market,
            analysis_period=t.analysis_period,
            status=t.status,
            created_at=t.created_at,
            updated_at=t.updated_at,
            error_message=t.error_message,
            has_report=t.report is not None
        )
        for t in recent_tasks
    ]

    # Watchlist preview (first 5)
    watchlist_items = saved_stocks_q.order_by(SavedStock.created_at.desc()).limit(5).all()
    watchlist_preview = [SavedStockResponse.model_validate(s) for s in watchlist_items]

    return DashboardOverviewResponse(
        total_research=total_research,
        completed_research=completed_research,
        pending_research=pending_research,
        failed_research=failed_research,
        total_saved_stocks=total_saved_stocks,
        recent_research=recent_list,
        watchlist_preview=watchlist_preview
    )


@router.get("/{task_id}", response_model=ResearchTaskResponse)
def get_research_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve details for a specific research task, enforcing strict user authorization."""
    task = db.query(ResearchTask).filter(ResearchTask.task_id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research task not found."
        )

    # Security check: User can only access their own tasks
    if task.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this research task."
        )

    return ResearchTaskResponse(
        task_id=task.task_id,
        user_id=task.user_id,
        company_name=task.company_name,
        ticker=task.ticker,
        market=task.market,
        analysis_period=task.analysis_period,
        status=task.status,
        created_at=task.created_at,
        updated_at=task.updated_at,
        error_message=task.error_message,
        has_report=task.report is not None
    )


@router.get("/{task_id}/report", response_model=ResearchReportResponse)
def get_research_report(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Open and view previously generated research report.
    Enforces user authorization and handles pending/failed states.
    """
    task = db.query(ResearchTask).filter(ResearchTask.task_id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research task not found."
        )

    # Security check
    if task.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this report."
        )

    if task.status in ["Pending", "Processing"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Research report is currently being generated. Please wait a moment."
        )

    if task.status == "Failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Research task failed: {task.error_message or 'Unknown error'}"
        )

    report = db.query(ResearchReport).filter(ResearchReport.task_id == task_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No report content found for this task."
        )

    # Parse JSON report content
    try:
        content = json.loads(report.report_content)
    except Exception:
        content = report.report_content

    return ResearchReportResponse(
        report_id=report.report_id,
        task_id=report.task_id,
        report_content=content,
        created_at=report.created_at
    )
