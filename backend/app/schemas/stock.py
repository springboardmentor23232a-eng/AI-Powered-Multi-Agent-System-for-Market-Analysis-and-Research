from typing import List, Optional
from pydantic import BaseModel


class StockSearchResult(BaseModel):
    ticker: str
    company_name: str
    exchange: Optional[str] = "Unknown"
    sector: Optional[str] = None
    country: Optional[str] = None


class StockSearchResponse(BaseModel):
    query: str
    count: int
    results: List[StockSearchResult]


class OHLCVCandle(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class StockSummaryStats(BaseModel):
    start_date: str
    end_date: str
    highest_price: float
    lowest_price: float
    average_volume: float
    total_trading_days: int
    period_change_pct: float


class ValidationReport(BaseModel):
    total_raw_records: int
    cleaned_records: int
    missing_values_handled: int
    duplicates_removed: int
    invalid_rows_removed: int
    is_chronological: bool


class StockOverviewResponse(BaseModel):
    ticker: str
    company_name: str
    exchange: Optional[str] = None
    currency: Optional[str] = "USD"
    sector: Optional[str] = None
    industry: Optional[str] = None
    current_price: Optional[float] = None
    previous_close: Optional[float] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    market_cap: Optional[int] = None
    pe_ratio: Optional[float] = None
    volume: Optional[int] = None
    average_volume: Optional[int] = None
    dividend_yield: Optional[float] = None
    business_summary: Optional[str] = None
    data_source: str = "yfinance"
    retrieved_at: str


class HistoricalDataResponse(BaseModel):
    ticker: str
    period: str
    interval: str = "1d"
    count: int
    data_source: str = "yfinance"
    retrieved_at: str
    stats: StockSummaryStats
    validation: ValidationReport
    candles: List[OHLCVCandle]

