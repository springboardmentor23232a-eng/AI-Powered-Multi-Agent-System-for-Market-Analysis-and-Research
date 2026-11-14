from fastapi import APIRouter, Depends

from ..dependencies import CurrentUser, get_db, get_current_user
from ..services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def stats(user: CurrentUser = Depends(get_current_user), conn=Depends(get_db)):
    return dashboard_service.get_stats(conn, user)
