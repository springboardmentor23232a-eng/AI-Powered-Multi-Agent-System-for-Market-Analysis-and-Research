import hmac
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .security import decode_access_token


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    token = request.cookies.get("access_token")
    if not token:
        authorization = request.headers.get("Authorization", "")
        if authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please sign in to continue.",
        )

    try:
        payload = decode_access_token(token)
        user_id = UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session is invalid or has expired. Please sign in again.",
        )

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The account for this session could not be found.",
        )
    return user


def require_csrf_for_cookie_auth(request: Request):
    # Bearer-token clients are not using cookie-based authentication.
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.cookies.get("access_token"):
        cookie_token = request.cookies.get("csrf_token", "")
        header_token = request.headers.get("X-CSRF-Token", "")
        if (
            not cookie_token
            or not header_token
            or not hmac.compare_digest(cookie_token, header_token)
        ):
            raise HTTPException(status_code=403, detail="CSRF validation failed.")
