from datetime import datetime, timezone
from typing import Optional
from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.rate_limiter import login_rate_limiter
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    validate_password_strength,
    verify_password,
)
from app.database import get_db
from app.models.preference import UserPreference
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest

security_bearer = HTTPBearer(auto_error=False)


class AuthService:
    @staticmethod
    def register_user(db: Session, reg_data: RegisterRequest) -> User:
        """Register a new user with secure password hash and default preferences."""
        # 1. Check if email already exists
        existing_user = db.query(User).filter(User.email == reg_data.email.lower()).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists."
            )

        # 2. Check password strength
        is_valid, msg = validate_password_strength(reg_data.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=msg
            )

        # 3. Hash password securely
        password_hash = get_password_hash(reg_data.password)

        # 4. Create user
        new_user = User(
            full_name=reg_data.full_name.strip(),
            email=reg_data.email.lower().strip(),
            password_hash=password_hash,
        )
        db.add(new_user)
        db.flush()  # to get new_user.user_id

        # 5. Create default user preference
        default_pref = UserPreference(
            user_id=new_user.user_id,
            preferred_market=settings.DEFAULT_MARKET,
            analysis_period=settings.DEFAULT_ANALYSIS_PERIOD,
        )
        db.add(default_pref)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def authenticate_user(
        db: Session,
        login_data: LoginRequest,
        client_ip: str,
        response: Response
    ) -> dict:
        """Verify user credentials, rate limit failures, generate JWT and set secure cookie."""
        # Check brute force rate limit by client IP and email
        rate_key = f"{client_ip}:{login_data.email.lower().strip()}"
        login_rate_limiter.check_rate_limit(rate_key)

        user = db.query(User).filter(User.email == login_data.email.lower().strip()).first()
        if not user or not verify_password(login_data.password, user.password_hash):
            login_rate_limiter.record_failure(rate_key)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Reset rate limiter on successful authentication
        login_rate_limiter.reset(rate_key)

        # Generate token
        token = create_access_token(subject=user.user_id)

        # Set secure HTTP-only cookie
        is_prod = settings.ENVIRONMENT.lower() == "production"
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=is_prod,
            samesite="lax",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    @staticmethod
    def logout_user(response: Response) -> None:
        """Clear the auth cookie."""
        response.delete_cookie(
            key="access_token",
            httponly=True,
            samesite="lax"
        )


def get_current_user(
    request: Request,
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> User:
    """
    Authenticate request via Authorization Bearer token header or HTTP-only access_token cookie.
    Derives user strictly from validated JWT claims.
    """
    token: Optional[str] = None

    if auth_header and auth_header.credentials:
        token = auth_header.credentials
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or token is invalid. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token user identifier.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this token no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

