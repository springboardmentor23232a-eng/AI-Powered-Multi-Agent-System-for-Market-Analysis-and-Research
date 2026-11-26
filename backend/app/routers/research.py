import json
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.agent_result import AgentResult
from app.models.preference import UserPreference
from app.models.research_report import ResearchReport
from app.models.research_task import ResearchTask
from app.models.saved_stock import SavedStock
from app.models.source_document import SourceDocument
from app.models.user import User
from app.schemas.research import (
    AgentResultResponse,
    DashboardOverviewResponse,
    ResearchCreateRequest,
    ResearchReportResponse,
    ResearchTaskResponse,
    SourceDocumentResponse,
)
from app.schemas.saved_stock import SavedStockResponse
from app.services.auth_service import get_current_user
from app.services.research_engine import (
    execute_research_task_background,
    render_markdown_report,
)
from app.services.stock_data_service import StockDataService

router = APIRouter(prefix="/research", tags=["Research"])


def _task_to_response(t: ResearchTask) -> ResearchTaskResponse:
    return ResearchTaskResponse(
        task_id=t.task_id,
        user_id=t.user_id,
        company_name=t.company_name,
        ticker=t.ticker,
        market=t.market,
        analysis_period=t.analysis_period,
        status=t.status,
        created_at=t.created_at,
        updated_at=t.updated_at,
        completed_at=t.completed_at,
        error_message=t.error_message,
        has_report=t.report is not None,
    )


def _get_authorized_task(task_id: int, db: Session, current_user: User) -> ResearchTask:
    task = db.query(ResearchTask).filter(ResearchTask.task_id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research task not found.",
        )
    if task.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this research task.",
        )
    return task


@router.post("", response_model=ResearchTaskResponse, status_code=status.HTTP_201_CREATED)
def start_research_task(
    req: ResearchCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Initiate a new stock research task for the authenticated user.
    Falls back to user preferences for market and analysis period if not provided.
    Enqueues the multi-agent research coordinator pipeline as a background worker.
    """
    user_pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.user_id).first()
    preferred_market = user_pref.preferred_market if user_pref else "NASDAQ"
    preferred_period = user_pref.analysis_period if user_pref else "1 Year"

    market = req.market or preferred_market
    analysis_period = req.analysis_period or preferred_period

    company_name = req.company_name
    if not company_name:
        profile = StockDataService.get_stock_profile(req.ticker, market)
        company_name = profile.get("company_name", req.ticker)

    task = ResearchTask(
        user_id=current_user.user_id,
        company_name=company_name,
        ticker=req.ticker,
        market=market,
        analysis_period=analysis_period,
        status="Pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    background_tasks.add_task(execute_research_task_background, task.task_id)

    return _task_to_response(task)


@router.get("/history", response_model=List[ResearchTaskResponse])
def get_research_history(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    sort: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    return [_task_to_response(t) for t in tasks]


@router.get("/dashboard/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Aggregate dashboard statistics, recent research activities,
    and watchlist preview strictly for the authenticated user.
    """
    user_tasks_q = db.query(ResearchTask).filter(ResearchTask.user_id == current_user.user_id)
    total_research = user_tasks_q.count()
    completed_research = user_tasks_q.filter(ResearchTask.status == "Completed").count()
    pending_research = user_tasks_q.filter(ResearchTask.status.in_(["Pending", "Processing"])).count()
    failed_research = user_tasks_q.filter(ResearchTask.status == "Failed").count()

    saved_stocks_q = db.query(SavedStock).filter(SavedStock.user_id == current_user.user_id)
    total_saved_stocks = saved_stocks_q.count()

    recent_tasks = user_tasks_q.order_by(ResearchTask.created_at.desc()).limit(5).all()
    recent_list = [_task_to_response(t) for t in recent_tasks]

    watchlist_items = saved_stocks_q.order_by(SavedStock.created_at.desc()).limit(5).all()
    watchlist_preview = [SavedStockResponse.model_validate(s) for s in watchlist_items]

    return DashboardOverviewResponse(
        total_research=total_research,
        completed_research=completed_research,
        pending_research=pending_research,
        failed_research=failed_research,
        total_saved_stocks=total_saved_stocks,
        recent_research=recent_list,
        watchlist_preview=watchlist_preview,
    )


@router.get("/{task_id}", response_model=ResearchTaskResponse)
def get_research_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve details for a specific research task, enforcing strict user authorization."""
    task = _get_authorized_task(task_id, db, current_user)
    return _task_to_response(task)


@router.get("/{task_id}/report", response_model=ResearchReportResponse)
def get_research_report(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Open and view previously generated research report."""
    task = _get_authorized_task(task_id, db, current_user)

    if task.status in ["Pending", "Processing"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Research report is currently being generated. Please wait a moment.",
        )

    if task.status == "Failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Research task failed: {task.error_message or 'Unknown error'}",
        )

    report = db.query(ResearchReport).filter(ResearchReport.task_id == task_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No report content found for this task.",
        )

    try:
        content = json.loads(report.report_content)
    except Exception:
        content = report.report_content

    return ResearchReportResponse(
        report_id=report.report_id,
        task_id=report.task_id,
        report_content=content,
        summary=report.summary,
        limitations=report.limitations,
        created_at=report.created_at,
    )


@router.get("/{task_id}/agents", response_model=List[AgentResultResponse])
def get_task_agent_results(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve individual persisted AgentResult rows for a research task."""
    _get_authorized_task(task_id, db, current_user)
    rows = (
        db.query(AgentResult)
        .filter(AgentResult.task_id == task_id)
        .order_by(AgentResult.result_id.asc())
        .all()
    )
    results: List[AgentResultResponse] = []
    for r in rows:
        parsed_out = None
        if r.output_json:
            try:
                parsed_out = json.loads(r.output_json)
            except Exception:
                parsed_out = r.output_json
        results.append(AgentResultResponse(
            result_id=r.result_id,
            task_id=r.task_id,
            agent_name=r.agent_name,
            status=r.status,
            output_json=parsed_out,
            error_message=r.error_message,
            execution_time_ms=r.execution_time_ms,
            created_at=r.created_at,
        ))
    return results


@router.get("/{task_id}/sources", response_model=List[SourceDocumentResponse])
def get_task_source_documents(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve recorded data provenance SourceDocument rows for a research task."""
    _get_authorized_task(task_id, db, current_user)
    docs = (
        db.query(SourceDocument)
        .filter(SourceDocument.task_id == task_id)
        .order_by(SourceDocument.source_id.asc())
        .all()
    )
    return [SourceDocumentResponse.model_validate(d) for d in docs]


@router.get("/{task_id}/export/markdown")
def export_research_report_markdown(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download the structured research report as a Markdown (.md) file."""
    task = _get_authorized_task(task_id, db, current_user)
    report = db.query(ResearchReport).filter(ResearchReport.task_id == task_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No report found to export.",
        )

    try:
        content = json.loads(report.report_content)
    except Exception:
        content = {}

    md = render_markdown_report(task, content if isinstance(content, dict) else {})
    filename = f"{task.ticker}_{task.market}_research_report.md"
    return Response(
        content=md,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
