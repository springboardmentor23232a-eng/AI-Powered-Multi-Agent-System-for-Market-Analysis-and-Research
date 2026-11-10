from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models import ResearchTask, SourceDocument, User
from app.services import market_data as md
from app.services.market_data import ProviderError
from tests.fakes import FakeProvider

NOW = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)


def test_ticker_normalization():
    assert md.normalize_ticker(" tcs.ns ") == "TCS"
    assert md.provider_symbol("tcs", "NSE") == "TCS.NS"


def test_cache_hit_avoids_second_provider_call(db):
    p = FakeProvider()
    a = md.get_prices(db, p, "TCS", now=NOW)
    b = md.get_prices(db, p, "TCS", now=NOW + timedelta(hours=1))
    assert p.calls == 1 and not a.source.from_cache and b.source.from_cache
    assert a.source.content_hash == b.source.content_hash and len(a.rows) == 120


def test_expired_cache_refetches(db):
    p = FakeProvider()
    md.get_prices(db, p, "TCS", now=NOW)
    md.get_prices(db, p, "TCS", now=NOW + timedelta(hours=13))
    assert p.calls == 2


def test_provider_failure_falls_back_to_stale_snapshot(db):
    md.get_prices(db, FakeProvider(), "TCS", now=NOW)
    res = md.get_prices(db, FakeProvider(fail=True), "TCS", now=NOW + timedelta(days=2))
    assert res.source.stale_cache
    assert "provider_unavailable" in {i.code for i in res.validation.issues}


def test_provider_failure_without_cache_raises(db):
    with pytest.raises(ProviderError):
        md.get_prices(db, FakeProvider(fail=True), "TCS", now=NOW)


def test_as_of_replay_excludes_future_rows(db):
    res = md.get_prices(db, FakeProvider(), "TCS", period="3mo", as_of=date(2026, 9, 15), now=NOW)
    assert res.rows and res.rows[-1]["date"] <= "2026-09-15"
    assert res.rows[0]["date"] >= "2026-06-15"


def test_source_document_logged_for_task(db):
    user = User(email="u@x.com", password_hash="x")
    db.add(user); db.commit()
    task = ResearchTask(user_id=user.user_id, ticker="TCS")
    db.add(task); db.commit()
    md.get_prices(db, FakeProvider(), "TCS", task_id=task.task_id, now=NOW)
    md.get_financials(db, FakeProvider(), "TCS", task_id=task.task_id, now=NOW)
    docs = db.scalars(select(SourceDocument)).all()
    assert {d.source_type for d in docs} == {"price", "financials"}
    assert all(len(d.content_hash) == 64 for d in docs)


def test_financials_report_missing_fields(db):
    res = md.get_financials(db, FakeProvider(), "TCS", now=NOW)
    assert "missing_total_debt" in {i.code for i in res.issues}
