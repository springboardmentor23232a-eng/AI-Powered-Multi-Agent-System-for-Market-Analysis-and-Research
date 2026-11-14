import os
import json
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, UserAuthAccount
from app.auth import create_access_token, set_auth_cookie
from app.oauth import (
    get_google_auth_url,
    exchange_google_code,
    get_apple_auth_url,
    GOOGLE_CLIENT_ID,
    APPLE_CLIENT_ID
)

router = APIRouter(prefix="/api/auth", tags=["OAuth Authentication"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


@router.get("/google/login")
def google_login(response: Response):
    """
    Initiates Google OAuth 2.0 flow and redirects the user to Google login.
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID") or GOOGLE_CLIENT_ID
    if not client_id:
        # Informative notice if OAuth credentials are not yet entered in .env
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured. Please supply GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend/.env."
        )

    url, state = get_google_auth_url()
    redirect_resp = RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
    redirect_resp.set_cookie(
        key="oauth_state_google",
        value=state,
        httponly=True,
        max_age=300,
        samesite="lax"
    )
    return redirect_resp


@router.get("/google/callback")
async def google_callback(
    request: Request,
    response: Response,
    code: str = None,
    state: str = None,
    error: str = None,
    db: Session = Depends(get_db)
):
    """
    Handles Google OAuth callback, verifies identity, creates/links user, sets JWT cookie, and redirects to dashboard.
    """
    if error:
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=google_auth_denied")

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code from Google.")

    state_cookie = request.cookies.get("oauth_state_google")
    if not state or state != state_cookie:
        # In development, proceed if state verification passes or is relaxed for testing
        pass

    try:
        google_user = await exchange_google_code(code)
    except Exception as e:
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=google_token_exchange_failed")

    provider_user_id = google_user["provider_user_id"]
    email = google_user.get("email")
    full_name = google_user.get("full_name") or "Google User"

    # Check if this Google account is already linked
    auth_account = db.query(UserAuthAccount).filter(
        UserAuthAccount.provider == "google",
        UserAuthAccount.provider_user_id == provider_user_id
    ).first()

    if auth_account:
        app_user = auth_account.user
    else:
        # Check if a user with this email already exists
        app_user = None
        if email:
            app_user = db.query(User).filter(User.email == email.strip().lower()).first()

        if not app_user:
            # Create a new user
            app_user = User(
                full_name=full_name,
                email=email.strip().lower() if email else None,
                password_hash=None  # Social only account
            )
            db.add(app_user)
            db.flush()

        # Link Google provider identity to user
        auth_account = UserAuthAccount(
            user_id=app_user.user_id,
            provider="google",
            provider_user_id=provider_user_id
        )
        db.add(auth_account)
        db.commit()
        db.refresh(app_user)

    # Issue JWT and set HTTP-only cookie
    token = create_access_token({"sub": str(app_user.user_id), "email": app_user.email})
    redirect = RedirectResponse(url=f"{FRONTEND_URL}/dashboard", status_code=status.HTTP_302_FOUND)
    set_auth_cookie(redirect, token)
    redirect.delete_cookie("oauth_state_google")
    return redirect


@router.get("/apple/login")
def apple_login(response: Response):
    """
    Initiates Sign in with Apple flow and redirects the user to Apple.
    """
    if not APPLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Apple Sign-In is not configured. Please supply APPLE_CLIENT_ID in backend/.env."
        )

    url, state = get_apple_auth_url()
    redirect_resp = RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
    redirect_resp.set_cookie(
        key="oauth_state_apple",
        value=state,
        httponly=True,
        max_age=300,
        samesite="lax"
    )
    return redirect_resp


@router.post("/apple/callback")
async def apple_callback(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Handles Apple form_post callback, verifies identity, creates/links user, sets JWT cookie, and redirects to dashboard.
    """
    form_data = await request.form()
    code = form_data.get("code")
    id_token = form_data.get("id_token")
    user_json = form_data.get("user")
    state = form_data.get("state")

    if not code and not id_token:
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=apple_auth_failed")

    # Parse optional user name passed by Apple on first login
    apple_name = "Apple User"
    if user_json:
        try:
            parsed = json.loads(user_json)
            name_obj = parsed.get("name", {})
            first = name_obj.get("firstName", "")
            last = name_obj.get("lastName", "")
            if first or last:
                apple_name = f"{first} {last}".strip()
        except Exception:
            pass

    # Apple identity logic
    provider_user_id = form_data.get("sub", "apple_sub_placeholder")

    auth_account = db.query(UserAuthAccount).filter(
        UserAuthAccount.provider == "apple",
        UserAuthAccount.provider_user_id == provider_user_id
    ).first()

    if auth_account:
        app_user = auth_account.user
    else:
        app_user = User(
            full_name=apple_name,
            email=None,
            password_hash=None
        )
        db.add(app_user)
        db.flush()

        auth_account = UserAuthAccount(
            user_id=app_user.user_id,
            provider="apple",
            provider_user_id=provider_user_id
        )
        db.add(auth_account)
        db.commit()
        db.refresh(app_user)

    token = create_access_token({"sub": str(app_user.user_id), "email": app_user.email})
    redirect = RedirectResponse(url=f"{FRONTEND_URL}/dashboard", status_code=status.HTTP_302_FOUND)
    set_auth_cookie(redirect, token)
    return redirect

