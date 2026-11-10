import uuid
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.schemas.claims import CalcEvidence, ClaimDraft, ClaimType, FactEvidence, InterpretationEvidence
from app.services.llm import LLMClient
from app.services.market_data import MarketDataProvider
from app.services.news import NewsProvider
from app.tools import run_tool


@dataclass
class AgentContext:
    db: Session
    market: MarketDataProvider
    news: NewsProvider
    llm: LLMClient
    ticker: str
    market_code: str = "NSE"
    period: str = "2y"
    as_of: date | None = None
    task_id: uuid.UUID | None = None
    now: datetime | None = None


class ClaimBuilder:
    """Creates typed claims. CALCULATED claims are produced by running the registered tool,
    so the stored result is the tool's output by construction."""

    def __init__(self, agent: str):
        self.agent = agent
        self.claims: list[ClaimDraft] = []
        self.index: dict[str, str] = {}  # metric key -> claim_id
        self.evidence_ids: list[str] = []  # FACT/CALCULATED ids, usable as interpretation support

    def _add(self, ctype, text, evidence, key=None, supportable=True) -> str:
        cid = f"{self.agent}-{len(self.claims) + 1}"
        self.claims.append(ClaimDraft(claim_id=cid, agent=self.agent, type=ctype, text=text, evidence=evidence))
        if key:
            self.index[key] = cid
        if supportable:
            self.evidence_ids.append(cid)
        return cid

    def fact(self, text: str, content_hash: str, quote: str, url: str | None = None, key: str | None = None) -> str:
        return self._add(ClaimType.FACT, text, FactEvidence(content_hash=content_hash, source_url=url, quote=quote), key)

    def calc(self, text: str, function: str, inputs: dict, key: str | None = None):
        """Run the tool; record a claim only if it yields a value. Returns the value (or None)."""
        result = run_tool(function, inputs)
        if result is None or (isinstance(result, dict) and all(v is None for v in result.values())):
            return None
        self._add(ClaimType.CALCULATED, text, CalcEvidence(function=function, inputs=inputs, result=result), key)
        return result

    def interpret(self, text: str, supports: list[str] | None = None, key: str | None = None) -> str | None:
        supports = supports if supports is not None else list(self.evidence_ids)
        if not supports:
            return None
        return self._add(ClaimType.INTERPRETATION, text, InterpretationEvidence(supports=supports), key, supportable=False)


def pct(x: float | None) -> str:
    return "n/a" if x is None else f"{x * 100:.1f}%"


def num(x: float | None, nd: int = 2) -> str:
    return "n/a" if x is None else f"{x:,.{nd}f}"
