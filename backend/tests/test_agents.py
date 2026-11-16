from datetime import datetime, timezone
import pytest
from app.schemas.agent_outputs import (
    FinancialAnalysisOutput,
    MarketResearchOutput,
    RiskAnalysisOutput,
    SentimentAnalysisOutput,
    TechnicalAnalysisOutput,
)
from app.schemas.market_data import (
    CompanyProfile,
    FundamentalMetrics,
    NewsArticle,
    PriceSummary,
    StockMarketData,
    TechnicalIndicators,
)
from app.services.agents.financial_analysis_agent import FinancialAnalysisAgent
from app.services.agents.market_research_agent import MarketResearchAgent
from app.services.agents.risk_analysis_agent import RiskAnalysisAgent
from app.services.agents.sentiment_analysis_agent import SentimentAnalysisAgent
from app.services.agents.technical_analysis_agent import TechnicalAnalysisAgent


@pytest.fixture
def sample_complete_market_data() -> StockMarketData:
    """Fixture providing complete, realistic stock market data for a blue-chip company."""
    return StockMarketData(
        ticker="BLUE",
        company_name="BlueChip Corporation",
        fetched_at=datetime.now(timezone.utc).isoformat(),
        profile=CompanyProfile(
            ticker="BLUE",
            company_name="BlueChip Corporation",
            sector="Technology",
            industry="Enterprise Software",
            country="United States",
            website="https://bluechip.example.com",
            beta=1.05,
            business_summary="BlueChip Corp provides mission-critical enterprise cloud and analytics software globally. The firm serves thousands of corporate clients.",
        ),
        price=PriceSummary(
            current_price=200.00,
            previous_close=198.00,
            day_change=2.00,
            day_change_percent=1.01,
            day_high=202.00,
            day_low=197.50,
            fifty_two_week_high=220.00,
            fifty_two_week_low=160.00,
            market_cap=350_000_000_000.0,
            currency="USD",
        ),
        fundamentals=FundamentalMetrics(
            pe_ratio=26.5,
            forward_pe=22.0,
            price_to_book=6.2,
            enterprise_to_ebitda=16.0,
            profit_margins=0.24,
            operating_margins=0.30,
            gross_margins=0.55,
            revenue_growth=0.14,
            earnings_growth=0.18,
            total_revenue=50_000_000_000.0,
            ebitda=18_000_000_000.0,
            total_debt=12_000_000_000.0,
            total_cash=20_000_000_000.0,
            debt_to_equity=40.0,
            free_cash_flow=11_000_000_000.0,
            dividend_yield=0.018,
        ),
        technicals=TechnicalIndicators(
            sma_50=192.00,
            sma_200=180.00,
            rsi_14=56.5,
            trend_signal="BULLISH",
            price_change_30d_pct=4.5,
            price_change_90d_pct=11.2,
            support_level=170.00,
            resistance_level=215.00,
            recent_history=[{"date": "2026-11-14", "close": 200.00, "volume": 5000000}],
        ),
        news=[
            NewsArticle(
                title="BlueChip Corp Beats Earnings Estimates on Strong Cloud Demand",
                summary="Revenue expanded by 14% year over year.",
                publisher="WSJ",
                link="https://example.com/blue1",
                published_at="2026-11-14T10:00:00Z",
            ),
            NewsArticle(
                title="BlueChip Announces Higher Dividend and Share Buyback Expansion",
                summary="Board authorizes $10 billion capital return.",
                publisher="Bloomberg",
                link="https://example.com/blue2",
                published_at="2026-11-14T08:00:00Z",
            ),
        ],
        has_full_data=True,
    )


@pytest.fixture
def sample_sparse_market_data() -> StockMarketData:
    """Fixture providing sparse market data with missing values to test edge-case resilience."""
    return StockMarketData(
        ticker="SPARSE",
        company_name="Sparse Biotech Corp",
        fetched_at=datetime.now(timezone.utc).isoformat(),
        profile=CompanyProfile(
            ticker="SPARSE",
            company_name="Sparse Biotech Corp",
            sector=None,  # Missing sector
            industry=None,  # Missing industry
            country="United States",
            beta=None,  # Missing beta
            business_summary=None,  # Missing summary
        ),
        price=PriceSummary(
            current_price=12.50,
            previous_close=13.00,
            day_change=-0.50,
            day_change_percent=-3.85,
            market_cap=None,  # Missing market cap
        ),
        fundamentals=FundamentalMetrics(
            pe_ratio=None,  # Unprofitable
            forward_pe=None,
            profit_margins=None,
            revenue_growth=None,
            debt_to_equity=None,
            free_cash_flow=None,
        ),
        technicals=TechnicalIndicators(
            sma_50=None,
            sma_200=None,
            rsi_14=None,
            trend_signal="NEUTRAL",
            support_level=None,
            resistance_level=None,
            recent_history=[],
        ),
        news=[],  # No news
        has_full_data=False,
    )


# ==============================================================================
# 1. Market Research Agent Tests
# ==============================================================================
def test_market_research_agent_complete_data(sample_complete_market_data):
    output = MarketResearchAgent.analyze(sample_complete_market_data)

    assert isinstance(output, MarketResearchOutput)
    assert output.agent_name == "Market Research Specialist"
    assert output.market_cap_category == "Mega-Cap"
    assert output.sector == "Technology"
    assert output.industry == "Enterprise Software"
    assert output.confidence_level >= 0.85
    assert len(output.key_findings) >= 3
    assert "supporting_data" in output.model_dump()
    assert output.supporting_data["market_cap"] == 350_000_000_000.0


def test_market_research_agent_missing_data(sample_sparse_market_data):
    output = MarketResearchAgent.analyze(sample_sparse_market_data)

    assert output.market_cap_category == "Unknown"
    assert output.sector is None
    assert output.confidence_level < 0.70
    assert len(output.warnings_and_limitations) >= 3
    assert any("Market capitalization" in w for w in output.warnings_and_limitations)
    assert any("Sector and industry" in w for w in output.warnings_and_limitations)


# ==============================================================================
# 2. Financial Analysis Agent Tests
# ==============================================================================
def test_financial_analysis_agent_complete_data(sample_complete_market_data):
    output = FinancialAnalysisAgent.analyze(sample_complete_market_data)

    assert isinstance(output, FinancialAnalysisOutput)
    assert output.agent_name == "Financial & Valuation Analyst"
    assert output.valuation_status == "FAIRLY_VALUED"
    assert output.profitability_grade == "HIGH"
    assert output.solvency_risk == "LOW"
    assert output.financial_health_score is not None
    assert output.financial_health_score >= 70.0
    assert output.confidence_level >= 0.85


def test_financial_analysis_agent_sparse_data(sample_sparse_market_data):
    output = FinancialAnalysisAgent.analyze(sample_sparse_market_data)

    assert output.valuation_status == "INSUFFICIENT_DATA"
    assert output.confidence_level <= 0.30
    assert len(output.warnings_and_limitations) >= 3
    # Crucial assertion: never invents health score or missing P/E
    assert output.supporting_data["pe_ratio"] is None
    assert output.supporting_data["free_cash_flow"] is None


# ==============================================================================
# 3. Technical Analysis Agent Tests
# ==============================================================================
def test_technical_analysis_agent_complete_data(sample_complete_market_data):
    output = TechnicalAnalysisAgent.analyze(sample_complete_market_data)

    assert isinstance(output, TechnicalAnalysisOutput)
    assert output.agent_name == "Technical Analysis Specialist"
    assert output.trend_direction == "BULLISH"
    assert output.momentum_state == "NEUTRAL"
    assert output.key_support == 170.00
    assert output.key_resistance == 215.00
    assert output.confidence_level >= 0.80


def test_technical_analysis_agent_sparse_data(sample_sparse_market_data):
    output = TechnicalAnalysisAgent.analyze(sample_sparse_market_data)

    assert output.trend_direction == "NEUTRAL"
    assert output.confidence_level <= 0.60
    assert len(output.warnings_and_limitations) >= 2


# ==============================================================================
# 4. Sentiment Analysis Agent Tests
# ==============================================================================
def test_sentiment_analysis_agent_with_positive_news(sample_complete_market_data):
    output = SentimentAnalysisAgent.analyze(sample_complete_market_data)

    assert isinstance(output, SentimentAnalysisOutput)
    assert output.agent_name == "News & Market Sentiment Analyst"
    assert output.sentiment_score > 0.10
    assert output.sentiment_label in ["BULLISH", "VERY_BULLISH"]
    assert output.news_sample_size == 2
    assert len(output.positive_catalysts) >= 1
    assert output.confidence_level >= 0.60


def test_sentiment_analysis_agent_empty_news(sample_sparse_market_data):
    output = SentimentAnalysisAgent.analyze(sample_sparse_market_data)

    assert output.sentiment_score == 0.0
    assert output.sentiment_label == "NEUTRAL"
    assert output.news_sample_size == 0
    assert output.confidence_level == 0.30
    assert len(output.warnings_and_limitations) >= 1


# ==============================================================================
# 5. Risk Analysis Agent Tests
# ==============================================================================
def test_risk_analysis_agent_complete_data(sample_complete_market_data):
    output = RiskAnalysisAgent.analyze(sample_complete_market_data)

    assert isinstance(output, RiskAnalysisOutput)
    assert output.agent_name == "Risk & Downside Analyst"
    assert output.risk_level in ["LOW", "MODERATE"]
    assert output.risk_score < 5.0
    assert len(output.bear_case_scenario) > 20
    assert output.confidence_level >= 0.80


def test_risk_analysis_agent_high_leverage_stress():
    """Verify Risk Agent accurately identifies elevated debt and multiple stretch."""
    high_risk_data = StockMarketData(
        ticker="RISKY",
        company_name="Highly Levered Tech",
        fetched_at=datetime.now(timezone.utc).isoformat(),
        profile=CompanyProfile(
            ticker="RISKY",
            company_name="Highly Levered Tech",
            sector="Technology",
            beta=1.85,  # High volatility
        ),
        price=PriceSummary(current_price=100.00, market_cap=5_000_000_000.0),
        fundamentals=FundamentalMetrics(
            pe_ratio=85.0,  # Extreme valuation stretch
            debt_to_equity=250.0,  # High debt leverage
            free_cash_flow=-500_000_000.0,  # Negative cash flow / cash burn
            revenue_growth=-0.08,  # Negative top-line contraction
        ),
        technicals=TechnicalIndicators(trend_signal="BEARISH", support_level=75.00),
        news=[],
        has_full_data=True,
    )

    output = RiskAnalysisAgent.analyze(high_risk_data)

    assert output.risk_level in ["HIGH", "CRITICAL"]
    assert output.risk_score >= 6.5
    assert len(output.primary_risk_factors) >= 4
    assert any("Valuation Stretch" in f for f in output.primary_risk_factors)
    assert any("High Debt Leverage" in f for f in output.primary_risk_factors)
    assert any("Cash Burn Risk" in f for f in output.primary_risk_factors)

