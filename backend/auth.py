import os

import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    UserOut,
)
from security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from schemas import GoogleLoginRequest
router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_NAME = "access_token"
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() == "true"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")


def set_auth_cookie(response: Response, user_id: int):
    response.set_cookie(
        key=COOKIE_NAME,
        value=create_access_token(user_id),
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=60 * 60,
        path="/",
    )


def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    """Reads the JWT from the cookie, verifies it, and returns the user."""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_access_token(access_token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired, please sign in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token, please sign in again")

    user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    email = data.email.lower()

    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        full_name=data.full_name.strip(),
        email=email,
        password_hash=hash_password(data.password),
        auth_provider="local",
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")
    db.refresh(user)

    return {"message": "Registration successful", "user": user}


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))

    # Same message for "no such email" and "wrong password" so attackers
    # can't discover which emails are registered. Google users have no password.
    if not user or not user.password_hash or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user.user_id)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,          # JavaScript cannot read it
        secure=COOKIE_SECURE,   # HTTPS only in production
        samesite="lax",         # basic CSRF protection
        max_age=60 * 60,        # matches the 60-minute token expiry
        path="/",
    )
    return {"message": "Login successful", "user": user}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"message": "Logged out"}
@router.post("/google", response_model=LoginResponse)
def google_login(data: GoogleLoginRequest, response: Response, db: Session = Depends(get_db)):
    # Google signs this token; verify the signature and that it was issued for OUR app
    try:
        info = id_token.verify_oauth2_token(
            data.credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10,
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    if not info.get("email_verified"):
        raise HTTPException(status_code=401, detail="Google email is not verified")

    email = info["email"].lower()
    user = db.scalar(select(User).where(User.email == email))

    if not user:
        user = User(
            full_name=(info.get("name") or email.split("@")[0])[:100],
            email=email,
            password_hash=None,
            auth_provider="google",
            provider_user_id=info["sub"],
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    set_auth_cookie(response, user.user_id)
    return {"message": "Login successful", "user": user}