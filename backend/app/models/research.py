from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ResearchSession(Base):
    """
    Tracks an end-to-end multi-agent stock research session initiated by a user.
    Statuses: PENDING, IN_PROGRESS, COMPLETED, FAILED.
    """
    __tablename__ = "research_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
        nullable=False,
        index=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user = relationship("User", back_populates="research_sessions")
    report = relationship(
        "ResearchReport",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ResearchSession(id={self.id}, ticker='{self.ticker}', status='{self.status}', user_id={self.user_id})>"


class ResearchReport(Base):
    """
    Stores the synthesized multi-agent equity research report.
    Contains findings from Fundamental, Technical, Sentiment, and Risk agents,
    along with CIO consensus recommendations.
    """
    __tablename__ = "research_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("research_sessions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(150), nullable=False)
    current_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recommendation: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )  # STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 to 1.0
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False)

    # Specialist Agent Outputs (JSON data)
    fundamental_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    technical_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    sentiment_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    risk_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    session = relationship("ResearchSession", back_populates="report")

    def __repr__(self) -> str:
        return f"<ResearchReport(id={self.id}, ticker='{self.ticker}', rec='{self.recommendation}', target={self.target_price})>"

