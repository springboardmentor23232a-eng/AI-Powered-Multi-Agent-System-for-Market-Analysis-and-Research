import re
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150, description="Full Name of the user")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, description="Password meeting security criteria")
    confirm_password: str = Field(..., description="Confirm password matching original")

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Full name cannot be empty or blank")
        return stripped

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", v):
            raise ValueError("Password must contain at least one special character")
        return v

    @model_validator(mode="after")
    def verify_password_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserOut(BaseModel):
    user_id: UUID
    full_name: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    message: str
    user: Optional[UserOut] = None


class SavedStockCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=30)

    @field_validator("ticker")
    @classmethod
    def clean_ticker(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not cleaned:
            raise ValueError("Ticker cannot be blank")
        return cleaned


class SavedStockOut(BaseModel):
    saved_stock_id: UUID
    ticker: str
    company_name: Optional[str] = None
    market: Optional[str] = None
    exchange: Optional[str] = None
    currency: Optional[str] = "USD"
    currency_symbol: Optional[str] = "$"
    current_price: Optional[float] = None
    change_percent: Optional[float] = None
    is_us_market: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class ResearchTaskCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=30)
    company_name: Optional[str] = None
    market: Optional[str] = "NSE"
    requested_period: Optional[str] = "6 Months"
    confirmed_us_currency: Optional[bool] = False


class ResearchTaskOut(BaseModel):
    task_id: UUID
    ticker: str
    company_name: Optional[str] = None
    market: Optional[str] = None
    requested_period: Optional[str] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    has_report: bool = True

    class Config:
        from_attributes = True


class ResearchReportOut(BaseModel):
    report_id: UUID
    task_id: UUID
    ticker: str
    company_name: str
    summary: str
    report_content: str
    limitations: str
    created_at: datetime

    class Config:
        from_attributes = True


class StockSearchResult(BaseModel):
    ticker: str
    name: str
    market: str
    exchange: Optional[str] = None
    currency: Optional[str] = "USD"
    currency_symbol: Optional[str] = "$"
    current_price: Optional[float] = None
    change_percent: Optional[float] = None
    is_us_market: bool = False


class StockSearchResponse(BaseModel):
    query: str
    count: int
    results: List[StockSearchResult]


class UserPreferenceUpdate(BaseModel):
    preferred_market: str = Field(..., description="Default market choice (NSE, BSE, NASDAQ, NYSE)")
    preferred_period: str = Field(..., description="Default analysis period (1 Month, 3 Months, 6 Months, 1 Year, 5 Years)")

    @field_validator("preferred_market")
    @classmethod
    def validate_market(cls, v: str) -> str:
        valid_markets = ["NSE", "BSE", "NASDAQ", "NYSE"]
        cleaned = v.strip().upper()
        if cleaned not in valid_markets:
            raise ValueError(f"Market must be one of {valid_markets}")
        return cleaned

    @field_validator("preferred_period")
    @classmethod
    def validate_period(cls, v: str) -> str:
        valid_periods = ["1 Month", "3 Months", "6 Months", "1 Year", "5 Years"]
        if v not in valid_periods:
            raise ValueError(f"Analysis period must be one of {valid_periods}")
        return v


class UserPreferenceOut(BaseModel):
    preferred_market: str
    preferred_period: str
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

