"""Shared pytest fixtures.

By default tests run against an in-memory SQLite database (fast, nothing to install).
To run the same tests against PostgreSQL, set TEST_DATABASE_URL, e.g.
    TEST_DATABASE_URL=postgresql+psycopg://stockapp:stockapp@localhost:5432/stock_research_test pytest
Every test starts with empty tables.
"""

import os

# Must be set before the app is imported, because settings are read at import time.
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-that-is-at-least-32-characters")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, build_engine, get_db
from app.main import app

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "sqlite://")
API = "/api/v1"
DEFAULT_PASSWORD = "Str0ngPassw0rd"


def _make_engine():
    if TEST_DATABASE_URL != "sqlite://":
        return build_engine(TEST_DATABASE_URL)

    # In-memory SQLite: StaticPool makes every connection share the same database.
    engine = create_engine(
        TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    return engine


test_engine = _make_engine()
TestingSession = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def db_session():
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(test_engine)  # leave the test database empty afterwards


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def register(client, email="alice@example.com", password=DEFAULT_PASSWORD):
    return client.post(f"{API}/auth/register", json={"email": email, "password": password})


def login(client, email="alice@example.com", password=DEFAULT_PASSWORD):
    return client.post(f"{API}/auth/login", data={"username": email, "password": password})


def auth_headers_for(client, email="alice@example.com", password=DEFAULT_PASSWORD):
    register(client, email, password)
    token = login(client, email, password).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def auth_headers(client):
    return auth_headers_for(client)
