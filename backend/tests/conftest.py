import os
import tempfile

# Must be set BEFORE the app is imported. Defaults to SQLite so tests run anywhere;
# run against PostgreSQL with:  TEST_DATABASE_URL=postgresql+psycopg2://... pytest
_db = os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["DATABASE_URL"] = _db
os.environ["WORKFLOW_DELAY_SECONDS"] = "0"
os.environ["MARKET_DATA_PROVIDER"] = "demo"
os.environ["BCRYPT_ROUNDS"] = "4"
os.environ["COOKIE_SECURE"] = "false"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


GOOD = {"full_name": "Asha Verma", "email": "asha@example.com", "password": "Str0ngPass", "confirm_password": "Str0ngPass"}


def register(c, **over):
    return c.post("/api/auth/register", json={**GOOD, **over})


def login(c, email="asha@example.com", password="Str0ngPass"):
    r = c.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture
def user_client(client):
    """A client signed in as Asha. Sends CSRF header automatically."""
    register(client)
    data = login(client)
    client.headers["X-CSRF-Token"] = data["csrf_token"]
    return client


@pytest.fixture
def make_client():
    """Create an additional independent signed-in client (a second user)."""
    clients = []

    def _make(email, name="Other User"):
        c = TestClient(app)
        c.__enter__()
        clients.append(c)
        register(c, email=email, full_name=name)
        data = login(c, email=email)
        c.headers["X-CSRF-Token"] = data["csrf_token"]
        return c

    yield _make
    for c in clients:
        c.__exit__(None, None, None)
