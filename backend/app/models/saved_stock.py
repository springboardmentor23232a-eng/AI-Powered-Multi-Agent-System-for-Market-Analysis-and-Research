from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship
from app.database import Base


class SavedStock(Base):
    __tablename__ = "saved_stocks"

    saved_stock_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    ticker = Column(String(50), nullable=False, index=True)
    market = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="saved_stocks")

    __table_args__ = (
        UniqueConstraint("user_id", "ticker", "market", name="uq_user_ticker_market"),
    )

