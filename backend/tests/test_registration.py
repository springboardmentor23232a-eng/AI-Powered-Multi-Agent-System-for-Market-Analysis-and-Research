from app.models.user import User


def test_successful_user_registration(client, db_session):
    payload = {
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["email"] == "john.doe@example.com"
    assert data["data"]["full_name"] == "John Doe"
    assert "user_id" in data["data"]
    assert "password" not in data["data"]
    assert "password_hash" not in data["data"]

    # Verify in DB
    db_user = db_session.query(User).filter(User.email == "john.doe@example.com").first()
    assert db_user is not None
    assert db_user.password_hash.startswith("$2b$")


def test_camel_case_compatibility(client):
    payload = {
        "fullName": "Alice Smith",
        "email": "alice@example.com",
        "password": "SecurePass88",
        "confirmPassword": "SecurePass88",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    assert response.json()["data"]["email"] == "alice@example.com"


def test_duplicate_email_registration_fails(client):
    payload = {
        "full_name": "Bob Jones",
        "email": "bob@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
    }
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_password_mismatch_fails(client):
    payload = {
        "full_name": "Charlie Brown",
        "email": "charlie@example.com",
        "password": "Password123!",
        "confirm_password": "DifferentPassword999!",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422
    assert "not match" in response.json()["detail"].lower()


def test_invalid_email_format_fails(client):
    payload = {
        "full_name": "David Miller",
        "email": "invalid-email-format",
        "password": "Password123!",
        "confirm_password": "Password123!",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422


def test_weak_password_missing_number(client):
    payload = {
        "full_name": "Eve Adams",
        "email": "eve@example.com",
        "password": "NoNumbersHere!",
        "confirm_password": "NoNumbersHere!",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422
    assert "digit" in response.json()["detail"].lower()


def test_weak_password_missing_uppercase(client):
    payload = {
        "full_name": "Frank White",
        "email": "frank@example.com",
        "password": "lowercase1234!",
        "confirm_password": "lowercase1234!",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422
    assert "uppercase" in response.json()["detail"].lower()
