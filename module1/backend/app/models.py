"""SQLAlchemy models = the PostgreSQL tables for Module 1.

Relationships
  users 1 ── 1 user_preferences
  users 1 ── * oauth_identities   (Google / Apple sign-in links)
  users 1 ── * saved_stocks      (unique per user+ticker)
  users 1 ── * research_tasks
  research_tasks 1 ── 0..1 research_reports   (linked through task_id)
  research_tasks 1 ── * agent_results       (one row per agent output - filled by the agents in Milestone 2+)
  research_tasks 1 ── * source_documents    (every data retrieval: where from, when, how clean)
  users 1 ── * source_documents             (retrievals made outside a task, e.g. the dashboard price chart)
"""
from datetime import datetime

from sqlalchemy import (
    JSON, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

MARKETS = ("NSE", "BSE", "NASDAQ", "NYSE")
PERIODS = ("1M", "3M", "6M", "1Y", "5Y")
STATUSES = ("Pending", "Processing", "Completed", "Failed")
AUTH_PROVIDERS = ("google", "apple")
DOC_TYPES = ("ohlcv", "profile", "financials", "news")

JsonType = JSON().with_variant(JSONB(), "postgresql")


def _in(col: str, values) -> str:
    return f"{col} IN ({', '.join(repr(v) for v in values)})"


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)  # unique -> indexed
    # bcrypt hash only. NULL for accounts created through "Continue with Google / Apple" (they have no password).
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    preferences: Mapped["UserPreference"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    oauth_identities: Mapped[list["OAuthIdentity"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    saved_stocks: Mapped[list["SavedStock"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    research_tasks: Mapped[list["ResearchTask"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class OAuthIdentity(Base):
    """Links a user to a "Continue with Google / Apple" account. `provider_user_id` is the provider's stable `sub`."""
    __tablename__ = "oauth_identities"
    __table_args__ = (
        CheckConstraint(_in("provider", AUTH_PROVIDERS), name="ck_oauth_provider"),
        UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_identity"),
        UniqueConstraint("user_id", "provider", name="uq_oauth_user_provider"),
    )

    identity_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(10), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="oauth_identities")


class UserPreference(Base):
    __tablename__ = "user_preferences"
    __table_args__ = (
        CheckConstraint(_in("market", MARKETS), name="ck_pref_market"),
        CheckConstraint(_in("analysis_period", PERIODS), name="ck_pref_period"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    market: Mapped[str] = mapped_column(String(10), nullable=False, default="NASDAQ")
    analysis_period: Mapped[str] = mapped_column(String(3), nullable=False, default="1Y")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="preferences")


class SavedStock(Base):
    __tablename__ = "saved_stocks"
    __table_args__ = (
        UniqueConstraint("user_id", "ticker", name="uq_saved_stock_user_ticker"),  # no duplicates per user
        Index("ix_saved_stocks_user_id", "user_id"),
    )

    saved_stock_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    # convenience columns (not required by the guide): remember where the ticker is listed
    company_name: Mapped[str] = mapped_column(String(150), nullable=False)
    market: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="saved_stocks")


class ResearchTask(Base):
    __tablename__ = "research_tasks"
    __table_args__ = (
        CheckConstraint(_in("status", STATUSES), name="ck_task_status"),
        CheckConstraint(_in("market", MARKETS), name="ck_task_market"),
        CheckConstraint(_in("analysis_period", PERIODS), name="ck_task_period"),
        Index("ix_research_tasks_user_created", "user_id", "created_at"),
        Index("ix_research_tasks_status", "status"),
    )

    task_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    company_name: Mapped[str] = mapped_column(String(150), nullable=False)
    market: Mapped[str] = mapped_column(String(10), nullable=False)
    analysis_period: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="Pending")
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="research_tasks")
    report: Mapped["ResearchReport"] = relationship(back_populates="task", cascade="all, delete-orphan", uselist=False)
    agent_results: Mapped[list["AgentResult"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    source_documents: Mapped[list["SourceDocument"]] = relationship(back_populates="task", cascade="all, delete-orphan")


class ResearchReport(Base):
    __tablename__ = "research_reports"

    report_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("research_tasks.task_id", ondelete="CASCADE"), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[dict] = mapped_column(JsonType, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    task: Mapped[ResearchTask] = relationship(back_populates="report")


class AgentResult(Base):
    """Individual agent output (Fundamental / Technical / News / Risk / Supervisor). Filled from Milestone 2 on."""
    __tablename__ = "agent_results"
    __table_args__ = (
        CheckConstraint(_in("status", ("Completed", "Failed", "Unavailable")), name="ck_agent_result_status"),
        Index("ix_agent_results_task_id", "task_id"),
    )

    result_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("research_tasks.task_id", ondelete="CASCADE"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="Completed")
    output: Mapped[dict] = mapped_column(JsonType, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    task: Mapped[ResearchTask] = relationship(back_populates="agent_results")


class SourceDocument(Base):
    """One row per data retrieval: what was fetched, from which source, when, and the data-quality report."""
    __tablename__ = "source_documents"
    __table_args__ = (
        CheckConstraint(_in("doc_type", DOC_TYPES), name="ck_source_doc_type"),
        Index("ix_source_documents_task_id", "task_id"),
        Index("ix_source_documents_user_retrieved", "user_id", "retrieved_at"),
    )

    source_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("research_tasks.task_id", ondelete="CASCADE"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"))
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    market: Mapped[str] = mapped_column(String(10), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(12), nullable=False)
    source_name: Mapped[str] = mapped_column(String(150), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500))
    is_synthetic: Mapped[bool] = mapped_column(nullable=False, default=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    record_count: Mapped[int | None] = mapped_column(Integer)
    quality: Mapped[dict | None] = mapped_column(JsonType)

    task: Mapped[ResearchTask | None] = relationship(back_populates="source_documents")
