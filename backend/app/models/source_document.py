from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class SourceDocument(Base):
    """Data provenance record capturing external data source URLs, timestamps, and hashes."""

    __tablename__ = "source_documents"

    source_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("research_tasks.task_id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String(100), nullable=False)
    title = Column(String(500), nullable=False)
    source_url = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    retrieved_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    content_hash = Column(String(128), nullable=True)

    task = relationship("ResearchTask", back_populates="source_documents")

