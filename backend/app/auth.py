import os
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import Response
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "e83a45c71d8f764a02937be4889c26cf81a6c0b938f830d12e6bf542a1885f92")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

IS_PRODUCTION = ENVIRONMENT.lower() == "production"


def hash_password(password: str) -> str:
    """
    Hashes a plain-text password securely using bcrypt.
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against a bcrypt hash.
    """
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a cryptographically signed JWT with sub, iat, and exp claims.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodes and validates JWT signature and expiration.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def set_auth_cookie(response: Response, token: str):
    """
    Configures an HTTP-only secure cookie containing the JWT.
    """
    max_age = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=max_age,
        expires=max_age,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        path="/"
    )


def clear_auth_cookie(response: Response):
    """
    Clears the authentication cookie upon logout.
    """
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        path="/"
    )

