from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.graph.workflow import Deps, build_graph
from app.models import (AgentResult as AgentRow, Claim, ResearchReport, ResearchTask, SourceDocument, TaskStatus, User)
from app.services.llm import TemplateLLM
from app.services.research import execute_task
from tests.fakes import FIN, FakeNews, FakeProvider, article, make_ohlcv

NOW = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)


def new_task(factory, **kw):
    with factory() as db:
        u = User(email=f"{kw.get('ticker','TCS')}@x.com", password_hash="x"); db.add(u); db.commit()
        t = ResearchTask(user_id=u.user_id, ticker=kw.get("ticker", "TCS"), requested_period="2y",
                         as_of_date=kw.get("as_of")); db.add(t); db.commit()
        return t.task_id


def deps(factory, news=None, market=None, **kw):
    arts = [article("TCS profit rises as results beat estimates", 1), article("TCS wins large deal", 2)]
    return Deps(session_factory=factory, market=market or FakeProvider(df=make_ohlcv(400), financials=FIN),
                news=news if news is not None else FakeNews(arts), llm=TemplateLLM(), backoff_seconds=0, now=NOW, **kw)


def snapshot(factory, task_id):
    with factory() as db:
        task = db.get(ResearchTask, task_id)
        agents = {a.agent_name: a for a in db.scalars(select(AgentRow).where(AgentRow.task_id == task_id))}
        claims = list(db.scalars(select(Claim).where(Claim.task_id == task_id)))
        report = db.scalar(select(ResearchReport).where(ResearchReport.task_id == task_id))
        return task, agents, claims, report


def test_end_to_end_completed(file_session_factory):
    tid = new_task(file_session_factory)
    execute_task(tid, deps(file_session_factory))
    task, agents, claims, report = snapshot(file_session_factory, tid)
    assert task.status == TaskStatus.completed and task.latency_ms is not None
    assert set(agents) == {"fundamental", "technical", "news", "risk"}
    assert all(a.status.value == "success" for a in agents.values())
    assert claims and all(c.verified for c in claims)            # every emitted claim verifies
    assert report and "Evidence score" in report.report_content and "TCS" in report.report_content
    for ref in ("fundamental-1", "technical-1"):
        assert ref in report.report_content
    with file_session_factory() as db:   # source docs are deduplicated per task
        docs = list(db.scalars(select(SourceDocument).where(SourceDocument.task_id == tid)))
    assert len({(d.source_type, d.content_hash) for d in docs}) == len(docs)


def test_failure_drill_news_down_marks_unavailable_and_invents_nothing(file_session_factory):
    tid = new_task(file_session_factory)
    execute_task(tid, deps(file_session_factory, news=FakeNews(fail=True), max_retries=2))
    task, agents, claims, report = snapshot(file_session_factory, tid)
    assert task.status == TaskStatus.partial
    assert agents["news"].status.value == "unavailable" and agents["news"].attempts == 3   # 1 try + 2 retries
    assert not [c for c in claims if c.agent_name == "news"]
    assert "> **Unavailable.**" in report.report_content and "[news] section unavailable" in report.limitations
    assert agents["fundamental"].status.value == "success"


def test_retry_recovers_from_transient_failure(file_session_factory):
    class Flaky(FakeNews):
        def fetch(self, query, limit=15):
            self.n = getattr(self, "n", 0) + 1
            if self.n == 1:
                from app.services.market_data import ProviderError
                raise ProviderError("blip")
            return super().fetch(query, limit)
    tid = new_task(file_session_factory)
    execute_task(tid, deps(file_session_factory, news=Flaky([article("TCS wins large deal")])))
    task, agents, *_ = snapshot(file_session_factory, tid)
    assert agents["news"].status.value == "success" and agents["news"].attempts == 2
    assert task.status == TaskStatus.completed


def test_market_data_outage_gives_partial_report_from_news_only(file_session_factory):
    tid = new_task(file_session_factory)
    execute_task(tid, deps(file_session_factory, market=FakeProvider(fail=True), max_retries=1))
    task, agents, claims, report = snapshot(file_session_factory, tid)
    assert task.status == TaskStatus.partial
    assert {n: a.status.value for n, a in agents.items()} == {
        "fundamental": "unavailable", "technical": "unavailable", "news": "success", "risk": "unavailable"}
    assert report and all(c.agent_name == "news" for c in claims)


def test_total_outage_fails_task_without_report(file_session_factory):
    tid = new_task(file_session_factory)
    execute_task(tid, deps(file_session_factory, market=FakeProvider(fail=True), news=FakeNews(fail=True), max_retries=1))
    task, agents, claims, report = snapshot(file_session_factory, tid)
    assert task.status == TaskStatus.failed and report is None and "No analysis" in task.error_message


def test_replay_mode_skips_news(file_session_factory):
    tid = new_task(file_session_factory, as_of=datetime(2026, 7, 1, tzinfo=timezone.utc))
    execute_task(tid, deps(file_session_factory))
    task, agents, claims, report = snapshot(file_session_factory, tid)
    assert agents["news"].status.value == "unavailable"
    assert "Replay as of 2026-07-01" in report.report_content


def test_unexpected_agent_error_is_recorded_as_failed(file_session_factory):
    class Boom(FakeProvider):
        def get_financials(self, symbol):
            raise RuntimeError("parser exploded")
    tid = new_task(file_session_factory)
    execute_task(tid, deps(file_session_factory, market=Boom(df=make_ohlcv(400))))
    task, agents, *_ = snapshot(file_session_factory, tid)
    assert agents["fundamental"].status.value == "failed" and agents["technical"].status.value == "success"
    assert task.status == TaskStatus.partial


def test_graph_returns_structured_state(file_session_factory):
    tid = new_task(file_session_factory)
    final = build_graph(deps(file_session_factory)).invoke(
        {"ticker": "TCS", "market": "NSE", "period": "2y", "as_of": None, "task_id": tid})
    assert set(final["results"]) == {"fundamental", "technical", "news", "risk"} and final["report"]["score"]["percent"] == 100.0
