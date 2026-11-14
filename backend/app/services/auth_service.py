from datetime import datetime, timezone

from fastapi import HTTPException, status

from ..config import settings
from ..dependencies import CurrentUser
from ..rate_limit import is_rate_limited, record_attempt, reset_attempts
from ..repositories import audit_repo, team_repo, token_repo, user_repo
from ..security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    verify_password,
)
from . import audit_service

REFRESH_COOKIE = "netshield_refresh"


def _set_refresh_cookie(response, raw_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=raw_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/api/v1/auth",
    )


def _clear_refresh_cookie(response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE, path="/api/v1/auth")


def _issue_tokens(conn, user_row) -> tuple[str, str]:
    profile = user_repo.get_user_auth_profile(conn, user_row["id"])
    access = create_access_token(user_row["id"], list(profile["roles"]))
    refresh = generate_refresh_token()
    token_repo.create_refresh_token(conn, user_row["id"], refresh, token_repo.refresh_expiry())
    return access, refresh


def login(conn, identifier: str, password: str, ip: str | None, response):
    rate_key = f"{ip or 'unknown'}:{identifier.lower()}"
    if is_rate_limited(rate_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    user = user_repo.find_by_identifier(conn, identifier)

    # Generic failure path — never reveal which part was wrong.
    if user is None or not verify_password(password, user["password_hash"]):
        record_attempt(rate_key)
        audit_service.log(
            conn, actor_user_id=user["id"] if user else None,
            action="auth.login", status="failure",
            details={"reason": "invalid_credentials", "identifier": identifier[:100]},
            ip_address=ip,
        )
        conn.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if user["status"] != "active":
        record_attempt(rate_key)
        audit_service.log(
            conn, actor_user_id=user["id"],
            action="auth.login", status="failure",
            details={"reason": f"account_{user['status']}"},
            ip_address=ip,
        )
        conn.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active. Contact an administrator.",
        )

    reset_attempts(rate_key)
    access, refresh = _issue_tokens(conn, user)
    audit_service.log(
        conn, actor_user_id=user["id"], action="auth.login", status="success", ip_address=ip
    )
    conn.commit()
    _set_refresh_cookie(response, refresh)

    profile = user_repo.get_user_auth_profile(conn, user["id"])
    return {
        "access_token": access,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"],
            "status": user["status"],
            "roles": profile["roles"],
            "permissions": profile["permissions"],
        },
    }


def refresh(conn, raw_refresh: str | None, response):
    if not raw_refresh:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")
    row = token_repo.get_valid_refresh_token(conn, raw_refresh)
    if row is None or row["revoked"] or row["expires_at"].timestamp() < __import__("time").time():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    user = user_repo.get_user_by_id(conn, row["user_id"])
    if user is None or user["status"] != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account unavailable")

    # Rotate: revoke old, issue new pair.
    token_repo.revoke_token(conn, row["id"])
    access, new_refresh = _issue_tokens(conn, user)
    conn.commit()
    _set_refresh_cookie(response, new_refresh)

    profile = user_repo.get_user_auth_profile(conn, user["id"])
    return {
        "access_token": access,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"],
            "status": user["status"],
            "roles": profile["roles"],
            "permissions": profile["permissions"],
        },
    }


def logout(conn, user: CurrentUser, raw_refresh: str | None, response, ip: str | None):
    if raw_refresh:
        row = token_repo.get_valid_refresh_token(conn, raw_refresh)
        if row and row["user_id"] == user.id:
            token_repo.revoke_token(conn, row["id"])
    audit_service.log(conn, actor_user_id=user.id, action="auth.logout", status="success", ip_address=ip)
    conn.commit()
    _clear_refresh_cookie(response)
    return {"message": "Logged out"}


def change_password(conn, user: CurrentUser, current_password: str, new_password: str, ip: str | None):
    row = user_repo.find_by_identifier(conn, user.username)
    if row is None or not verify_password(current_password, row["password_hash"]):
        audit_service.log(
            conn, actor_user_id=user.id, action="auth.password_change", status="failure",
            details={"reason": "incorrect_current_password"}, ip_address=ip,
        )
        conn.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    user_repo.set_user_password(conn, user.id, hash_password(new_password))
    revoked = token_repo.revoke_all_user_tokens(conn, user.id)
    audit_service.log(
        conn, actor_user_id=user.id, action="auth.password_change", status="success",
        details={"sessions_revoked": revoked}, ip_address=ip,
    )
    conn.commit()
    return {"message": "Password changed. Please log in again.", "sessions_revoked": revoked}


def me_payload(user: CurrentUser, conn):
    profile = user_repo.get_user_auth_profile(conn, user.id)
    team_ids = team_repo.user_team_ids(conn, user.id)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "status": user.status,
        "roles": profile["roles"],
        "permissions": profile["permissions"],
        "team_ids": team_ids,
    }
