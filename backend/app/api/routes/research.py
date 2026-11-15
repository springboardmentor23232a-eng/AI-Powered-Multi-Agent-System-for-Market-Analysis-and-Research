"""Research history endpoint."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.schemas import ResearchHistoryPage
from app.services import research_service

router = APIRouter(prefix="/research", tags=["research"])


@router.get("/history", response_model=ResearchHistoryPage)
def read_research_history(
    current_user: CurrentUser,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    items, total = research_service.list_research_history(db, current_user, limit, offset)
    return ResearchHistoryPage(items=items, total=total, limit=limit, offset=offset)
