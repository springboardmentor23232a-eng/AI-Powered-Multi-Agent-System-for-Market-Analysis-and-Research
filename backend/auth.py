
import bcrypt
import jwt

from datetime import datetime, timedelta, timezone

from config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)


# 1. Hash a user's password
def hash_password(password: str) -> str:

    password_bytes = password.encode("utf-8")

    # bcrypt supports a maximum of 72 password bytes
    if len(password_bytes) > 72:
        raise ValueError("Password must not exceed 72 UTF-8 bytes")

    salt = bcrypt.gensalt()

    hashed = bcrypt.hashpw(password_bytes, salt)

    return hashed.decode("utf-8")


# 2. Verify a password during login
def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:

    password_bytes = plain_password.encode("utf-8")

    if len(password_bytes) > 72:
        return False

    return bcrypt.checkpw(
        password_bytes,
        hashed_password.encode("utf-8")
    )


# 3. Generate a JWT access token
def create_access_token(data: dict) -> str:

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire
    })

    token = jwt.encode(
        to_encode,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )

    return token


# 4. Verify and decode a JWT access token
def verify_access_token(token: str) -> dict:

    payload = jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM]
    )

    return payload
