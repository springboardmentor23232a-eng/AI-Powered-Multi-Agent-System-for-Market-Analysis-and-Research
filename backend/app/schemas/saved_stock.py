from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.core.config import settings


class SavedStockCreate(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    ticker: str = Field(..., min_length=1, max_length=50)
    market: str = Field(..., min_length=1, max_length=50)

    @field_validator("ticker")
    @classmethod
    def clean_ticker(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("market")
    @classmethod
    def clean_market(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if v_upper not in settings.SUPPORTED_MARKETS:
            raise ValueError(f"Market '{v}' is not supported. Supported: {', '.join(settings.SUPPORTED_MARKETS)}")
        return v_upper


class SavedStockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    saved_stock_id: int
    user_id: int
    company_name: str
    ticker: str
    market: str
    created_at: datetime
