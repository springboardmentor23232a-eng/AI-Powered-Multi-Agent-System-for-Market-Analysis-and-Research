from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.config import settings
from app.database import get_db
from app.models import User, UserPreference
from app.schemas import OAuthLoginRequest, TokenResponse, UserLogin, UserRegister, UserResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _issue_session_response(user: User, response: Response) -> TokenResponse:
    token = create_access_token(user.user_id)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address is already registered.",
        )

    user = User(
        full_name=payload.full_name.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        auth_provider="local",
    )
    db.add(user)
    db.flush()

    default_pref = UserPreference(user_id=user.user_id, market="NSE", analysis_period="1Y")
    db.add(default_pref)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login_user(payload: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password.",
        )
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This account uses {user.auth_provider.title()} sign-in. Please continue with {user.auth_provider.title()}.",
        )
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password.",
        )

    return _issue_session_response(user, response)


@router.post("/oauth", response_model=TokenResponse)
def oauth_login_or_register(
    payload: OAuthLoginRequest, response: Response, db: Session = Depends(get_db)
):
    """Register or sign in an account using Google or Apple."""
    email = payload.email.lower()
    user = db.query(User).filter(User.email == email).first()

    if not user:
        display_name = (payload.full_name or email.split("@")[0]).strip()
        user = User(
            full_name=display_name,
            email=email,
            password_hash=None,
            auth_provider=payload.provider,
        )
        db.add(user)
        db.flush()
        db.add(UserPreference(user_id=user.user_id, market="NSE", analysis_period="1Y"))
        db.commit()
        db.refresh(user)

    return _issue_session_response(user, response)


@router.post("/logout")
def logout_user(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Signed out successfully."}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
