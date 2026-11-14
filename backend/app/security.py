from datetime import datetime, timedelta, timezone
from uuid import UUID
import secrets

import jwt
from pwdlib import PasswordHash

from .config import settings


password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        return password_hasher.verify(password, password_hash)
    except Exception:
        return False


def create_access_token(user_id: UUID | str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)
