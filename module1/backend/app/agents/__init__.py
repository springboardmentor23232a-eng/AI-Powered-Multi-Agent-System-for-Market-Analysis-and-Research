"""The four Milestone-2 research agents + a simple sequential runner.

The Supervisor Agent (LangGraph: planning, routing, retries, validation) comes in Milestone 3 and will call these same
`run_agent` functions; here they are run in a fixed order because the Risk agent reads the other three outputs.
"""
import logging
from datetime import datetime, timezone

from . import fundamental, news, risk, technical
from .context import ResearchContext, build_context
from .schemas import AGENT_MODELS, AGENT_ORDER, AgentInput, AgentOutput

__all__ = ["run_agent", "run_all", "build_context", "ResearchContext", "AGENT_ORDER", "AgentInput", "AgentOutput"]
log = logging.getLogger(__name__)


def _failed(name: str, ctx: ResearchContext, exc: Exception) -> AgentOutput:
    return AGENT_MODELS[name](status="Failed", ticker=ctx.stock.ticker, market=ctx.stock.market,
                              generated_at=datetime.now(timezone.utc), summary=f"The {name} analysis failed.",
                              error=str(exc)[:300], limitations=["The agent raised an error; its result is not part of this report."])


def run_agent(name: str, ctx: ResearchContext, prior: dict | None = None) -> AgentOutput:
    """Run one agent. Never raises: a crash becomes a Failed output so one agent cannot take down the whole report."""
    prior = prior or {}
    try:
        if name == "fundamental":
            return fundamental.run(ctx)
        if name == "technical":
            return technical.run(ctx)
        if name == "news":
            return news.run(ctx)
        if name == "risk":
            return risk.run(ctx, prior.get("fundamental"), prior.get("technical"), prior.get("news"))
        raise KeyError(name)
    except KeyError:
        raise
    except Exception as exc:
        log.exception("Agent %s failed for %s", name, ctx.stock.ticker)
        return _failed(name, ctx, exc)


def run_all(ctx: ResearchContext) -> dict[str, AgentOutput]:
    out: dict[str, AgentOutput] = {}
    for name in AGENT_ORDER:
        out[name] = run_agent(name, ctx, out)
    return out
