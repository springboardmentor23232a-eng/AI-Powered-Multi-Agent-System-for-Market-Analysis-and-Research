from fastapi import APIRouter, Cookie, Depends, Request, Response

from ..dependencies import CurrentUser, get_current_user, get_db
from ..models.schemas import ChangePasswordRequest, LoginRequest
from ..services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str | None:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post("/login")
def login(payload: LoginRequest, request: Request, response: Response, conn=Depends(get_db)):
    return auth_service.login(
        conn, payload.identifier, payload.password, _client_ip(request), response
    )


@router.post("/refresh")
def refresh(
    response: Response,
    netshield_refresh: str | None = Cookie(default=None),
    conn=Depends(get_db),
):
    return auth_service.refresh(conn, netshield_refresh, response)


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    user: CurrentUser = Depends(get_current_user),
    netshield_refresh: str | None = Cookie(default=None),
    conn=Depends(get_db),
):
    return auth_service.logout(conn, user, netshield_refresh, response, _client_ip(request))


@router.get("/me")
def me(user: CurrentUser = Depends(get_current_user), conn=Depends(get_db)):
    return auth_service.me_payload(user, conn)


@router.post("/me/password")
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    conn=Depends(get_db),
):
    return auth_service.change_password(
        conn, user, payload.current_password, payload.new_password, _client_ip(request)
    )
