import re
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator

# ==========================================
# Authentication Schemas (Module 1, Section 1 & 2)
# ==========================================

class UserRegisterRequest(BaseModel):
    """
    Registration form schema requiring Full Name, Email, Password,
    and Confirm Password as explicitly stated in Module 1 Guide.
    """
    full_name: str
    email: EmailStr
    password: str
    confirm_password: str

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("Full name must be at least 2 characters long")
        return cleaned

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter (A-Z)")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter (a-z)")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit (0-9)")
        if not re.search(r"[^a-zA-Z0-9\s]", v):
            raise ValueError("Password must contain at least one special character (e.g. !@#$%^&*)")
        return v

    @field_validator("confirm_password")
    @classmethod
    def validate_passwords_match(cls, v: str, info) -> str:
        password = info.data.get("password")
        if password and v != password:
            raise ValueError("Password and Confirm Password do not match")
        return v


class UserLoginRequest(BaseModel):
    """
    Login schema requiring Email and Password as per Module 1 Guide.
    """
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    """
    Google OAuth one-click authentication schema.
    mode can be 'login' (verifies user exists) or 'register' (creates user if new).
    """
    email: EmailStr
    full_name: Optional[str] = "Google User"
    mode: Optional[str] = "login"


class UserResponse(BaseModel):
    """
    Public safe user response (never exposes password hash).
    """
    user_id: int
    full_name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """
    JWT Token response returned upon successful login.
    """
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class RegisterResponse(BaseModel):
    """
    Registration success response message and user details.
    """
    message: str
    user: UserResponse


# ==========================================
# Market Data Schemas (Module 2 & Module 1 Watchlist)
# ==========================================

class StockQuoteResponse(BaseModel):
    ticker: str
    resolved_symbol: str
    company_name: str
    market: str
    currency: str
    price: float
    change: float
    change_percent: float
    previous_close: float
    day_high: float
    day_low: float
    fifty_two_week_high: float
    fifty_two_week_low: float
    volume: int
    market_cap: float
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    roe: Optional[float] = None
    debt_to_equity: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    data_source: str
    retrieved_at: str


class HistoricalCandleResponse(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


# ==========================================
# Watchlist Schemas (Module 1, Section 5)
# ==========================================

class WatchlistAddRequest(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    market: Optional[str] = "NSE"


class WatchlistItemResponse(BaseModel):
    saved_stock_id: int
    user_id: int
    ticker: str
    company_name: Optional[str] = None
    market: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# User Preferences Schemas (Module 1, Section 6)
# ==========================================

class UserPreferenceUpdate(BaseModel):
    market: str
    analysis_period: str


class UserPreferenceResponse(BaseModel):
    preference_id: int
    user_id: int
    market: str
    analysis_period: str
    updated_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# Research Task Schemas (Module 1, Section 4)
# ==========================================

class ResearchTaskCreate(BaseModel):
    ticker: str
    market: str = "NSE"
    requested_period: str = "1 Year"


class ResearchTaskResponse(BaseModel):
    task_id: int
    user_id: int
    ticker: str
    market: str
    requested_period: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
