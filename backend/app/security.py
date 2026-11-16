import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from .config import settings

# Used to burn equal CPU time when the email does not exist (reduces user-enumeration via timing)
_DUMMY_HASH = bcrypt.hashpw(b"dummy-password", bcrypt.gensalt(rounds=settings.bcrypt_rounds)).decode()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=settings.bcrypt_rounds)).decode()


def verify_password(password: str, password_hash: str | None) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), (password_hash or _DUMMY_HASH).encode()) and password_hash is not None
    except ValueError:
        return False


def create_access_token(user_id: int) -> tuple[str, str, int]:
    """JWT holds ONLY: sub (user id), iat, exp and a random CSRF nonce. No password / personal data."""
    now = datetime.now(timezone.utc)
    expires = timedelta(minutes=settings.access_token_expire_minutes)
    csrf = secrets.token_urlsafe(24)
    payload = {"sub": str(user_id), "iat": now, "exp": now + expires, "csrf": csrf}
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, csrf, int(expires.total_seconds())


def decode_access_token(token: str) -> dict:
    """Verifies signature + expiry. Raises jwt.ExpiredSignatureError / jwt.InvalidTokenError."""
    return jwt.decode(
        token, settings.secret_key, algorithms=[settings.jwt_algorithm],
        options={"require": ["exp", "sub"]},
    )
