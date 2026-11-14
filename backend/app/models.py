import uuid
from sqlalchemy import (
    Column,
    String,
    Text,
    ForeignKey,
    UniqueConstraint,
    DateTime,
    Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(150), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    auth_accounts = relationship("UserAuthAccount", back_populates="user", cascade="all, delete-orphan")
    research_tasks = relationship("ResearchTask", back_populates="user", cascade="all, delete-orphan")
    saved_stocks = relationship("SavedStock", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")


class UserAuthAccount(Base):
    __tablename__ = "user_auth_accounts"

    auth_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(30), nullable=False)  # 'google' or 'apple'
    provider_user_id = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_provider_provider_user_id"),
    )

    # Relationships
    user = relationship("User", back_populates="auth_accounts")


class ResearchTask(Base):
    __tablename__ = "research_tasks"

    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    ticker = Column(String(30), nullable=False)
    market = Column(String(30), nullable=True)
    requested_period = Column(String(30), nullable=True)
    status = Column(String(30), default="Pending", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="research_tasks")
    agent_results = relationship("AgentResult", back_populates="task", cascade="all, delete-orphan")
    source_documents = relationship("SourceDocument", back_populates="task", cascade="all, delete-orphan")
    reports = relationship("ResearchReport", back_populates="task", cascade="all, delete-orphan")


class AgentResult(Base):
    __tablename__ = "agent_results"

    result_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("research_tasks.task_id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    status = Column(String(30), nullable=False)
    output_json = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    task = relationship("ResearchTask", back_populates="agent_results")


class SourceDocument(Base):
    __tablename__ = "source_documents"

    source_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("research_tasks.task_id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String(100), nullable=True)
    title = Column(Text, nullable=True)
    source_url = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    retrieved_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    content_hash = Column(String(255), nullable=True)

    # Relationships
    task = relationship("ResearchTask", back_populates="source_documents")


class ResearchReport(Base):
    __tablename__ = "research_reports"

    report_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("research_tasks.task_id", ondelete="CASCADE"), nullable=False, index=True)
    report_content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    limitations = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    task = relationship("ResearchTask", back_populates="reports")


class SavedStock(Base):
    __tablename__ = "saved_stocks"

    saved_stock_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    ticker = Column(String(30), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "ticker", name="uq_user_ticker"),
    )

    # Relationships
    user = relationship("User", back_populates="saved_stocks")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    preference_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    preferred_market = Column(String(30), default="NSE", nullable=False)  # 'NSE', 'BSE', 'NASDAQ', 'NYSE'
    preferred_period = Column(String(30), default="6 Months", nullable=False)  # '1 Month', '3 Months', '6 Months', '1 Year', '5 Years'
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="preferences")


