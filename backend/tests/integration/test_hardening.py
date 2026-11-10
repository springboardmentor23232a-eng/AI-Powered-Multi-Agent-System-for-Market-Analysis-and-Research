import json
import logging
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.api.research import get_llm, get_news_provider
from app.api.stocks import get_provider
from app.core.config import Settings, settings, validate_production
from app.core.logging import JsonFormatter
from app.core.ratelimit import SlidingWindowLimiter
from app.main import app
from app.models import ResearchTask, TaskStatus, User
from app.services.llm import TemplateLLM
from app.services.maintenance import reconcile_stale_tasks
from tests.fakes import FIN, FakeNews, FakeProvider, article, make_ohlcv

GOOD = dict(environment="production", jwt_secret="x" * 40, database_url="postgresql+psycopg2://u:p@db/v",
            cors_origins="https://app.example.com")


def test_production_config_guard():
    validate_production(Settings(**GOOD))                              # safe config starts
    validate_production(Settings())                                    # development is not restricted
    for bad, fragment in [({"jwt_secret": "dev-only-secret-change-me"}, "JWT_SECRET"), ({"jwt_secret": "short"}, "JWT_SECRET"),
                          ({"database_url": "sqlite:///x.db"}, "PostgreSQL"), ({"cors_origins": "*"}, "CORS_ORIGINS")]:
        with pytest.raises(RuntimeError, match=fragment):
            validate_production(Settings(**{**GOOD, **bad}))


def test_sliding_window_limiter():
    t = [0.0]
    lim = SlidingWindowLimiter(60, clock=lambda: t[0])
    assert all(lim.allow("ip", 3) for _ in range(3)) and not lim.allow("ip", 3)
    assert lim.allow("other", 3)                                       # keys are independent
    t[0] = 61
    assert lim.allow("ip", 3)                                          # window slid


def test_auth_endpoints_are_rate_limited(client, monkeypatch):
    monkeypatch.setattr(settings, "auth_attempts_per_minute", 3)
    codes = [client.post("/auth/login", json={"email": "a@b.com", "password": "password123"}).status_code for _ in range(5)]
    assert codes == [401, 401, 401, 429, 429]
    r = client.post("/auth/register", json={"email": "z@b.com", "password": "password123"})
    assert r.status_code == 429 and r.headers["Retry-After"] == "60"


@pytest.fixture()
def api(file_client):
    app.dependency_overrides[get_provider] = lambda: FakeProvider(df=make_ohlcv(400), financials=FIN)
    app.dependency_overrides[get_news_provider] = lambda: FakeNews([article("TCS wins large deal", 1)])
    app.dependency_overrides[get_llm] = lambda: TemplateLLM()
    return file_client


def _login(c):
    t = c.post("/auth/register", json={"email": "a@b.com", "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {t}"}


def test_active_task_quota(api, file_session_factory, monkeypatch):
    h = _login(api)
    with file_session_factory() as db:
        uid = db.scalar(select(User)).user_id
        for _ in range(3):
            db.add(ResearchTask(user_id=uid, ticker="TCS", status=TaskStatus.running))
        db.commit()
    r = api.post("/research", json={"ticker": "TCS"}, headers=h)
    assert r.status_code == 429 and "already have 3" in r.json()["detail"]


def test_daily_task_quota(api, monkeypatch):
    monkeypatch.setattr(settings, "max_tasks_per_day", 2)
    h = _login(api)
    assert [api.post("/research", json={"ticker": "TCS"}, headers=h).status_code for _ in range(3)] == [202, 202, 429]


def test_stale_tasks_are_failed_on_startup(file_session_factory):
    now = datetime(2026, 11, 5, 12, tzinfo=timezone.utc)
    with file_session_factory() as db:
        u = User(email="u@x.com", password_hash="x"); db.add(u); db.commit()
        old = ResearchTask(user_id=u.user_id, ticker="TCS", status=TaskStatus.running, created_at=now - timedelta(hours=2))
        fresh = ResearchTask(user_id=u.user_id, ticker="INFY", status=TaskStatus.queued, created_at=now - timedelta(minutes=2))
        done = ResearchTask(user_id=u.user_id, ticker="ITC", status=TaskStatus.completed, created_at=now - timedelta(hours=5))
        db.add_all([old, fresh, done]); db.commit()
        ids = (old.task_id, fresh.task_id, done.task_id)
    assert reconcile_stale_tasks(file_session_factory, 30, now) == 1
    with file_session_factory() as db:
        o, f, d = (db.get(ResearchTask, i) for i in ids)
        assert o.status == TaskStatus.failed and "restart" in o.error_message and o.completed_at is not None
        assert f.status == TaskStatus.queued and d.status == TaskStatus.completed


def test_ready_and_request_logging(client, caplog):
    with caplog.at_level(logging.INFO, logger="veritas.api"):
        r = client.get("/health", headers={"Authorization": "Bearer secret-token"})
    assert r.status_code == 200 and len(r.headers["X-Request-ID"]) == 12
    rec = next(x for x in caplog.records if x.name == "veritas.api")
    line = json.loads(JsonFormatter().format(rec))
    assert line["path"] == "/health" and line["status"] == 200 and line["request_id"] == r.headers["X-Request-ID"]
    assert "secret-token" not in json.dumps(line)                       # credentials are never logged


def test_ready_reports_database_state(client, monkeypatch, tmp_path):
    import app.main as main
    from sqlalchemy import create_engine
    monkeypatch.setattr(main, "engine", create_engine(f"sqlite:///{tmp_path / 'ok.db'}"))
    assert client.get("/ready").json() == {"status": "ready"}
    monkeypatch.setattr(main, "engine", create_engine("postgresql+psycopg2://u:p@127.0.0.1:1/none", connect_args={"connect_timeout": 1}))
    assert client.get("/ready").status_code == 503
