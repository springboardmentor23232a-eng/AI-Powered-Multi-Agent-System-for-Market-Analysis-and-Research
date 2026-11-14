from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Literal
from datetime import datetime

Market = Literal["NSE", "BSE", "NASDAQ", "NYSE"]
Period = Literal["1 Month", "3 Months", "6 Months", "1 Year", "5 Years"]

class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

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
