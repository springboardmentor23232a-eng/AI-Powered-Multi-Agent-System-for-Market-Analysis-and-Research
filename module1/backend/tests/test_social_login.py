"""Continue with Google / Continue with Apple."""
import time
from urllib.parse import parse_qs, urlparse

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from sqlalchemy import select

import app.oauth as oauth
from app.config import settings
from app.database import SessionLocal
from app.models import OAuthIdentity, User

from .conftest import login, register


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    for k, v in dict(google_client_id="g-id", google_client_secret="g-secret", apple_client_id="com.example.web",
                     apple_team_id="TEAM123456", apple_key_id="KEY1234567").items():
        monkeypatch.setattr(settings, k, v)
    key = ec.generate_private_key(ec.SECP256R1())
    pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    monkeypatch.setattr(settings, "apple_private_key", pem.decode().replace("\n", "\\n"))  # as pasted into .env
    return key


def start(client, provider):
    r = client.get(f"/api/auth/{provider}/login", follow_redirects=False)
    assert r.status_code == 303
    q = parse_qs(urlparse(r.headers["location"]).query)
    return r, q


def callback(client, provider, state, code="abc", **extra):
    if provider == "apple":
        return client.post("/api/auth/apple/callback", data={"code": code, "state": state, **extra}, follow_redirects=False)
    return client.get(f"/api/auth/google/callback?code={code}&state={state}", follow_redirects=False)


def fake_claims(monkeypatch, **claims):
    base = {"sub": "sub-1", "email": "new@example.com", "email_verified": True, "name": "Nina Shah"}
    monkeypatch.setattr(oauth, "fetch_claims", lambda p, code, nonce: {**base, **claims})


# ------------------------------------------------------------------------------------- start
def test_providers_endpoint_reports_configuration(client, monkeypatch):
    assert client.get("/api/auth/providers").json() == {"google": True, "apple": True}
    monkeypatch.setattr(settings, "apple_team_id", "")
    assert client.get("/api/auth/providers").json() == {"google": True, "apple": False}


def test_google_login_redirects_with_correct_parameters(client):
    r, q = start(client, "google")
    assert r.headers["location"].startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert q["client_id"] == ["g-id"] and q["response_type"] == ["code"] and "openid" in q["scope"][0]
    assert q["redirect_uri"] == ["http://localhost:5173/api/auth/google/callback"]
    assert q["state"] and q["nonce"] and "oauth_state" in r.headers["set-cookie"] and "HttpOnly" in r.headers["set-cookie"]


def test_apple_login_uses_form_post(client):
    r, q = start(client, "apple")
    assert r.headers["location"].startswith("https://appleid.apple.com/auth/authorize?")
    assert q["response_mode"] == ["form_post"] and q["scope"] == ["name email"] and q["client_id"] == ["com.example.web"]


def test_unconfigured_provider_redirects_back_with_clear_message(client, monkeypatch):
    monkeypatch.setattr(settings, "google_client_secret", "")
    r = client.get("/api/auth/google/login", follow_redirects=False)
    loc = r.headers["location"]
    assert loc.startswith("http://localhost:5173/login?oauth_error=") and "not+set+up" in loc


def test_unknown_provider_404(client):
    assert client.get("/api/auth/facebook/login", follow_redirects=False).status_code == 404


# ----------------------------------------------------------------------------------- callback
@pytest.mark.parametrize("provider", ["google", "apple"])
def test_new_user_is_created_signed_in_and_gets_defaults(client, monkeypatch, provider):
    fake_claims(monkeypatch)
    _, q = start(client, provider)
    r = callback(client, provider, q["state"][0])
    assert r.status_code == 303 and r.headers["location"] == "http://localhost:5173/dashboard"
    assert "access_token=" in r.headers["set-cookie"] or "access_token" in client.cookies
    me = client.get("/api/auth/me").json()
    assert me["user"]["email"] == "new@example.com" and me["user"]["full_name"] == "Nina Shah" and me["csrf_token"]
    assert client.get("/api/preferences").json()["market"] == "NASDAQ"
    with SessionLocal() as db:
        u = db.scalar(select(User))
        assert u.password_hash is None
        assert db.scalar(select(OAuthIdentity)).provider == provider


def test_state_cookie_is_removed_after_use(client, monkeypatch):
    fake_claims(monkeypatch)
    _, q = start(client, "google")
    callback(client, "google", q["state"][0])
    assert "oauth_state" not in client.cookies


def test_returning_user_is_matched_by_provider_id_not_duplicated(client, monkeypatch):
    fake_claims(monkeypatch)
    for _ in range(2):
        _, q = start(client, "google")
        assert callback(client, "google", q["state"][0]).headers["location"].endswith("/dashboard")
        client.post("/api/auth/logout")
    with SessionLocal() as db:
        assert len(db.scalars(select(User)).all()) == 1 and len(db.scalars(select(OAuthIdentity)).all()) == 1


def test_existing_password_account_is_linked_by_verified_email(client, monkeypatch):
    register(client)  # asha@example.com with a password
    fake_claims(monkeypatch, email="Asha@Example.com", sub="g-77")
    _, q = start(client, "google")
    callback(client, "google", q["state"][0])
    assert client.get("/api/auth/me").json()["user"]["full_name"] == "Asha Verma"  # same account, not a new one
    client.post("/api/auth/logout")
    login(client)  # the password still works afterwards
    with SessionLocal() as db:
        assert len(db.scalars(select(User)).all()) == 1


def test_google_and_apple_can_both_link_to_one_account(client, monkeypatch):
    fake_claims(monkeypatch)
    for p in ("google", "apple"):
        _, q = start(client, p)
        callback(client, p, q["state"][0])
        client.post("/api/auth/logout")
    with SessionLocal() as db:
        assert len(db.scalars(select(User)).all()) == 1 and len(db.scalars(select(OAuthIdentity)).all()) == 2


def test_social_only_account_cannot_use_password_login(client, monkeypatch):
    fake_claims(monkeypatch)
    _, q = start(client, "google")
    callback(client, "google", q["state"][0])
    client.post("/api/auth/logout")
    r = client.post("/api/auth/login", json={"email": "new@example.com", "password": "Str0ngPass"})
    assert r.status_code == 401 and r.json()["detail"] == "Invalid email or password."


def test_unverified_or_missing_email_is_refused(client, monkeypatch):
    for bad in ({"email_verified": False}, {"email": None}):
        fake_claims(monkeypatch, **bad)
        _, q = start(client, "google")
        r = callback(client, "google", q["state"][0])
        assert "oauth_error" in r.headers["location"] and "verified" in r.headers["location"]
    with SessionLocal() as db:
        assert db.scalars(select(User)).all() == []


def test_apple_string_true_email_verified_and_first_time_name(client, monkeypatch):
    fake_claims(monkeypatch, email_verified="true", name=None)
    _, q = start(client, "apple")
    callback(client, "apple", q["state"][0], user='{"name": {"firstName": "Ravi", "lastName": "Rao"}}')
    assert client.get("/api/auth/me").json()["user"]["full_name"] == "Ravi Rao"


def test_missing_name_falls_back_to_email_prefix(client, monkeypatch):
    fake_claims(monkeypatch, name=None)
    _, q = start(client, "google")
    callback(client, "google", q["state"][0])
    assert client.get("/api/auth/me").json()["user"]["full_name"] == "new"


# --------------------------------------------------------------------------------- attack cases
def test_callback_without_state_cookie_is_rejected(client, monkeypatch):
    fake_claims(monkeypatch)
    _, q = start(client, "google")
    client.cookies.clear()  # attacker's link opened in a browser that never started the flow
    r = callback(client, "google", q["state"][0])
    assert "oauth_error" in r.headers["location"] and client.get("/api/auth/me").status_code == 401


def test_tampered_expired_or_wrong_provider_state_rejected(client, monkeypatch):
    fake_claims(monkeypatch)
    expired = jwt.encode({"p": "google", "n": "x", "exp": int(time.time()) - 5}, settings.secret_key, algorithm="HS256")
    forged = jwt.encode({"p": "google", "n": "x", "exp": int(time.time()) + 99}, "wrong-secret-wrong-secret-wrong!!", algorithm="HS256")
    apple_state, _ = oauth.make_state("apple")
    for state in (expired, forged, apple_state, "garbage"):
        client.cookies.set("oauth_state", state, path="/api/auth")
        assert "oauth_error" in callback(client, "google", state).headers["location"]
    assert client.get("/api/auth/me").status_code == 401


def test_user_cancelling_at_provider_shows_message(client):
    _, q = start(client, "google")
    r = client.get(f"/api/auth/google/callback?error=access_denied&state={q['state'][0]}", follow_redirects=False)
    assert "cancelled" in r.headers["location"]


def test_provider_exchange_failure_is_reported_not_crashed(client, monkeypatch):
    def boom(*a):
        raise oauth.OAuthError("Google did not accept the sign-in. Please try again.")
    monkeypatch.setattr(oauth, "fetch_claims", boom)
    _, q = start(client, "google")
    assert "did+not+accept" in callback(client, "google", q["state"][0]).headers["location"]


# ---------------------------------------------------------------- real ID-token verification
@pytest.fixture
def rsa_key(monkeypatch):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(oauth, "_signing_key", lambda provider, token: key.public_key())
    return key


def make_id_token(key, **over):
    claims = {"iss": "https://accounts.google.com", "aud": "g-id", "sub": "1", "exp": int(time.time()) + 300,
              "nonce": "N1", "email": "a@b.com", "email_verified": True, **over}
    return jwt.encode({k: v for k, v in claims.items() if v is not None}, key, algorithm="RS256")


def test_id_token_valid(rsa_key):
    assert oauth.verify_id_token("google", make_id_token(rsa_key), "N1")["sub"] == "1"


@pytest.mark.parametrize("over", [
    {"aud": "someone-else"}, {"iss": "https://evil.example"}, {"exp": int(time.time()) - 10},
    {"nonce": "other"}, {"nonce": None}, {"sub": None},
])
def test_id_token_rejects_bad_claims(rsa_key, over):
    with pytest.raises(oauth.OAuthError):
        oauth.verify_id_token("google", make_id_token(rsa_key, **over), "N1")


def test_id_token_signed_by_a_different_key_rejected(rsa_key):
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(oauth.OAuthError):
        oauth.verify_id_token("google", make_id_token(other), "N1")


def test_alg_none_token_rejected(rsa_key):
    tok = jwt.encode({"iss": "https://accounts.google.com", "aud": "g-id", "sub": "1", "exp": int(time.time()) + 99, "nonce": "N1"},
                     None, algorithm="none")
    with pytest.raises(oauth.OAuthError):
        oauth.verify_id_token("google", tok, "N1")


def test_apple_client_secret_is_a_valid_es256_jwt(configured):
    secret = oauth.apple_client_secret()
    hdr = jwt.get_unverified_header(secret)
    claims = jwt.decode(secret, configured.public_key(), algorithms=["ES256"], audience="https://appleid.apple.com")
    assert hdr["kid"] == "KEY1234567" and claims["iss"] == "TEAM123456" and claims["sub"] == "com.example.web"
    assert claims["exp"] - claims["iat"] <= 300


def test_code_exchange_posts_to_provider_and_verifies(rsa_key, monkeypatch):
    seen = {}

    class R:
        def raise_for_status(self): pass
        def json(self): return {"id_token": make_id_token(rsa_key)}

    def fake_post(url, data, timeout):
        seen.update(url=url, data=data)
        return R()
    monkeypatch.setattr(oauth.httpx, "post", fake_post)
    claims = oauth.fetch_claims("google", "the-code", "N1")
    assert claims["email"] == "a@b.com" and seen["url"] == "https://oauth2.googleapis.com/token"
    assert seen["data"]["code"] == "the-code" and seen["data"]["client_secret"] == "g-secret"


# ---- not-configured diagnosis and the redirect to the provider (fake credentials: no real round trip is made)
def test_not_configured_message_names_missing_settings_in_local_mode(client, monkeypatch):
    from urllib.parse import unquote_plus
    monkeypatch.setattr(settings, "cookie_secure", False)
    for name in ("google_client_id", "google_client_secret"):
        monkeypatch.setattr(settings, name, "")
    loc = unquote_plus(client.get("/api/auth/google/login", follow_redirects=False).headers["location"])
    assert "GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET" in loc and "not set up" in loc
    monkeypatch.setattr(settings, "apple_client_id", "")
    loc = unquote_plus(client.get("/api/auth/apple/login", follow_redirects=False).headers["location"])
    assert "APPLE_CLIENT_ID" in loc and "cannot work on http://localhost" in loc


def test_not_configured_message_hides_env_names_in_production(client, monkeypatch):
    from urllib.parse import unquote_plus
    monkeypatch.setattr(settings, "cookie_secure", True)
    monkeypatch.setattr(settings, "google_client_id", "")
    loc = unquote_plus(client.get("/api/auth/google/login", follow_redirects=False).headers["location"])
    assert "GOOGLE_CLIENT_ID" not in loc and "not set up" in loc


def test_google_login_redirects_to_google_with_state_cookie_when_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "fake-id.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "google_client_secret", "fake-secret")
    monkeypatch.setattr(settings, "public_base_url", "http://localhost:5173")
    r = client.get("/api/auth/google/login", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A5173%2Fapi%2Fauth%2Fgoogle%2Fcallback" in r.headers["location"]
    assert "oauth_state=" in r.headers["set-cookie"]
