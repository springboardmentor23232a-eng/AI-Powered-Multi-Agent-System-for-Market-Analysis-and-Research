from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, Float, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    preferences = relationship("Preference", back_populates="user", uselist=False, cascade="all,delete-orphan")
    watchlist = relationship("WatchlistItem", back_populates="user", cascade="all,delete-orphan")

class Preference(Base):
    __tablename__ = "preferences"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    market: Mapped[str] = mapped_column(String(20), default="NSE")
    period: Mapped[str] = mapped_column(String(10), default="3mo")
    user = relationship("User", back_populates="preferences")

class WatchlistItem(Base):
    __tablename__ = "watchlist"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(180), default="")
    market: Mapped[str] = mapped_column(String(20))
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint("user_id", "symbol", "market"),)
    user = relationship("User", back_populates="watchlist")

class ResearchRequest(Base):
    __tablename__ = "research_requests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(180), default="")
    market: Mapped[str] = mapped_column(String(20))
    period: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), default="Pending")
    report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class MarketBar(Base):
    __tablename__ = "market_bars"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(40), index=True)
    market: Mapped[str] = mapped_column(String(20), index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    open: Mapped[float | None] = mapped_column(Float)
    high: Mapped[float | None] = mapped_column(Float)
    low: Mapped[float | None] = mapped_column(Float)
    close: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(80), default="Yahoo Finance")
