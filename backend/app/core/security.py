"""Password hashing and JWT creation/verification.

- Passwords are hashed with Argon2 (a slow, salted, one-way algorithm), so the
  database never stores a usable password.
- A JWT is a signed token. The server signs it with JWT_SECRET_KEY; anyone who
  changes the token breaks the signature, so the server can trust its contents.
"""

from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

_password_hasher = PasswordHash.recommended()  # Argon2id

# Hash of a random string, used so that a login attempt for an unknown email
# takes as long as one for a real email (prevents discovering registered emails by timing).
_DUMMY_HASH = _password_hasher.hash("timing-attack-protection-placeholder")


class InvalidTokenError(Exception):
    """Raised when a token is missing, expired, forged or malformed."""


def hash_password(plain_password: str) -> str:
    return _password_hasher.hash(plain_password)


def verify_password(plain_password: str, password_hash: str | None) -> bool:
    if password_hash is None:
        _password_hasher.verify(plain_password, _DUMMY_HASH)
        return False
    return _password_hasher.verify(plain_password, password_hash)


def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload = {"sub": str(user_id), "iat": now, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> int:
    """Return the user id stored in a valid token, or raise InvalidTokenError."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp", "iat"]},
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc

    if payload.get("type") != "access":
        raise InvalidTokenError("Wrong token type")
    try:
        return int(payload["sub"])
    except (TypeError, ValueError) as exc:
        raise InvalidTokenError("Invalid subject") from exc
