from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class ResearchReport(Base):
    __tablename__ = "research_reports"

    report_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("research_tasks.task_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    report_content = Column(Text, nullable=False)  # JSON or structured markdown
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    task = relationship("ResearchTask", back_populates="report")

