import json
import logging
import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from .. import oauth
from ..models import OAuthIdentity, User, UserPreference
from ..schemas import LoginRequest, LoginResponse, MeResponse, RegisterRequest, RegisterResponse, UserOut
from ..security import create_access_token, hash_password, verify_password

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str, expires_in: int) -> None:
    response.set_cookie(
        settings.cookie_name, token, max_age=expires_in, httponly=True,
        secure=settings.cookie_secure, samesite=settings.cookie_samesite, path="/",
    )


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
    _set_session_cookie(response, token, expires_in)
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


# ------------------------------------------------------------------ Continue with Google / Apple
def _state_cookie_kwargs(provider: str) -> dict:
    # Apple returns via a cross-site form POST, so its state cookie must be SameSite=None (which needs HTTPS).
    same_site = "none" if (provider == "apple" and settings.cookie_secure) else "lax"
    return dict(httponly=True, secure=settings.cookie_secure, samesite=same_site, path="/api/auth")


def _login_redirect(error: str | None = None, provider: str | None = None) -> RedirectResponse:
    base = settings.public_base_url.rstrip("/")
    if error:
        return RedirectResponse(f"{base}/login?{urlencode({'oauth_error': error})}", status_code=303)
    return RedirectResponse(f"{base}/dashboard", status_code=303)


def _check_provider(provider: str) -> None:
    if provider not in oauth.PROVIDERS:
        raise HTTPException(404, "Unknown sign-in provider.")


@router.get("/providers")
def sign_in_providers():
    """Which social sign-in buttons are fully configured on this server."""
    return {p: oauth.is_configured(p) for p in oauth.PROVIDERS}


@router.get("/{provider}/login")
def social_login(provider: str):
    """Starts "Continue with <provider>": redirects the browser to the provider's consent screen."""
    _check_provider(provider)
    label = oauth.PROVIDERS[provider].label
    if not oauth.is_configured(provider):
        msg = f"Sign in with {label} is not set up on this server yet. Please use your email and password instead."
        if not settings.cookie_secure:  # local development: tell the developer exactly what to fill in (never shown in production)
            msg += f" (Developer note: set {', '.join(oauth.missing_settings(provider))} in backend/.env, then restart the backend.)"
            if provider == "apple":
                msg += " Apple also needs a paid Apple Developer account and an https domain, so it cannot work on http://localhost."
        return _login_redirect(msg)
    state, nonce = oauth.make_state(provider)
    resp = RedirectResponse(oauth.authorize_url(provider, state, nonce), status_code=303)
    resp.set_cookie(oauth.STATE_COOKIE, state, max_age=oauth.STATE_TTL, **_state_cookie_kwargs(provider))
    return resp


def _find_or_create_user(db: Session, provider: str, claims: dict, apple_name: str | None) -> User:
    sub = str(claims["sub"])
    identity = db.scalar(select(OAuthIdentity).where(OAuthIdentity.provider == provider,
                                                     OAuthIdentity.provider_user_id == sub))
    if identity:
        return identity.user

    email = (claims.get("email") or "").strip().lower()
    if not email or not oauth.is_email_verified(claims):
        raise oauth.OAuthError(f"{oauth.PROVIDERS[provider].label} did not share a verified email address, "
                               "so we cannot create your account.")
    user = db.scalar(select(User).where(User.email == email))  # same verified email -> same person: link
    if user is None:
        name = " ".join((claims.get("name") or apple_name or email.split("@")[0]).split())[:100]
        user = User(full_name=name if len(name) >= 2 else email.split("@")[0].ljust(2, "_"), email=email, password_hash=None)
        user.preferences = UserPreference()
        db.add(user)
        db.flush()
    db.add(OAuthIdentity(user_id=user.user_id, provider=provider, provider_user_id=sub))
    try:
        db.commit()
    except IntegrityError:  # two simultaneous first sign-ins
        db.rollback()
        identity = db.scalar(select(OAuthIdentity).where(OAuthIdentity.provider == provider,
                                                         OAuthIdentity.provider_user_id == sub))
        if identity:
            return identity.user
        raise
    db.refresh(user)
    return user


def _finish_social_login(provider: str, request: Request, db: Session, code: str | None, state: str | None,
                         error: str | None, apple_user_json: str | None = None) -> RedirectResponse:
    label = oauth.PROVIDERS[provider].label
    cookie_state = request.cookies.get(oauth.STATE_COOKIE, "")
    try:
        if error:  # e.g. the user pressed Cancel on the consent screen
            raise oauth.OAuthError(f"{label} sign-in was cancelled.")
        if not code or not state or not cookie_state or not secrets.compare_digest(state, cookie_state):
            raise oauth.OAuthError("Invalid sign-in request. Please try again.")
        nonce = oauth.read_state(state, provider)
        claims = oauth.fetch_claims(provider, code, nonce)
        apple_name = None
        if provider == "apple" and apple_user_json:  # Apple sends the name only on the very first sign-in
            try:
                n = json.loads(apple_user_json).get("name") or {}
                apple_name = f"{n.get('firstName', '')} {n.get('lastName', '')}".strip() or None
            except (ValueError, AttributeError):
                pass
        user = _find_or_create_user(db, provider, claims, apple_name)
    except oauth.OAuthError as exc:
        resp = _login_redirect(str(exc))
    except Exception:
        log.exception("Social login with %s failed", provider)
        resp = _login_redirect(f"Something went wrong signing in with {label}. Please try again.")
    else:
        token, _csrf, expires_in = create_access_token(user.user_id)
        resp = _login_redirect()
        _set_session_cookie(resp, token, expires_in)  # the dashboard fetches the CSRF token from /auth/me
    resp.delete_cookie(oauth.STATE_COOKIE, **{k: v for k, v in _state_cookie_kwargs(provider).items() if k != "httponly"})
    return resp


@router.get("/google/callback", include_in_schema=False)
def google_callback(request: Request, code: str | None = None, state: str | None = None,
                    error: str | None = None, db: Session = Depends(get_db)):
    return _finish_social_login("google", request, db, code, state, error)


@router.post("/apple/callback", include_in_schema=False)
async def apple_callback(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    return _finish_social_login("apple", request, db, form.get("code"), form.get("state"), form.get("error"),
                                form.get("user"))
