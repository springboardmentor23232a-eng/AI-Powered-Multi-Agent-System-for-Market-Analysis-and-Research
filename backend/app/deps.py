import secrets

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User
from .security import decode_access_token

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, detail, headers={"WWW-Authenticate": "Bearer"})


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Identity ALWAYS comes from the verified JWT - never from anything the browser sends as a user_id."""
    from_cookie = False
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
    else:
        token = request.cookies.get(settings.cookie_name)
        from_cookie = True
    if not token:
        raise _unauthorized("Not signed in. Please sign in to continue.")  # missing token

    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Your session has expired. Please sign in again.")
    except jwt.InvalidTokenError:
        raise _unauthorized("Invalid session. Please sign in again.")

    # CSRF protection for cookie-authenticated state-changing requests (bearer tokens are not auto-sent by browsers)
    if from_cookie and request.method in UNSAFE_METHODS:
        header = request.headers.get("X-CSRF-Token", "")
        if not header or not secrets.compare_digest(header, str(payload.get("csrf", ""))):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "CSRF token missing or invalid.")

    try:
        user_id = int(payload["sub"])
    except (ValueError, KeyError):
        raise _unauthorized("Invalid session. Please sign in again.")
    user = db.get(User, user_id)
    if user is None:
        raise _unauthorized("Account no longer exists. Please sign in again.")
    request.state.csrf = payload.get("csrf")
    return user
