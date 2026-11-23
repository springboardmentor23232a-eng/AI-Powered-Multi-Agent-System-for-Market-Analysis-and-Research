import re
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Literal
from datetime import datetime

Market = Literal["NSE", "BSE", "NASDAQ", "NYSE"]
Period = Literal["1 Day", "5 Days", "1 Month", "3 Months", "6 Months", "1 Year", "5 Years", "Max", "Maximum"]

class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if len(v) > 128:
            raise ValueError("Password cannot exceed 128 characters.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter (A-Z).")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter (a-z).")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number (0-9).")
        if not re.search(r"[@#$!%&*]", v):
            raise ValueError("Password must contain at least one special character from @#$!%&*")
        return v

class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

class GoogleIn(BaseModel):
    credential: str = Field(min_length=20)

class UserOut(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ResearchCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    ticker: str = Field(min_length=1, max_length=32)
    market: Market | None = None
    analysis_period: Period | None = None

class ResearchOut(BaseModel):
    id: str
    company_name: str
    ticker: str
    market: str
    analysis_period: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None
    report_available: bool = False
    model_config = ConfigDict(from_attributes=True)

class WatchlistCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=32)
    company_name: str | None = Field(default=None, max_length=200)
    market: Market | None = None
    provider_symbol: str | None = Field(default=None, max_length=40)

class WatchlistOut(BaseModel):
    id: str
    company_name: str
    ticker: str
    market: str
    created_at: datetime
    provider_symbol: str | None = None
    model_config = ConfigDict(from_attributes=True)

class PreferencesIn(BaseModel):
    default_market: Market
    default_analysis_period: Period

class PreferencesOut(PreferencesIn):
    updated_at: datetime | None = None

class StockSearchResult(BaseModel):
    company_name: str
    ticker: str
    market: str
    provider_symbol: str
    price: float | None = None
    change_percent: float | None = None
    currency: str | None = None

class StockSearchResponse(BaseModel):
    results: list[StockSearchResult]
    source: str = "Yahoo Finance"
    market: str | None = None
    retrieval_timestamp: datetime
    note: str | None = None

class StockQuoteOut(BaseModel):
    ticker: str
    market: str
    provider_symbol: str
    price: float | None = None
    previous_close: float | None = None
    change_percent: float | None = None
    currency: str | None = None
    source: str = "Yahoo Finance"
    retrieval_timestamp: datetime
    as_of: str | None = None

class StockHistoryRow(BaseModel):
    date: str
    formatted_date: str
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: int | None = None

class StockHistoryOut(BaseModel):
    ticker: str
    market: str
    provider_symbol: str
    currency: str | None = None
    period: str
    latest_trading_date: str | None = None
    source: str = "Yahoo Finance"
    retrieval_timestamp: datetime
    as_of: str | None = None
    count: int = 0
    provider_note: str | None = None
    history: list[StockHistoryRow]

class StockAnalyticsOut(BaseModel):
    ticker: str
    market: str
    provider_symbol: str
    period: str
    period_high: float | None = None
    period_low: float | None = None
    horizon_return: float | None = None
    maximum_drawdown: float | None = None
    annualized_volatility: float | None = None
    sma_50: float | None = None
    sma_200: float | None = None
    rsi_14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    sentiment: Literal["Bullish", "Bearish", "Neutral"]
    confidence: int = 50
    explanation: str
    signals: list[str] = Field(default_factory=list)
    disclaimer: str = "Technical analysis signal based on historical indicators. Informational only, not investment advice."
    source: str = "Yahoo Finance"
    retrieval_timestamp: datetime
    as_of: str | None = None

class StockProfileOut(BaseModel):
    ticker: str
    company_name: str
    market: str
    provider_symbol: str
    exchange: str | None = None
    sector: str | None = None
    industry: str | None = None
    description: str | None = None
    country: str | None = None
    city: str | None = None
    website: str | None = None
    market_cap: float | None = None
    full_time_employees: int | None = None
    currency: str | None = None
    source: str = "Yahoo Finance"
    retrieval_timestamp: datetime
    as_of: str | None = None

class FinancialMetricRow(BaseModel):
    name: str
    values: dict[str, float | None]

class FinancialStatementData(BaseModel):
    periods: list[str] = Field(default_factory=list)
    metrics: list[FinancialMetricRow] = Field(default_factory=list)

class FinancialStatementsGroup(BaseModel):
    income_statement: FinancialStatementData
    balance_sheet: FinancialStatementData
    cash_flow: FinancialStatementData

class StockFinancialsOut(BaseModel):
    ticker: str
    market: str
    provider_symbol: str
    currency: str | None = None
    source: str = "Yahoo Finance"
    retrieval_timestamp: datetime
    as_of: str | None = None
    annual: FinancialStatementsGroup
    quarterly: FinancialStatementsGroup

