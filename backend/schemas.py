from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator


# ---------- Auth ----------
class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserOut(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr

    model_config = {"from_attributes": True}


class RegisterResponse(BaseModel):
    message: str
    user: UserOut


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    message: str
    user: UserOut


class GoogleLoginRequest(BaseModel):
    credential: str


# ---------- Workspace ----------
Market = Literal["NSE", "BSE", "NASDAQ", "NYSE"]
Period = Literal["1M", "3M", "6M", "1Y", "5Y"]


class PreferencesIn(BaseModel):
    market: Market
    analysis_period: Period


class PreferencesOut(PreferencesIn):
    model_config = {"from_attributes": True}


class StockOut(BaseModel):
    name: str
    ticker: str
    market: str


class ResearchStart(BaseModel):
    ticker: str = Field(min_length=1, max_length=30)


class ResearchTaskOut(BaseModel):
    task_id: int
    company_name: str
    ticker: str
    market: str
    analysis_period: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PricePoint(BaseModel):
    date: str
    close: float


class PriceHistory(BaseModel):
    ticker: str
    name: str
    market: str
    period: str
    points: list[PricePoint]


# ---------- Watchlists ----------
class SavedStockOut(BaseModel):
    saved_stock_id: int
    ticker: str
    company_name: str
    market: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WatchlistOut(BaseModel):
    watchlist_id: int
    name: str
    created_at: datetime
    stocks: list[SavedStockOut]


class WatchlistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class StockAdd(BaseModel):
    ticker: str = Field(min_length=1, max_length=30)


class SavedStockMove(BaseModel):
    watchlist_id: int

Horizon = Literal["short_term", "long_term"]


class WatchlistAdd(BaseModel):
    ticker: str = Field(min_length=1, max_length=30)
    horizon: Horizon = "long_term"


class WatchlistItem(BaseModel):
    saved_stock_id: int
    ticker: str
    name: str | None = None
    market: str | None = None
    horizon: Horizon
    created_at: datetime


class HorizonUpdate(BaseModel):
    horizon: Horizon