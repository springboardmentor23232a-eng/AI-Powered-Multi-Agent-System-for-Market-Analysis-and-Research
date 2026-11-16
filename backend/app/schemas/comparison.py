from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ComparisonRequest(BaseModel):
    """
    Request payload to compare 2 to 5 completed research sessions.
    Strictly evaluates existing completed sessions without triggering unwanted queries.
    """
    session_ids: List[int] = Field(
        ...,
        min_length=2,
        max_length=5,
        description="List of 2 to 5 completed research session IDs belonging to the authenticated user.",
        examples=[[1, 2]],
    )


class ComparisonItem(BaseModel):
    """Normalized multi-agent metrics for a single stock research report."""
    session_id: int
    ticker: str
    company_name: str
    current_price: Optional[float] = None
    target_price: Optional[float] = None
    implied_upside_percent: Optional[float] = None
    recommendation: str
    confidence_score: float

    # Valuation & Fundamentals
    valuation_status: Optional[str] = None
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    price_to_book: Optional[float] = None
    profitability_grade: Optional[str] = None
    solvency_risk: Optional[str] = None
    profit_margins: Optional[float] = None
    operating_margins: Optional[float] = None
    debt_to_equity: Optional[float] = None
    total_cash: Optional[float] = None
    total_debt: Optional[float] = None
    free_cash_flow: Optional[float] = None

    # Technical Indicators
    trend_direction: Optional[str] = None
    momentum_state: Optional[str] = None
    rsi_14: Optional[float] = None
    key_support: Optional[float] = None
    key_resistance: Optional[float] = None

    # Sentiment & Media
    sentiment_label: Optional[str] = None
    sentiment_score: Optional[float] = None

    # Risk Metrics
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None

    # Sector & Classification
    sector: Optional[str] = None
    industry: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ComparisonMatrixRow(BaseModel):
    """A row in the side-by-side metric comparison matrix."""
    category: str  # Consensus, Valuation, Technicals, Sentiment, Risk, Classification
    metric: str
    values: Dict[str, Any]  # Ticker symbol -> formatted metric value (or None / "N/A")


class ComparisonResponse(BaseModel):
    """Consolidated comparative analysis response across 2 to 5 equities."""
    total_compared: int
    items: List[ComparisonItem]
    matrix: List[ComparisonMatrixRow]
