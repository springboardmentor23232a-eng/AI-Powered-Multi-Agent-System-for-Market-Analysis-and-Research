"""Creates the PostgreSQL database (if missing) and all tables.

Usage: python init_db.py
"""
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.config import DATABASE_URL
from app.database import Base, engine
from app import models  # noqa: F401  (registers the tables)


def create_database():
    url = make_url(DATABASE_URL)
    if url.get_backend_name() != "postgresql":
        return
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": url.database})
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{url.database}"'))
            print(f"Created database {url.database}")
    admin.dispose()


if __name__ == "__main__":
    create_database()
    Base.metadata.create_all(engine)
    print("Tables ready:", ", ".join(Base.metadata.tables))
