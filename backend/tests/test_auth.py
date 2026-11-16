import time

import jwt
import pytest
from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.models import User
from .conftest import GOOD, login, register


def test_register_success_and_password_is_hashed(client):
    r = register(client)
    assert r.status_code == 201
    assert "successful" in r.json()["message"].lower()
    assert "password" not in str(r.json()["user"]).lower()
    with SessionLocal() as db:
        u = db.scalar(select(User).where(User.email == "asha@example.com"))
        assert u.password_hash != "Str0ngPass" and u.password_hash.startswith("$2")  # bcrypt


def test_register_duplicate_email_rejected_case_insensitive(client):
    assert register(client).status_code == 201
    r = register(client, email="ASHA@Example.com")
    assert r.status_code == 409 and "already registered" in r.json()["detail"]


@pytest.mark.parametrize("over,fragment", [
    ({"email": "not-an-email"}, "email"),
    ({"password": "short1A", "confirm_password": "short1A"}, "8 characters"),
    ({"password": "alllowercase1", "confirm_password": "alllowercase1"}, "uppercase"),
    ({"password": "NoDigitsHere", "confirm_password": "NoDigitsHere"}, "digit"),
    ({"confirm_password": "Different1A"}, "do not match"),
    ({"full_name": " "}, "name"),
    ({"password": "A1a" * 30, "confirm_password": "A1a" * 30}, "72"),
])
def test_register_validation(client, over, fragment):
    r = register(client, **over)
    assert r.status_code == 422 and fragment.lower() in r.text.lower()


def test_login_success_sets_httponly_cookie_and_jwt_has_no_sensitive_data(client):
    register(client)
    r = client.post("/api/auth/login", json={"email": "asha@example.com", "password": "Str0ngPass"})
    assert r.status_code == 200
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie
    claims = jwt.decode(r.json()["access_token"], settings.secret_key, algorithms=["HS256"])
    assert set(claims) == {"sub", "iat", "exp", "csrf"}  # user id + expiry only
    assert claims["sub"] == str(r.json()["user"]["user_id"])


def test_login_wrong_password_and_unknown_email_same_clear_error(client):
    register(client)
    a = client.post("/api/auth/login", json={"email": "asha@example.com", "password": "WrongPass1"})
    b = client.post("/api/auth/login", json={"email": "ghost@example.com", "password": "WrongPass1"})
    assert a.status_code == b.status_code == 401
    assert a.json()["detail"] == b.json()["detail"] == "Invalid email or password."


def test_protected_route_requires_token(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401 and "sign in" in r.json()["detail"].lower()


def test_me_with_cookie_and_with_bearer(client):
    register(client)
    data = login(client)
    assert client.get("/api/auth/me").json()["user"]["email"] == "asha@example.com"
    client.cookies.clear()
    assert client.get("/api/auth/me").status_code == 401
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"})
    assert r.status_code == 200


def test_tampered_token_rejected(client):
    register(client)
    data = login(client)
    client.cookies.clear()
    bad = data["access_token"][:-3] + ("aaa" if not data["access_token"].endswith("aaa") else "bbb")
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {bad}"}).status_code == 401


def test_token_signed_with_other_key_rejected(client):
    register(client)
    forged = jwt.encode({"sub": "1", "exp": int(time.time()) + 600}, "attacker-key-attacker-key-attacker-key", algorithm="HS256")
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_alg_none_token_rejected(client):
    register(client)
    forged = jwt.encode({"sub": "1", "exp": int(time.time()) + 600}, None, algorithm="none")
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_expired_token_rejected_with_resign_in_message(client):
    register(client)
    expired = jwt.encode({"sub": "1", "exp": int(time.time()) - 10}, settings.secret_key, algorithm="HS256")
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401 and "expired" in r.json()["detail"].lower()


def test_logout_clears_cookie(user_client):
    assert user_client.post("/api/auth/logout").status_code == 200
    user_client.cookies.clear()
    assert user_client.get("/api/auth/me").status_code == 401


def test_csrf_required_for_cookie_authenticated_writes(client):
    register(client)
    login(client)  # cookie set, but NO csrf header
    r = client.put("/api/preferences", json={"market": "NSE", "analysis_period": "6M"})
    assert r.status_code == 403
    r = client.put("/api/preferences", json={"market": "NSE", "analysis_period": "6M"}, headers={"X-CSRF-Token": "wrong"})
    assert r.status_code == 403


def test_security_headers(client):
    r = client.get("/api/health")
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers["x-frame-options"] == "DENY"
