import logging
from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
import jwt

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.services.security import decode_access_token

logger = logging.getLogger("uvicorn.error")


def get_token_from_request(request: Request) -> Optional[str]:
    """
    Extracts the JWT access token from:
    1. HTTP-only cookie (primary browser mechanism)
    2. Authorization: Bearer <token> header (standard API & test fallback)
    """
    # 1. Prefer HTTP-only cookie
    token = request.cookies.get(settings.AUTH_COOKIE_NAME)
    if token:
        return token

    # 2. Fall back to Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[len("Bearer "):].strip()

    return None


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI authentication dependency:
    - Extracts JWT from cookie or Authorization header.
    - Cryptographically verifies signature and expiry against configured algorithm.
    - Extracts authenticated user_id from 'sub' claim.
    - Retrieves User from PostgreSQL 'users' table.
    - Rejects missing, expired, invalid, or nonexistent users with HTTP 401.
    """
    token = get_token_from_request(request)
    if not token:
        logger.warning(f"Unauthenticated request to protected endpoint: {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in to continue.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(token)
        user_id_raw = payload.get("sub")
        if user_id_raw is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token. Missing user identity.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = int(user_id_raw)
    except jwt.ExpiredSignatureError:
        logger.warning("Rejected expired JWT token.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.InvalidTokenError, ValueError, TypeError) as exc:
        logger.warning(f"JWT validation failed: {type(exc).__name__}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        logger.warning(f"Token contains user_id {user_id} which does not exist in PostgreSQL users table.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account associated with this token no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def verify_csrf(request: Request) -> None:
    """
    CSRF verification dependency for state-changing cookie-authenticated requests.
    Validates X-CSRF-Token header against csrf_token cookie or verified origin.
    """
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return

    # If client uses Authorization header directly, CSRF token is not required
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return

    # Check origin/referer
    origin = request.headers.get("Origin") or request.headers.get("Referer")
    if origin and any(allowed in origin for allowed in settings.cors_origins_list):
        return

    csrf_cookie = request.cookies.get(settings.CSRF_COOKIE_NAME)
    csrf_header = request.headers.get("X-CSRF-Token") or request.headers.get("X-XSRF-Token")

    if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed. Missing or mismatched CSRF token.",
        )

