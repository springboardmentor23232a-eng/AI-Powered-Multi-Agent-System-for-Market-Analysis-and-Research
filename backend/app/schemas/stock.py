from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class StockSearchResult(BaseModel):
    ticker: str
    company_name: str
    exchange: Optional[str] = "Unknown"
    market: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None


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
    ticker: Optional[str] = None
    total_raw_records: int = 0
    cleaned_records: int = 0
    missing_values_handled: int = 0
    duplicates_removed: int = 0
    invalid_rows_removed: int = 0
    is_chronological: bool = True
    # Extended Module 2 compliance fields
    total_input_rows: Optional[int] = 0
    valid_rows: Optional[int] = 0
    removed_rows: Optional[int] = 0
    missing_value_count: Optional[int] = 0
    duplicate_date_count: Optional[int] = 0
    invalid_price_count: Optional[int] = 0
    invalid_ohlc_count: Optional[int] = 0
    warnings: List[str] = Field(default_factory=list)
    validation_status: str = "PASSED"


class FinancialStatementItem(BaseModel):
    line_item: str
    metric: Optional[str] = None
    values: Dict[str, Optional[float]] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if not self.metric:
            self.metric = self.line_item
        elif not self.line_item:
            self.line_item = self.metric


class StatementData(BaseModel):
    statement_type: str
    available: bool = True
    raw_available: Optional[bool] = None
    periods: List[str] = Field(default_factory=list)
    line_items: List[FinancialStatementItem] = Field(default_factory=list)
    items: Optional[List[FinancialStatementItem]] = None
    message: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        if self.raw_available is None:
            self.raw_available = self.available
        else:
            self.available = self.raw_available

        if self.items is None:
            self.items = self.line_items
        elif not self.line_items:
            self.line_items = self.items


class FinancialSection(BaseModel):
    annual: StatementData
    quarterly: StatementData


class FinancialStatementsResponse(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    currency: Optional[str] = "USD"
    financial_currency: Optional[str] = None
    data_source: str = "yfinance"
    retrieved_at: str
    has_data: bool = True
    income_statement: FinancialSection
    balance_sheet: FinancialSection
    cash_flow_statement: Optional[FinancialSection] = None
    cash_flow: Optional[FinancialSection] = None

    def model_post_init(self, __context: Any) -> None:
        if self.cash_flow is None and self.cash_flow_statement is not None:
            self.cash_flow = self.cash_flow_statement
        elif self.cash_flow_statement is None and self.cash_flow is not None:
            self.cash_flow_statement = self.cash_flow


class StockOverviewResponse(BaseModel):
    ticker: str
    company_name: str
    exchange: Optional[str] = None
    currency: Optional[str] = "USD"
    financial_currency: Optional[str] = None
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
    trailing_pe: Optional[float] = None
    forward_pe: Optional[float] = None
    price_to_book: Optional[float] = None
    book_value: Optional[float] = None
    forward_eps: Optional[float] = None
    trailing_eps: Optional[float] = None
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

