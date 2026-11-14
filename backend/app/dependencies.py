from dataclasses import dataclass, field

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from . import database
from .repositories import user_repo
from .security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


@dataclass
class CurrentUser:
    id: int
    username: str
    email: str
    full_name: str
    status: str
    roles: list[str] = field(default_factory=list)
    permissions: set[str] = field(default_factory=set)

    @property
    def is_admin(self) -> bool:
        return "administrator" in self.roles

    def has_permission(self, code: str) -> bool:
        return self.is_admin or code in self.permissions

    def has_any_permission(self, codes: tuple[str, ...]) -> bool:
        return self.is_admin or any(c in self.permissions for c in codes)


def get_db():
    conn = database.get_connection()
    try:
        yield conn
    finally:
        database.put_connection(conn)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    conn=Depends(get_db),
) -> CurrentUser:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exc
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exc
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise credentials_exc

    row = user_repo.get_user_auth_profile(conn, user_id)
    if row is None or row["status"] != "active":
        raise credentials_exc

    return CurrentUser(
        id=row["id"],
        username=row["username"],
        email=row["email"],
        full_name=row["full_name"],
        status=row["status"],
        roles=row["roles"],
        permissions=set(row["permissions"]),
    )


def require_permissions(*codes: str):
    """Dependency factory: user must hold at least one of the given permission codes."""

    def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not user.has_any_permission(codes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return checker
