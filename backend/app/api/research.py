import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.api.stocks import get_provider
from app.core.config import settings
from app.core.database import SessionLocal, get_db
from app.data.universe import UNIVERSE
from app.graph.workflow import Deps
from app.models import (AgentResult, Claim, Contradiction, ResearchReport, ResearchTask, TaskStatus, User)
from app.schemas.research import ResearchRequest, ResearchTaskOut
from app.services import market_data
from app.services.llm import build_llm
from app.services.news import build_news_provider
from app.services.research import execute_task

router = APIRouter(prefix="/research", tags=["research"])


def get_session_factory():
    return SessionLocal


def get_news_provider():
    return build_news_provider()


def get_llm():
    return build_llm()


def _enforce_quotas(db: Session, user: User) -> None:
    """Protect LLM and data-provider cost: limit concurrent and daily research per user."""
    active = db.scalar(select(func.count()).select_from(ResearchTask).where(
        ResearchTask.user_id == user.user_id, ResearchTask.status.in_([TaskStatus.queued, TaskStatus.running]))) or 0
    if active >= settings.max_active_tasks_per_user:
        raise HTTPException(429, f"You already have {active} research tasks running. Wait for one to finish.")
    since = datetime.now(timezone.utc) - timedelta(days=1)
    today = db.scalar(select(func.count()).select_from(ResearchTask).where(
        ResearchTask.user_id == user.user_id, ResearchTask.created_at >= since)) or 0
    if today >= settings.max_tasks_per_day:
        raise HTTPException(429, f"Daily limit of {settings.max_tasks_per_day} research tasks reached.")


def _own_task(db: Session, user: User, task_id: uuid.UUID) -> ResearchTask:
    task = db.get(ResearchTask, task_id)
    if task is None or task.user_id != user.user_id:
        raise HTTPException(404, "Research task not found")
    return task


@router.post("", status_code=202, response_model=ResearchTaskOut)
def create_research(body: ResearchRequest, background: BackgroundTasks, db: Session = Depends(get_db),
                    user: User = Depends(current_user), market=Depends(get_provider),
                    news=Depends(get_news_provider), llm=Depends(get_llm), factory=Depends(get_session_factory)):
    ticker = market_data.normalize_ticker(body.ticker)
    if ticker not in UNIVERSE:
        raise HTTPException(404, f"{ticker} is not in the supported NSE research universe")
    if body.market.upper() != "NSE":
        raise HTTPException(422, "Only the NSE market is supported")
    if body.as_of_date_in_future():
        raise HTTPException(422, "as_of must be a past date")
    _enforce_quotas(db, user)
    period = body.period or (user.preferences or {}).get("analysis_period") or "2y"
    task = ResearchTask(user_id=user.user_id, ticker=ticker, market="NSE", requested_period=period,
                        as_of_date=datetime.combine(body.as_of, datetime.min.time(), tzinfo=timezone.utc)
                        if body.as_of else None)
    db.add(task)
    db.commit()
    background.add_task(execute_task, task.task_id, Deps(session_factory=factory, market=market, news=news, llm=llm))
    return ResearchTaskOut(
        task_id=task.task_id,
        ticker=task.ticker,
        company_name=UNIVERSE.get(task.ticker),
        market=task.market,
        requested_period=task.requested_period,
        status=task.status.value if hasattr(task.status, "value") else str(task.status),
        created_at=task.created_at,
        completed_at=task.completed_at,
    )


@router.get("", response_model=list[ResearchTaskOut])
def history(limit: int = Query(50, le=200), db: Session = Depends(get_db), user: User = Depends(current_user)):
    tasks = db.scalars(select(ResearchTask).where(ResearchTask.user_id == user.user_id)
                      .order_by(ResearchTask.created_at.desc()).limit(limit)).all()
    return [
        ResearchTaskOut(
            task_id=t.task_id,
            ticker=t.ticker,
            company_name=UNIVERSE.get(t.ticker),
            market=t.market,
            requested_period=t.requested_period,
            status=t.status.value if hasattr(t.status, "value") else str(t.status),
            created_at=t.created_at,
            completed_at=t.completed_at,
        )
        for t in tasks
    ]


@router.get("/{task_id}")
def detail(task_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    task = _own_task(db, user, task_id)
    agents = db.scalars(select(AgentResult).where(AgentResult.task_id == task_id)).all()
    total = db.scalar(select(func.count()).select_from(Claim).where(Claim.task_id == task_id)) or 0
    ok = db.scalar(select(func.count()).select_from(Claim).where(Claim.task_id == task_id, Claim.verified.is_(True))) or 0
    return {
        "task_id": task.task_id, "ticker": task.ticker, "market": task.market, "period": task.requested_period,
        "as_of": task.as_of_date.date() if task.as_of_date else None, "status": task.status.value,
        "created_at": task.created_at, "completed_at": task.completed_at, "latency_ms": task.latency_ms,
        "tokens_used": task.tokens_used, "error": task.error_message,
        "agents": [{"agent": a.agent_name, "status": a.status.value, "attempts": a.attempts,
                    "latency_ms": a.latency_ms, "error": a.error_message} for a in agents],
        "evidence": {"total": total, "verified": ok, "percent": round(100 * ok / total, 1) if total else 0.0},
    }


@router.get("/{task_id}/report")
def report(task_id: uuid.UUID, format: str = Query("json", pattern="^(json|md)$"), db: Session = Depends(get_db),
           user: User = Depends(current_user)):
    task = _own_task(db, user, task_id)
    if task.status in (TaskStatus.queued, TaskStatus.running):
        raise HTTPException(409, "Research is still running")
    rep = db.scalar(select(ResearchReport).where(ResearchReport.task_id == task_id))
    if rep is None:
        raise HTTPException(404, "No report was produced for this task")
    if format == "md":
        name = f"{task.ticker}_research_report_{rep.created_at:%Y%m%d}.md"
        return PlainTextResponse(rep.report_content, media_type="text/markdown",
                                 headers={"Content-Disposition": f'attachment; filename="{name}"'})
    return {"report_id": rep.report_id, "summary": rep.summary, "limitations": rep.limitations,
            "content": rep.report_content, "created_at": rep.created_at}


@router.get("/{task_id}/claims")
def claims(task_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    _own_task(db, user, task_id)
    rows = db.scalars(select(Claim).where(Claim.task_id == task_id).order_by(Claim.agent_name, Claim.ref)).all()
    return [{"claim_id": c.ref, "agent": c.agent_name, "type": c.claim_type.value, "text": c.text,
             "evidence": c.evidence, "verified": c.verified, "note": c.verification_note} for c in rows]


@router.get("/{task_id}/contradictions")
def contradictions(task_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    _own_task(db, user, task_id)
    rows = db.scalars(select(Contradiction).where(Contradiction.task_id == task_id)).all()
    return [{"agent_a": c.agent_a, "agent_b": c.agent_b, "severity": c.severity, "description": c.description}
            for c in rows]


@router.get("/{task_id}/agents/{name}")
def agent_output(task_id: uuid.UUID, name: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    _own_task(db, user, task_id)
    row = db.scalar(select(AgentResult).where(AgentResult.task_id == task_id, AgentResult.agent_name == name))
    if row is None:
        raise HTTPException(404, "Agent result not found")
    return {"agent": name, "status": row.status.value, "attempts": row.attempts, "error": row.error_message,
            **(row.output_json or {})}
