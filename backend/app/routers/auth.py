import secrets
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.database import get_db
from app.models import User, UserPreference, GoogleIdentity
from app.schemas import RegisterIn, LoginIn, GoogleIn, UserOut
from app.security import hash_password, verify_password, set_session_cookies, clear_session_cookies, require_csrf
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: RegisterIn, response: Response, db: Session = Depends(get_db)):
    if payload.password != payload.confirm_password:
        raise HTTPException(422, "Passwords do not match.")
    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "An account with this email already exists.")
    user = User(full_name=payload.full_name.strip(), email=email, password_hash=hash_password(payload.password), auth_provider="local", is_active=True)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "An account with this email already exists.")
    db.refresh(user)
    db.add(UserPreference(user_id=user.id))
    db.commit()
    set_session_cookies(response, user.id)
    return user

@router.post("/google", response_model=UserOut)
def google_login(payload: GoogleIn, response: Response, db: Session = Depends(get_db)):
    from app.core.config import settings
    if not settings.google_client_id or settings.google_client_id.startswith("YOUR_"):
        raise HTTPException(503, "Google Sign-In is not configured on the backend.")
    try:
        info = id_token.verify_oauth2_token(payload.credential, google_requests.Request(), settings.google_client_id)
    except ValueError:
        raise HTTPException(401, "Google credential could not be verified.")
    email = str(info.get("email") or "").lower().strip()
    google_sub = str(info.get("sub") or "")
    if not email or not google_sub or not info.get("email_verified"):
        raise HTTPException(401, "Google account email is not verified.")
    identity = db.query(GoogleIdentity).filter(GoogleIdentity.google_sub == google_sub).first()
    user = identity.user if identity else db.query(User).filter((User.google_sub == google_sub) | (User.email == email)).first()
    if user is None:
        user = User(full_name=info.get("name") or email.split("@")[0], email=email, password_hash=hash_password(secrets.token_urlsafe(32)), auth_provider="google", google_sub=google_sub, is_active=True)
        db.add(user)
        db.flush()
        db.add(UserPreference(user_id=user.id))
    elif identity is None:
        existing_email_identity = db.query(GoogleIdentity).filter(GoogleIdentity.user_id == user.id).first()
        if existing_email_identity and existing_email_identity.google_sub != google_sub:
            raise HTTPException(409, "This email is already linked to a different Google account.")
        if user.google_sub and user.google_sub != google_sub:
            raise HTTPException(409, "This email is already linked to a different Google account.")
        user.google_sub = google_sub
        user.auth_provider = "google"
    if identity is None:
        db.add(GoogleIdentity(user_id=user.id, google_sub=google_sub))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "This Google account is already linked to another user.")
    db.refresh(user)
    set_session_cookies(response, user.id)
    return user

@router.post("/login", response_model=UserOut)
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Incorrect email address or password.")
    set_session_cookies(response, user.id)
    return user

@router.get("/csrf")
def csrf(request: Request):
    token = request.cookies.get("csrf_token")
    if not token:
        raise HTTPException(401, "No active session.")
    return {"csrf_token": token}

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user

@router.post("/logout")
def logout(request: Request, response: Response, user: User = Depends(get_current_user)):
    require_csrf(request)
    clear_session_cookies(response)
    return {"message": "Signed out successfully."}
