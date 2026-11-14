import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from .config import settings

_pool: pool.ThreadedConnectionPool | None = None


def init_pool() -> None:
    global _pool
    if _pool is None:
        _pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            dbname=settings.DATABASE_NAME,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD,
            cursor_factory=RealDictCursor,
        )


def get_connection():
    if _pool is None:
        init_pool()
    return _pool.getconn()


def put_connection(conn) -> None:
    _pool.putconn(conn)


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None
