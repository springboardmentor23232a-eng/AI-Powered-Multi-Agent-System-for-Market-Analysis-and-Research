from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    auth_provider = Column(String(20), default="local", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    preferences = relationship(
        "UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    saved_stocks = relationship(
        "SavedStock", back_populates="user", cascade="all, delete-orphan"
    )
    research_tasks = relationship(
        "ResearchTask", back_populates="user", cascade="all, delete-orphan"
    )
    source_documents = relationship(
        "SourceDocument", back_populates="user", cascade="all, delete-orphan"
    )
    portfolio_holdings = relationship(
        "PortfolioHolding", back_populates="user", cascade="all, delete-orphan"
    )
    portfolio_orders = relationship(
        "PortfolioOrder", back_populates="user", cascade="all, delete-orphan"
    )


class UserPreference(Base):
    __tablename__ = "user_preferences"

    preference_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False
    )
    market = Column(String(20), default="NSE", nullable=False)
    analysis_period = Column(String(20), default="1Y", nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="preferences")


class SavedStock(Base):
    __tablename__ = "saved_stocks"
    __table_args__ = (UniqueConstraint("user_id", "ticker", name="uq_user_saved_ticker"),)

    saved_stock_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False
    )
    ticker = Column(String(32), nullable=False)
    company_name = Column(String(200), nullable=True)
    market = Column(String(20), default="NSE", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", back_populates="saved_stocks")


class ResearchTask(Base):
    __tablename__ = "research_tasks"

    task_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False
    )
    ticker = Column(String(32), index=True, nullable=False)
    company_name = Column(String(200), nullable=True)
    market = Column(String(20), nullable=False)
    analysis_period = Column(String(20), nullable=False)
    status = Column(String(20), default="Pending", nullable=False)
    error_message = Column(Text, nullable=True)
    report_json = Column(Text, nullable=True)
    summary_markdown = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="research_tasks")
    sources = relationship("SourceDocument", back_populates="task", cascade="all, delete-orphan")


class SourceDocument(Base):
    __tablename__ = "source_documents"

    source_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False
    )
    task_id = Column(
        Integer, ForeignKey("research_tasks.task_id", ondelete="CASCADE"), index=True, nullable=True
    )
    ticker = Column(String(32), index=True, nullable=False)
    market = Column(String(20), nullable=False)
    source_name = Column(String(120), default="Yahoo Finance (yfinance)", nullable=False)
    source_url = Column(String(500), nullable=False)
    data_type = Column(String(80), nullable=False)
    retrieved_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", back_populates="source_documents")
    task = relationship("ResearchTask", back_populates="sources")


class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"
    __table_args__ = (UniqueConstraint("user_id", "ticker", "market", name="uq_user_holding"),)

    holding_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False
    )
    ticker = Column(String(32), nullable=False)
    company_name = Column(String(200), nullable=True)
    market = Column(String(20), nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    average_price = Column(Float, default=0.0, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="portfolio_holdings")


class PortfolioOrder(Base):
    __tablename__ = "portfolio_orders"

    order_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False
    )
    ticker = Column(String(32), nullable=False)
    company_name = Column(String(200), nullable=True)
    market = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # BUY or SELL
    quantity = Column(Integer, nullable=False)
    price_per_share = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(String(20), default="Executed", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", back_populates="portfolio_orders")