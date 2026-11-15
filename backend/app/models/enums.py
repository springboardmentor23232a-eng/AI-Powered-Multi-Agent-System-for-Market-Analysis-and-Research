"""Fixed sets of allowed values shared by models, schemas and the frontend."""

from enum import StrEnum


class Market(StrEnum):
    NSE = "NSE"
    BSE = "BSE"
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"


class AnalysisPeriod(StrEnum):
    ONE_MONTH = "1M"
    THREE_MONTHS = "3M"
    SIX_MONTHS = "6M"
    ONE_YEAR = "1Y"
    TWO_YEARS = "2Y"
    FIVE_YEARS = "5Y"


class TaskStatus(StrEnum):
    """Lifecycle of a research task (used from Module 7 onwards)."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"  # finished, but some agents' analyses were unavailable
    FAILED = "failed"


class AgentStatus(StrEnum):
    """Outcome of one agent's work on a task (used from Module 3 onwards)."""

    SUCCESS = "success"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"  # e.g. no news found: recorded honestly, never invented


DEFAULT_MARKET = Market.NSE
DEFAULT_ANALYSIS_PERIOD = AnalysisPeriod.ONE_YEAR
