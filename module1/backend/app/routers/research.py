from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import desc, exists, select
from sqlalchemy.orm import Session

from .. import catalog
from ..database import get_db
from ..deps import get_current_user
from ..models import ResearchReport, ResearchTask, User
from ..schemas import ReportOut, ResearchCreate, ResearchTaskOut, Status
from ..workflow import run_research_task
from .preferences import get_or_create_prefs

router = APIRouter(prefix="/api/research", tags=["research"])


def to_out(task: ResearchTask, has_report: bool) -> ResearchTaskOut:
    return ResearchTaskOut(
        task_id=task.task_id, ticker=task.ticker, company_name=task.company_name, market=task.market,
        analysis_period=task.analysis_period, status=task.status, research_date=task.created_at,
        completed_at=task.completed_at, error_message=task.error_message, report_available=has_report,
    )


def create_task(db: Session, user: User, ticker: str, market: str | None, period: str | None,
                background: BackgroundTasks) -> ResearchTaskOut:
    """Shared by 'start research' and 'research a saved stock'. Applies saved preferences as defaults."""
    prefs = get_or_create_prefs(db, user)
    market, period = market or prefs.market, period or prefs.analysis_period
    try:
        stock = catalog.validate_research_request(ticker, market, period)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    task = ResearchTask(user_id=user.user_id, ticker=stock.ticker, company_name=stock.name,
                        market=stock.market, analysis_period=period, status="Pending")
    db.add(task)
    db.commit()
    db.refresh(task)
    background.add_task(run_research_task, task.task_id)
    return to_out(task, False)


@router.post("", response_model=ResearchTaskOut, status_code=status.HTTP_201_CREATED)
def start_research(body: ResearchCreate, background: BackgroundTasks,
                   user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return create_task(db, user, body.ticker, body.market, body.analysis_period, background)


@router.get("", response_model=list[ResearchTaskOut])
def list_my_research(status_filter: Status | None = Query(None, alias="status"),
                     limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
                     user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Only the logged-in user's tasks - user id comes from the verified JWT."""
    has_report = exists().where(ResearchReport.task_id == ResearchTask.task_id)
    stmt = select(ResearchTask, has_report).where(ResearchTask.user_id == user.user_id)
    if status_filter:
        stmt = stmt.where(ResearchTask.status == status_filter)
    stmt = stmt.order_by(desc(ResearchTask.created_at), desc(ResearchTask.task_id)).limit(limit).offset(offset)
    return [to_out(t, bool(r)) for t, r in db.execute(stmt).all()]


def _own_task(db: Session, user: User, task_id: int) -> ResearchTask:
    task = db.scalar(select(ResearchTask).where(ResearchTask.task_id == task_id, ResearchTask.user_id == user.user_id))
    if task is None:  # same 404 whether it doesn't exist or belongs to someone else
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Research task not found.")
    return task


@router.get("/{task_id}", response_model=ResearchTaskOut)
def get_task(task_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = _own_task(db, user, task_id)
    return to_out(task, task.report is not None)


@router.get("/{task_id}/report", response_model=ReportOut)
def get_report(task_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = _own_task(db, user, task_id)
    if task.report is None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Report is not available yet (task status: {task.status}).")
    r = task.report
    return ReportOut(task_id=task.task_id, title=r.title, summary=r.summary, content=r.content, created_at=r.created_at)
