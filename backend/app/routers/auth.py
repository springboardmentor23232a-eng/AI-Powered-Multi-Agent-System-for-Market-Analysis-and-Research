from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..models import User, UserPreference
from ..schemas import LoginRequest, LoginResponse, MeResponse, RegisterRequest, RegisterResponse, UserOut
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "This email is already registered. Please sign in instead.")
    user = User(full_name=body.full_name, email=body.email, password_hash=hash_password(body.password))
    user.preferences = UserPreference()  # defaults: NASDAQ / 1Y
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # two simultaneous registrations with the same email
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "This email is already registered. Please sign in instead.")
    db.refresh(user)
    return RegisterResponse(message="Registration successful! You can now sign in.", user=UserOut.model_validate(user))


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email))
    # verify_password runs bcrypt even when the user is missing (constant-ish time)
    if not verify_password(body.password, user.password_hash if user else None):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password.")
    token, csrf, expires_in = create_access_token(user.user_id)
    response.set_cookie(
        settings.cookie_name, token, max_age=expires_in, httponly=True,
        secure=settings.cookie_secure, samesite=settings.cookie_samesite, path="/",
    )
    return LoginResponse(
        message="Login successful.", user=UserOut.model_validate(user), csrf_token=csrf, expires_in=expires_in,
        access_token=token if settings.expose_token_in_body else None,
    )


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(settings.cookie_name, path="/", secure=settings.cookie_secure,
                           httponly=True, samesite=settings.cookie_samesite)
    return {"message": "Signed out."}


@router.get("/me", response_model=MeResponse)
def me(request: Request, user: User = Depends(get_current_user)):
    return MeResponse(user=UserOut.model_validate(user), csrf_token=getattr(request.state, "csrf", None))
