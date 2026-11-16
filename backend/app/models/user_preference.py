from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class UserPreference(Base):
    """
    SQLAlchemy model representing the 'user_preferences' table.
    Stores user-configured default market (NSE, BSE, NASDAQ, NYSE)
    and analysis period (1mo, 3mo, 6mo, 1y, 5y).
    Enforces a strict 1-to-1 relationship with the 'users' table via unique user_id constraint.
    """
    __tablename__ = "user_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_preference_user_id"),
    )

    preference_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    market = Column(String(20), nullable=False, default="NSE")
    analysis_period = Column(String(20), nullable=False, default="1mo")
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="preference")

    def __repr__(self) -> str:
        return (
            f"<UserPreference(preference_id={self.preference_id}, "
            f"user_id={self.user_id}, market='{self.market}', "
            f"analysis_period='{self.analysis_period}')>"
        )
