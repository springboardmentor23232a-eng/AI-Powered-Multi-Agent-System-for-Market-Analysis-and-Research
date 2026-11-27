from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class MetricItem(BaseModel):
    """
    Transparent data envelope for financial metrics.
    Guarantees every metric identifies its value, reporting period,
    data source, status, calculation method, and explanatory notes.
    """
    name: str
    value: Optional[float] = None
    formatted: str = "N/A"
    period: Optional[str] = None
    data_source: str = "yfinance"
    status: str = "calculated"  # calculated | reported | unavailable | loss_making | negative_equity | zero_denominator | insufficient_data
    method: Optional[str] = None  # average_equity | ending_equity | standard_cagr | ttm | etc.
    notes: Optional[str] = None


class RevenueEarningsSection(BaseModel):
    revenue: MetricItem
    revenue_growth_yoy: MetricItem
    revenue_growth_qoq: MetricItem
    revenue_cagr: MetricItem
    gross_profit: MetricItem
    operating_income: MetricItem
    net_income: MetricItem
    net_income_growth_yoy: MetricItem
    net_income_cagr: MetricItem
    diluted_eps: MetricItem
    basic_eps: MetricItem
    earnings_quality_ratio: MetricItem  # Operating Cash Flow / Net Income
    summary_narrative: str = ""


class ProfitabilitySection(BaseModel):
    gross_margin: MetricItem
    operating_margin: MetricItem
    net_margin: MetricItem
    return_on_assets: MetricItem
    return_on_equity: MetricItem
    margin_trend: str = "Stable"  # Expanding | Contracting | Stable | Insufficient Data
    summary_narrative: str = ""


class DebtStabilitySection(BaseModel):
    total_debt: MetricItem
    net_debt: MetricItem
    debt_to_equity: MetricItem
    debt_to_assets: MetricItem
    equity_ratio: MetricItem = Field(default_factory=lambda: MetricItem(name="equity_ratio", status="unavailable"))
    current_ratio: MetricItem
    quick_ratio: MetricItem
    interest_coverage: MetricItem
    free_cash_flow: MetricItem
    short_term_debt: Optional[MetricItem] = None
    long_term_debt: Optional[MetricItem] = None
    current_liabilities: Optional[MetricItem] = None
    total_liabilities: Optional[MetricItem] = None
    total_assets: Optional[MetricItem] = None
    stockholders_equity: Optional[MetricItem] = None
    stability_rating: str = "Moderate"  # Strong | Moderate | Elevated Risk | High Risk | Insufficient Data
    summary_narrative: str = ""


class ValuationSection(BaseModel):
    trailing_pe: MetricItem
    forward_pe: MetricItem
    price_to_book: MetricItem
    return_on_equity: MetricItem
    summary_narrative: str = ""


class HistoricalStatementYear(BaseModel):
    period: str
    total_revenue: Optional[float] = None
    revenue: Optional[float] = None  # Compatibility alias
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    operating_cash_flow: Optional[float] = None
    capital_expenditures: Optional[float] = None
    free_cash_flow: Optional[float] = None
    total_assets: Optional[float] = None
    total_debt: Optional[float] = None
    stockholders_equity: Optional[float] = None
    gross_margin_pct: Optional[float] = None
    operating_margin_pct: Optional[float] = None
    net_margin_pct: Optional[float] = None
    roa_pct: Optional[float] = None
    roe_pct: Optional[float] = None
    diluted_eps: Optional[float] = None
    total_liabilities: Optional[float] = None
    revenue_growth_yoy: Optional[float] = None
    net_income_growth_yoy: Optional[float] = None

    def model_post_init(self, __context: Any) -> None:
        if self.revenue is None and self.total_revenue is not None:
            self.revenue = self.total_revenue
        elif self.total_revenue is None and self.revenue is not None:
            self.total_revenue = self.revenue


class HistoricalStatementComparison(BaseModel):
    periods: List[str] = Field(default_factory=list)
    years: List[HistoricalStatementYear] = Field(default_factory=list)
    statement_currency: Optional[str] = None
    summary_narrative: str = ""


class PeerBenchmarkItem(BaseModel):
    ticker: str
    company_name: str
    market: str
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    pb_ratio: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    gross_margin: Optional[float] = None
    debt_to_equity: Optional[float] = None
    revenue_growth_yoy: Optional[float] = None
    is_target: bool = False
    data_status: str = "available"  # available | partial | unavailable


class PeerComparisonSection(BaseModel):
    target_ticker: str
    peers: List[PeerBenchmarkItem] = Field(default_factory=list)
    peer_median_pe: Optional[float] = None
    peer_median_forward_pe: Optional[float] = None
    peer_median_pb: Optional[float] = None
    peer_median_roe: Optional[float] = None
    peer_median_roa: Optional[float] = None
    peer_median_operating_margin: Optional[float] = None
    peer_median_net_margin: Optional[float] = None
    peer_median_gross_margin: Optional[float] = None
    peer_median_debt_to_equity: Optional[float] = None
    peer_median_revenue_growth: Optional[float] = None
    relative_valuation_position: str = "In Line"  # Below Peer Median (Discount) | In Line | Above Peer Median (Premium) | Not Computable | Not Applicable (Loss-Making)
    relative_profitability_position: str = "In Line"  # Above Peer Median (Outperforming) | In Line | Below Peer Median (Underperforming) | Not Computable
    relative_leverage_position: str = "In Line"  # Conservative | In Line | Elevated | Not Computable
    relative_financial_strength_position: str = "In Line"  # Strong | In Line | Vulnerable | Not Computable
    data_status: str = "available"  # available | partial | unavailable
    summary_narrative: str = ""


class BalanceSheetPeriodAudit(BaseModel):
    period: str
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    stockholders_equity: Optional[float] = None
    discrepancy_amount: Optional[float] = None
    discrepancy_pct: Optional[float] = None
    equation_holds: Optional[bool] = True
    status: str = "balanced"  # balanced | discrepancy | unavailable | insufficient_data


class AuditFindingItem(BaseModel):
    category: str  # completeness | consistency | plausibility | period_alignment | currency
    title: str
    statement: Optional[str] = None  # Income Statement | Balance Sheet | Cash Flow | Cross-Statement
    period: Optional[str] = None
    severity: str = "warning"  # critical | warning | info
    explanation: str
    values: Dict[str, Any] = Field(default_factory=dict)


class AuditCategoryScores(BaseModel):
    completeness: float = 100.0  # Weight: 40%
    consistency: float = 100.0   # Weight: 30%
    plausibility: float = 100.0  # Weight: 20%
    period_alignment: float = 100.0  # Weight: 10%


class DataIntegrityAudit(BaseModel):
    is_consistent: bool = True
    balance_sheet_equation_holds: Optional[bool] = None
    balance_sheet_discrepancy_pct: Optional[float] = None
    missing_line_items: List[str] = Field(default_factory=list)
    inconsistent_items: List[str] = Field(default_factory=list)
    audit_warnings: List[str] = Field(default_factory=list)
    data_quality_score: float = 100.0

    # Task 7 Comprehensive Enhancements (100% Backward Compatible)
    data_quality_tier: str = "High Quality"  # High Quality | Acceptable | Caveats | Low Quality
    category_scores: Optional[AuditCategoryScores] = Field(default_factory=AuditCategoryScores)

    currency_mismatch_detected: bool = False
    trading_currency: Optional[str] = None
    reporting_currency: Optional[str] = None
    currency_notes: Optional[str] = None

    period_alignment_status: str = "aligned"  # aligned | misaligned | partial
    period_alignment_notes: Optional[str] = None
    periods_audited: List[str] = Field(default_factory=list)

    suspicious_values_detected: List[str] = Field(default_factory=list)
    multi_period_balance_audits: List[BalanceSheetPeriodAudit] = Field(default_factory=list)
    structured_findings: List[AuditFindingItem] = Field(default_factory=list)

    overall_status: str = "pass"  # pass | caveats | fail
    summary_narrative: str = ""


class OptionalEnhancementsSection(BaseModel):
    """
    Segregated secondary enhancement metrics.
    These are optional and absence never breaks mandatory compliance.
    """
    return_on_invested_capital: Optional[MetricItem] = None
    price_to_sales: Optional[MetricItem] = None
    enterprise_value_to_ebitda: Optional[MetricItem] = None
    dividend_yield: Optional[MetricItem] = None
    payout_ratio: Optional[MetricItem] = None


class FundamentalAnalysisResponse(BaseModel):
    status: str = "success"
    ticker: str
    company_name: str
    market: str
    currency: str = "USD"
    statement_currency: Optional[str] = None
    retrieval_timestamp: str
    data_source: str = "yfinance"
    revenue_and_earnings: RevenueEarningsSection
    profitability: ProfitabilitySection
    debt_and_stability: DebtStabilitySection
    valuation_ratios: ValuationSection
    historical_comparison: HistoricalStatementComparison
    peer_comparison: PeerComparisonSection
    data_integrity_audit: DataIntegrityAudit
    optional_enhancements: Optional[OptionalEnhancementsSection] = None
    executive_summary: str = ""
