from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator
from app.core.config import settings


class PreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    preference_id: int
    user_id: int
    preferred_market: str
    analysis_period: str
    updated_at: datetime


class PreferenceUpdateRequest(BaseModel):
    preferred_market: str
    analysis_period: str

    @field_validator("preferred_market")
    @classmethod
    def validate_market(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if v_upper not in settings.SUPPORTED_MARKETS:
            raise ValueError(f"Market '{v}' is not supported. Supported markets: {', '.join(settings.SUPPORTED_MARKETS)}")
        return v_upper

    @field_validator("analysis_period")
    @classmethod
    def validate_period(cls, v: str) -> str:
        v_stripped = v.strip()
        if v_stripped not in settings.SUPPORTED_PERIODS:
            raise ValueError(f"Analysis period '{v}' is not supported. Supported periods: {', '.join(settings.SUPPORTED_PERIODS)}")
        return v_stripped
