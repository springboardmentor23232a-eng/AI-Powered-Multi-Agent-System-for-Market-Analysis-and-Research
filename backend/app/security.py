import hashlib
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
import jwt
from fastapi import HTTPException, status
from app.config import settings


def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using bcrypt with a generated salt.
    Enforces the standard bcrypt 72-byte limit safely.
    """
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password cannot exceed 72 bytes in length.",
        )
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against a stored bcrypt hash.
    Returns False if comparison fails or an error occurs.
    """
    try:
        plain_bytes = plain_password.encode("utf-8")
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(plain_bytes, hash_bytes)
    except Exception:
        return False


def hash_token(token: str) -> str:
    """
    Computes a cryptographic SHA-256 hash of a JWT token string.
    Used for secure, indexed token revocation checks in PostgreSQL without
    storing raw JWT strings in plaintext.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(
    user_id: int,
    expires_delta: Optional[timedelta] = None,
    jti: Optional[str] = None,
) -> str:
    """
    Generates a cryptographically signed JWT access token.
    Payload contains:
      - 'sub': user ID
      - 'jti': unique token identifier (JWT ID) for revocation tracking
      - 'iat': issued-at timestamp
      - 'exp': expiration timestamp
    Never includes sensitive personal data or passwords.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "jti": jti or uuid.uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decodes and validates a JWT access token's signature and expiration.
    Raises HTTPException 401 if invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token signature or payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def validate_password_strength(password: str) -> None:
    """
    Validates that a password satisfies security strength requirements:
    - Minimum 8 characters
    - Maximum 72 characters
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one digit (0-9)
    - At least one special symbol (!@#$%^&*...)
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password cannot exceed 72 bytes.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("Password must contain at least one special character (!@#$%^&*...).")
