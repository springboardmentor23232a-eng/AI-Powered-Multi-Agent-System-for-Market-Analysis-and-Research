import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ResearchCreateRequest(BaseModel):
    """
    Request payload to initiate stock equity research.
    Validates ticker symbols (1-10 alphanumeric characters, permitting '.' and '-').
    """
    ticker: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Stock ticker symbol (e.g. AAPL, MSFT, GOOGL, NVDA, RELIANCE.NS, BRK.B)",
        examples=["AAPL"],
    )

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Ticker symbol cannot be empty.")
        cleaned = v.strip().upper()
        if not re.match(r"^[A-Z0-9.\-]{1,10}$", cleaned):
            raise ValueError(
                f"Invalid ticker symbol format: '{v}'. Ticker must be 1 to 10 alphanumeric characters."
            )
        return cleaned


class ResearchReportResponse(BaseModel):
    """
    Consolidated equity research report response schema.
    Contains consensus recommendation, price targets, executive narrative,
    and structured specialist agent outputs.
    """
    id: int
    session_id: int
    ticker: str
    company_name: str
    current_price: Optional[float] = None
    target_price: Optional[float] = None
    recommendation: str  # STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
    confidence_score: float  # 0.0 to 1.0
    executive_summary: str
    fundamental_data: Optional[Dict[str, Any]] = None
    technical_data: Optional[Dict[str, Any]] = None
    sentiment_data: Optional[Dict[str, Any]] = None
    risk_data: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResearchSessionResponse(BaseModel):
    """
    Summary representation of a stock research session.
    Used for session lists and creation responses.
    """
    id: int
    user_id: int
    ticker: str
    company_name: Optional[str] = None
    status: str  # PENDING, IN_PROGRESS, COMPLETED, FAILED
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ResearchSessionDetailResponse(BaseModel):
    """
    Detailed session representation including status, error info,
    and the associated research report if completed.
    """
    id: int
    user_id: int
    ticker: str
    company_name: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    report: Optional[ResearchReportResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ResearchSessionListResponse(BaseModel):
    """Paginated or bounded list of research sessions for the authenticated user."""
    total: int
    sessions: List[ResearchSessionResponse]

