from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest
from sqlalchemy import select

from app.agents.base import AgentContext
from app.agents.contradictions import detect_contradictions
from app.agents.fundamental import FundamentalAgent
from app.agents.news import NewsAgent, event_type
from app.agents.risk import RiskAgent
from app.agents.technical import TechnicalAgent
from app.models import ResearchTask, SourceDocument, User
from app.schemas.agents import AgentResult, AgentStatus
from app.schemas.claims import ClaimType
from app.services.llm import TemplateLLM, numbers_grounded
from app.services.market_data import ProviderError
from app.tools import run_tool
from tests.fakes import FIN, FakeNews, FakeProvider, article, make_ohlcv

NOW = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)


def ctx_for(db, market=None, news=None, **kw):
    return AgentContext(db=db, market=market or FakeProvider(financials=FIN), news=news or FakeNews(),
                        llm=TemplateLLM(), ticker="TCS", now=NOW, **kw)


def assert_reproducible(result: AgentResult):
    """Every CALCULATED claim must re-run through the tool registry to the same value."""
    n = 0
    for c in result.claims:
        if c.type == ClaimType.CALCULATED:
            again = run_tool(c.evidence.function, c.evidence.inputs)
            assert again == pytest.approx(c.evidence.result, abs=1e-9) if not isinstance(again, dict) else \
                all(again[k] == pytest.approx(c.evidence.result[k], abs=1e-9) for k in again)
            n += 1
    assert n > 0


def test_fundamental_values_and_claims(db):
    r = FundamentalAgent().run(ctx_for(db))
    assert r.status == AgentStatus.success
    m = r.data["metrics"]
    assert m["revenue_growth"] == pytest.approx(100 / 90 - 1)
    assert m["net_margin"] == pytest.approx(0.15) and m["debt_to_equity"] == pytest.approx(0.375)
    assert m["roe"] == pytest.approx(15 / 75)
    assert m["pe"] == pytest.approx(159.5 / 3.0) and m["pb"] == pytest.approx(159.5 / 16.0)
    assert_reproducible(r)
    types = {c.type for c in r.claims}
    assert types == {ClaimType.FACT, ClaimType.CALCULATED, ClaimType.INTERPRETATION}
    assert r.data["signal"] == "bullish"


def test_fundamental_unavailable_without_statements(db):
    r = FundamentalAgent().run(ctx_for(db, market=FakeProvider(financials={"profile": {"longName": "x"}, "annual": []})))
    assert r.status == AgentStatus.unavailable and not r.claims


def test_fundamental_reports_missing_data_instead_of_inventing(db):
    fin = {"profile": {}, "annual": [{"year": 2025, "revenue": 100.0, "net_income": -5.0}]}
    r = FundamentalAgent().run(ctx_for(db, market=FakeProvider(financials=fin)))
    assert r.data["metrics"]["debt_to_equity"] is None and r.data["metrics"]["pe"] is None
    assert any("P/E" in l for l in r.limitations)


def test_technical_bullish_trend(db):
    r = TechnicalAgent().run(ctx_for(db, market=FakeProvider(df=make_ohlcv(300))))
    assert r.status == AgentStatus.success and r.data["signal"] == "bullish"
    assert r.data["indicators"]["rsi14"] > 70 and "RSI above 70 (overbought)" in r.data["conditions"]
    assert_reproducible(r)
    chart = r.data["chart"]
    assert len(chart["dates"]) == len(chart["close"]) == len(chart["sma50"]) and chart["sma50"][0] is None


def test_technical_bearish_trend(db):
    df = make_ohlcv(300)
    df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].iloc[::-1].to_numpy()
    r = TechnicalAgent().run(ctx_for(db, market=FakeProvider(df=df)))
    assert r.data["signal"] == "bearish"


def test_technical_short_history_is_neutral_and_flags_missing_sma200(db):
    r = TechnicalAgent().run(ctx_for(db))   # 120 sessions: no 200-day SMA possible
    assert r.data["signal"] == "neutral" and r.data["indicators"]["sma200"] is None
    assert any("200-day SMA not computed" in l for l in r.limitations)


def test_technical_unavailable_on_short_history(db):
    r = TechnicalAgent().run(ctx_for(db, market=FakeProvider(df=make_ohlcv(10))))
    assert r.status == AgentStatus.unavailable and not r.claims


def test_news_claims_sources_and_sentiment(db):
    user = User(email="u@x.com", password_hash="x"); db.add(user); db.commit()
    task = ResearchTask(user_id=user.user_id, ticker="TCS"); db.add(task); db.commit()
    arts = [article("TCS profit rises as quarter results beat estimates", 1),
            article("TCS shares fall after SEBI probe announced", 2),
            article("TCS profit rises as quarter results beat estimates", 3, url="https://news.test/dup"),
            article("Old story about TCS", 90)]
    arts.append(arts[0])  # exact duplicate (same url)
    r = NewsAgent().run(ctx_for(db, news=FakeNews(arts), task_id=task.task_id))
    assert r.status == AgentStatus.success
    items = r.data["items"]
    assert len(items) == 3                                   # old + exact duplicate dropped
    assert {i["sentiment"] for i in items} == {"positive", "negative"}
    # every FACT quote is literally present in its logged source document
    docs = {d.content_hash: d for d in db.scalars(select(SourceDocument).where(SourceDocument.source_type == "news"))}
    facts = [c for c in r.claims if c.type == ClaimType.FACT]
    assert len(facts) == 3 and all(f.evidence.quote in docs[f.evidence.content_hash].content_excerpt for f in facts)


def test_news_conflicting_reports_flagged(db):
    arts = [article("TCS profit rises, results beat estimates"), article("TCS quarterly results disappoint, profit falls")]
    r = NewsAgent().run(ctx_for(db, news=FakeNews(arts)))
    assert any("Conflicting reports on earnings" in l for l in r.limitations)


def test_news_failure_and_empty_and_replay(db):
    with pytest.raises(ProviderError):
        NewsAgent().run(ctx_for(db, news=FakeNews(fail=True)))
    assert NewsAgent().run(ctx_for(db, news=FakeNews([]))).status == AgentStatus.unavailable
    replay = NewsAgent().run(ctx_for(db, news=FakeNews([article("x")]), as_of=NOW.date()))
    assert replay.status == AgentStatus.unavailable


def test_event_types():
    assert event_type("Infosys to acquire firm") == "acquisition"
    assert event_type("SEBI penalty on bank") == "regulatory"
    assert event_type("Random headline") == "other"


def test_risk_flags_and_contradictions(db):
    rng = np.random.default_rng(1)
    c = 100 * np.exp(np.cumsum(rng.normal(-0.002, 0.04, 400)))
    df = make_ohlcv(400)
    df["close"] = c; df["open"] = c; df["high"] = c * 1.01; df["low"] = c * 0.99
    c1 = ctx_for(db, market=FakeProvider(df=df, financials={**FIN, "annual": [
        {"year": 2025, "revenue": 90.0, "operating_income": 5.0, "net_income": -3.0, "total_debt": 200.0, "total_equity": 80.0},
        {"year": 2024, "revenue": 100.0, "operating_income": 18.0, "net_income": 13.0, "total_debt": 25.0, "total_equity": 70.0}]}))
    fund, tech = FundamentalAgent().run(c1), TechnicalAgent().run(c1)
    r = RiskAgent().run(c1, {"fundamental": fund, "technical": tech})
    assert r.status == AgentStatus.success
    assert_reproducible(r)
    assert any("Volatility" in x for x in r.data["risks"])
    assert any("net loss" in x for x in r.data["risks"]) and any("Leverage" in x for x in r.data["risks"])
    assert "News analysis unavailable" in r.data["stale_or_missing"]
    # every interpretation claim points at existing claim ids
    ids = {x.claim_id for x in r.claims} | {x.claim_id for x in fund.claims}
    for cl in r.claims:
        if cl.type == ClaimType.INTERPRETATION:
            assert set(cl.evidence.supports) <= ids


def test_contradiction_rules():
    def res(agent, signal, **data):
        return AgentResult(agent=agent, status=AgentStatus.success, data={"signal": signal, **data})
    up = {"fundamental": res("fundamental", "bearish", metrics={"net_margin": 0.05, "net_margin_prev": 0.10}),
          "technical": res("technical", "bullish"), "news": res("news", "neutral")}
    found = detect_contradictions(up)
    assert {(c.agent_a, c.agent_b, c.severity) for c in found} == {
        ("fundamental", "technical", "high"), ("technical", "fundamental", "medium")}
    assert detect_contradictions({"technical": res("technical", "bullish")}) == []


def test_numbers_grounding_guard():
    facts = {"ROE": "18.8%", "P/E": "53.17"}
    assert numbers_grounded("ROE is 18.8% and P/E is 53.17.", facts)
    assert not numbers_grounded("ROE is 18.8% and growth will reach 25%.", facts)
