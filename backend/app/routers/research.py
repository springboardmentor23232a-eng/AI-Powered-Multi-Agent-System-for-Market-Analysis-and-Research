from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import market as mkt
from ..database import get_db
from ..deps import get_current_user
from ..models import ResearchTask, User, UserPreference
from ..schemas import ResearchDetail, ResearchIn, ResearchOut

router = APIRouter(prefix="/research", tags=["research"])


def _out(task: ResearchTask, schema):
    obj = schema.model_validate(task)
    obj.has_report = bool(task.report)
    return obj


@router.get("", response_model=list[ResearchOut])
def history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # user identity always comes from the verified JWT, never from the request
    stmt = select(ResearchTask).where(ResearchTask.user_id == user.user_id).order_by(ResearchTask.created_at.desc())
    return [_out(t, ResearchOut) for t in db.scalars(stmt)]


@router.get("/{task_id}", response_model=ResearchDetail)
def open_report(task_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.scalar(select(ResearchTask).where(ResearchTask.task_id == task_id, ResearchTask.user_id == user.user_id))
    if not task:
        raise HTTPException(404, "Research task not found")
    return _out(task, ResearchDetail)


@router.post("", response_model=ResearchOut, status_code=201)
def start_research(data: ResearchIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    pref = db.get(UserPreference, user.user_id)
    period = pref.analysis_period if pref else "1Y"
    try:
        ticker = mkt.normalize_symbol(data.ticker, data.market)
    except ValueError as e:
        raise HTTPException(422, str(e))
    try:
        valid = mkt.has_price_data(ticker, period)
    except Exception:
        raise HTTPException(502, "Market data provider is unavailable right now")
    if not valid:
        raise HTTPException(422, f"{ticker} has no price data for the selected analysis period")
    task = ResearchTask(
        user_id=user.user_id, company_name=data.company_name[:200], ticker=ticker,
        market=data.market, analysis_period=period, status="Pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _out(task, ResearchOut)
