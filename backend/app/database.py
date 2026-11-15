from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.config import settings

# Ensure connection string uses psycopg 3 driver (postgresql+psycopg://)
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

# Create the SQLAlchemy 2 engine
engine = create_engine(
    db_url,
    pool_pre_ping=True,  # Test connections before using from pool to handle stale connections
    echo=False,          # Set to True if detailed SQL queries logging is desired
)

# Session factory for generating database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """
    SQLAlchemy 2.0 DeclarativeBase.
    All database models will inherit from this base class.
    """
    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a scoped database session per request.
    Automatically closes the session after the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

