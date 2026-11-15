import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

Market = Literal["NSE", "BSE", "NASDAQ", "NYSE"]
Period = Literal["1M", "3M", "6M", "1Y", "5Y"]
Status = Literal["Pending", "Processing", "Completed", "Failed"]


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str
    confirm_password: str

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 2:
            raise ValueError("Full name must be at least 2 characters.")
        return v

    @field_validator("email")
    @classmethod
    def lower_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        problems = []
        if len(v) < 8:
            problems.append("at least 8 characters")
        if len(v.encode()) > 72:
            problems.append("at most 72 bytes (bcrypt limit)")
        if not re.search(r"[a-z]", v):
            problems.append("a lowercase letter")
        if not re.search(r"[A-Z]", v):
            problems.append("an uppercase letter")
        if not re.search(r"\d", v):
            problems.append("a digit")
        if problems:
            raise ValueError("Password must contain " + ", ".join(problems) + ".")
        return v

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)

    @field_validator("email")
    @classmethod
    def lower_email(cls, v: str) -> str:
        return v.strip().lower()


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    full_name: str
    email: EmailStr
    created_at: datetime


class RegisterResponse(BaseModel):
    message: str
    user: UserOut


class LoginResponse(BaseModel):
    message: str
    user: UserOut
    csrf_token: str
    expires_in: int
    token_type: str = "bearer"
    access_token: str | None = None


class MeResponse(BaseModel):
    user: UserOut
    csrf_token: str | None


class PreferencesIn(BaseModel):
    market: Market
    analysis_period: Period


class PreferencesOut(PreferencesIn):
    model_config = ConfigDict(from_attributes=True)
    updated_at: datetime | None = None


class StockOut(BaseModel):
    ticker: str
    name: str
    market: Market


class WatchlistAdd(BaseModel):
    ticker: str = Field(min_length=1, max_length=20)
    market: Market | None = None

    @field_validator("ticker")
    @classmethod
    def upper(cls, v: str) -> str:
        return v.strip().upper()


class WatchlistItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    saved_stock_id: int
    ticker: str
    company_name: str
    market: Market
    created_at: datetime


class ResearchCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=20)
    market: Market | None = None            # defaults to the user's saved preference
    analysis_period: Period | None = None   # defaults to the user's saved preference

    @field_validator("ticker")
    @classmethod
    def upper(cls, v: str) -> str:
        return v.strip().upper()


class ResearchTaskOut(BaseModel):
    task_id: int
    ticker: str
    company_name: str
    market: Market
    analysis_period: Period
    status: Status
    research_date: datetime
    completed_at: datetime | None
    error_message: str | None
    report_available: bool


class ReportOut(BaseModel):
    task_id: int
    title: str
    summary: str
    content: dict
    created_at: datetime
