import uuid
from datetime import datetime, timedelta, timezone
from typing import Tuple
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_token_payload, get_current_user
from app.models.revoked_token import RevokedToken
from app.models.user import User
from app.schemas.auth import (
    MessageResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.schemas.user import UserResponse
from app.security import create_access_token, hash_password, hash_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Validates user registration details, verifies password complexity, hashes the password securely using bcrypt, and creates a new user profile.",
)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    normalized_email = payload.email.lower().strip()

    # Check for existing user with this email
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # Securely hash password
    password_hash = hash_password(payload.password)

    # Create new User instance
    new_user = User(
        full_name=payload.full_name.strip(),
        email=normalized_email,
        hashed_password=password_hash,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticates user credentials and returns a signed JWT Bearer access token with user details.",
)
def login(
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
):
    normalized_email = payload.email.lower().strip()

    # Query user by email
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    # Generate signed JWT Bearer access token
    access_token = create_access_token(user_id=user.id)
    expires_in_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in_seconds,
        user=user,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Retrieves the profile of the currently authenticated user using a valid, non-revoked Authorization Bearer access token.",
)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout and revoke access token",
    description="Revokes the submitted Authorization Bearer token by adding it to the database denylist until its expiration. Any subsequent attempt to use this token will be rejected with HTTP 401 Unauthorized.",
)
def logout(
    token_and_payload: Tuple[str, dict] = Depends(get_current_token_payload),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    raw_token, payload = token_and_payload
    jti = payload.get("jti") or uuid.uuid4().hex
    exp_timestamp = payload.get("exp")

    if exp_timestamp:
        expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
    else:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    token_hash_val = hash_token(raw_token)

    # Verify if already revoked
    existing = (
        db.query(RevokedToken)
        .filter(
            (RevokedToken.jti == jti) | (RevokedToken.token_hash == token_hash_val)
        )
        .first()
    )

    if not existing:
        revoked_token_entry = RevokedToken(
            jti=jti,
            token_hash=token_hash_val,
            user_id=current_user.id,
            expires_at=expires_at,
        )
        db.add(revoked_token_entry)
        db.commit()

    return MessageResponse(
        message="Successfully logged out. Token has been revoked."
    )
