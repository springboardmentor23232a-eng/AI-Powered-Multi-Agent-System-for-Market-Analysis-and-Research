import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, ResearchTask, UserPreference
from app.schemas import ResearchTaskCreate, ResearchTaskOut
from app.auth import get_current_user
from app.mock_data import resolve_stock_info
from app.research_engine import generate_multi_agent_research_report

router = APIRouter(prefix="/research", tags=["Research Tasks & History"])

def _format_task_response(task: ResearchTask) -> dict:
    report_dict = None
    if task.report_data:
        try:
            report_dict = json.loads(task.report_data)
        except Exception:
            report_dict = {"raw": task.report_data}

    return {
        "task_id": task.task_id,
        "user_id": task.user_id,
        "ticker": task.ticker,
        "company_name": task.company_name,
        "market": task.market,
        "analysis_period": task.analysis_period,
        "status": task.status,
        "report_summary": task.report_summary,
        "report_data": report_dict,
        "created_at": task.created_at
    }

@router.get("/tasks")
def get_user_research_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve research tasks strictly associated with the authenticated user ID.
    Enforces security requirement: user_id is derived exclusively from JWT.
    """
    tasks = (
        db.query(ResearchTask)
        .filter(ResearchTask.user_id == current_user.user_id)
        .order_by(ResearchTask.created_at.desc())
        .all()
    )
    return [_format_task_response(t) for t in tasks]


@router.post("/tasks", status_code=status.HTTP_201_CREATED)
def start_research_task(
    task_in: ResearchTaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initiate an autonomous stock research task for the authenticated user:
    1. Resolves company and default market/period from preferences if omitted.
    2. Synthesizes multi-agent valuation, technical, and sentiment research.
    3. Persists task and full report in database.
    """
    clean_ticker = task_in.ticker.strip().upper()

    # Determine user preferences
    pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.user_id).first()
    default_market = pref.market if pref else "NASDAQ"
    default_period = pref.analysis_period if pref else "1 Year"

    market = task_in.market or default_market
    analysis_period = task_in.analysis_period or default_period

    resolved = resolve_stock_info(clean_ticker, preferred_market=market)
    company_name = task_in.company_name or resolved["company_name"]

    # Generate multi-agent research report
    report_json = generate_multi_agent_research_report(
        ticker=clean_ticker,
        company_name=company_name,
        market=market,
        analysis_period=analysis_period
    )

    summary_text = report_json.get("executive_summary", f"Completed research report for {clean_ticker}")

    new_task = ResearchTask(
        user_id=current_user.user_id,
        ticker=clean_ticker,
        company_name=company_name,
        market=market,
        analysis_period=analysis_period,
        status="Completed",
        report_summary=summary_text,
        report_data=json.dumps(report_json)
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return _format_task_response(new_task)


@router.get("/tasks/{task_id}")
def get_task_report(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch complete research task and multi-agent report for a given task ID."""
    task = (
        db.query(ResearchTask)
        .filter(ResearchTask.task_id == task_id, ResearchTask.user_id == current_user.user_id)
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research task not found or you do not have permission to view it."
        )

    return _format_task_response(task)
