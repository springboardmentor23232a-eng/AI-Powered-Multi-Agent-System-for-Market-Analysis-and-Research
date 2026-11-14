import secrets
from datetime import datetime, timedelta, timezone
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from fastapi import Request, HTTPException, status
from app.core.config import settings

_hasher = PasswordHasher()

def hash_password(password: str) -> str:
    return _hasher.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, password)
    except (VerifyMismatchError, InvalidHashError):
        return False

def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "iat": now, "exp": now + timedelta(minutes=settings.access_token_minutes), "jti": secrets.token_urlsafe(12)}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Missing subject")
        return str(user_id)
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Your session is invalid or expired. Please sign in again.")

def set_session_cookies(response, user_id: str):
    response.set_cookie("access_token", create_access_token(user_id), httponly=True, secure=settings.cookie_secure, samesite=settings.cookie_samesite, max_age=settings.access_token_minutes * 60, path="/")
    response.set_cookie("csrf_token", secrets.token_urlsafe(32), httponly=False, secure=settings.cookie_secure, samesite=settings.cookie_samesite, max_age=settings.access_token_minutes * 60, path="/")

def clear_session_cookies(response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("csrf_token", path="/")

def require_csrf(request: Request):
    cookie_token = request.cookies.get("csrf_token")
    header_token = request.headers.get("X-CSRF-Token")
    if not cookie_token or not header_token or not secrets.compare_digest(cookie_token, header_token):
        raise HTTPException(status_code=403, detail="CSRF validation failed. Refresh and try again.")
