from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

Market = Literal["NSE", "BSE", "NASDAQ", "NYSE"]
Period = Literal["1M", "3M", "6M", "1Y", "5Y"]


class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8)
    confirm_password: str

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Enter your full name")
        return v

    @model_validator(mode="after")
    def check_password(self):
        if len(self.password.encode()) > 72:
            raise ValueError("Password must be at most 72 bytes")
        if not (any(c.isalpha() for c in self.password) and any(c.isdigit() for c in self.password)):
            raise ValueError("Password must contain at least one letter and one number")
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    full_name: str
    email: EmailStr
    created_at: datetime


class PreferenceIO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    market: Market
    analysis_period: Period


class StockResult(BaseModel):
    ticker: str
    company_name: str
    market: Market


class SavedStockOut(StockResult):
    model_config = ConfigDict(from_attributes=True)
    saved_stock_id: int
    created_at: datetime


class ResearchIn(StockResult):
    pass


class ResearchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    task_id: int
    company_name: str
    ticker: str
    market: Market
    analysis_period: Period
    status: str
    created_at: datetime
    has_report: bool = False


class ResearchDetail(ResearchOut):
    report: str | None = None
    error_message: str | None = None


class CollectIn(BaseModel):
    ticker: str = Field(min_length=1, max_length=20)
    market: Market
    company_name: str | None = Field(default=None, max_length=200)


class IssueOut(BaseModel):
    check: str
    label: str
    count: int
    action: str
    examples: list[str] = []


class ReportOut(BaseModel):
    rows_in: int
    rows_out: int
    issues: list[IssueOut]


class CollectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    collection_id: int
    ticker: str
    company_name: str
    market: Market
    analysis_period: Period
    source: str
    retrieved_at: datetime
    rows_raw: int
    rows_clean: int
    status: str


class CollectionDetail(CollectionOut):
    report: ReportOut
    profile: dict | None = None
    financials: dict[str, dict[str, dict[str, float | None]]] | None = None


class PriceBarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int


class SymbolInfo(BaseModel):
    symbol: str
    name: str
    market: Market


class SourceInfo(BaseModel):
    name: str
    kind: str
    symbols: list[SymbolInfo] | None = None
