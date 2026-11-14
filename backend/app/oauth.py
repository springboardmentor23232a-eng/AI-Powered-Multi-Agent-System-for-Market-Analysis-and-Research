import os
import urllib.parse
import secrets
import httpx
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv

load_dotenv()

# Google Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")

# Apple Configuration
APPLE_CLIENT_ID = os.getenv("APPLE_CLIENT_ID", "")
APPLE_TEAM_ID = os.getenv("APPLE_TEAM_ID", "")
APPLE_KEY_ID = os.getenv("APPLE_KEY_ID", "")
APPLE_PRIVATE_KEY = os.getenv("APPLE_PRIVATE_KEY", "")
APPLE_REDIRECT_URI = os.getenv("APPLE_REDIRECT_URI", "http://localhost:8000/api/auth/apple/callback")


def get_google_auth_url() -> Tuple[str, str]:
    """
    Constructs Google OAuth 2.0 authorization URL with state CSRF token.
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID") or GOOGLE_CLIENT_ID
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", GOOGLE_REDIRECT_URI)

    if not client_id:
        raise ValueError("GOOGLE_CLIENT_ID is not configured in backend/.env")

    state = secrets.token_urlsafe(32)
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "state": state,
        "prompt": "select_account"
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return url, state


async def exchange_google_code(code: str) -> Dict[str, Any]:
    """
    Exchanges Google authorization code for tokens and verified userinfo.
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID") or GOOGLE_CLIENT_ID
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET") or GOOGLE_CLIENT_SECRET
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", GOOGLE_REDIRECT_URI)

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(token_url, data=data)
        if resp.status_code != 200:
            raise ValueError(f"Failed to exchange Google authorization code: {resp.text}")

        token_data = resp.json()
        access_token = token_data.get("access_token")

        # Fetch verified user profile from Google UserInfo endpoint
        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if userinfo_resp.status_code != 200:
            raise ValueError(f"Failed to fetch Google userinfo: {userinfo_resp.text}")

        userinfo = userinfo_resp.json()
        return {
            "provider_user_id": userinfo.get("sub"),
            "email": userinfo.get("email"),
            "email_verified": userinfo.get("email_verified", False),
            "full_name": userinfo.get("name") or userinfo.get("given_name", "Google User"),
            "picture": userinfo.get("picture")
        }


def get_apple_auth_url() -> Tuple[str, str]:
    """
    Constructs Sign in with Apple authorization URL with state CSRF token.
    """
    if not APPLE_CLIENT_ID:
        raise ValueError("APPLE_CLIENT_ID is not configured in backend/.env")

    state = secrets.token_urlsafe(32)
    params = {
        "client_id": APPLE_CLIENT_ID,
        "redirect_uri": APPLE_REDIRECT_URI,
        "response_type": "code id_token",
        "response_mode": "form_post",
        "scope": "name email",
        "state": state
    }
    url = f"https://appleid.apple.com/auth/authorize?{urllib.parse.urlencode(params)}"
    return url, state

