from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.claims import ClaimDraft


class AgentStatus(str, Enum):
    success = "success"
    unavailable = "unavailable"
    failed = "failed"


class AgentResult(BaseModel):
    agent: str
    status: AgentStatus
    data: dict = Field(default_factory=dict)
    claims: list[ClaimDraft] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    error: str | None = None
    attempts: int = 1
    latency_ms: int | None = None


class Signal(str, Enum):
    bullish = "bullish"
    bearish = "bearish"
    neutral = "neutral"


class FundamentalOutput(BaseModel):
    metrics: dict[str, float | None]
    trend: dict[str, list[float]] = Field(default_factory=dict)
    signal: Signal
    summary: str


class TechnicalOutput(BaseModel):
    indicators: dict[str, float | None]
    conditions: list[str] = Field(default_factory=list)
    signal: Signal
    summary: str
    chart: dict = Field(default_factory=dict)


class NewsItem(BaseModel):
    title: str
    url: str
    published_at: datetime | None
    sentiment: str  # positive | negative | neutral
    event_type: str | None = None  # earnings | acquisition | regulatory | other
    content_hash: str


class NewsOutput(BaseModel):
    items: list[NewsItem]
    signal: Signal
    summary: str


class RiskOutput(BaseModel):
    volatility_annualized: float | None
    max_drawdown: float | None
    risks: list[str]
    scenarios: list[str]
    stale_or_missing: list[str]
    contradictions: list["ContradictionOut"] = Field(default_factory=list)
    summary: str


class ContradictionOut(BaseModel):
    agent_a: str
    agent_b: str
    description: str
    severity: str = "medium"


RiskOutput.model_rebuild()
