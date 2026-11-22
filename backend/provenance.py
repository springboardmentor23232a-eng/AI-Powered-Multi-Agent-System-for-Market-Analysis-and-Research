import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models import DataFetchLog

SOURCE = "Yahoo Finance (yfinance)"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def elapsed_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


def log_fetch(
    db: Session,
    *,
    user_id,
    data_type: str,
    status: str,
    ticker: str | None = None,
    detail: str | None = None,
    record_count: int | None = None,
    as_of: str | None = None,
    duration_ms: int | None = None,
    error: str | None = None,
    retrieved_at: datetime | None = None,
) -> None:
    """Writes one provenance record. Logging must never break the real request."""
    try:
        db.add(
            DataFetchLog(
                user_id=user_id,
                source=SOURCE,
                data_type=data_type,
                ticker=ticker,
                request_detail=detail,
                status=status,
                record_count=record_count,
                as_of=as_of,
                duration_ms=duration_ms,
                error_message=error[:500] if error else None,
                retrieved_at=retrieved_at or now_utc(),
            )
        )
        db.commit()
    except Exception:
        db.rollback()