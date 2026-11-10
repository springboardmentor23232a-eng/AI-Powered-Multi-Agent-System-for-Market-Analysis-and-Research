def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_register_login_and_protected_route(client):
    r = client.post("/auth/register", json={"email": "a@b.com", "password": "password123"})
    assert r.status_code == 201
    assert client.post("/auth/register", json={"email": "A@b.com", "password": "password123"}).status_code == 409

    token = client.post("/auth/login", json={"email": "a@b.com", "password": "password123"}).json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200 and me.json()["email"] == "a@b.com"


def test_bad_credentials_and_missing_token(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "password123"})
    assert client.post("/auth/login", json={"email": "a@b.com", "password": "wrong-password"}).status_code == 401
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer junk"}).status_code == 401


def test_registration_full_name_and_password_confirmation(client):
    # Password mismatch
    mismatch = client.post("/auth/register", json={
        "full_name": "Test Analyst",
        "email": "analyst@veritas.com",
        "password": "Password123!",
        "confirm_password": "DifferentPassword!"
    })
    assert mismatch.status_code == 422

    # Successful registration with full name and matching password
    success = client.post("/auth/register", json={
        "full_name": "Test Analyst",
        "email": "analyst@veritas.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    assert success.status_code == 201
    token = success.json()["access_token"]

    # Verify full name returned in /auth/me
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["full_name"] == "Test Analyst"
    assert me.json()["email"] == "analyst@veritas.com"
