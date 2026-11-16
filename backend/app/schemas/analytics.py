from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class WorkspaceSummaryResponse(BaseModel):
    """
    Comprehensive workspace analytics summary for the authenticated user.
    Handles empty workspaces safely without errors or division by zero.
    """
    total_sessions: int = 0
    status_counts: Dict[str, int] = Field(
        default_factory=lambda: {"pending": 0, "in_progress": 0, "completed": 0, "failed": 0}
    )
    recommendation_distribution: Dict[str, int] = Field(
        default_factory=lambda: {
            "STRONG_BUY": 0,
            "BUY": 0,
            "HOLD": 0,
            "SELL": 0,
            "STRONG_SELL": 0,
        }
    )
    recommendation_summary: Dict[str, int] = Field(
        default_factory=lambda: {"buy": 0, "hold": 0, "sell": 0}
    )
    average_confidence: float = 0.0
    sector_allocation: Dict[str, int] = Field(default_factory=dict)
    sector_percentages: Dict[str, float] = Field(default_factory=dict)
    latest_activity_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
