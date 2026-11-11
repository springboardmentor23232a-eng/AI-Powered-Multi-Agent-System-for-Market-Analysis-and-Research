import pytest


def test_register_success(client):
    payload = {
        "full_name": "Jane Doe",
        "email": "jane@example.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!"
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201
    assert res.json()["success"] is True


def test_register_duplicate_email(client):
    payload = {
        "full_name": "Jane Doe",
        "email": "jane_dup@example.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!"
    }
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    # Second attempt with same email
    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_register_password_mismatch(client):
    payload = {
        "full_name": "Bob Smith",
        "email": "bob@example.com",
        "password": "SecurePassword123!",
        "confirm_password": "DifferentPassword123!"
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 422


def test_register_weak_password(client):
    payload = {
        "full_name": "Bob Smith",
        "email": "bob_weak@example.com",
        "password": "weak",
        "confirm_password": "weak"
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 422


def test_login_success_and_me(client):
    reg = {
        "full_name": "Alice Johnson",
        "email": "alice@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    }
    client.post("/api/auth/register", json=reg)

    login_res = client.post("/api/auth/login", json={"email": "alice@example.com", "password": "Password123!"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    assert token is not None

    # Test me endpoint with bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "alice@example.com"
    assert me_res.json()["full_name"] == "Alice Johnson"


def test_login_invalid_password(client):
    reg = {
        "full_name": "Charlie Brown",
        "email": "charlie@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    }
    client.post("/api/auth/register", json=reg)

    res = client.post("/api/auth/login", json={"email": "charlie@example.com", "password": "WrongPassword!"})
    assert res.status_code == 401


def test_protected_route_unauthorized(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401

