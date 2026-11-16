from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    RegisterSuccessResponse,
    LoginSuccessResponse,
    LogoutSuccessResponse,
    CurrentUserResponse,
)
from app.services.security import create_access_token, generate_csrf_token
from app.services.user_service import register_new_user, authenticate_user

router = APIRouter(prefix="/auth", tags=["User Authentication"])


@router.post(
    "/register",
    response_model=RegisterSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Validates user credentials, ensures email uniqueness, securely hashes the password with bcrypt, and creates a user record in the database.",
    responses={
        201: {
            "description": "User successfully created.",
            "model": RegisterSuccessResponse,
        },
        400: {
            "description": "Validation error (e.g. invalid email format, weak password, or password mismatch).",
        },
        409: {
            "description": "Conflict: A user with this email address is already registered.",
        },
        500: {
            "description": "Internal database or server error.",
        },
    },
)
def register_user(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> RegisterSuccessResponse:
    """
    Registers a new user in the PostgreSQL database.
    - **full_name**: User's full name (min 2 characters)
    - **email**: Valid email address
    - **password**: Secure password (min 8 chars, 1 uppercase, 1 digit)
    - **confirm_password**: Must match password exactly
    """
    new_user = register_new_user(db=db, request=payload)
    
    return RegisterSuccessResponse(
        status="success",
        message="User registered successfully.",
        data=UserResponse.model_validate(new_user),
    )


@router.post(
    "/login",
    response_model=LoginSuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate existing user",
    description="Validates user credentials, generates a signed JWT, and sets an HTTP-only secure cookie.",
    responses={
        200: {
            "description": "User successfully authenticated.",
            "model": LoginSuccessResponse,
        },
        401: {
            "description": "Unauthorized: Invalid email or password.",
        },
    },
)
def login_user(
    payload: UserLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> LoginSuccessResponse:
    """
    Authenticates a user with email and password.
    Issues a signed JWT inside an HTTP-only cookie to prevent XSS access.
    Also issues a CSRF token cookie for state-changing protection.
    """
    user = authenticate_user(db=db, request=payload)

    # Generate signed JWT with user ID ('sub') and expiration ('exp')
    access_token = create_access_token(user_id=user.user_id, email=user.email)
    csrf_token = generate_csrf_token()

    # Transmit JWT securely via HTTP-only cookie
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
    )

    # Set CSRF defense cookie (readable by frontend for inclusion in state-changing headers)
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
    )

    return LoginSuccessResponse(
        status="success",
        message="Login successful.",
        data=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
    description="Validates the JWT authentication cookie and returns the active user profile.",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> CurrentUserResponse:
    """
    Protected route to retrieve current authenticated user details.
    """
    return CurrentUserResponse(
        status="success",
        data=UserResponse.model_validate(current_user),
    )


@router.post(
    "/logout",
    response_model=LogoutSuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Log out user and clear authentication cookies",
)
def logout_user(
    response: Response,
) -> LogoutSuccessResponse:
    """
    Clears the HTTP-only JWT cookie and CSRF cookie.
    """
    response.delete_cookie(
        key=settings.AUTH_COOKIE_NAME,
        path="/",
        samesite=settings.COOKIE_SAMESITE,
    )
    response.delete_cookie(
        key=settings.CSRF_COOKIE_NAME,
        path="/",
        samesite=settings.COOKIE_SAMESITE,
    )

    return LogoutSuccessResponse(
        status="success",
        message="Logged out successfully.",
    )
