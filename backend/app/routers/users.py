from fastapi import APIRouter, Depends, Query, Request

from ..dependencies import CurrentUser, get_db, require_permissions
from ..models.schemas import UserCreate, UserRolesUpdate, UserStatusUpdate, UserUpdate
from ..services import user_service

router = APIRouter(prefix="/users", tags=["users"])

VIEW = require_permissions("users.view")
CREATE = require_permissions("users.create")
UPDATE = require_permissions("users.update")
STATUS = require_permissions("users.activate")
ROLES = require_permissions("users.assign_roles")


def _ip(request: Request) -> str | None:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


@router.get("")
def list_users(
    search: str | None = Query(default=None, max_length=100),
    status: str | None = Query(default=None, pattern=r"^(active|inactive|locked)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: CurrentUser = Depends(VIEW),
    conn=Depends(get_db),
):
    return user_service.list_users(conn, search, status, page, page_size)


@router.post("", status_code=201)
def create_user(
    payload: UserCreate,
    request: Request,
    user: CurrentUser = Depends(CREATE),
    conn=Depends(get_db),
):
    return user_service.create_user(conn, payload, user, _ip(request))


@router.get("/{user_id}")
def get_user(
    user_id: int,
    user: CurrentUser = Depends(VIEW),
    conn=Depends(get_db),
):
    return user_service.get_user(conn, user_id)


@router.put("/{user_id}")
def update_user(
    user_id: int,
    payload: UserUpdate,
    request: Request,
    user: CurrentUser = Depends(UPDATE),
    conn=Depends(get_db),
):
    return user_service.update_user(conn, user_id, payload, user, _ip(request))


@router.post("/{user_id}/status")
def set_status(
    user_id: int,
    payload: UserStatusUpdate,
    request: Request,
    user: CurrentUser = Depends(STATUS),
    conn=Depends(get_db),
):
    return user_service.set_status(conn, user_id, payload.status, user, _ip(request))


@router.put("/{user_id}/roles")
def set_roles(
    user_id: int,
    payload: UserRolesUpdate,
    request: Request,
    user: CurrentUser = Depends(ROLES),
    conn=Depends(get_db),
):
    return user_service.set_roles(conn, user_id, payload.role_ids, user, _ip(request))
