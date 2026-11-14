
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..dependencies import get_current_user, require_csrf_for_cookie_auth
from ..models import User, UserPreference
from ..oauth import oauth
from ..schemas import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    UserResponse,
)
from ..security import (
    create_access_token,
    hash_password,
    new_csrf_token,
    verify_password,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/auth",
    tags=["authentication"]
)


# --------------------------------------------------
# AUTHENTICATION COOKIES
# --------------------------------------------------

def set_auth_cookies(response: Response, user_id: UUID):
    token = create_access_token(user_id)
    csrf = new_csrf_token()

    cookie_options = {
        "max_age": settings.access_token_expire_minutes * 60,
        "secure": settings.cookie_secure,
        "samesite": settings.cookie_samesite,
        "path": "/",
    }

    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        **cookie_options
    )

    response.set_cookie(
        "csrf_token",
        csrf,
        httponly=False,
        **cookie_options
    )


# --------------------------------------------------
# CUSTOMER REGISTRATION
# --------------------------------------------------

@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db)
):
    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=422,
            detail="Passwords do not match."
        )

    email = str(payload.email).strip().lower()

    existing = db.scalar(
        select(User).where(User.email == email)
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists."
        )

    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
    )

    try:
        db.add(user)
        db.flush()

        db.add(
            UserPreference(user_id=user.user_id)
        )

        db.commit()

    except Exception:
        db.rollback()
        logger.exception("Customer registration failed")
        raise HTTPException(
            status_code=500,
            detail="Unable to create your account."
        )

    return {
        "message": "Your account has been created. You can now sign in."
    }


# --------------------------------------------------
# EMAIL AND PASSWORD LOGIN
# --------------------------------------------------

@router.post(
    "/login",
    response_model=UserResponse
)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    email = str(payload.email).strip().lower()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if user is None or not user.password_hash:
        raise HTTPException(
            status_code=401,
            detail="This account uses Google sign-in or the credentials are incorrect."
        )

    if not verify_password(
        payload.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="The email or password is incorrect."
        )

    set_auth_cookies(response, user.user_id)

    return user


# --------------------------------------------------
# GOOGLE LOGIN
# --------------------------------------------------

@router.get("/google/login")
async def google_login(request: Request):

    if (
        not settings.google_client_id
        or not settings.google_client_secret
    ):
        raise HTTPException(
            status_code=503,
            detail="Google sign-in is not configured on the backend."
        )

    return await oauth.google.authorize_redirect(
        request,
        settings.google_redirect_uri
    )


# --------------------------------------------------
# GOOGLE LOGIN CALLBACK
# --------------------------------------------------

@router.get("/google/callback")
async def google_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        # Exchange Google's authorization code for a token.
        token = await oauth.google.authorize_access_token(request)

        # Get the customer's Google profile.
        identity = token.get("userinfo")

        if not identity:
            identity = await oauth.google.parse_id_token(
                request,
                token
            )

        if not identity:
            raise ValueError("Google identity information is missing.")

        google_sub = identity.get("sub")

        email = str(
            identity.get("email", "")
        ).strip().lower()

        email_verified = identity.get("email_verified") is True

        full_name = (
            identity.get("name") or email.split("@")[0]
        ).strip()

        if not google_sub or not email or not email_verified:
            raise ValueError(
                "Google did not return a verified email identity."
            )

        # First, check whether this Google account already exists.
        user = db.scalar(
            select(User).where(
                User.google_sub == google_sub
            )
        )

        if user is None:

            # Check whether the email already belongs to a customer.
            user = db.scalar(
                select(User).where(
                    User.email == email
                )
            )

            if user is not None:

                # Link Google to the existing verified-email account.
                if user.google_sub and user.google_sub != google_sub:
                    raise ValueError(
                        "This email is linked to another Google account."
                    )

                user.google_sub = google_sub

            else:

                # Create a new Google-only customer.
                user = User(
                    full_name=full_name[:120] or "Google User",
                    email=email,
                    google_sub=google_sub,
                    password_hash=None,
                )

                db.add(user)
                db.flush()

                # Create default research preferences.
                db.add(
                    UserPreference(
                        user_id=user.user_id
                    )
                )

        # Save the customer and preferences.
        db.commit()
        db.refresh(user)

        # Create an authenticated session.
        response = RedirectResponse(
            settings.frontend_origin,
            status_code=303
        )

        set_auth_cookies(
            response,
            user.user_id
        )

        return response

    except Exception:
        db.rollback()

        logger.exception(
            "Google sign-in callback failed"
        )

        return RedirectResponse(
            f"{settings.frontend_origin}/?auth_error=google_signin_failed",
            status_code=303
        )


# --------------------------------------------------
# CURRENT CUSTOMER PROFILE
# --------------------------------------------------

@router.get(
    "/me",
    response_model=UserResponse
)
def me(
    current_user: User = Depends(get_current_user)
):
    return current_user


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@router.post(
    "/logout",
    response_model=MessageResponse,
    dependencies=[Depends(require_csrf_for_cookie_auth)],
)
def logout(response: Response):

    response.delete_cookie(
        "access_token",
        path="/",
        secure=settings.cookie_secure,
        httponly=True,
        samesite=settings.cookie_samesite,
    )

    response.delete_cookie(
        "csrf_token",
        path="/",
        secure=settings.cookie_secure,
        httponly=False,
        samesite=settings.cookie_samesite,
    )

    return {
        "message": "You have been signed out."
    }
