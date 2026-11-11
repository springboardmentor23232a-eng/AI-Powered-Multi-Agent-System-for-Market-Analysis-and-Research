from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.core.config import settings
from app.schemas.saved_stock import SavedStockResponse


class ResearchCreateRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=50)
    company_name: Optional[str] = None
    market: Optional[str] = None
    analysis_period: Optional[str] = None

    @field_validator("ticker")
    @classmethod
    def clean_ticker(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("market")
    @classmethod
    def clean_market(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v_upper = v.strip().upper()
            if v_upper not in settings.SUPPORTED_MARKETS:
                raise ValueError(f"Market '{v}' is not supported.")
            return v_upper
        return v

    @field_validator("analysis_period")
    @classmethod
    def clean_period(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v_stripped = v.strip()
            if v_stripped not in settings.SUPPORTED_PERIODS:
                raise ValueError(f"Period '{v}' is not supported.")
            return v_stripped
        return v


class ResearchTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: int
    user_id: int
    company_name: str
    ticker: str
    market: str
    analysis_period: str
    status: str
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None
    has_report: bool = False


class ResearchReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    report_id: int
    task_id: int
    report_content: Dict[str, Any] | str
    created_at: datetime


class DashboardOverviewResponse(BaseModel):
    total_research: int
    completed_research: int
    pending_research: int
    failed_research: int
    total_saved_stocks: int
    recent_research: List[ResearchTaskResponse]
    watchlist_preview: List[SavedStockResponse]
