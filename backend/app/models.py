import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Text, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column("id", String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    auth_provider: Mapped[str] = mapped_column(String(20), default="local", nullable=False)
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    google_identities = relationship("GoogleIdentity", back_populates="user", cascade="all, delete-orphan")

class GoogleIdentity(Base):
    __tablename__ = "google_identities"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    google_sub: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    user = relationship("User", back_populates="google_identities")

class ResearchTask(Base):
    __tablename__ = "research_tasks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    market: Mapped[str] = mapped_column(String(16), nullable=False)
    analysis_period: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    report = relationship("ResearchReport", back_populates="task", uselist=False, cascade="all, delete-orphan")

    @property
    def report_available(self) -> bool:
        return self.report is not None

class ResearchReport(Base):
    __tablename__ = "research_reports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id: Mapped[str] = mapped_column(ForeignKey("research_tasks.id", ondelete="CASCADE"), unique=True, nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    report_content: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    limitations: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    task = relationship("ResearchTask", back_populates="report")

class SavedStock(Base):
    __tablename__ = "saved_stocks"
    __table_args__ = (UniqueConstraint("user_id", "ticker", "market", name="uq_user_ticker_market"),)
    id: Mapped[str] = mapped_column("id", String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    market: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    stock_metadata = relationship("SavedStockMetadata", back_populates="stock", uselist=False, cascade="all, delete-orphan")

class SavedStockMetadata(Base):
    __tablename__ = "saved_stock_metadata"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    saved_stock_id: Mapped[str] = mapped_column(String(36), ForeignKey("saved_stocks.id", ondelete="CASCADE"), unique=True, nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    market: Mapped[str | None] = mapped_column(String(16), nullable=True)
    provider_symbol: Mapped[str | None] = mapped_column(String(40), nullable=True)
    stock = relationship("SavedStock", back_populates="stock_metadata")

class UserPreference(Base):
    __tablename__ = "user_preferences"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    default_market: Mapped[str] = mapped_column(String(16), default="NASDAQ", nullable=False)
    default_analysis_period: Mapped[str] = mapped_column(String(20), default="1 Year", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    user = relationship("User", back_populates="preferences")
