"""Database table models.

All tables from the project specification are defined here in Module 1 so the
schema is finalized early (Milestone 1). Later modules add behaviour, not tables.
"""

from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import (
    DEFAULT_ANALYSIS_PERIOD,
    DEFAULT_MARKET,
    AgentStatus,
    AnalysisPeriod,
    Market,
    TaskStatus,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


def _enum(enum_cls, name: str) -> Enum:
    # Stored as VARCHAR + CHECK constraint (portable across PostgreSQL and SQLite).
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
        values_callable=lambda e: [member.value for member in e],
        length=20,
    )


TIMESTAMP = DateTime(timezone=True)
JSON_DOCUMENT = JSON().with_variant(JSONB(), "postgresql")


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now)

    preferences: Mapped["UserPreferences"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class UserPreferences(Base):
    """Addition to the spec: Module 1 requires preferences, but `users` has no columns for them."""

    __tablename__ = "user_preferences"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )
    default_market: Mapped[Market] = mapped_column(_enum(Market, "market"), default=DEFAULT_MARKET)
    analysis_period: Mapped[AnalysisPeriod] = mapped_column(
        _enum(AnalysisPeriod, "analysis_period"), default=DEFAULT_ANALYSIS_PERIOD
    )
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now, onupdate=utc_now)

    user: Mapped[User] = relationship(back_populates="preferences")


class SavedStock(Base):
    __tablename__ = "saved_stocks"
    __table_args__ = (UniqueConstraint("user_id", "ticker", "market", name="uq_saved_stock"),)

    saved_stock_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), index=True
    )
    ticker: Mapped[str] = mapped_column(String(20))
    # Addition to the spec: the same symbol can exist on several exchanges (e.g. NSE and BSE).
    market: Mapped[Market] = mapped_column(_enum(Market, "saved_stock_market"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now)


class ResearchTask(Base):
    __tablename__ = "research_tasks"

    task_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), index=True
    )
    ticker: Mapped[str] = mapped_column(String(20))
    market: Mapped[Market] = mapped_column(_enum(Market, "task_market"))
    requested_period: Mapped[AnalysisPeriod] = mapped_column(
        _enum(AnalysisPeriod, "requested_period")
    )
    status: Mapped[TaskStatus] = mapped_column(
        _enum(TaskStatus, "task_status"), default=TaskStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)

    agent_results: Mapped[list["AgentResult"]] = relationship(cascade="all, delete-orphan")
    source_documents: Mapped[list["SourceDocument"]] = relationship(cascade="all, delete-orphan")
    report: Mapped["ResearchReport | None"] = relationship(
        uselist=False, cascade="all, delete-orphan"
    )


class AgentResult(Base):
    __tablename__ = "agent_results"

    result_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("research_tasks.task_id", ondelete="CASCADE"), index=True
    )
    agent_name: Mapped[str] = mapped_column(String(50))
    status: Mapped[AgentStatus] = mapped_column(_enum(AgentStatus, "agent_status"))
    output_json: Mapped[dict | None] = mapped_column(JSON_DOCUMENT, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now)


class SourceDocument(Base):
    __tablename__ = "source_documents"

    source_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("research_tasks.task_id", ondelete="CASCADE"), index=True
    )
    source_type: Mapped[str] = mapped_column(String(50))  # e.g. market_data, news, filing
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # SHA-256 hex


class ResearchReport(Base):
    __tablename__ = "research_reports"

    report_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("research_tasks.task_id", ondelete="CASCADE"), unique=True
    )
    report_content: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now)


__all__ = [
    "AgentResult",
    "ResearchReport",
    "ResearchTask",
    "SavedStock",
    "SourceDocument",
    "User",
    "UserPreferences",
]
