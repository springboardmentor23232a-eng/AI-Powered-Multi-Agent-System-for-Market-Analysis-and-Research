from datetime import datetime
from ..database import SessionLocal
from ..models import (ResearchTask, ResearchReport, SourceDocument, AgentResult, utcnow)
from .market_data import get_history, MarketDataError


def run_research_stub(task_id: int):
    """TEMPORARY: price data asli hai, analysis abhi placeholder. Baad mein LangGraph supervisor."""
    db = SessionLocal()
    try:
        task = db.get(ResearchTask, task_id)
        if task is None:
            return
        task.status = "processing"
        db.commit()

        try:
            res = get_history(task.ticker, task.requested_period)
        except MarketDataError as e:
            db.add(AgentResult(task_id=task_id, agent_name="market_data",
                               status="failed", error_message=str(e)))
            task.status = "failed"
            task.completed_at = utcnow()
            db.commit()
            return

        db.add(SourceDocument(
            task_id=task_id, source_type="market_data",
            title=f"{task.ticker} OHLCV ({task.requested_period})",
            source_url=res.meta["source_url"],
            retrieved_at=datetime.fromisoformat(res.meta["retrieved_at"]),
            content_hash=res.meta["content_hash"],
        ))
        db.add(AgentResult(task_id=task_id, agent_name="market_data", status="completed",
                           output_json={"meta": res.meta, "validation": res.validation}))

        first, last = float(res.df["Close"].iloc[0]), float(res.df["Close"].iloc[-1])
        change = (last / first - 1) * 100
        warnings = [i["message"] for i in res.validation["issues"]]

        db.add(ResearchReport(
            task_id=task_id,
            report_content=(
                f"# Research Report: {task.ticker}\n\n"
                f"Market: {task.market} | Period: {task.requested_period}\n\n"
                f"## Price data (calculated)\n"
                f"- Trading days: {res.validation['rows_clean']}\n"
                f"- First close: {first:.2f} | Latest close: {last:.2f}\n"
                f"- Change over period: {change:+.2f}%\n\n"
                f"Source: {res.meta['provider']}, retrieved {res.meta['retrieved_at']}\n\n"
                "_Fundamental, technical, news and risk analysis will be added by agents (Week 3-6)._"
            ),
            summary=f"{task.ticker}: {change:+.2f}% over {task.requested_period}",
            limitations="; ".join(warnings) or "No data-quality issues detected.",
        ))
        task.status = "completed"
        task.completed_at = utcnow()
        db.commit()
    except Exception:
        db.rollback()
        task = db.get(ResearchTask, task_id)
        if task:
            task.status = "failed"
            task.completed_at = utcnow()
            db.commit()
    finally:
        db.close()