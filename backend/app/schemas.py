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
