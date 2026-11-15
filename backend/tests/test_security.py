"""Unit tests for password hashing and JWT handling."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.config import get_settings
from app.core.security import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_is_hashed_not_stored_plain():
    hashed = hash_password("Str0ngPassw0rd")
    assert hashed != "Str0ngPassw0rd"
    assert hashed.startswith("$argon2id$")


def test_same_password_gets_different_hashes():
    # A random salt is added each time, so equal passwords do not produce equal hashes.
    assert hash_password("Str0ngPassw0rd") != hash_password("Str0ngPassw0rd")


def test_verify_password_correct_and_incorrect():
    hashed = hash_password("Str0ngPassw0rd")
    assert verify_password("Str0ngPassw0rd", hashed) is True
    assert verify_password("wrong-password1", hashed) is False


def test_verify_password_without_user_returns_false():
    assert verify_password("anything1", None) is False


def test_token_round_trip():
    token = create_access_token(42)
    assert decode_access_token(token) == 42


def test_expired_token_is_rejected():
    token = create_access_token(1, expires_delta=timedelta(seconds=-1))
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_tampered_token_is_rejected():
    token = create_access_token(1)
    header, payload, signature = token.split(".")
    tampered = f"{header}.{payload}.{signature[:-2]}xx"
    with pytest.raises(InvalidTokenError):
        decode_access_token(tampered)


def test_token_signed_with_other_secret_is_rejected():
    forged = jwt.encode(
        {"sub": "1", "type": "access", "iat": datetime.now(UTC),
         "exp": datetime.now(UTC) + timedelta(minutes=5)},
        "some-other-secret-that-is-also-32-characters-long",
        algorithm="HS256",
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(forged)


def test_unsigned_none_algorithm_token_is_rejected():
    unsigned = jwt.encode(
        {"sub": "1", "type": "access", "iat": datetime.now(UTC),
         "exp": datetime.now(UTC) + timedelta(minutes=5)},
        key=None,
        algorithm="none",
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(unsigned)


def test_token_with_wrong_type_is_rejected():
    settings = get_settings()
    token = jwt.encode(
        {"sub": "1", "type": "refresh", "iat": datetime.now(UTC),
         "exp": datetime.now(UTC) + timedelta(minutes=5)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_token_with_non_numeric_subject_is_rejected():
    settings = get_settings()
    token = jwt.encode(
        {"sub": "not-a-number", "type": "access", "iat": datetime.now(UTC),
         "exp": datetime.now(UTC) + timedelta(minutes=5)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_token_missing_expiry_is_rejected():
    settings = get_settings()
    token = jwt.encode(
        {"sub": "1", "type": "access", "iat": datetime.now(UTC)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)
