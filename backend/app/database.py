import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:SANJU76@localhost:5432/multi_agent_stock_db"
)

logger = logging.getLogger("stock_analyst.database")
logging.basicConfig(level=logging.INFO)

# Create SQLAlchemy engine with connection pooling and pre-ping
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False
)

# Create session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base model
Base = declarative_base()


def get_db():
    """
    Reusable database dependency for FastAPI endpoints.
    Yields a database session and ensures clean closure.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initializes database tables and verifies connection to multi_agent_stock_db.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database(), current_user, version();"))
            db_name, db_user, db_version = result.fetchone()
            print(f"\n=======================================================")
            print(f"[DATABASE] Successfully connected to PostgreSQL!")
            print(f"[DATABASE] Active Database: {db_name}")
            print(f"[DATABASE] Connected User:   {db_user}")
            print(f"[DATABASE] Database Version: {db_version.split(',')[0]}")
            print(f"=======================================================\n")
            
        # Create all defined models in the database safely
        Base.metadata.create_all(bind=engine)
        print("[DATABASE] All 7 database tables verified and initialized successfully.")
        return True
    except Exception as e:
        logger.error(f"[DATABASE] Connection to multi_agent_stock_db failed: {e}")
        print(f"\n[ERROR] Failed to connect to multi_agent_stock_db: {e}\n")
        raise e

