from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    """
    Users Table: Stores core account credentials and metadata.
    Passwords are stored strictly as secure bcrypt hashes (never plain text).
    """
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    saved_stocks = relationship("SavedStock", back_populates="user", cascade="all, delete-orphan")
    research_tasks = relationship("ResearchTask", back_populates="user", cascade="all, delete-orphan")


class UserPreference(Base):
    """
    User Preferences Table: Tracks user market and analysis period preferences.
    """
    __tablename__ = "user_preferences"

    preference_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    market = Column(String(50), default="NSE", nullable=False)
    analysis_period = Column(String(50), default="1 Year", nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="preferences")


class SavedStock(Base):
    """
    Saved Stocks (Watchlist) Table: Personal watchlist per user.
    Enforces a unique constraint so a user cannot duplicate a stock ticker.
    """
    __tablename__ = "saved_stocks"

    saved_stock_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    ticker = Column(String(20), nullable=False, index=True)
    company_name = Column(String(255), nullable=True)
    market = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="saved_stocks")

    __table_args__ = (
        UniqueConstraint("user_id", "ticker", name="uq_user_ticker"),
    )


class ResearchTask(Base):
    """
    Research Tasks Table: Tracks stock research workflows requested by users.
    """
    __tablename__ = "research_tasks"

    task_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    ticker = Column(String(20), nullable=False)
    market = Column(String(50), default="NSE", nullable=False)
    requested_period = Column(String(50), default="1 Year", nullable=False)
    status = Column(String(50), default="Pending", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="research_tasks")
    agent_results = relationship("AgentResult", back_populates="task", cascade="all, delete-orphan")
    source_documents = relationship("SourceDocument", back_populates="task", cascade="all, delete-orphan")
    report = relationship("ResearchReport", back_populates="task", uselist=False, cascade="all, delete-orphan")


class AgentResult(Base):
    """
    Agent Results Table: Captures intermediate outputs from specialized agents.
    """
    __tablename__ = "agent_results"

    result_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("research_tasks.task_id", ondelete="CASCADE"), nullable=False)
    agent_name = Column(String(100), nullable=False)
    status = Column(String(50), default="Pending", nullable=False)
    output_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    task = relationship("ResearchTask", back_populates="agent_results")


class SourceDocument(Base):
    """
    Source Documents Table: Citations, data sources, and timestamps for factual audit.
    """
    __tablename__ = "source_documents"

    source_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("research_tasks.task_id", ondelete="CASCADE"), nullable=False)
    source_type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=True)
    source_url = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    retrieved_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    content_hash = Column(String(64), nullable=True)

    task = relationship("ResearchTask", back_populates="source_documents")


class ResearchReport(Base):
    """
    Research Reports Table: Consolidated final multi-agent stock research report.
    """
    __tablename__ = "research_reports"

    report_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("research_tasks.task_id", ondelete="CASCADE"), unique=True, nullable=False)
    report_content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    limitations = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    task = relationship("ResearchTask", back_populates="report")

