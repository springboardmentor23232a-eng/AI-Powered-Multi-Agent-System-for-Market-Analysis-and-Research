from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator

ALLOWED_MARKETS = ("NSE", "BSE", "NASDAQ", "NYSE")
ALLOWED_PERIODS = ("1mo", "3mo", "6mo", "1y", "5y")


class PreferenceUpdate(BaseModel):
    """
    Schema for updating authenticated user's preferences.
    Restricts market to: NSE, BSE, NASDAQ, NYSE.
    Restricts analysis_period to: 1mo, 3mo, 6mo, 1y, 5y.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    market: str
    analysis_period: str

    @field_validator("market")
    @classmethod
    def validate_market(cls, v: str) -> str:
        clean = v.strip().upper()
        if clean not in ALLOWED_MARKETS:
            raise ValueError(
                f"Invalid market '{v}'. Supported markets are: {', '.join(ALLOWED_MARKETS)}."
            )
        return clean

    @field_validator("analysis_period")
    @classmethod
    def validate_analysis_period(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ALLOWED_PERIODS:
            raise ValueError(
                f"Invalid analysis period '{v}'. Supported periods are: {', '.join(ALLOWED_PERIODS)}."
            )
        return clean


class PreferenceResponse(BaseModel):
    """
    Schema representing user preference details.
    """
    model_config = ConfigDict(from_attributes=True)

    status: str = "success"
    preference_id: Optional[int] = None
    user_id: int
    market: str
    analysis_period: str
    updated_at: datetime
