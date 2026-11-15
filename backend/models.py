
from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Text,
    Boolean,
    ForeignKey,
    UniqueConstraint,
    func
)
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class User(Base):
    # Name of the table in PostgreSQL
    __tablename__ = "users"

    # Unique ID for each user
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    # User's full name
    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    # Email must be unique
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    # Store the hashed password
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # Account activation status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Automatically store account creation date and time
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

class SavedStock(Base):
    __tablename__ = "saved_stocks"

    __table_args__ = (
        UniqueConstraint("user_id", "ticker", name="unique_user_stock"),
    )

    saved_stock_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    ticker: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )
    market: Mapped[str] = mapped_column(
    String(50),
    default="NSI",
    server_default="NSI",
    nullable=False
)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

class ResearchTask(Base):
    __tablename__ = "research_tasks"

    # Unique ID for each research task
    research_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    # Associate the research task with a registered user
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Company details
    company_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    ticker: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    market: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    # Analysis period (1mo, 6mo, 1y, 5y, etc.)
    analysis_period: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    # Research status
    status: Mapped[str] = mapped_column(
        String(20),
        default="Pending",
        nullable=False
    )

    # Generated research report
    report_content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Research creation date
    research_date: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class UserPreference(Base):
    __tablename__ = "user_preferences"

    # Each user can have only one preference record
    preference_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    # Link preferences to the registered user
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # User's preferred stock market
    market: Mapped[str] = mapped_column(
        String(50),
        default="NSI",
        server_default="NSI",
        nullable=False
    )

    # User's preferred historical analysis period
    analysis_period: Mapped[str] = mapped_column(
        String(20),
        default="1y",
        server_default="1y",
        nullable=False
    )

    # Automatically store last update time
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
