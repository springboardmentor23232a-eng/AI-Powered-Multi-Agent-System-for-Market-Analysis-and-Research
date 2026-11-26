"""Structured inputs/outputs for every research agent (Milestone 2: "Define structured inputs and outputs for each agent").

Each agent returns exactly one of these Pydantic models (`model_dump(mode="json")` is what is stored in
`agent_results.output` and sent to the browser), so the supervisor / report generator added later can rely on the shape.

`Finding.kind` keeps facts, calculations and interpretations apart (the report must distinguish them):
  fact           - a value taken from a data source
  calculated     - a number we computed (formula shown)
  interpretation - a rule-based reading of the numbers (deterministic, NOT a prediction or advice)
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

Status = Literal["Completed", "Unavailable", "Failed"]
Kind = Literal["fact", "calculated", "interpretation"]
Tone = Literal["positive", "negative", "neutral", "caution"]


class SourceRef(BaseModel):
    name: str
    url: Optional[str] = None
    retrieved_at: Optional[datetime] = None
    synthetic: bool = False


class Finding(BaseModel):
    text: str
    kind: Kind = "interpretation"
    tone: Tone = "neutral"


class AgentInput(BaseModel):
    """What every agent is asked: one stock, one analysis period."""
    ticker: str
    market: Literal["NSE", "BSE", "NASDAQ", "NYSE"]
    period: Literal["1M", "3M", "6M", "1Y", "5Y"]


class AgentOutput(BaseModel):
    agent: str
    status: Status = "Completed"
    ticker: str
    market: str
    generated_at: datetime
    summary: str
    findings: list[Finding] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    sources: list[SourceRef] = Field(default_factory=list)
    error: Optional[str] = None


# ------------------------------------------------------------------------------------------- fundamental
class RatioItem(BaseModel):
    key: str
    name: str
    value: Optional[float] = None
    unit: Literal["%", "x"]
    formula: str
    kind: Literal["calculated", "reported"] = "calculated"
    inputs: dict[str, Optional[float]] = Field(default_factory=dict)
    reason_unavailable: Optional[str] = None


class FundamentalOutput(AgentOutput):
    agent: Literal["fundamental"] = "fundamental"
    basis: Optional[str] = None                      # which data source the numbers come from
    currency: Optional[str] = None
    latest_period: Optional[str] = None
    ratios: list[RatioItem] = Field(default_factory=list)
    history: dict = Field(default_factory=dict)      # {"periods": [...], "series": {name: [values]}}
    peers: Optional[dict] = None                     # {"category", "year", "count", "company", "median", "members"}
    data_issues: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------------------------- technical
class Condition(BaseModel):
    code: str
    bias: Literal["bullish", "bearish", "neutral"]
    text: str


class ChartSeries(BaseModel):
    dates: list[str] = Field(default_factory=list)
    open: list[Optional[float]] = Field(default_factory=list)
    high: list[Optional[float]] = Field(default_factory=list)
    low: list[Optional[float]] = Field(default_factory=list)
    close: list[Optional[float]] = Field(default_factory=list)
    sma20: list[Optional[float]] = Field(default_factory=list)
    sma50: list[Optional[float]] = Field(default_factory=list)
    ema12: list[Optional[float]] = Field(default_factory=list)
    ema26: list[Optional[float]] = Field(default_factory=list)
    rsi14: list[Optional[float]] = Field(default_factory=list)
    macd: list[Optional[float]] = Field(default_factory=list)
    macd_signal: list[Optional[float]] = Field(default_factory=list)
    macd_hist: list[Optional[float]] = Field(default_factory=list)


class TechnicalOutput(AgentOutput):
    agent: Literal["technical"] = "technical"
    bias: Literal["upward", "downward", "mixed", "insufficient_data"] = "insufficient_data"
    currency: Optional[str] = None
    indicators: dict[str, Optional[float]] = Field(default_factory=dict)
    conditions: list[Condition] = Field(default_factory=list)
    chart: ChartSeries = Field(default_factory=ChartSeries)


# ------------------------------------------------------------------------------------------------- news
class Article(BaseModel):
    title: str
    url: Optional[str] = None
    source: Optional[str] = None
    published_at: Optional[datetime] = None
    summary: Optional[str] = None
    sentiment: Literal["Positive", "Negative", "Neutral"]
    score: float
    events: list[str] = Field(default_factory=list)
    uncertain: bool = False
    synthetic: bool = False


class NewsOutput(AgentOutput):
    agent: Literal["news"] = "news"
    articles: list[Article] = Field(default_factory=list)
    counts: dict[str, int] = Field(default_factory=dict)       # {"Positive": n, "Negative": n, "Neutral": n}
    net_score: Optional[float] = None                          # mean article score, -1..1
    tone: Optional[Literal["Positive", "Negative", "Neutral", "Mixed"]] = None
    key_events: dict[str, list[int]] = Field(default_factory=dict)   # event -> indexes into `articles`
    conflicts: list[str] = Field(default_factory=list)


# ------------------------------------------------------------------------------------------------- risk
class Scenario(BaseModel):
    name: str
    return_pct: float
    price: float
    description: str


class Conflict(BaseModel):
    between: list[str]
    description: str


class RiskOutput(AgentOutput):
    agent: Literal["risk"] = "risk"
    level: Literal["Low", "Moderate", "High", "Insufficient data"] = "Insufficient data"
    level_basis: list[str] = Field(default_factory=list)
    currency: Optional[str] = None
    metrics: dict[str, Optional[float]] = Field(default_factory=dict)
    drawdown: Optional[dict] = None
    scenarios: list[Scenario] = Field(default_factory=list)
    financial_risks: list[str] = Field(default_factory=list)
    sector_risks: list[str] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)


AGENT_MODELS = {"fundamental": FundamentalOutput, "technical": TechnicalOutput, "news": NewsOutput, "risk": RiskOutput}
AGENT_ORDER = ("fundamental", "technical", "news", "risk")   # the risk agent reads the other three
