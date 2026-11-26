"""Research workflow (Module 1 version).

Pending -> Processing -> Completed | Failed.  The later modules replace `_analyse` with the real
multi-agent pipeline; the task bookkeeping (status updates, report saving, failure recording) stays.
"""
import logging
import math
import time
from datetime import datetime, timezone

from .catalog import MARKET_INFO, PERIOD_INFO, lookup
from .config import settings
from .database import SessionLocal
from .agents import build_context, run_all
from .models import AgentResult, ResearchReport, ResearchTask

log = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _sma(values: list[float], n: int):
    return round(sum(values[-n:]) / n, 2) if len(values) >= n else None


def _analyse(task: ResearchTask, db) -> dict:
    stock = lookup(task.ticker, task.market)
    ctx = build_context(stock, task.analysis_period, db=db, user_id=task.user_id, task_id=task.task_id)  # fetch + validate + log source
    fetched, quality, bars = ctx.ohlcv, ctx.quality, ctx.window
    source = fetched.source
    series = [(b.date, b.close) for b in bars]
    closes = [c for _, c in series]
    rets = [math.log(b / a) for a, b in zip(closes, closes[1:])]
    mean = sum(rets) / len(rets)
    vol = math.sqrt(sum((r - mean) ** 2 for r in rets) / max(len(rets) - 1, 1)) * math.sqrt(252)
    change = (closes[-1] / closes[0] - 1) * 100
    cur = MARKET_INFO[task.market]["currency"]
    period_label = PERIOD_INFO[task.analysis_period]["label"]
    stats = {
        "start_date": series[0][0].isoformat(), "end_date": series[-1][0].isoformat(),
        "start_price": closes[0], "latest_price": closes[-1], "currency": cur,
        "period_return_pct": round(change, 2), "period_high": max(closes), "period_low": min(closes),
        "annualised_volatility_pct": round(vol * 100, 2),
        "sma_20": _sma(closes, 20), "sma_50": _sma(closes, 50), "data_points": len(closes),
    }
    agents = run_all(ctx)                      # fundamental -> technical -> news -> risk (Milestone 3 adds the supervisor)
    for name, out in agents.items():
        db.add(AgentResult(task_id=task.task_id, agent_name=name, status=out.status, output=out.model_dump(mode="json"),
                           error_message=out.error))
    db.commit()
    trend = "upward" if change > 0 else "downward"
    summary = (f"{stock.name} ({task.ticker}, {task.market}) moved {change:+.2f}% over the last {period_label.lower()} "
               f"({trend} trend), trading between {min(closes)} and {max(closes)} {cur}. "
               + " ".join(f"[{k.capitalize()}] {v.summary}" for k, v in agents.items() if v.status == "Completed"))
    return {
        "title": f"{stock.name} ({task.ticker}) - {period_label} research report",
        "summary": summary,
        "content": {
            "market": task.market, "analysis_period": task.analysis_period, "data_source": source,
            "data_retrieved_at": fetched.retrieved_at.isoformat(), "data_quality": quality,
            "statistics": stats,
            "price_history": [{"date": b.date.isoformat(), "open": b.open, "high": b.high, "low": b.low,
                               "close": b.close, "volume": b.volume} for b in bars[-250:]],
            "agents": {k: v.model_dump(mode="json", exclude={"chart"} if k == "technical" else None) for k, v in agents.items()},
            "note": "Individual agent analyses (Milestone 2). The Supervisor and consolidated report generation arrive in Milestone 3.",
        },
    }


def run_research_task(task_id: int) -> None:
    """Runs in a background task with its OWN database session."""
    with SessionLocal() as db:
        task = db.get(ResearchTask, task_id)
        if task is None:
            return
        try:
            task.status, task.started_at = "Processing", _now()
            db.commit()
            if settings.workflow_delay_seconds:
                time.sleep(settings.workflow_delay_seconds)
            result = _analyse(task, db)
            db.add(ResearchReport(task_id=task.task_id, **result))
            task.status, task.completed_at, task.error_message = "Completed", _now(), None
            db.commit()
        except Exception as exc:  # record failures clearly
            log.exception("Research task %s failed", task_id)
            db.rollback()
            task = db.get(ResearchTask, task_id)
            task.status, task.completed_at, task.error_message = "Failed", _now(), str(exc)[:500]
            db.commit()
