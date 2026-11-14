from datetime import datetime, timezone
import uuid
from sqlalchemy import text
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utc_now():
    return datetime.now(timezone.utc)



class User(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )

    full_name: Mapped[str] = mapped_column(
        String(120), nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )

    password_hash: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    google_sub: Mapped[str | None] = mapped_column(
        Text, unique=True, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    # Relationships
    preferences: Mapped["UserPreference | None"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    saved_stocks: Mapped[list["SavedStock"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    research_tasks: Mapped[list["ResearchTask"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )



class UserPreference(Base):
    __tablename__ = "user_preferences"

    preference_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    market: Mapped[str] = mapped_column(
        String(20),
        default="NSE",
        nullable=False
    )

    analysis_period: Mapped[str] = mapped_column(
        String(20),
        default="1 Year",
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    user: Mapped["User"] = relationship(
        back_populates="preferences"
    )




class SavedStock(Base):
    __tablename__ = "saved_stocks"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "ticker",
            "market",
            name="uq_saved_stock_user_ticker_market"
        ),
        Index("ix_saved_stocks_user_id", "user_id"),
    )

    saved_stock_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )

    ticker: Mapped[str] = mapped_column(
        String(30), nullable=False
    )

    company_name: Mapped[str] = mapped_column(
        String(200), nullable=False, default=""
    )

    market: Mapped[str] = mapped_column(
        String(20), nullable=False, default="NSE"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    user: Mapped["User"] = relationship(
        back_populates="saved_stocks"
    )



class ResearchTask(Base):
    __tablename__ = "research_tasks"
    __table_args__ = (Index("ix_research_tasks_user_created", "user_id", "created_at"),)

    task_id: Mapped[uuid.UUID] = mapped_column(
    PG_UUID(as_uuid=True),
    primary_key=True,
    default=uuid.uuid4,
    server_default=text("gen_random_uuid()")
)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    ticker: Mapped[str] = mapped_column(String(30), nullable=False)
    market: Mapped[str] = mapped_column(String(20), nullable=False)
    analysis_period: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="Pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="research_tasks")
    report: Mapped["ResearchReport | None"] = relationship(
        back_populates="task", cascade="all, delete-orphan", uselist=False
    )
    agent_results: Mapped[list["AgentResult"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    source_documents: Mapped[list["SourceDocument"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )


class ResearchReport(Base):
    __tablename__ = "research_reports"

    report_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_tasks.task_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    report_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    task: Mapped["ResearchTask"] = relationship(back_populates="report")


class AgentResult(Base):
    __tablename__ = "agent_results"
    __table_args__ = (Index("ix_agent_results_task_id", "task_id"),)

    result_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_tasks.task_id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    result: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="Pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    task: Mapped["ResearchTask"] = relationship(back_populates="agent_results")


class SourceDocument(Base):
    __tablename__ = "source_documents"
    __table_args__ = (Index("ix_source_documents_task_id", "task_id"),)

    document_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_tasks.task_id", ondelete="CASCADE"),
        nullable=False,
    )
    source_name: Mapped[str | None] = mapped_column(String(250), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_metadata: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    task: Mapped["ResearchTask"] = relationship(back_populates="source_documents")
