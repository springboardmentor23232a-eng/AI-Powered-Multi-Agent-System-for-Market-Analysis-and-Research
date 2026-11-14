from sqlalchemy import Column, Integer, String, DateTime, ForeignKey,Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    preferred_market = Column(String, default="NASDAQ",nullable=False)
    preferred_period = Column(String, default="1 Year",nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    saved_stocks = relationship("SavedStock", back_populates="owner",cascade="all, delete-orphan")
    research_tasks = relationship("ResearchTask", back_populates="owner",cascade="all, delete-orphan")
class SavedStock(Base):
    __tablename__ = "saved_stocks"
    saved_stock_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False,index=True)
    ticker = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner = relationship("User", back_populates="saved_stocks")
class ResearchTask(Base):
    __tablename__ = "research_tasks"
    task_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False,index=True)
    company_name = Column(String, nullable=False)
    ticker = Column(String, nullable=False)
    market = Column(String, nullable=False)
    analysis_period = Column(String, nullable=False)
    status = Column(String, default="Completed",nullable=False)
    report_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner = relationship("User", back_populates="research_tasks")