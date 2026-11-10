"""LangGraph supervisor: plan -> [fundamental | technical | news] (parallel) -> risk -> verify -> report.

Each agent node opens its own DB session, retries retrieval failures a bounded number of times, validates its
structured output, and degrades to `unavailable` instead of inventing content.
"""
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Annotated, Callable, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from app.agents.base import AgentContext
from app.agents.fundamental import FundamentalAgent
from app.agents.news import NewsAgent
from app.agents.risk import RiskAgent
from app.agents.technical import TechnicalAgent
from app.data.universe import UNIVERSE
from app.models import SourceDocument
from app.schemas.agents import (AgentResult, AgentStatus, FundamentalOutput, NewsOutput, RiskOutput,
                                TechnicalOutput)
from app.services import market_data as md
from app.services.llm import LLMClient
from app.services.market_data import MarketDataProvider, ProviderError
from app.services.news import NewsProvider
from app.services.report import build_report
from app.services.verifier import verify_claims
from sqlalchemy import select

OUTPUT_SCHEMAS = {"fundamental": FundamentalOutput, "technical": TechnicalOutput, "news": NewsOutput, "risk": RiskOutput}


def _merge(a: dict, b: dict) -> dict:
    return {**(a or {}), **(b or {})}


class ResearchState(TypedDict, total=False):
    ticker: str
    market: str
    period: str
    as_of: date | None
    task_id: object
    plan: list[str]
    results: Annotated[dict, _merge]
    claims: list
    report: dict


@dataclass
class Deps:
    session_factory: Callable
    market: MarketDataProvider
    news: NewsProvider
    llm: LLMClient
    max_retries: int = 2
    backoff_seconds: float = 1.0
    now: datetime | None = None


def run_with_retry(name: str, attempt_fn: Callable[[], AgentResult], deps: Deps) -> AgentResult:
    """Retry retrieval failures up to deps.max_retries; any other failure is recorded, not retried."""
    t0, last, attempts = time.perf_counter(), None, 0
    for i in range(deps.max_retries + 1):
        attempts += 1
        try:
            res = attempt_fn()
            schema = OUTPUT_SCHEMAS[name]
            if res.status == AgentStatus.success:
                schema.model_validate(res.data)
            res.attempts, res.latency_ms = attempts, int((time.perf_counter() - t0) * 1000)
            return res
        except ProviderError as exc:
            last = exc
            if i < deps.max_retries:
                time.sleep(deps.backoff_seconds * (i + 1))
        except (ValidationError, Exception) as exc:  # noqa: BLE001 - recorded as a failed section
            return AgentResult(agent=name, status=AgentStatus.failed, error=f"{type(exc).__name__}: {exc}"[:500],
                               attempts=attempts, latency_ms=int((time.perf_counter() - t0) * 1000),
                               limitations=[f"{name} analysis failed unexpectedly and was excluded"])
    return AgentResult(agent=name, status=AgentStatus.unavailable, error=str(last)[:500], attempts=attempts,
                       latency_ms=int((time.perf_counter() - t0) * 1000),
                       limitations=[f"{name} data could not be retrieved after {attempts} attempts; "
                                    f"section marked unavailable"])


def build_graph(deps: Deps):
    def ctx_for(db, state) -> AgentContext:
        return AgentContext(db=db, market=deps.market, news=deps.news, llm=deps.llm, ticker=state["ticker"],
                            market_code=state["market"], period=state["period"], as_of=state.get("as_of"),
                            task_id=state["task_id"], now=deps.now)

    def plan(state: ResearchState):
        if state["ticker"].upper() not in UNIVERSE:
            raise ValueError(f"{state['ticker']} is outside the supported universe")
        agents = ["fundamental", "technical"] + ([] if state.get("as_of") else ["news"])
        try:  # warm the cache once so parallel agents share one fetch and one source record
            with deps.session_factory() as db:
                c = ctx_for(db, state)
                md.get_prices(db, deps.market, c.ticker, c.market_code, c.period, c.as_of, c.task_id, deps.now)
                md.get_financials(db, deps.market, c.ticker, c.market_code, c.task_id, deps.now)
        except Exception:  # noqa: BLE001 - best effort; each agent retries and reports on its own
            pass
        return {"plan": agents}

    def agent_node(agent):
        def node(state: ResearchState):
            if agent.name not in state["plan"]:
                return {"results": {agent.name: AgentResult(
                    agent=agent.name, status=AgentStatus.unavailable,
                    limitations=[f"{agent.name} analysis skipped by the research plan (not available in replay mode)"])}}

            def attempt():
                with deps.session_factory() as db:
                    return agent.run(ctx_for(db, state))
            return {"results": {agent.name: run_with_retry(agent.name, attempt, deps)}}
        return node

    def risk(state: ResearchState):
        def attempt():
            with deps.session_factory() as db:
                return RiskAgent().run(ctx_for(db, state), state["results"])
        return {"results": {"risk": run_with_retry("risk", attempt, deps)}}

    def route(state: ResearchState):
        return "verify" if any(r.status == AgentStatus.success for r in state["results"].values()) else END

    def verify(state: ResearchState):
        drafts = [c for r in state["results"].values() for c in r.claims]
        with deps.session_factory() as db:
            return {"claims": verify_claims(db, state["task_id"], drafts)}

    def report(state: ResearchState):
        results = state["results"]
        risk_r = results.get("risk")
        contradictions = []
        if risk_r and risk_r.status == AgentStatus.success:
            from app.schemas.agents import ContradictionOut
            contradictions = [ContradictionOut(**c) for c in risk_r.data.get("contradictions", [])]
        with deps.session_factory() as db:
            sources = list(db.scalars(select(SourceDocument).where(SourceDocument.task_id == state["task_id"])
                                      .order_by(SourceDocument.source_type, SourceDocument.retrieved_at)))
        rep = build_report(ticker=state["ticker"].upper(), market=state["market"], period=state["period"],
                           as_of=state.get("as_of"), generated_at=deps.now or datetime.now(timezone.utc),
                           results=results, claims=state["claims"], contradictions=contradictions, sources=sources,
                           company_name=UNIVERSE.get(state["ticker"].upper()))
        rep["contradictions"] = contradictions
        return {"report": rep}

    g = StateGraph(ResearchState)
    g.add_node("plan", plan)
    for a in (FundamentalAgent(), TechnicalAgent(), NewsAgent()):
        g.add_node(a.name, agent_node(a))
        g.add_edge("plan", a.name)
    g.add_node("risk", risk)
    g.add_node("verify", verify)
    g.add_node("report", report)
    g.add_edge(START, "plan")
    g.add_edge(["fundamental", "technical", "news"], "risk")
    g.add_conditional_edges("risk", route, {"verify": "verify", END: END})
    g.add_edge("verify", "report")
    g.add_edge("report", END)
    return g.compile()
