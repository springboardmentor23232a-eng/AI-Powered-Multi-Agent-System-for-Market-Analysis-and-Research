import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models import ResearchTask, TaskStatus

log = logging.getLogger("veritas.maintenance")


def reconcile_stale_tasks(session_factory, stale_minutes: int, now: datetime | None = None) -> int:
    """Fail tasks left queued/running by a restart or crash; background work does not survive a restart."""
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=stale_minutes)
    n = 0
    with session_factory() as db:
        for t in db.scalars(select(ResearchTask).where(ResearchTask.status.in_([TaskStatus.queued, TaskStatus.running]))):
            created = t.created_at if t.created_at.tzinfo else t.created_at.replace(tzinfo=timezone.utc)
            if created < cutoff:
                t.status, t.completed_at = TaskStatus.failed, now
                t.error_message = "Interrupted by a server restart or timeout; please run the research again"
                n += 1
        db.commit()
    if n:
        log.warning("failed %d stale research task(s)", n)
    return n
