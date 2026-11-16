import logging
from typing import Any, Dict, Generator
from urllib.parse import urlparse
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.config import settings

logger = logging.getLogger("uvicorn.error")

# Configure database engine arguments
connect_args = {}
db_url = settings.DATABASE_URL

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Create SQLAlchemy engine with pool_pre_ping to verify liveness of pooled connections
engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a SQLAlchemy database session per request.
    Ensures sessions are closed and cleaned up properly.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_connection() -> Dict[str, Any]:
    """
    Verifies connection to the database and inspects existing tables.
    Returns diagnostic metadata without exposing sensitive credentials or passwords.
    """
    parsed = urlparse(db_url)
    sanitized_host = parsed.hostname or "localhost"
    sanitized_port = parsed.port or 5432
    sanitized_db = parsed.path.lstrip("/") if parsed.path else "unknown"

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        inspector = inspect(engine)
        tables = inspector.get_table_names()

    return {
        "connected": True,
        "dialect": engine.dialect.name,
        "database": sanitized_db,
        "host": sanitized_host,
        "port": sanitized_port,
        "tables": tables,
    }


def init_db() -> None:
    """
    Initializes database schema and ensures all models/tables exist in the database.
    Guarantees that Task 4 compliance columns exist in research_reports.
    """
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Safe column integrity check for existing research_reports table
    try:
        inspector = inspect(engine)
        if "research_reports" in inspector.get_table_names():
            cols = {c["name"] for c in inspector.get_columns("research_reports")}
            with engine.begin() as conn:
                if "report_content" not in cols:
                    conn.execute(text("ALTER TABLE research_reports ADD COLUMN IF NOT EXISTS report_content JSON;"))
                if "limitations" not in cols:
                    conn.execute(text("ALTER TABLE research_reports ADD COLUMN IF NOT EXISTS limitations TEXT;"))
    except Exception as exc:
        logger.warning(f"Database schema verification notice: {exc}")

