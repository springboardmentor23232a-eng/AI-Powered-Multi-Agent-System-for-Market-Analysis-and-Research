from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AgentBaseOutput(BaseModel):
    """
    Base schema contract implemented by all specialist stock research agents.
    Guarantees every agent returns:
    1. Comprehensive narrative analysis
    2. Bulleted key findings
    3. Supporting numerical/factual data
    4. Explicit warnings and limitations
    5. Quantitative confidence level (0.0 to 1.0)
    """
    agent_name: str
    analysis: str
    key_findings: List[str] = Field(default_factory=list)
    supporting_data: Dict[str, Any] = Field(default_factory=dict)
    warnings_and_limitations: List[str] = Field(default_factory=list)
    confidence_level: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 (unreliable) and 1.0 (highest confidence)",
    )

    model_config = ConfigDict(from_attributes=True)


class MarketResearchOutput(AgentBaseOutput):
    """Specialist output for market capitalization, sector positioning, and competitive landscape."""
    ticker: str
    company_name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap_category: str = "Unknown"  # Mega-Cap, Large-Cap, Mid-Cap, Small-Cap, Micro-Cap


class FinancialAnalysisOutput(AgentBaseOutput):
    """Specialist output for valuation multiples, margins, leverage, and earnings growth."""
    valuation_status: str  # UNDERVALUED, FAIRLY_VALUED, OVERVALUED, SPECULATIVE, INSUFFICIENT_DATA
    financial_health_score: Optional[float] = None  # 0 to 100 composite score
    profitability_grade: str  # HIGH, MODERATE, LOW, NEGATIVE
    solvency_risk: str  # LOW, MODERATE, HIGH, INSUFFICIENT_DATA


class TechnicalAnalysisOutput(AgentBaseOutput):
    """Specialist output for price trends, moving averages, momentum (RSI), and key levels."""
    trend_direction: str  # BULLISH, BEARISH, NEUTRAL
    momentum_state: str  # OVERBOUGHT, OVERSOLD, NEUTRAL
    key_support: Optional[float] = None
    key_resistance: Optional[float] = None


class SentimentAnalysisOutput(AgentBaseOutput):
    """Specialist output for financial news sentiment, positive catalysts, and headlines."""
    sentiment_score: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Normalized sentiment score from -1.0 (extremely negative) to +1.0 (extremely positive)",
    )
    sentiment_label: str  # VERY_BULLISH, BULLISH, NEUTRAL, BEARISH, VERY_BEARISH
    positive_catalysts: List[str] = Field(default_factory=list)
    negative_concerns: List[str] = Field(default_factory=list)
    news_sample_size: int = 0


class RiskAnalysisOutput(AgentBaseOutput):
    """Specialist output for downside exposure, leverage risks, beta volatility, and bear case."""
    risk_level: str  # LOW, MODERATE, HIGH, CRITICAL
    risk_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Risk severity score from 0.0 (minimal risk) to 10.0 (critical risk)",
    )
    primary_risk_factors: List[str] = Field(default_factory=list)
    bear_case_scenario: str

