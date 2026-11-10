"""Runs only when TEST_DATABASE_URL points at a disposable PostgreSQL database."""
import os
import subprocess
import sys
import threading
from datetime import datetime, timezone

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import MetaData, create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.graph.workflow import Deps
from app.models import Claim, ResearchReport, ResearchTask, TaskStatus, User
from app.services.llm import TemplateLLM
from app.services.research import execute_task
from tests.fakes import FIN, FakeNews, FakeProvider, article, make_ohlcv

URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="TEST_DATABASE_URL not set")
BACKEND = os.path.join(os.path.dirname(__file__), "..", "..")


@pytest.fixture(scope="module")
def engine():
    eng = create_engine(URL, pool_pre_ping=True)
    meta = MetaData()
    meta.reflect(bind=eng)
    meta.drop_all(bind=eng)                                   # start from an empty database
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True, cwd=BACKEND,
                   env={**os.environ, "DATABASE_URL": URL})
    return eng


def test_migrations_match_models(engine):
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diff == [], diff


def test_concurrent_workflows_on_postgres(engine):
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    now = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
    with factory() as db:
        user = User(email="pg@x.com", password_hash="x"); db.add(user); db.commit()
        ids = []
        for ticker in ("TCS", "TCS", "INFY"):                  # two tasks share one cache key: exercises the race path
            t = ResearchTask(user_id=user.user_id, ticker=ticker, requested_period="2y"); db.add(t); db.commit()
            ids.append(t.task_id)

    def run(tid):
        execute_task(tid, Deps(session_factory=factory, market=FakeProvider(df=make_ohlcv(400), financials=FIN),
                               news=FakeNews([article("TCS wins large deal")]), llm=TemplateLLM(),
                               backoff_seconds=0, now=now))

    threads = [threading.Thread(target=run, args=(i,)) for i in ids]
    [t.start() for t in threads]
    [t.join() for t in threads]

    with factory() as db:
        for tid in ids:
            assert db.get(ResearchTask, tid).status == TaskStatus.completed
            claims = list(db.scalars(select(Claim).where(Claim.task_id == tid)))
            assert claims and all(c.verified for c in claims)
            assert db.scalar(select(ResearchReport).where(ResearchReport.task_id == tid))
