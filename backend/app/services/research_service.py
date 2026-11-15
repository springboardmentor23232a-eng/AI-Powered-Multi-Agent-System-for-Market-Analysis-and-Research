"""Read access to a user's research history.

Research tasks are created by the Supervisor workflow (Module 7). Until then
this history is genuinely empty; the ownership rules are in place and tested.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ResearchTask, User


def list_research_history(
    db: Session, user: User, limit: int, offset: int
) -> tuple[list[ResearchTask], int]:
    base = select(ResearchTask).where(ResearchTask.user_id == user.user_id)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    items = db.scalars(
        base.order_by(ResearchTask.created_at.desc(), ResearchTask.task_id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(items), total
