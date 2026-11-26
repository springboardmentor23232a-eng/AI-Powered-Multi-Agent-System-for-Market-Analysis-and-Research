"""OHLCV data validation (Milestone 1: "validate missing values, duplicate dates and inconsistent data").

`validate_ohlcv` never invents data. It returns the rows that are safe to use plus a report that says exactly
what was found and what was done about it, so the dashboard and later agents can show data-quality limits.

Policy
  missing O/H/L/C value      -> row removed
  duplicate date             -> first-seen order kept, LAST occurrence wins (providers re-issue corrected bars)
  inconsistent prices        -> row removed (High < Low, Open/Close outside [Low, High], price <= 0)
  negative volume            -> row removed;  missing volume -> row kept, volume = None (flagged)
  out-of-order dates         -> sorted ascending (flagged)
  daily close move > 40 %    -> kept but flagged (could be a split / bad tick; never silently "fixed")
"""
import math
from dataclasses import dataclass
from datetime import date

MIN_USABLE_ROWS = 5
EXTREME_MOVE_PCT = 40.0
_SAMPLE = 5  # how many example dates to list per issue


@dataclass(frozen=True)
class Bar:
    date: date
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    volume: float | None


def _missing(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v))


def _issue(kind: str, severity: str, dates: list[date], action: str, message: str) -> dict:
    return {
        "type": kind, "severity": severity, "count": len(dates), "action": action, "message": message,
        "example_dates": [d.isoformat() for d in sorted(dates)[:_SAMPLE]],
    }


def validate_ohlcv(raw: list[Bar]) -> tuple[list[Bar], dict]:
    issues: list[dict] = []
    received = len(raw)

    # 1. duplicate dates (last occurrence wins)
    seen: dict[date, Bar] = {}
    dup_dates: list[date] = []
    for b in raw:
        if b.date in seen:
            dup_dates.append(b.date)
        seen[b.date] = b
    if dup_dates:
        issues.append(_issue("duplicate_dates", "warning", dup_dates, "kept last occurrence of each date",
                             f"{len(dup_dates)} duplicate date(s) found."))
    deduped = list(seen.values())

    # 2. order
    if any(a.date > b.date for a, b in zip(deduped, deduped[1:])):
        issues.append(_issue("out_of_order", "info", [], "sorted ascending by date",
                             "Rows were not in chronological order."))
        deduped.sort(key=lambda b: b.date)

    # 3. row-level checks
    clean: list[Bar] = []
    missing_dates, inconsistent_dates, neg_vol_dates, missing_vol_dates = [], [], [], []
    for b in deduped:
        if any(_missing(v) for v in (b.open, b.high, b.low, b.close)):
            missing_dates.append(b.date)
            continue
        if min(b.open, b.high, b.low, b.close) <= 0 or b.high < b.low or not (b.low <= b.open <= b.high) \
                or not (b.low <= b.close <= b.high):
            inconsistent_dates.append(b.date)
            continue
        if not _missing(b.volume) and b.volume < 0:
            neg_vol_dates.append(b.date)
            continue
        if _missing(b.volume):
            missing_vol_dates.append(b.date)
            b = Bar(b.date, b.open, b.high, b.low, b.close, None)
        clean.append(b)
    if missing_dates:
        issues.append(_issue("missing_values", "warning", missing_dates, "rows removed",
                             f"{len(missing_dates)} row(s) had a missing Open/High/Low/Close value."))
    if inconsistent_dates:
        issues.append(_issue("inconsistent_prices", "warning", inconsistent_dates, "rows removed",
                             f"{len(inconsistent_dates)} row(s) had impossible prices "
                             "(High below Low, Open/Close outside the day's range, or a price <= 0)."))
    if neg_vol_dates:
        issues.append(_issue("negative_volume", "warning", neg_vol_dates, "rows removed",
                             f"{len(neg_vol_dates)} row(s) had negative volume."))
    if missing_vol_dates:
        issues.append(_issue("missing_volume", "info", missing_vol_dates, "kept; volume left empty",
                             f"{len(missing_vol_dates)} row(s) had no volume figure."))

    # 4. suspicious jumps (flag only)
    jumps = [b.date for a, b in zip(clean, clean[1:]) if abs(b.close / a.close - 1) * 100 > EXTREME_MOVE_PCT]
    if jumps:
        issues.append(_issue("extreme_price_move", "warning", jumps, "kept; please verify",
                             f"{len(jumps)} day(s) with a close-to-close move above {EXTREME_MOVE_PCT:.0f}% "
                             "(could be a stock split, corporate action or a bad data point)."))

    usable = len(clean) >= MIN_USABLE_ROWS
    if not usable:
        issues.append(_issue("insufficient_data", "error", [], "analysis blocked",
                             f"Only {len(clean)} valid row(s) remain; at least {MIN_USABLE_ROWS} are needed."))
    report = {
        "rows_received": received, "rows_valid": len(clean), "rows_removed": received - len(clean),
        "is_clean": not any(i["severity"] != "info" for i in issues),
        "usable": usable,
        "first_date": clean[0].date.isoformat() if clean else None,
        "last_date": clean[-1].date.isoformat() if clean else None,
        "issues": issues,
    }
    return clean, report
