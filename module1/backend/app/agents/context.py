"""Shared inputs for one research run: the stock, the validated price history, and (optionally) where to log sources."""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..catalog import MARKET_INFO, PERIOD_INFO, Stock
from ..market_data import Fetched, fetch_ohlcv
from ..sources import record_source
from ..validation import Bar, validate_ohlcv

WARMUP_PERIOD = "1Y"      # indicators like SMA50/MACD/RSI need history before the window starts
_SHORT = {"1M", "3M", "6M"}


@dataclass
class ResearchContext:
    stock: Stock
    period: str
    bars: list[Bar]                  # validated, ascending, >= 1 year when available (indicator warm-up)
    window: list[Bar]                # the part of `bars` inside the selected analysis period
    quality: dict
    ohlcv: Fetched
    db: Session | None = None
    user_id: int | None = None
    task_id: int | None = None
    today: date = field(default_factory=lambda: datetime.now(timezone.utc).date())

    @property
    def currency(self) -> str:
        return MARKET_INFO[self.stock.market]["currency"]

    @property
    def price_is_synthetic(self) -> bool:
        return self.ohlcv.synthetic

    @property
    def last_price(self) -> float | None:
        return self.bars[-1].close if self.bars else None

    def record(self, doc_type: str, fetched: Fetched, count: int | None = None, quality: dict | None = None) -> None:
        """Log a data retrieval (source + timestamp) when a database session is attached."""
        if self.db is not None:
            record_source(self.db, self.stock, doc_type, fetched, user_id=self.user_id, task_id=self.task_id,
                          record_count=count, quality=quality)


def build_context(stock: Stock, period: str, db: Session | None = None, user_id: int | None = None,
                  task_id: int | None = None) -> ResearchContext:
    """Fetch + validate prices once for all agents. Raises MarketDataError / ValueError when no usable data exists."""
    fetch_period = WARMUP_PERIOD if period in _SHORT else period
    fetched = fetch_ohlcv(stock, fetch_period)
    bars, quality = validate_ohlcv(fetched.data)
    ctx = ResearchContext(stock, period, bars, bars, quality, fetched, db, user_id, task_id)
    ctx.record("ohlcv", fetched, len(bars), quality)
    if not quality["usable"]:
        raise ValueError(f"Price data for {stock.ticker} failed validation ({len(bars)} valid rows).")
    cutoff = bars[-1].date - timedelta(days=PERIOD_INFO[period]["days"])
    ctx.window = [b for b in bars if b.date >= cutoff]
    return ctx
