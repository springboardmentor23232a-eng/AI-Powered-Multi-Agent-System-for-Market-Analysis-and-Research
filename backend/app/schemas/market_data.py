from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class NewsArticle(BaseModel):
    """Structured representation of a financial news headline and summary."""
    title: str
    summary: Optional[str] = None
    publisher: Optional[str] = None
    link: Optional[str] = None
    published_at: Optional[str] = None


class PriceSummary(BaseModel):
    """Current and historical trading price statistics."""
    current_price: Optional[float] = None
    previous_close: Optional[float] = None
    day_change: Optional[float] = None
    day_change_percent: Optional[float] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    market_cap: Optional[float] = None
    currency: str = "USD"


class FundamentalMetrics(BaseModel):
    """Valuation, profitability, growth, and leverage metrics."""
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    price_to_book: Optional[float] = None
    enterprise_to_ebitda: Optional[float] = None
    profit_margins: Optional[float] = None
    operating_margins: Optional[float] = None
    gross_margins: Optional[float] = None
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    total_revenue: Optional[float] = None
    ebitda: Optional[float] = None
    total_debt: Optional[float] = None
    total_cash: Optional[float] = None
    debt_to_equity: Optional[float] = None
    free_cash_flow: Optional[float] = None
    dividend_yield: Optional[float] = None


class TechnicalIndicators(BaseModel):
    """Technical trend momentum and historical pricing indicators."""
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    rsi_14: Optional[float] = None
    trend_signal: str = "NEUTRAL"  # BULLISH, BEARISH, NEUTRAL
    price_change_30d_pct: Optional[float] = None
    price_change_90d_pct: Optional[float] = None
    support_level: Optional[float] = None
    resistance_level: Optional[float] = None
    recent_history: List[Dict[str, Any]] = Field(default_factory=list)


class CompanyProfile(BaseModel):
    """Core company metadata and industry categorization."""
    ticker: str
    company_name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    beta: Optional[float] = None
    business_summary: Optional[str] = None


class StockMarketData(BaseModel):
    """
    Consolidated real market data for a stock ticker.
    Supplies the five specialist agents with authentic quantitative & qualitative inputs.
    Never fabricates missing metrics.
    """
    ticker: str
    company_name: str
    fetched_at: str
    profile: CompanyProfile
    price: PriceSummary
    fundamentals: FundamentalMetrics
    technicals: TechnicalIndicators
    news: List[NewsArticle] = Field(default_factory=list)
    has_full_data: bool = True

    model_config = ConfigDict(
        from_attributes=True,
    )

