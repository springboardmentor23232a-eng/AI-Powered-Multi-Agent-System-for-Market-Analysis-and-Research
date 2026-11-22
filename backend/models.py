from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    auth_provider: Mapped[str] = mapped_column(String(20), default="local")
    provider_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class Watchlist(Base):
    __tablename__ = "watchlists"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_watchlists_user_name"),
    )

    watchlist_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class SavedStock(Base):
    __tablename__ = "saved_stocks"
    __table_args__ = (
        # A stock can appear once per watchlist (but may be in several lists)
        UniqueConstraint("watchlist_id", "ticker", name="uq_saved_stocks_watchlist_ticker"),
    )

    saved_stock_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), index=True
    )
    watchlist_id: Mapped[int] = mapped_column(
        ForeignKey("watchlists.watchlist_id", ondelete="CASCADE"), index=True
    )
    ticker: Mapped[str] = mapped_column(String(30))
    company_name: Mapped[str] = mapped_column(String(200))
    market: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )
    market: Mapped[str] = mapped_column(String(10), default="NSE")
    analysis_period: Mapped[str] = mapped_column(String(10), default="1Y")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ResearchTask(Base):
    __tablename__ = "research_tasks"

    task_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), index=True
    )
    company_name: Mapped[str] = mapped_column(String(200))
    ticker: Mapped[str] = mapped_column(String(30))
    market: Mapped[str] = mapped_column(String(10))
    analysis_period: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), default="Pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class DataFetchLog(Base):
    __tablename__ = "data_fetch_logs"

    fetch_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id", ondelete="SET NULL"), index=True, nullable=True
    )
    task_id: Mapped[int | None] = mapped_column(
        ForeignKey("research_tasks.task_id", ondelete="SET NULL"), nullable=True
    )  # filled in later, when the agent workflow uses this data
    source: Mapped[str] = mapped_column(String(60))
    data_type: Mapped[str] = mapped_column(String(30))
    ticker: Mapped[str | None] = mapped_column(String(30), index=True, nullable=True)
    request_detail: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(10))  # success / partial / failed
    record_count: Mapped[int | None] = mapped_column(nullable=True)
    as_of: Mapped[str | None] = mapped_column(String(10), nullable=True)  # latest data date
    duration_ms: Mapped[int | None] = mapped_column(nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )  