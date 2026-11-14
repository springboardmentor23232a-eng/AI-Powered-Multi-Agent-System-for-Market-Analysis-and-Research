from uuid import UUID
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth import decode_access_token


def get_token_from_request(request: Request) -> Optional[str]:
    """
    Extracts JWT from HTTP-only cookie first, then Authorization Bearer header.
    """
    token = request.cookies.get("access_token")
    if token:
        return token

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]

    return None


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Verifies JWT token and resolves the authenticated User from PostgreSQL.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or session has expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = get_token_from_request(request)
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str: str = payload.get("sub")
    if not user_id_str:
        raise credentials_exception

    try:
        user_uuid = UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    user = db.query(User).filter(User.user_id == user_uuid).first()
    if user is None:
        raise credentials_exception

    return user


def get_optional_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Returns authenticated user if present and valid, otherwise None without raising.
    """
    try:
        return get_current_user(request, db)
    except HTTPException:
        return None

