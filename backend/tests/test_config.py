"""Tests for settings validation."""

import pytest
from pydantic import ValidationError

from app.core.config import INSECURE_DEFAULT_SECRET, Settings


def test_short_jwt_secret_is_rejected():
    with pytest.raises(ValidationError):
        Settings(jwt_secret_key="too-short")


def test_production_refuses_placeholder_secret():
    settings = Settings(environment="production", jwt_secret_key=INSECURE_DEFAULT_SECRET)
    with pytest.raises(RuntimeError):
        settings.assert_safe_for_production()


def test_production_accepts_real_secret():
    settings = Settings(environment="production", jwt_secret_key="x" * 48)
    settings.assert_safe_for_production()  # does not raise


def test_cors_origins_are_split_and_trimmed():
    settings = Settings(
        jwt_secret_key="x" * 48, cors_origins=" http://localhost:5173 , https://app.example.com ,"
    )
    assert settings.cors_origin_list == ["http://localhost:5173", "https://app.example.com"]
