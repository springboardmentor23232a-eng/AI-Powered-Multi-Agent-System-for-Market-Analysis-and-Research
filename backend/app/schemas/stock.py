from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class StockSearchResult(BaseModel):
    ticker: str
    company_name: str
    market: str
    exchange: Optional[str] = None
    currency: Optional[str] = "USD"
    sector: Optional[str] = None
    type: Optional[str] = "EQUITY"


class OHLCVBar(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class DataQualityReport(BaseModel):
    total_raw_rows: int
    valid_rows: int
    duplicate_dates_removed: int = 0
    duplicate_dates: List[str] = []
    missing_values_count: int = 0
    missing_value_details: List[str] = []
    inconsistent_rows_count: int = 0
    inconsistent_row_details: List[str] = []
    date_gaps: List[str] = []
    quality_status: str = "VALID"  # VALID, VALID_WITH_WARNINGS, DEGRADED
    validated_at: str
    notes: List[str] = []


class DataSourceMetadata(BaseModel):
    source_type: str
    title: str
    source_url: Optional[str] = None
    published_at: Optional[str] = None
    retrieved_at: str
    content_hash: str


class FinancialStatementTable(BaseModel):
    statement_type: str
    currency: str = "USD"
    periods: List[str] = []
    rows: Dict[str, List[Optional[float]]] = {}


class MarketDataCollectionResponse(BaseModel):
    ticker: str
    market: str
    yf_symbol: str
    period: str
    retrieved_at: str
    profile: Dict[str, Any]
    period_performance: Dict[str, Any]
    ohlcv: List[OHLCVBar]
    data_quality: DataQualityReport
    financial_statements: Dict[str, FinancialStatementTable]
    sources: List[DataSourceMetadata]
