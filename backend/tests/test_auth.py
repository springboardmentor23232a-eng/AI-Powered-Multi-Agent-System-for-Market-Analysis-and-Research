import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
import jwt
from sqlalchemy import text
from app.config import settings
from app.database import SessionLocal
from app.main import app
from app.models.revoked_token import RevokedToken
from app.models.user import User
from app.security import hash_password, verify_password

client = TestClient(app)

TEST_RUN_ID = uuid.uuid4().hex[:6]
TEST_PASSWORD = "StrongSecurePass@2026"
TEST_USER_1_EMAIL = f"test_analyst_{TEST_RUN_ID}_1@fincrew.com"
TEST_USER_2_EMAIL = f"test_analyst_{TEST_RUN_ID}_2@fincrew.com"

# Shared state populated across test order
auth_state = {}


def test_01_library_compatibility():
    """Verify bcrypt and PyJWT are 100% compatible with Python 3.15.2."""
    pwd_hash = hash_password("TestSecret@123")
    assert verify_password("TestSecret@123", pwd_hash) is True
    assert verify_password("WrongPassword@123", pwd_hash) is False

    payload = {
        "sub": "42",
        "jti": uuid.uuid4().hex,
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()),
    }
    encoded = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    decoded = jwt.decode(encoded, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded["sub"] == "42"
    assert "jti" in decoded


def test_02_registration_weak_passwords():
    """Verify registration rejects passwords failing strength requirements."""
    weak_passwords = [
        "Short1!",
        "nouppercase123!",
        "NOLOWERCASE123!",
        "NoDigitsInPassword!",
        "NoSpecialChar123",
    ]
    for weak_pwd in weak_passwords:
        res = client.post(
            "/api/auth/register",
            json={
                "full_name": "Weak Pass User",
                "email": f"weak_{uuid.uuid4().hex[:4]}@fincrew.com",
                "password": weak_pwd,
                "confirm_password": weak_pwd,
            },
        )
        assert res.status_code == 422


def test_03_registration_password_mismatch():
    """Verify registration rejects passwords when confirmation does not match."""
    res = client.post(
        "/api/auth/register",
        json={
            "full_name": "Mismatch User",
            "email": f"mismatch_{uuid.uuid4().hex[:4]}@fincrew.com",
            "password": TEST_PASSWORD,
            "confirm_password": "CompletelyDifferent@2026",
        },
    )
    assert res.status_code == 422
    assert "Passwords do not match" in res.text


def test_04_registration_invalid_email():
    """Verify registration rejects invalid email formats."""
    res = client.post(
        "/api/auth/register",
        json={
            "full_name": "Bad Email User",
            "email": "not-a-valid-email-string",
            "password": TEST_PASSWORD,
            "confirm_password": TEST_PASSWORD,
        },
    )
    assert res.status_code == 422


def test_05_registration_new_user():
    """Verify successful registration of a new user."""
    res = client.post(
        "/api/auth/register",
        json={
            "full_name": "Verified Analyst",
            "email": TEST_USER_1_EMAIL,
            "password": TEST_PASSWORD,
            "confirm_password": TEST_PASSWORD,
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == TEST_USER_1_EMAIL
    assert data["full_name"] == "Verified Analyst"
    assert "user_id" in data
    assert "password_hash" not in data
    assert "hashed_password" not in data
    auth_state["user_1_id"] = data["user_id"]


def test_06_registration_duplicate_email_rejection():
    """Verify duplicate email registration is rejected with HTTP 400."""
    res = client.post(
        "/api/auth/register",
        json={
            "full_name": "Duplicate User",
            "email": TEST_USER_1_EMAIL,
            "password": TEST_PASSWORD,
            "confirm_password": TEST_PASSWORD,
        },
    )
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]


def test_07_password_hashing_in_postgresql():
    """Verify password is stored as a bcrypt hash in PostgreSQL, never plaintext."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == auth_state["user_1_id"]).first()
        assert user is not None
        assert user.hashed_password.startswith("$2")
        assert len(user.hashed_password) == 60
        assert user.hashed_password != TEST_PASSWORD
        assert verify_password(TEST_PASSWORD, user.hashed_password) is True
    finally:
        db.close()


def test_08_login_incorrect_password():
    """Verify login with incorrect password returns HTTP 401."""
    res = client.post(
        "/api/auth/login",
        json={
            "email": TEST_USER_1_EMAIL,
            "password": "WrongPassword@2026",
        },
    )
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]


def test_09_login_nonexistent_user():
    """Verify login with nonexistent email returns HTTP 401."""
    res = client.post(
        "/api/auth/login",
        json={
            "email": f"nonexistent_{uuid.uuid4().hex[:4]}@fincrew.com",
            "password": TEST_PASSWORD,
        },
    )
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]


def test_10_login_successful_user_1():
    """Verify successful login returns valid JWT Bearer access token."""
    res = client.post(
        "/api/auth/login",
        json={
            "email": TEST_USER_1_EMAIL,
            "password": TEST_PASSWORD,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 3600
    assert data["user"]["user_id"] == auth_state["user_1_id"]
    auth_state["token_1"] = data["access_token"]


def test_11_get_auth_me_bearer_jwt():
    """Verify GET /api/auth/me returns current user with Bearer token."""
    res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {auth_state['token_1']}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == auth_state["user_1_id"]
    assert data["email"] == TEST_USER_1_EMAIL
    assert data["full_name"] == "Verified Analyst"
    assert "hashed_password" not in data


def test_12_unauthenticated_request_rejected():
    """Verify protected endpoints reject unauthenticated requests."""
    res = client.get("/api/auth/me")
    assert res.status_code == 401 or res.status_code == 403


def test_13_unauthenticated_logout_rejected():
    """Verify logout without Authorization Bearer header is rejected."""
    res = client.post("/api/auth/logout")
    assert res.status_code == 401 or res.status_code == 403


def test_14_invalid_jwt_rejected():
    """Verify forged or corrupted JWT is rejected with HTTP 401."""
    res = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer forged.tampered.token.123"},
    )
    assert res.status_code == 401
    assert "Invalid authentication token" in res.json()["detail"]


def test_15_expired_jwt_rejected():
    """Verify expired JWT is rejected with HTTP 401."""
    past_now = datetime.now(timezone.utc) - timedelta(hours=2)
    expired_token = jwt.encode(
        {
            "sub": str(auth_state["user_1_id"]),
            "jti": uuid.uuid4().hex,
            "iat": int(past_now.timestamp()),
            "exp": int((past_now + timedelta(minutes=10)).timestamp()),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res.status_code == 401
    assert "Session token has expired" in res.json()["detail"]


def test_16_user_isolation_between_two_users():
    """Verify two different users receive their own identity."""
    res_reg2 = client.post(
        "/api/auth/register",
        json={
            "full_name": "Second Analyst",
            "email": TEST_USER_2_EMAIL,
            "password": TEST_PASSWORD,
            "confirm_password": TEST_PASSWORD,
        },
    )
    assert res_reg2.status_code == 201
    user_2_id = res_reg2.json()["user_id"]

    res_login2 = client.post(
        "/api/auth/login",
        json={"email": TEST_USER_2_EMAIL, "password": TEST_PASSWORD},
    )
    assert res_login2.status_code == 200
    token_2 = res_login2.json()["access_token"]

    res_u1 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {auth_state['token_1']}"})
    res_u2 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_2}"})

    assert res_u1.json()["user_id"] == auth_state["user_1_id"]
    assert res_u1.json()["email"] == TEST_USER_1_EMAIL
    assert res_u2.json()["user_id"] == user_2_id
    assert res_u2.json()["email"] == TEST_USER_2_EMAIL
    assert res_u1.json()["user_id"] != res_u2.json()["user_id"]


def test_17_logout_revokes_token_in_database():
    """Verify POST /api/auth/logout requires valid Bearer token and stores revocation in DB."""
    token_to_revoke = auth_state["token_1"]
    res = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token_to_revoke}"},
    )
    assert res.status_code == 200
    assert "Token has been revoked" in res.json()["message"]

    # Verify directly in PostgreSQL revoked_tokens table
    db = SessionLocal()
    try:
        revoked_record = db.query(RevokedToken).filter(RevokedToken.user_id == auth_state["user_1_id"]).first()
        assert revoked_record is not None
        assert revoked_record.jti is not None
        assert len(revoked_record.token_hash) == 64
    finally:
        db.close()


def test_18_reuse_of_revoked_token_rejected():
    """Verify reuse of the old revoked token on protected endpoints is rejected with HTTP 401."""
    revoked_token = auth_state["token_1"]

    # Attempt 1: Calling /api/auth/me with revoked token
    res_me = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {revoked_token}"},
    )
    assert res_me.status_code == 401
    assert "Token has been revoked" in res_me.json()["detail"]

    # Attempt 2: Calling /api/auth/logout again with already-revoked token
    res_logout = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {revoked_token}"},
    )
    assert res_logout.status_code == 401
    assert "Token has been revoked" in res_logout.json()["detail"]


def test_19_login_after_logout_issues_new_valid_token():
    """Verify logging in again after logout issues a fresh valid token that works."""
    res_relogin = client.post(
        "/api/auth/login",
        json={
            "email": TEST_USER_1_EMAIL,
            "password": TEST_PASSWORD,
        },
    )
    assert res_relogin.status_code == 200
    new_token = res_relogin.json()["access_token"]
    assert new_token != auth_state["token_1"]

    # Verify new token works on /api/auth/me
    res_me_new = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {new_token}"},
    )
    assert res_me_new.status_code == 200
    assert res_me_new.json()["email"] == TEST_USER_1_EMAIL


def test_20_existing_data_and_database_state():
    """Verify existing database data and Alembic migration status."""
    db = SessionLocal()
    try:
        # Check Alembic version table has current revision
        res_alembic = db.execute(text("SELECT version_num FROM alembic_version;")).scalar()
        assert res_alembic is not None
        assert len(res_alembic) > 0

        # Check existing pre-created users are still intact
        count = db.execute(text("SELECT count(*) FROM users WHERE id IN (2, 3);")).scalar()
        assert count == 2
    finally:
        db.close()
