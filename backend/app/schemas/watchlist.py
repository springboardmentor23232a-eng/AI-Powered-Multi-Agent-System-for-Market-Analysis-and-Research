from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class SavedStockCreate(BaseModel):
    """
    Schema for saving a stock ticker to user watchlist.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    ticker: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Stock ticker symbol (e.g. INFY.NS, TCS.NS, AAPL, MSFT)",
        examples=["INFY.NS"]
    )

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, v: str) -> str:
        clean = v.strip().upper()
        if not clean:
            raise ValueError("Ticker symbol cannot be empty.")
        return clean


class SavedStockResponse(BaseModel):
    """
    Schema for individual saved stock response.
    """
    model_config = ConfigDict(from_attributes=True)

    saved_stock_id: int
    user_id: int
    ticker: str
    company_name: Optional[str] = None
    exchange: Optional[str] = None
    created_at: datetime


class WatchlistResponse(BaseModel):
    """
    Response schema returning the authenticated user's watchlist.
    """
    status: str = "success"
    count: int
    data: List[SavedStockResponse]

