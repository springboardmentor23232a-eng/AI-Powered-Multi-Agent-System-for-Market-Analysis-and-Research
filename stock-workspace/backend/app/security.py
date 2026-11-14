from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .config import COOKIE_NAME, JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET
from .database import get_db
from .models import User

# Used so that "unknown email" and "wrong password" take similar time.
_DUMMY_HASH = bcrypt.hashpw(b"dummy-password", bcrypt.gensalt())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str | None) -> bool:
    target = password_hash.encode() if password_hash else _DUMMY_HASH
    ok = bcrypt.checkpw(password.encode()[:72], target)
    return ok and password_hash is not None


def create_token(user_id: int) -> str:
    # Only the user id and expiry go in the token: never passwords or personal data.
    exp = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": exp}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    # CSRF defence for cookie auth: SameSite=Lax cookie + a custom header that
    # cross-site forms cannot send. Safe (read-only) methods are exempt.
    if request.method not in ("GET", "HEAD", "OPTIONS") and request.headers.get("x-requested-with") != "XMLHttpRequest":
        raise HTTPException(403, "Missing CSRF header")

    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(401, "Please sign in to continue")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Your session has expired. Please sign in again")
    except Exception:
        raise HTTPException(401, "Invalid session. Please sign in again")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(401, "Account not found")
    return user
