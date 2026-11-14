import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    saved_stocks = relationship("SavedStock", back_populates="user", cascade="all, delete-orphan")
    research_tasks = relationship("ResearchTask", back_populates="user", cascade="all, delete-orphan")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    preference_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    market = Column(String(20), default="NASDAQ", nullable=False)  # NSE, BSE, NASDAQ, NYSE
    analysis_period = Column(String(20), default="1 Year", nullable=False)  # 1 Month, 3 Months, 6 Months, 1 Year, 5 Years
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="preferences")


class SavedStock(Base):
    __tablename__ = "saved_stocks"

    saved_stock_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    ticker = Column(String(20), nullable=False)
    company_name = Column(String(255), nullable=False)
    market = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "ticker", name="uq_user_ticker"),
    )

    user = relationship("User", back_populates="saved_stocks")


class ResearchTask(Base):
    __tablename__ = "research_tasks"

    task_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    ticker = Column(String(20), nullable=False)
    company_name = Column(String(255), nullable=False)
    market = Column(String(20), nullable=False)
    analysis_period = Column(String(20), nullable=False)
    status = Column(String(30), default="Pending", nullable=False)  # Pending, Processing, Completed, Failed
    report_summary = Column(Text, nullable=True)
    report_data = Column(Text, nullable=True)  # JSON-serialized comprehensive multi-agent report
    created_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("User", back_populates="research_tasks")
