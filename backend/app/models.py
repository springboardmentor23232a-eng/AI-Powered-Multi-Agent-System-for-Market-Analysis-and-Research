import datetime as dt

from sqlalchemy import (JSON, BigInteger, Date, DateTime, Float, ForeignKey, Integer,
                        String, Text, UniqueConstraint, func)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    preferences: Mapped["UserPreference"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    market: Mapped[str] = mapped_column(String(10), default="NASDAQ")
    analysis_period: Mapped[str] = mapped_column(String(3), default="1Y")

    user: Mapped[User] = relationship(back_populates="preferences")


class SavedStock(Base):
    __tablename__ = "saved_stocks"
    __table_args__ = (UniqueConstraint("user_id", "ticker", name="uq_saved_stock_user_ticker"),)

    saved_stock_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    ticker: Mapped[str] = mapped_column(String(20))
    company_name: Mapped[str] = mapped_column(String(200))
    market: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ResearchTask(Base):
    __tablename__ = "research_tasks"

    task_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    company_name: Mapped[str] = mapped_column(String(200))
    ticker: Mapped[str] = mapped_column(String(20))
    market: Mapped[str] = mapped_column(String(10))
    analysis_period: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(12), default="Pending")  # Pending, Processing, Completed, Failed
    report: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DataCollection(Base):
    """One retrieval of market data for a ticker, with where it came from and when."""
    __tablename__ = "data_collections"

    collection_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    ticker: Mapped[str] = mapped_column(String(20))
    company_name: Mapped[str] = mapped_column(String(200))
    market: Mapped[str] = mapped_column(String(10))
    analysis_period: Mapped[str] = mapped_column(String(3))
    source: Mapped[str] = mapped_column(String(80))
    retrieved_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    rows_raw: Mapped[int] = mapped_column(Integer)
    rows_clean: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(10))  # Clean, or Cleaned when problems were found and fixed
    report: Mapped[dict] = mapped_column(JSON)       # validation report
    profile: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    financials: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class PriceBar(Base):
    """One cleaned OHLCV row belonging to a collection."""
    __tablename__ = "price_bars"
    __table_args__ = (UniqueConstraint("collection_id", "date", name="uq_price_bar_collection_date"),)

    bar_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    collection_id: Mapped[int] = mapped_column(ForeignKey("data_collections.collection_id", ondelete="CASCADE"), index=True)
    date: Mapped[dt.date] = mapped_column(Date)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[int] = mapped_column(BigInteger)
