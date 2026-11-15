
import secrets
import jwt

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from google.oauth2 import id_token
from google.auth.transport import requests

from database import get_db
from models import User
from schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    GoogleLoginRequest
)
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    verify_access_token
)
from config import GOOGLE_CLIENT_ID


router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


# 1. User registration
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    hashed_password = hash_password(user_data.password)

    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        hashed_password=hashed_password
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    return new_user


# 2. Normal email/password login
@router.post("/login", response_model=TokenResponse)
def login_user(user_data: UserLogin, db: Session = Depends(get_db)):

    user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive"
        )

    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# 3. Google login
@router.post("/google", response_model=TokenResponse)
def google_login(
    google_data: GoogleLoginRequest,
    db: Session = Depends(get_db)
):

    try:
        google_user = id_token.verify_oauth2_token(
            google_data.credential,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )

    except (ValueError, Exception):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google authentication token"
        )

    email = google_user.get("email")
    email_verified = google_user.get("email_verified")

    if not email or email_verified is not True:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google email is not verified"
        )

    user = db.query(User).filter(
        User.email == email
    ).first()

    # Create an account if this email is new
    if not user:

        random_password = secrets.token_urlsafe(32)

        new_user = User(
            full_name=google_user.get("name") or email.split("@")[0],
            email=email,
            hashed_password=hash_password(random_password)
        )

        try:
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user = new_user

        except IntegrityError:
            db.rollback()
            user = db.query(User).filter(
                User.email == email
            ).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Unable to create Google account"
                )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive"
        )

    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# 4. Get current authenticated user
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):

    token = credentials.credentials

    try:
        payload = verify_access_token(token)
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )

        user_id = int(user_id)

    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive"
        )

    return user


# 5. Current user profile
@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user
