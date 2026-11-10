import logging
import time
from datetime import datetime, timezone

from app.graph.workflow import Deps, build_graph
from app.models import AgentResult as AgentResultRow
from app.models import AgentStatus as DbAgentStatus
from app.models import Claim, ClaimType as DbClaimType, Contradiction, ResearchReport, ResearchTask, TaskStatus
from app.schemas.agents import AgentStatus

log = logging.getLogger("veritas.research")
ALL_AGENTS = ("fundamental", "technical", "news", "risk")


def execute_task(task_id, deps: Deps) -> None:
    """Run the workflow for one task and persist everything. Never raises: failures are recorded on the task."""
    with deps.session_factory() as db:
        task = db.get(ResearchTask, task_id)
        task.status = TaskStatus.running
        state = {"ticker": task.ticker, "market": task.market, "period": task.requested_period,
                 "as_of": task.as_of_date.date() if task.as_of_date else None, "task_id": task_id}
        db.commit()
    t0 = time.perf_counter()
    try:
        final = build_graph(deps).invoke(state)
    except Exception as exc:  # noqa: BLE001
        log.exception("research workflow crashed", extra={"task_id": str(task_id)})
        with deps.session_factory() as db:
            task = db.get(ResearchTask, task_id)
            task.status, task.error_message = TaskStatus.failed, f"{type(exc).__name__}: {exc}"[:500]
            task.completed_at = datetime.now(timezone.utc)
            db.commit()
        return

    results, report = final.get("results", {}), final.get("report")
    with deps.session_factory() as db:
        task = db.get(ResearchTask, task_id)
        for name, r in results.items():
            db.add(AgentResultRow(task_id=task_id, agent_name=name, status=DbAgentStatus(r.status.value),
                                  output_json={"data": r.data, "limitations": r.limitations},
                                  error_message=r.error, attempts=r.attempts, latency_ms=r.latency_ms))
        if report:
            for c in final["claims"]:
                db.add(Claim(task_id=task_id, ref=c.claim_id, agent_name=c.agent, claim_type=DbClaimType(c.type.value),
                             text=c.text, evidence=c.evidence.model_dump(mode="json"), verified=c.verified,
                             verification_note=c.verification_note))
            for c in report["contradictions"]:
                db.add(Contradiction(task_id=task_id, agent_a=c.agent_a, agent_b=c.agent_b,
                                     description=c.description, severity=c.severity))
            db.add(ResearchReport(task_id=task_id, report_content=report["content"], summary=report["summary"],
                                  limitations=report["limitations"]))
            ok = all(name in results and results[name].status == AgentStatus.success for name in ALL_AGENTS)
            task.status = TaskStatus.completed if ok else TaskStatus.partial
        else:
            task.status = TaskStatus.failed
            task.error_message = "No analysis could be completed: " + "; ".join(
                f"{n}: {r.error or r.status.value}" for n, r in results.items())[:400]
        task.completed_at = datetime.now(timezone.utc)
        task.latency_ms = int((time.perf_counter() - t0) * 1000)
        task.tokens_used = deps.llm.tokens_used
        db.commit()
