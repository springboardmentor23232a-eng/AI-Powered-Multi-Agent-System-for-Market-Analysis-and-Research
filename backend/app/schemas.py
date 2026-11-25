import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)  # bcrypt limit 72 bytes
    confirm_password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("Password must contain at least one letter and one number")
        return v

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr
    model_config = {"from_attributes": True}
    
    # ---------------- STOCK MARKET SCHEMAS ----------------

Market = Literal["NSE", "BSE", "NASDAQ", "NYSE"]
Period = Literal["1mo", "3mo", "6mo", "1y", "5y"]

TICKER_RE = re.compile(r"^[A-Z0-9.\-]{1,20}$")


def _clean_ticker(v: str) -> str:
    v = v.strip().upper()
    if not TICKER_RE.match(v):
        raise ValueError("Invalid ticker format")
    return v
class PreferenceIO(BaseModel):
    market: Market
    analysis_period: Period


class WatchlistAdd(BaseModel):
    ticker: str
    company_name: Optional[str] = Field(default=None, max_length=200)
    market: Optional[Market] = None

    @field_validator("ticker")
    @classmethod
    def _t(cls, v):
        return _clean_ticker(v)


class SavedStockOut(BaseModel):
    saved_stock_id: int
    ticker: str
    company_name: Optional[str]
    market: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ResearchCreate(BaseModel):
    ticker: str
    company_name: Optional[str] = Field(default=None, max_length=200)
    market: Optional[Market] = None
    analysis_period: Optional[Period] = None

    @field_validator("ticker")
    @classmethod
    def _t(cls, v):
        return _clean_ticker(v)


class ResearchOut(BaseModel):
    task_id: int
    ticker: str
    company_name: Optional[str]
    market: str
    requested_period: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ReportOut(BaseModel):
    report_id: int
    report_content: str
    summary: Optional[str]
    limitations: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ResearchDetail(ResearchOut):
    report: Optional[ReportOut] = None
