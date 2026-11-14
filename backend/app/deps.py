import jwt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .security import decode_token

COOKIE_NAME = "access_token"


def csrf_guard(request: Request):
    # Browsers cannot attach a custom header cross-site without a CORS preflight,
    # so requiring it on state-changing requests blocks forged form posts.
    if request.method not in ("GET", "HEAD", "OPTIONS") and request.headers.get("x-requested-with") != "XMLHttpRequest":
        raise HTTPException(403, "Missing CSRF header")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(401, "Please sign in to continue")
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Your session has expired. Please sign in again")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid session. Please sign in again")
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(401, "Invalid session. Please sign in again")
    return user
