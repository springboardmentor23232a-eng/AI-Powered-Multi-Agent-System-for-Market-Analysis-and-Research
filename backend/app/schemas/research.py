from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ResearchTaskCreate(BaseModel):
    """
    Schema for starting a new stock research task.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    ticker: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Stock ticker symbol (e.g. INFY.NS, TCS.NS, AAPL)",
        examples=["INFY.NS"]
    )
    period: str = Field(
        default="1mo",
        description="Historical analysis duration: 1mo, 3mo, 6mo, 1y, 2y, 5y, max",
        examples=["1mo"]
    )
    market: Optional[str] = Field(
        default=None,
        description="Market exchange override (e.g. NSE, BSE, NASDAQ, NYSE)",
        examples=["NSE"]
    )


class ResearchReportResponse(BaseModel):
    """
    Schema for the saved research output, consolidated report, and validated metrics.
    """
    model_config = ConfigDict(from_attributes=True)

    report_id: int
    task_id: int
    report_content: Optional[Dict[str, Any]] = None
    overview_data: Optional[Dict[str, Any]] = None
    history_data: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    limitations: Optional[str] = None
    created_at: datetime


class ResearchTaskItemResponse(BaseModel):
    """
    Schema for individual research task items displayed in research history.
    """
    model_config = ConfigDict(from_attributes=True)

    task_id: int
    user_id: int
    ticker: str
    company_name: str
    market: str
    requested_period: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    has_report: bool = False


class ResearchHistoryResponse(BaseModel):
    """
    Standardized response returning the authenticated user's research history.
    """
    status: str = "success"
    count: int
    data: List[ResearchTaskItemResponse]


class ResearchTaskDetailResponse(BaseModel):
    """
    Detailed response returning a research task and its persisted report.
    """
    status: str = "success"
    task: ResearchTaskItemResponse
    report: Optional[ResearchReportResponse] = None

