"""API tests for registration, login and the /auth/me endpoint."""

import pytest
from sqlalchemy import select

from app.models import User
from tests.conftest import API, DEFAULT_PASSWORD, login, register


# ---------- Registration ----------


def test_register_success_returns_public_fields_only(client):
    response = register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert isinstance(body["user_id"], int)
    assert "created_at" in body
    assert "password" not in body and "password_hash" not in body


def test_register_stores_hash_and_creates_default_preferences(client, db_session):
    register(client)
    user = db_session.scalar(select(User).where(User.email == "alice@example.com"))
    assert user.password_hash != DEFAULT_PASSWORD
    assert user.preferences.default_market == "NSE"
    assert user.preferences.analysis_period == "1Y"


def test_register_normalises_email_case_and_spaces(client):
    response = register(client, email="  Alice@Example.COM ")
    assert response.status_code == 201
    assert response.json()["email"] == "alice@example.com"


def test_register_duplicate_email_is_rejected(client):
    assert register(client).status_code == 201
    response = register(client, email="ALICE@example.com")
    assert response.status_code == 409
    assert response.json()["detail"] == "Email is already registered"


@pytest.mark.parametrize(
    "email",
    ["not-an-email", "", "alice@", "@example.com"],
)
def test_register_invalid_email_is_rejected(client, email):
    assert register(client, email=email).status_code == 422


@pytest.mark.parametrize(
    "password, reason",
    [
        ("Ab1", "too short"),
        ("abcdefgh", "no digit"),
        ("12345678", "no letter"),
        (" Str0ngPass", "leading space"),
        ("a1" * 65, "too long (130 chars)"),
    ],
)
def test_register_weak_password_is_rejected(client, password, reason):
    assert register(client, password=password).status_code == 422, reason


def test_register_missing_fields_is_rejected(client):
    assert client.post(f"{API}/auth/register", json={}).status_code == 422


# ---------- Login ----------


def test_login_success_returns_bearer_token(client):
    register(client)
    response = login(client)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 60 * 60
    assert body["access_token"].count(".") == 2  # header.payload.signature


def test_login_email_is_case_insensitive(client):
    register(client)
    assert login(client, email="ALICE@EXAMPLE.COM").status_code == 200


def test_login_wrong_password_is_rejected(client):
    register(client)
    response = login(client, password="WrongPassw0rd")
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_login_unknown_email_gives_same_error_as_wrong_password(client):
    response = login(client, email="nobody@example.com")
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_login_missing_form_fields_is_rejected(client):
    assert client.post(f"{API}/auth/login", data={}).status_code == 422


# ---------- /auth/me and protection of endpoints ----------


def test_me_returns_current_user(client, auth_headers):
    response = client.get(f"{API}/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "alice@example.com"


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Bearer"},
        {"Authorization": "Bearer not-a-real-token"},
        {"Authorization": "Basic YWxpY2U6cGFzcw=="},
    ],
)
def test_protected_endpoints_reject_missing_or_invalid_token(client, headers):
    for method, path in [
        ("get", "/auth/me"),
        ("get", "/users/me/preferences"),
        ("get", "/watchlist"),
        ("get", "/research/history"),
    ]:
        response = getattr(client, method)(f"{API}{path}", headers=headers)
        assert response.status_code == 401, (path, headers)


def test_token_of_deleted_user_is_rejected(client, auth_headers, db_session):
    user = db_session.scalar(select(User).where(User.email == "alice@example.com"))
    db_session.delete(user)
    db_session.commit()
    assert client.get(f"{API}/auth/me", headers=auth_headers).status_code == 401
