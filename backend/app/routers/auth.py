from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserProfileResponse
from app.services.auth_service import AuthService, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user account with validated credentials and hashed password.
    Returns success message and directs user to login.
    """
    AuthService.register_user(db, user_data)
    return MessageResponse(
        success=True,
        message="Registration successful! You can now log in."
    )


@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Authenticate user credentials, enforce rate limits, and generate JWT access token.
    Sets secure HTTP-only cookie and returns token in JSON response.
    """
    client_ip = request.client.host if request.client else "unknown"
    auth_result = AuthService.authenticate_user(db, login_data, client_ip, response)
    return auth_result


@router.post("/logout", response_model=MessageResponse)
def logout(response: Response, current_user: User = Depends(get_current_user)):
    """Log out the authenticated user and invalidate session cookie."""
    AuthService.logout_user(response)
    return MessageResponse(success=True, message="Successfully logged out.")


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Return profile details of the authenticated user derived strictly from JWT."""
    return current_user

