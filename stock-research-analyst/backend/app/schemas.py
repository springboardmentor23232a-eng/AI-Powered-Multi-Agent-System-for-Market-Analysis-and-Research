from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


MarketType = Literal["NSE", "BSE", "NASDAQ", "NYSE"]
PeriodType = Literal["1M", "3M", "6M", "1Y", "5Y"]
OAuthProviderType = Literal["google", "apple"]


class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class OAuthLoginRequest(BaseModel):
    provider: OAuthProviderType
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=120)
    id_token: Optional[str] = None


class UserResponse(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr
    auth_provider: str = "local"
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class PreferenceUpdate(BaseModel):
    market: MarketType
    analysis_period: PeriodType


class PreferenceResponse(BaseModel):
    market: MarketType
    analysis_period: PeriodType
    updated_at: datetime

    model_config = {"from_attributes": True}


class SavedStockCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=32)
    company_name: Optional[str] = Field(None, max_length=200)
    market: MarketType = "NSE"

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, v: str) -> str:
        return v.strip().upper()


class SavedStockResponse(BaseModel):
    saved_stock_id: int
    ticker: str
    company_name: Optional[str]
    market: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ResearchRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=32)
    market: Optional[MarketType] = None
    analysis_period: Optional[PeriodType] = None

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, v: str) -> str:
        return v.strip().upper()


class ResearchTaskResponse(BaseModel):
    task_id: int
    ticker: str
    company_name: Optional[str]
    market: str
    analysis_period: str
    status: str
    error_message: Optional[str] = None
    summary_markdown: Optional[str] = None
    report_data: Optional[dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
