from fastapi import APIRouter, Depends, Request

from ..dependencies import CurrentUser, get_db, require_permissions
from ..models.schemas import RolePermissionUpdate
from ..services import role_service

router = APIRouter(prefix="/roles", tags=["roles"])

VIEW = require_permissions("roles.view")
MANAGE = require_permissions("roles.manage")


def _ip(request: Request) -> str | None:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


@router.get("")
def list_roles(user: CurrentUser = Depends(VIEW), conn=Depends(get_db)):
    return role_service.list_roles(conn)


@router.get("/permissions")
def list_permissions(user: CurrentUser = Depends(VIEW), conn=Depends(get_db)):
    return role_service.list_permissions(conn)


@router.get("/{role_id}/permissions")
def get_role_permissions(role_id: int, user: CurrentUser = Depends(VIEW), conn=Depends(get_db)):
    return role_service.get_role_permissions(conn, role_id)


@router.put("/{role_id}/permissions")
def set_role_permissions(
    role_id: int,
    payload: RolePermissionUpdate,
    request: Request,
    user: CurrentUser = Depends(MANAGE),
    conn=Depends(get_db),
):
    return role_service.set_role_permissions(conn, role_id, payload.permission_ids, user, _ip(request))
