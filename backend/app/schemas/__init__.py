"""Pydantic models: the exact shape of data the API accepts and returns.

Schemas are deliberately separate from database models so we never leak
internal fields (for example `password_hash`) in a response.
"""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import AnalysisPeriod, Market, TaskStatus

# Letters, digits and the separators used by real symbols (BRK.B, BAJAJ-AUTO, M&M), 1-20 chars.
TICKER_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9.&\-]{0,19}$")

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Auth ----------


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)

    @field_validator("email")
    @classmethod
    def normalise_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if value.strip() != value:
            raise ValueError("Password must not start or end with spaces")
        if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
            raise ValueError("Password must contain at least one letter and one number")
        return value


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Lifetime of the token in seconds")


class UserOut(ORMModel):
    user_id: int
    email: EmailStr
    created_at: datetime


# ---------- Preferences ----------


class PreferencesOut(ORMModel):
    default_market: Market
    analysis_period: AnalysisPeriod
    updated_at: datetime


class PreferencesUpdate(BaseModel):
    """Partial update: send only the fields you want to change."""

    model_config = ConfigDict(extra="forbid")

    default_market: Market | None = None
    analysis_period: AnalysisPeriod | None = None


# ---------- Watchlist (saved stocks) ----------


class SavedStockCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(min_length=1, max_length=20)
    market: Market

    @field_validator("ticker")
    @classmethod
    def normalise_ticker(cls, value: str) -> str:
        ticker = value.strip().upper()
        if not TICKER_PATTERN.fullmatch(ticker):
            raise ValueError(
                "Ticker may contain only letters, digits, '.', '-' or '&' (max 20 characters)"
            )
        return ticker


class SavedStockOut(ORMModel):
    saved_stock_id: int
    ticker: str
    market: Market
    created_at: datetime


# ---------- Research history ----------


class ResearchTaskSummary(ORMModel):
    task_id: int
    ticker: str
    market: Market
    requested_period: AnalysisPeriod
    status: TaskStatus
    created_at: datetime
    completed_at: datetime | None


class ResearchHistoryPage(BaseModel):
    items: list[ResearchTaskSummary]
    total: int
    limit: int
    offset: int


__all__ = [
    "PreferencesOut",
    "PreferencesUpdate",
    "ResearchHistoryPage",
    "ResearchTaskSummary",
    "SavedStockCreate",
    "SavedStockOut",
    "Token",
    "UserOut",
    "UserRegister",
]
