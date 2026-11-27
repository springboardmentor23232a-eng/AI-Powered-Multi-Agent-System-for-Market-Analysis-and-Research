from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class DatasetCollectionRequest(BaseModel):
    """
    Payload to trigger automated stock market dataset collection and validation.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    ticker: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Stock ticker symbol (e.g. INFY.NS, TCS.BO, AAPL, IBM)",
        examples=["INFY.NS"],
    )
    period: str = Field(
        default="1mo",
        description="Historical analysis duration: 1mo, 3mo, 6mo, 1y, 2y, 5y, max",
        examples=["1mo"],
    )
    market: Optional[str] = Field(
        default=None,
        description="Market exchange override: NSE, BSE, NASDAQ, NYSE",
        examples=["NSE"],
    )


class ValidationIssueItem(BaseModel):
    """
    Individual audit log item for any detected issue, anomaly, or transformation.
    Guarantees no silent deletion or modification.
    """
    row_index: int = Field(..., description="0-based row index in raw dataset")
    date: Optional[str] = Field(default=None, description="Trading date string or unparseable value")
    column: str = Field(..., description="Affected column name or 'Date' or 'ALL'")
    issue_type: str = Field(..., description="Category code: MISSING_VALUE, DUPLICATE_DATE, etc.")
    severity: str = Field(..., description="ERROR or WARNING")
    raw_values: Dict[str, Any] = Field(default_factory=dict, description="Complete raw values of the row")
    message: str = Field(..., description="Human-readable explanation of the defect")
    action_taken: str = Field(..., description="Action taken: FLAGGED_EXCLUDED, DEDUPLICATED, etc.")


class RawDatasetSnapshot(BaseModel):
    """
    Immutable representation of raw source data exactly as retrieved from provider.
    """
    total_records: int
    columns: List[str]
    sha256_hash: str
    retrieved_at: str
    data_source: str
    records_sample: List[Dict[str, Any]] = Field(default_factory=list)


class FiftyTwoWeekMetrics(BaseModel):
    """
    52-week pricing metrics with strict >=250 valid trading days enforcement.
    """
    status: str = Field(..., description="'verified' or 'unavailable'")
    high: Optional[float] = None
    low: Optional[float] = None
    range_pct: Optional[float] = None
    valid_trading_days: int
    notes: str


class ValidatedDatasetSummary(BaseModel):
    """
    Summary of the validated, clean dataset ready for downstream quantitative research.
    """
    valid_records_count: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    highest_price: Optional[float] = None
    lowest_price: Optional[float] = None
    average_volume: Optional[float] = None
    period_change_pct: Optional[float] = None
    fifty_two_week_metrics: FiftyTwoWeekMetrics
    candles_sample: List[Dict[str, Any]] = Field(default_factory=list)


class DataQualityMetrics(BaseModel):
    """
    Deterministic mathematical data quality score and defect counts.
    """
    total_raw_records: int
    valid_records: int
    excluded_records: int
    duplicate_dates_count: int
    missing_values_count: int
    missing_values_by_column: Dict[str, int] = Field(default_factory=dict)
    negative_prices_count: int
    negative_volumes_count: int
    inconsistent_ohlc_count: int
    invalid_date_formats_count: int
    reordered_chronology: bool
    data_quality_score: float
    fatal_defect_penalty: float
    duplicate_penalty: float
    chronology_penalty: float
    validation_status: str = Field(..., description="Strictly PASSED, WARNING, or FAILED")


class ProviderAttemptLog(BaseModel):
    """
    Provenance log of provider query attempts, latency, and status.
    """
    provider: str
    market: str
    status: str = Field(..., description="SUCCESS, FAILED, or CHALLENGED")
    http_code: Optional[int] = None
    latency_ms: Optional[float] = None
    records_retrieved: int = 0
    message: str
    timestamp: str


class AINarrativeExplanation(BaseModel):
    """
    AI-driven narrative contextualizing verified deterministic results.
    Strictly forbids speculative event attribution without verified filings.
    """
    executive_summary: str
    market_anomaly_interpretation: str
    cleaning_transparency_notes: str
    research_readiness_assessment: str


class DatasetValidationReportResponse(BaseModel):
    """
    Consolidated response for an automated dataset collection and validation run.
    """
    model_config = ConfigDict(from_attributes=True)

    report_id: Optional[int] = None
    task_id: Optional[int] = None
    ticker: str
    company_name: str
    market: str
    requested_period: str
    active_provider: str
    retrieval_timestamp: str
    latency_ms: float
    validation_status: str
    quality_metrics: DataQualityMetrics
    raw_snapshot: RawDatasetSnapshot
    validated_summary: ValidatedDatasetSummary
    provider_attempts: List[ProviderAttemptLog] = Field(default_factory=list)
    issues: List[ValidationIssueItem] = Field(default_factory=list)
    ai_explanation: AINarrativeExplanation
    download_url_json: Optional[str] = None
    download_url_csv: Optional[str] = None


class DatasetReportListItem(BaseModel):
    """
    Summary item for user's past dataset collection and validation reports.
    """
    model_config = ConfigDict(from_attributes=True)

    report_id: int
    task_id: int
    ticker: str
    company_name: str
    market: str
    requested_period: str
    data_source: str
    validation_status: str
    data_quality_score: float
    valid_records: int
    created_at: str


class DatasetReportsHistoryResponse(BaseModel):
    """
    List of dataset validation reports belonging to authenticated user.
    """
    status: str = "success"
    count: int
    data: List[DatasetReportListItem] = Field(default_factory=list)
