from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Create SQLAlchemy engine connected to PostgreSQL
engine = create_engine(
    settings.DATABASE_URL,
    echo=False
)

# Session factory for handling database transactions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy ORM models
Base = declarative_base()

def get_db():
    """
    Dependency that creates a new database session for each request
    and ensures it is cleanly closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

