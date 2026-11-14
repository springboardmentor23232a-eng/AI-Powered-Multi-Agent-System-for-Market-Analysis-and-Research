import re
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def _validate_email(v: str) -> str:
    """Validate basic email format. Accepts internal domains (e.g. .local)
    since this is an internal platform — uniqueness is enforced by the DB."""
    v = v.strip()
    if not _EMAIL_RE.match(v) or len(v) > 255:
        raise ValueError("Enter a valid email address")
    return v


EmailAddress = Annotated[str, BeforeValidator(_validate_email)]

# ---------- Auth ----------

class LoginRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=255)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=255)
    new_password: str = Field(min_length=8, max_length=255)


# ---------- Users ----------

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.-]+$")
    email: EmailAddress
    full_name: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=8, max_length=255)
    role_ids: list[int] = Field(default_factory=list)


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.-]+$")
    email: EmailAddress | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=150)


class UserStatusUpdate(BaseModel):
    status: str = Field(pattern=r"^(active|inactive|locked)$")


class UserRolesUpdate(BaseModel):
    role_ids: list[int]


# ---------- Roles / Permissions ----------

class RolePermissionUpdate(BaseModel):
    permission_ids: list[int]


# ---------- Teams ----------

class TeamCreate(BaseModel):
    team_name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    lead_user_id: int | None = None


class TeamUpdate(BaseModel):
    team_name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    lead_user_id: int | None = None


class TeamMemberAdd(BaseModel):
    user_id: int
