
from fastapi import APIRouter, Depends

from ..dependencies import CurrentUser, get_db, get_current_user
from ..services import network_service

router = APIRouter(prefix="/network", tags=["network"])


@router.get("/summary")
def network_summary(
    user: CurrentUser = Depends(get_current_user),
    conn=Depends(get_db),
):
    return network_service.get_network_summary(conn)
