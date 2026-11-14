import re
import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict

# Allowed Markets and Analysis Periods according to implementation guide
ALLOWED_MARKETS = ["NSE", "BSE", "NASDAQ", "NYSE"]
ALLOWED_PERIODS = ["1 Month", "3 Months", "6 Months", "1 Year", "5 Years"]

# ----------------- Auth Schemas -----------------
class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, description="Full Name of the user")
    email: str = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, description="Password (at least 6 characters)")
    confirm_password: str = Field(..., description="Confirm password matching password")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean_email = v.strip().lower()
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_regex, clean_email):
            raise ValueError("Invalid email format")
        return clean_email

    @field_validator("confirm_password")
    @classmethod
    def validate_passwords_match(cls, v: str, info) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def clean_email(cls, v: str) -> str:
        return v.strip().lower()


class PreferenceOut(BaseModel):
    market: str
    analysis_period: str
    updated_at: Optional[datetime.datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserOut(BaseModel):
    user_id: int
    full_name: str
    email: str
    created_at: datetime.datetime
    preferences: Optional[PreferenceOut] = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ----------------- Preference Schemas -----------------
class PreferenceUpdate(BaseModel):
    market: str = Field(..., description="Target market (NSE, BSE, NASDAQ, NYSE)")
    analysis_period: str = Field(..., description="Period (1 Month, 3 Months, 6 Months, 1 Year, 5 Years)")

    @field_validator("market")
    @classmethod
    def check_market(cls, v: str) -> str:
        upper = v.upper()
        if upper not in ALLOWED_MARKETS:
            raise ValueError(f"Market must be one of: {', '.join(ALLOWED_MARKETS)}")
        return upper

    @field_validator("analysis_period")
    @classmethod
    def check_period(cls, v: str) -> str:
        if v not in ALLOWED_PERIODS:
            raise ValueError(f"Analysis period must be one of: {', '.join(ALLOWED_PERIODS)}")
        return v


# ----------------- Saved Stock Schemas -----------------
class SavedStockCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)
    company_name: Optional[str] = None
    market: Optional[str] = None

    @field_validator("ticker")
    @classmethod
    def clean_ticker(cls, v: str) -> str:
        return v.strip().upper()


class SavedStockOut(BaseModel):
    saved_stock_id: int
    user_id: int
    ticker: str
    company_name: str
    market: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------- Research Task Schemas -----------------
class ResearchTaskCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)
    company_name: Optional[str] = None
    market: Optional[str] = None
    analysis_period: Optional[str] = None

    @field_validator("ticker")
    @classmethod
    def clean_ticker(cls, v: str) -> str:
        return v.strip().upper()


class ResearchTaskOut(BaseModel):
    task_id: int
    user_id: int
    ticker: str
    company_name: str
    market: str
    analysis_period: str
    status: str
    report_summary: Optional[str] = None
    report_data: Optional[Any] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
