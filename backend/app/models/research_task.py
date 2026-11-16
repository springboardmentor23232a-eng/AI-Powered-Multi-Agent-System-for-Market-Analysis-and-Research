from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ResearchTask(Base):
    """
    SQLAlchemy model representing the 'research_tasks' table.
    Tracks individual stock research requests executed by users.
    """
    __tablename__ = "research_tasks"

    task_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    ticker = Column(String(20), index=True, nullable=False)
    company_name = Column(String(255), nullable=False)
    market = Column(String(50), nullable=False, default="NSE")
    requested_period = Column(String(20), nullable=False, default="1mo")
    status = Column(String(20), index=True, nullable=False, default="Pending")  # Pending, Processing, Completed, Failed
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="research_tasks")
    report = relationship("ResearchReport", back_populates="task", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ResearchTask(task_id={self.task_id}, user_id={self.user_id}, ticker='{self.ticker}', status='{self.status}')>"


class ResearchReport(Base):
    """
    SQLAlchemy model representing the 'research_reports' table.
    Stores the consolidated research report, business summary, data limitations,
    and underlying market telemetry.
    """
    __tablename__ = "research_reports"

    report_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("research_tasks.task_id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    report_content = Column(JSON, nullable=True)
    overview_data = Column(JSON, nullable=False)
    history_data = Column(JSON, nullable=False)
    summary = Column(Text, nullable=True)
    limitations = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    task = relationship("ResearchTask", back_populates="report")

    def __repr__(self) -> str:
        return f"<ResearchReport(report_id={self.report_id}, task_id={self.task_id})>"
