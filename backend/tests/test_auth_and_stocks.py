from datetime import timedelta
import jwt
from app.config import settings
from app.services.security import create_access_token


def test_registration_and_login_flow(client):
    # 1. Register
    reg_payload = {
        "fullName": "Sai Kumar",
        "email": "saikumar.test@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    assert reg_res.json()["data"]["email"] == "saikumar.test@example.com"

    # 2. Login with correct credentials
    login_payload = {
        "email": "saikumar.test@example.com",
        "password": "Password123!",
    }
    login_res = client.post("/api/auth/login", json=login_payload)
    assert login_res.status_code == 200
    assert login_res.json()["status"] == "success"
    assert login_res.json()["data"]["full_name"] == "Sai Kumar"

    # Verify HTTP-only cookie was issued
    assert settings.AUTH_COOKIE_NAME in login_res.cookies
    token = login_res.cookies[settings.AUTH_COOKIE_NAME]

    # Decode and verify token structure
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert payload["sub"] == str(login_res.json()["data"]["user_id"])
    assert "exp" in payload
    assert payload["email"] == "saikumar.test@example.com"

    # 3. Access protected /me endpoint with cookie
    me_res = client.get("/api/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["data"]["email"] == "saikumar.test@example.com"

    # 4. Access protected stock endpoints with authenticated session
    stock_res = client.get("/api/stocks/search?q=Infosys")
    assert stock_res.status_code == 200
    assert stock_res.json()["count"] >= 1

    # 5. Logout clears the cookie
    logout_res = client.post("/api/auth/logout")
    assert logout_res.status_code == 200
    assert logout_res.json()["message"] == "Logged out successfully."

    # 6. Accessing protected endpoint after logout fails with 401
    post_logout_res = client.get("/api/auth/me")
    assert post_logout_res.status_code == 401

    # 7. Login with wrong password fails
    wrong_login = {
        "email": "saikumar.test@example.com",
        "password": "WrongPassword999!",
    }
    wrong_res = client.post("/api/auth/login", json=wrong_login)
    assert wrong_res.status_code == 401
    assert "Invalid email or password" in wrong_res.json()["detail"]


def test_unauthenticated_request_rejected(client):
    # Ensure client has no cookies
    client.cookies.clear()
    res = client.get("/api/stocks/search?q=Infosys")
    assert res.status_code == 401
    assert "Authentication required" in res.json()["detail"]


def test_invalid_token_rejected(client):
    client.cookies.clear()
    client.cookies.set(settings.AUTH_COOKIE_NAME, "this.is.a.completely.invalid.token")
    res = client.get("/api/stocks/search?q=Infosys")
    assert res.status_code == 401
    assert "Invalid or malformed" in res.json()["detail"]


def test_expired_token_rejected(client):
    client.cookies.clear()
    expired_token = create_access_token(
        user_id=1,
        email="expired@example.com",
        expires_delta=timedelta(minutes=-10),  # expired 10 minutes ago
    )
    client.cookies.set(settings.AUTH_COOKIE_NAME, expired_token)
    res = client.get("/api/stocks/search?q=Infosys")
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower()


def test_nonexistent_user_id_in_token_rejected(client):
    client.cookies.clear()
    nonexistent_token = create_access_token(
        user_id=999999,
        email="ghost@example.com",
    )
    client.cookies.set(settings.AUTH_COOKIE_NAME, nonexistent_token)
    res = client.get("/api/stocks/search?q=Infosys")
    assert res.status_code == 401
    assert "no longer exists" in res.json()["detail"].lower()
