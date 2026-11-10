import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _now() -> datetime:
    return datetime.now(timezone.utc)


class TaskStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    partial = "partial"
    failed = "failed"


class AgentStatus(str, enum.Enum):
    success = "success"
    unavailable = "unavailable"
    failed = "failed"


class ClaimType(str, enum.Enum):
    fact = "FACT"
    calculated = "CALCULATED"
    interpretation = "INTERPRETATION"


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class ResearchTask(Base):
    __tablename__ = "research_tasks"
    task_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id"), index=True)
    ticker: Mapped[str] = mapped_column(String(32), index=True)
    market: Mapped[str] = mapped_column(String(16), default="NSE")
    requested_period: Mapped[str] = mapped_column(String(16), default="2y")
    as_of_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.queued)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_results: Mapped[list["AgentResult"]] = relationship(back_populates="task", cascade="all, delete-orphan")


class AgentResult(Base):
    __tablename__ = "agent_results"
    result_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("research_tasks.task_id"), index=True)
    agent_name: Mapped[str] = mapped_column(String(32))
    status: Mapped[AgentStatus] = mapped_column(Enum(AgentStatus))
    output_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=1)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    task: Mapped[ResearchTask] = relationship(back_populates="agent_results")


class SourceDocument(Base):
    __tablename__ = "source_documents"
    source_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("research_tasks.task_id"), index=True)
    source_type: Mapped[str] = mapped_column(String(32))  # price | financials | news | announcement
    title: Mapped[str] = mapped_column(String(512))
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    content_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)


class ResearchReport(Base):
    __tablename__ = "research_reports"
    report_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("research_tasks.task_id"), unique=True)
    report_content: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text)
    limitations: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class SavedStock(Base):
    __tablename__ = "saved_stocks"
    __table_args__ = (UniqueConstraint("user_id", "ticker", name="uq_saved_user_ticker"),)
    saved_stock_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id"), index=True)
    ticker: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Claim(Base):
    __tablename__ = "claims"
    claim_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("research_tasks.task_id"), index=True)
    ref: Mapped[str] = mapped_column(String(64))  # human-readable id used in reports, e.g. "fundamental-3"
    agent_name: Mapped[str] = mapped_column(String(32))
    claim_type: Mapped[ClaimType] = mapped_column(Enum(ClaimType))
    text: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_note: Mapped[str | None] = mapped_column(Text, nullable=True)


class Contradiction(Base):
    __tablename__ = "contradictions"
    contradiction_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("research_tasks.task_id"), index=True)
    agent_a: Mapped[str] = mapped_column(String(32))
    agent_b: Mapped[str] = mapped_column(String(32))
    claim_a_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    claim_b_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(8), default="medium")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    run_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class MarketSnapshot(Base):
    """Cached provider payloads so demos, tests and replays do not depend on live APIs."""

    __tablename__ = "market_snapshots"
    __table_args__ = (UniqueConstraint("symbol", "kind", "period", name="uq_snapshot_key"),)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    kind: Mapped[str] = mapped_column(String(16))  # prices | financials
    period: Mapped[str] = mapped_column(String(16), default="")
    provider: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict] = mapped_column(JSON)
    content_hash: Mapped[str] = mapped_column(String(64))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
