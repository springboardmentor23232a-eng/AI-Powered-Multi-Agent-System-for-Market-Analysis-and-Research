from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (String, Text, DateTime, ForeignKey, UniqueConstraint, Index, JSON)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    preference: Mapped[Optional["UserPreference"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan")
    saved_stocks: Mapped[list["SavedStock"]] = relationship(
        back_populates="user", cascade="all, delete-orphan")
    research_tasks: Mapped[list["ResearchTask"]] = relationship(
        back_populates="user", cascade="all, delete-orphan")


class UserPreference(Base):
    __tablename__ = "user_preferences"
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)  # one-to-one
    market: Mapped[str] = mapped_column(String(10), default="NSE")
    analysis_period: Mapped[str] = mapped_column(String(10), default="1y")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped["User"] = relationship(back_populates="preference")


class SavedStock(Base):
    __tablename__ = "saved_stocks"
    __table_args__ = (UniqueConstraint("user_id", "ticker", name="uq_saved_user_ticker"),)

    saved_stock_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    ticker: Mapped[str] = mapped_column(String(20))
    company_name: Mapped[Optional[str]] = mapped_column(String(200))
    market: Mapped[Optional[str]] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="saved_stocks")


class ResearchTask(Base):
    __tablename__ = "research_tasks"
    __table_args__ = (Index("ix_tasks_user_created", "user_id", "created_at"),)

    task_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    ticker: Mapped[str] = mapped_column(String(20))
    company_name: Mapped[Optional[str]] = mapped_column(String(200))
    market: Mapped[str] = mapped_column(String(10))
    requested_period: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="research_tasks")
    report: Mapped[Optional["ResearchReport"]] = relationship(
        back_populates="task", uselist=False, cascade="all, delete-orphan")
    agent_results: Mapped[list["AgentResult"]] = relationship(
        back_populates="task", cascade="all, delete-orphan")
    sources: Mapped[list["SourceDocument"]] = relationship(
        back_populates="task", cascade="all, delete-orphan")


class ResearchReport(Base):
    __tablename__ = "research_reports"
    report_id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("research_tasks.task_id", ondelete="CASCADE"), unique=True)  # 1 task = 1 report
    report_content: Mapped[str] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    limitations: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    task: Mapped["ResearchTask"] = relationship(back_populates="report")


class AgentResult(Base):
    __tablename__ = "agent_results"
    result_id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("research_tasks.task_id", ondelete="CASCADE"), index=True)
    agent_name: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20))
    output_json: Mapped[Optional[dict]] = mapped_column(JSON)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    task: Mapped["ResearchTask"] = relationship(back_populates="agent_results")


class SourceDocument(Base):
    __tablename__ = "source_documents"
    source_id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("research_tasks.task_id", ondelete="CASCADE"), index=True)
    source_type: Mapped[str] = mapped_column(String(30))
    title: Mapped[Optional[str]] = mapped_column(String(500))
    source_url: Mapped[Optional[str]] = mapped_column(String(1000))
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64))

    task: Mapped["ResearchTask"] = relationship(back_populates="sources")