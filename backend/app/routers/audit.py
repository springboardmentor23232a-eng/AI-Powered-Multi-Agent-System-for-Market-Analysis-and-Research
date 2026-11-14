from datetime import datetime

from fastapi import APIRouter, Depends, Query

from ..dependencies import CurrentUser, get_db, require_permissions
from ..services import audit_service_query as audit_query

router = APIRouter(prefix="/audit-logs", tags=["audit"])

VIEW = require_permissions("audit.view")


@router.get("")
def list_logs(
    actor_user_id: int | None = Query(default=None),
    action: str | None = Query(default=None, max_length=100),
    status: str | None = Query(default=None, pattern=r"^(success|failure)$"),
    target_type: str | None = Query(default=None, max_length=50),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    user: CurrentUser = Depends(VIEW),
    conn=Depends(get_db),
):
    return audit_query.query_logs(
        conn, user,
        actor_user_id=actor_user_id,
        action=action,
        status_filter=status,
        target_type=target_type,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
