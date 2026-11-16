from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class SavedStock(Base):
    """
    SQLAlchemy model representing the 'saved_stocks' table.
    Stores stocks saved to user watchlists.
    Enforces uniqueness per user and ticker via the 'uq_user_ticker' constraint.
    """
    __tablename__ = "saved_stocks"
    __table_args__ = (
        UniqueConstraint("user_id", "ticker", name="uq_user_ticker"),
    )

    saved_stock_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    ticker = Column(String(20), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="saved_stocks")

    def __repr__(self) -> str:
        return f"<SavedStock(saved_stock_id={self.saved_stock_id}, user_id={self.user_id}, ticker='{self.ticker}')>"
