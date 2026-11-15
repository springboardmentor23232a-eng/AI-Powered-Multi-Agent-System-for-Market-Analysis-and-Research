"""SQLAlchemy models = the PostgreSQL tables for Module 1.

Relationships
  users 1 ── 1 user_preferences
  users 1 ── * saved_stocks      (unique per user+ticker)
  users 1 ── * research_tasks
  research_tasks 1 ── 0..1 research_reports   (linked through task_id)
Full project tables Agent Results / Source Documents will also hang off research_tasks.task_id.
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

JsonType = JSON().with_variant(JSONB(), "postgresql")


def _in(col: str, values) -> str:
    return f"{col} IN ({', '.join(repr(v) for v in values)})"


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)  # unique -> indexed
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)  # bcrypt hash only
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    preferences: Mapped["UserPreference"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    saved_stocks: Mapped[list["SavedStock"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    research_tasks: Mapped[list["ResearchTask"]] = relationship(back_populates="user", cascade="all, delete-orphan")


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


class ResearchReport(Base):
    __tablename__ = "research_reports"

    report_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("research_tasks.task_id", ondelete="CASCADE"), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[dict] = mapped_column(JsonType, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    task: Mapped[ResearchTask] = relationship(back_populates="report")
