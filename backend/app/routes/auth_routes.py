from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserRegister, UserLogin, UserOut, AuthResponse
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    set_auth_cookie,
    clear_auth_cookie
)
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Registers a new user with Full Name, Email, and Password.
    Stores securely hashed password in PostgreSQL users table.
    """
    normalized_email = user_data.email.strip().lower()

    # Check for existing email in PostgreSQL
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please sign in instead."
        )

    # Hash the password securely
    hashed_pw = hash_password(user_data.password)

    # Create user in PostgreSQL database
    new_user = User(
        full_name=user_data.full_name,
        email=normalized_email,
        password_hash=hashed_pw
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error creating user account: {str(e)}"
        )

    return AuthResponse(
        message="Account created successfully! Please sign in to continue.",
        user=UserOut.model_validate(new_user)
    )


@router.post("/login", response_model=AuthResponse)
def login(login_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    """
    Authenticates user credentials, sets HTTP-only JWT cookie, and returns user profile.
    """
    normalized_email = login_data.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()

    if not user or not user.password_hash or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please try again."
        )

    # Generate JWT
    token_payload = {"sub": str(user.user_id), "email": user.email}
    access_token = create_access_token(token_payload)

    # Set secure HTTP-only cookie
    set_auth_cookie(response, access_token)

    return AuthResponse(
        message="Login successful",
        user=UserOut.model_validate(user)
    )


@router.post("/logout")
def logout(response: Response):
    """
    Clears the HTTP-only authentication cookie and terminates session.
    """
    clear_auth_cookie(response)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Returns the authenticated user's profile from PostgreSQL.
    """
    return UserOut.model_validate(current_user)

