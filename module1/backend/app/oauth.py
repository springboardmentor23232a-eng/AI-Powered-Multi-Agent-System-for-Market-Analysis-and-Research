"""OpenID Connect helpers for "Continue with Google" and "Continue with Apple" (authorization-code flow).

Flow: browser -> /api/auth/{provider}/login -> provider consent screen -> /api/auth/{provider}/callback
      -> we exchange the code for an ID token, VERIFY it (signature, issuer, audience, expiry, nonce),
         find/create the user, set the same HTTP-only JWT cookie as password login, redirect to the dashboard.

Security notes
  * `state` is a short-lived signed token that is ALSO stored in a cookie -> the callback must present both
    (blocks login-CSRF). It carries a random `nonce` that must come back inside the provider's ID token.
  * Nothing from the browser (user id, email, name) is trusted: identity comes only from the verified ID token.
"""
import secrets
import time
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx
import jwt
from jwt import PyJWKClient

from .config import settings


class OAuthError(Exception):
    """Message is safe to show to the user."""


@dataclass(frozen=True)
class Provider:
    key: str
    label: str
    authorize_url: str
    token_url: str
    jwks_url: str
    issuers: tuple[str, ...]
    scope: str
    algorithms: tuple[str, ...]


PROVIDERS = {
    "google": Provider(
        "google", "Google", "https://accounts.google.com/o/oauth2/v2/auth", "https://oauth2.googleapis.com/token",
        "https://www.googleapis.com/oauth2/v3/certs", ("https://accounts.google.com", "accounts.google.com"),
        "openid email profile", ("RS256",)),
    "apple": Provider(
        "apple", "Apple", "https://appleid.apple.com/auth/authorize", "https://appleid.apple.com/auth/token",
        "https://appleid.apple.com/auth/keys", ("https://appleid.apple.com",), "name email", ("RS256",)),
}

STATE_COOKIE = "oauth_state"
STATE_TTL = 600


def client_id(provider: str) -> str:
    return settings.google_client_id if provider == "google" else settings.apple_client_id


def is_configured(provider: str) -> bool:
    if provider == "google":
        return bool(settings.google_client_id and settings.google_client_secret)
    return bool(settings.apple_client_id and settings.apple_team_id and settings.apple_key_id and settings.apple_private_key)


def missing_settings(provider: str) -> list[str]:
    """Names of the backend/.env settings still empty for this provider (shown to the developer in local mode only)."""
    if provider == "google":
        need = {"GOOGLE_CLIENT_ID": settings.google_client_id, "GOOGLE_CLIENT_SECRET": settings.google_client_secret}
    else:
        need = {"APPLE_CLIENT_ID": settings.apple_client_id, "APPLE_TEAM_ID": settings.apple_team_id,
                "APPLE_KEY_ID": settings.apple_key_id, "APPLE_PRIVATE_KEY": settings.apple_private_key}
    return [k for k, v in need.items() if not v]


def redirect_uri(provider: str) -> str:
    return f"{settings.public_base_url.rstrip('/')}/api/auth/{provider}/callback"


# ---------------------------------------------------------------------------------------------- state
def make_state(provider: str) -> tuple[str, str]:
    """Returns (state, nonce). `state` is signed with SECRET_KEY and expires in 10 minutes."""
    nonce = secrets.token_urlsafe(16)
    state = jwt.encode({"p": provider, "n": nonce, "exp": int(time.time()) + STATE_TTL, "r": secrets.token_urlsafe(8)},
                       settings.secret_key, algorithm="HS256")
    return state, nonce


def read_state(state: str, provider: str) -> str:
    """Returns the nonce, or raises OAuthError."""
    try:
        data = jwt.decode(state, settings.secret_key, algorithms=["HS256"], options={"require": ["exp"]})
    except jwt.PyJWTError:
        raise OAuthError("The sign-in attempt expired. Please try again.")
    if data.get("p") != provider:
        raise OAuthError("Invalid sign-in request. Please try again.")
    return data["n"]


def authorize_url(provider: str, state: str, nonce: str) -> str:
    p = PROVIDERS[provider]
    params = {"client_id": client_id(provider), "redirect_uri": redirect_uri(provider), "response_type": "code",
              "scope": p.scope, "state": state, "nonce": nonce}
    if provider == "apple":
        params["response_mode"] = "form_post"  # required by Apple when requesting name/email
    else:
        params["prompt"] = "select_account"
    return f"{p.authorize_url}?{urlencode(params)}"


# ------------------------------------------------------------------------------------ client secret
def apple_client_secret() -> str:
    """Apple wants the client secret to be a short-lived ES256 JWT signed with your .p8 key."""
    now = int(time.time())
    key = settings.apple_private_key.replace("\\n", "\n")
    return jwt.encode(
        {"iss": settings.apple_team_id, "iat": now, "exp": now + 300, "aud": "https://appleid.apple.com",
         "sub": settings.apple_client_id},
        key, algorithm="ES256", headers={"kid": settings.apple_key_id})


def _client_secret(provider: str) -> str:
    return settings.google_client_secret if provider == "google" else apple_client_secret()


# ------------------------------------------------------------------------------------ token exchange
_jwk_clients: dict[str, PyJWKClient] = {}


def _signing_key(provider: str, id_token: str):
    client = _jwk_clients.setdefault(provider, PyJWKClient(PROVIDERS[provider].jwks_url, cache_keys=True))
    return client.get_signing_key_from_jwt(id_token).key


def verify_id_token(provider: str, id_token: str, nonce: str) -> dict:
    p = PROVIDERS[provider]
    try:
        claims = jwt.decode(id_token, _signing_key(provider, id_token), algorithms=list(p.algorithms),
                            audience=client_id(provider), options={"require": ["exp", "iss", "aud", "sub"]})
    except jwt.PyJWTError as exc:
        raise OAuthError("Could not verify your sign-in with the provider. Please try again.") from exc
    if claims["iss"] not in p.issuers:
        raise OAuthError("Could not verify your sign-in with the provider. Please try again.")
    if not secrets.compare_digest(str(claims.get("nonce", "")), nonce):
        raise OAuthError("Invalid sign-in response. Please try again.")
    return claims


def fetch_claims(provider: str, code: str, nonce: str) -> dict:
    """Exchange the authorization code for an ID token and return its VERIFIED claims."""
    p = PROVIDERS[provider]
    try:
        r = httpx.post(p.token_url, data={
            "grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri(provider),
            "client_id": client_id(provider), "client_secret": _client_secret(provider)}, timeout=10)
        r.raise_for_status()
        id_token = r.json()["id_token"]
    except Exception as exc:
        raise OAuthError(f"{p.label} did not accept the sign-in. Please try again.") from exc
    return verify_id_token(provider, id_token, nonce)


def is_email_verified(claims: dict) -> bool:
    v = claims.get("email_verified")
    return v is True or str(v).lower() == "true"  # Apple sends the string "true"
