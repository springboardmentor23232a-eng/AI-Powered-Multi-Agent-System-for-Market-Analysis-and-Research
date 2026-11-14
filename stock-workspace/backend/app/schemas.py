import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator

Market = Literal["NSE", "BSE", "NASDAQ", "NYSE"]
Period = Literal["1M", "3M", "6M", "1Y", "5Y"]


class RegisterIn(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    confirm_password: str

    @field_validator("full_name")
    @classmethod
    def name_ok(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Full name must be at least 2 characters")
        return v

    @field_validator("password")
    @classmethod
    def password_ok(cls, v):
        if len(v) < 8 or len(v.encode()) > 72:
            raise ValueError("Password must be 8-72 characters")
        if not (re.search(r"[A-Za-z]", v) and re.search(r"\d", v)):
            raise ValueError("Password must contain letters and numbers")
        return v

    @model_validator(mode="after")
    def match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    full_name: str
    email: str
    market: str
    analysis_period: str
    created_at: datetime


class PreferencesIn(BaseModel):
    market: Market
    analysis_period: Period


class WatchIn(BaseModel):
    ticker: str
    market: Market


class SavedOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    saved_stock_id: int
    ticker: str
    company_name: str
    market: str
    created_at: datetime


class ResearchIn(BaseModel):
    ticker: str
    market: Market | None = None          # defaults to the user's preference
    analysis_period: Period | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    task_id: int
    ticker: str
    company_name: str
    market: str
    analysis_period: str
    status: str
    error: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class TaskDetail(TaskOut):
    report: dict[str, Any] | None = None
