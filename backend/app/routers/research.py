from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from ..database import get_db
from ..deps import get_current_user
from ..models import User, UserPreference, ResearchTask
from ..schemas import ResearchCreate, ResearchOut, ResearchDetail
from ..services.tickers import normalize_ticker
from ..services.research_runner import run_research_stub

router = APIRouter(prefix="/research", tags=["research"])


@router.post("", response_model=ResearchOut, status_code=201)
def start_research(data: ResearchCreate, background: BackgroundTasks,
                   db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    pref = db.get(UserPreference, user.user_id)
    market = data.market or (pref.market if pref else "NSE")
    period = data.analysis_period or (pref.analysis_period if pref else "1y")

    task = ResearchTask(
        user_id=user.user_id,                       # JWT se, browser se nahi
        ticker=normalize_ticker(data.ticker, market),
        company_name=data.company_name,
        market=market,
        requested_period=period,
        status="pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    background.add_task(run_research_stub, task.task_id)
    return task


@router.get("", response_model=list[ResearchOut])
def my_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(ResearchTask).where(ResearchTask.user_id == user.user_id)
                      .order_by(ResearchTask.created_at.desc()).limit(100)).all()


@router.get("/{task_id}", response_model=ResearchDetail)
def open_report(task_id: int, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    task = db.scalar(select(ResearchTask).options(selectinload(ResearchTask.report))
                     .where(ResearchTask.task_id == task_id,
                            ResearchTask.user_id == user.user_id))
    if not task:
        raise HTTPException(404, "Research task not found.")  # dusre ka task bhi 404
    return task