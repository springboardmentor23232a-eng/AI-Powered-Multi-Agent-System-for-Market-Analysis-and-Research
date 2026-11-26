from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


MARKETS = {"NSE", "BSE", "NASDAQ", "NYSE"}
PERIODS = {"1 Month", "3 Months", "6 Months", "1 Year", "5 Years"}


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    user_id: UUID
    full_name: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str


class StockCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=30)
    company_name: str = Field(min_length=1, max_length=200)
    market: str

    @field_validator("ticker")
    @classmethod
    def clean_ticker(cls, value: str) -> str:
        value = value.strip().upper()
        if not value.replace(".", "").replace("-", "").isalnum():
            raise ValueError("Ticker can contain letters, numbers, dots and hyphens.")
        return value

    @field_validator("market")
    @classmethod
    def valid_market(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in MARKETS:
            raise ValueError("Choose NSE, BSE, NASDAQ or NYSE.")
        return value


class SavedStockResponse(BaseModel):
    saved_stock_id: UUID
    ticker: str
    company_name: str
    market: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PreferenceUpdate(BaseModel):
    market: str
    analysis_period: str

    @field_validator("market")
    @classmethod
    def valid_market(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in MARKETS:
            raise ValueError("Unsupported market.")
        return value

    @field_validator("analysis_period")
    @classmethod
    def valid_period(cls, value: str) -> str:
        if value not in PERIODS:
            raise ValueError("Unsupported analysis period.")
        return value


class PreferenceResponse(PreferenceUpdate):
    preference_id: UUID
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResearchTaskCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=30)
    company_name: str = Field(min_length=1, max_length=200)
    market: str | None = None
    analysis_period: str | None = None


class ResearchTaskResponse(BaseModel):
    task_id: UUID
    ticker: str
    company_name: str
    market: str
    analysis_period: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResearchReportResponse(BaseModel):
    report_id: UUID
    task_id: UUID
    report_content: str | None = None
    report_url: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StockSearchItem(BaseModel):
    ticker: str
    company_name: str
    market: str
    exchange: str
    quote_type: str = "EQUITY"
    currency: str = "USD"
    data_source: str = "Yahoo Finance via yfinance"
    retrieved_at: datetime


class OHLCVBar(BaseModel):
    date: str
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    adj_close: float | None = None
    volume: int


class HistoricalDataResponse(BaseModel):
    ticker: str
    company_name: str
    market: str
    period: str
    interval: str
    currency: str = "USD"
    current_price: float | None = None
    previous_close: float | None = None
    change: float | None = None
    change_percent: float | None = None
    price_status: str | None = None
    day_high: float | None = None
    day_low: float | None = None
    fifty_two_week_high: float | None = None
    fifty_two_week_low: float | None = None
    volume: int | None = None
    average_volume: int | None = None
    ohlcv: list[OHLCVBar] = []
    data_source: str = "Yahoo Finance via yfinance"
    retrieval_timestamp: datetime


class CompanyOfficer(BaseModel):
    name: str
    title: str
    age: int | None = None
    total_pay: str | None = None


class CompanyProfileResponse(BaseModel):
    ticker: str
    company_name: str
    market: str
    sector: str | None = None
    industry: str | None = None
    country: str | None = None
    city: str | None = None
    address: str | None = None
    website: str | None = None
    phone: str | None = None
    full_time_employees: int | None = None
    summary: str | None = None
    officers: list[CompanyOfficer] = []
    market_cap: str | None = None
    enterprise_value: str | None = None
    trailing_pe: float | None = None
    forward_pe: float | None = None
    peg_ratio: float | None = None
    price_to_book: float | None = None
    beta: float | None = None
    dividend_rate: float | None = None
    dividend_yield: float | None = None
    fifty_two_week_range: str | None = None
    data_source: str = "Yahoo Finance via yfinance"
    retrieval_timestamp: datetime


class FinancialStatementsResponse(BaseModel):
    ticker: str
    company_name: str
    market: str
    income_statement: list[dict] = []
    balance_sheet: list[dict] = []
    cash_flow: list[dict] = []
    key_ratios: dict = {}
    data_source: str = "Yahoo Finance via yfinance"
    retrieval_timestamp: datetime


class MarketDataCollectRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=30)
    company_name: str = Field(min_length=1, max_length=200)
    market: str = "NSE"
    period: str = "1y"
    interval: str = "1d"
    task_id: UUID | None = None


class MarketDataRecordResponse(BaseModel):
    record_id: UUID
    user_id: UUID
    task_id: UUID | None = None
    ticker: str
    company_name: str
    market: str
    period: str
    interval: str
    currency: str | None = None
    latest_price: float | None = None
    change: float | None = None
    change_percent: float | None = None
    data_source: str
    retrieval_timestamp: datetime
    created_at: datetime
    ohlcv_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class MarketDataFullResponse(BaseModel):
    record_id: UUID
    user_id: UUID
    task_id: UUID | None = None
    ticker: str
    company_name: str
    market: str
    period: str
    interval: str
    currency: str | None = None
    latest_price: float | None = None
    change: float | None = None
    change_percent: float | None = None
    data_source: str
    retrieval_timestamp: datetime
    created_at: datetime
    ohlcv_data: list[dict] = []
    profile_data: dict = {}
    financials_data: dict = {}

    model_config = ConfigDict(from_attributes=True)

