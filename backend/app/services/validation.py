from datetime import date

import pandas as pd
from pydantic import BaseModel

REQUIRED = ["date", "open", "high", "low", "close", "volume"]
MIN_ROWS = 30


class Issue(BaseModel):
    code: str
    severity: str  # warning | error
    message: str
    count: int = 1


class ValidationReport(BaseModel):
    rows_in: int
    rows_out: int
    issues: list[Issue]
    is_usable: bool


def validate_ohlcv(
    df: pd.DataFrame,
    reference_date: date | None = None,
    max_stale_days: int = 5,
    max_gap_days: int = 10,
    max_daily_move: float = 0.4,
) -> tuple[pd.DataFrame, ValidationReport]:
    """Clean OHLCV data and report every problem found. Never silently repairs."""
    issues: list[Issue] = []
    rows_in = len(df)

    def add(code, severity, message, count=1):
        issues.append(Issue(code=code, severity=severity, message=message, count=count))

    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        add("missing_columns", "error", f"Missing columns: {missing}")
        return pd.DataFrame(columns=REQUIRED), ValidationReport(
            rows_in=rows_in, rows_out=0, issues=issues, is_usable=False
        )

    d = df[REQUIRED].copy()
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    for c in REQUIRED[1:]:
        d[c] = pd.to_numeric(d[c], errors="coerce")

    n = int(d["date"].isna().sum())
    if n:
        add("invalid_date", "warning", "Rows with unparseable dates dropped", n)
        d = d.dropna(subset=["date"])

    n = int(d.duplicated(subset="date", keep="last").sum())
    if n:
        add("duplicate_dates", "warning", "Duplicate dates dropped (kept last)", n)
        d = d.drop_duplicates(subset="date", keep="last")

    n = int(d[["open", "high", "low", "close"]].isna().any(axis=1).sum())
    if n:
        add("null_prices", "warning", "Rows with null OHLC dropped", n)
        d = d.dropna(subset=["open", "high", "low", "close"])

    n = int(d["volume"].isna().sum())
    if n:
        add("null_volume", "warning", "Null volume set to 0", n)
        d["volume"] = d["volume"].fillna(0)

    bad = (d[["open", "high", "low", "close"]] <= 0).any(axis=1) | (d["volume"] < 0)
    if bad.any():
        add("non_positive_values", "warning", "Rows with non-positive price or negative volume dropped", int(bad.sum()))
        d = d[~bad]

    bad = d["high"] < d["low"]
    if bad.any():
        add("high_below_low", "warning", "Rows where high < low dropped", int(bad.sum()))
        d = d[~bad]

    bad = (
        (d["close"] > d["high"]) | (d["close"] < d["low"]) | (d["open"] > d["high"]) | (d["open"] < d["low"])
    )
    if bad.any():
        add("price_outside_range", "warning", "Rows where open/close fall outside high-low dropped", int(bad.sum()))
        d = d[~bad]

    d = d.sort_values("date").reset_index(drop=True)

    if len(d) > 1:
        moves = d["close"].pct_change().abs()
        n = int((moves > max_daily_move).sum())
        if n:
            add("extreme_move", "warning", f"Daily close moves above {max_daily_move:.0%} (possible split/bonus)", n)
        gaps = d["date"].diff().dt.days
        n = int((gaps > max_gap_days).sum())
        if n:
            add("date_gap", "warning", f"Gaps longer than {max_gap_days} calendar days", n)

    if len(d) == 0 or len(d) < MIN_ROWS:
        add("insufficient_history", "error", f"{len(d)} usable rows; at least {MIN_ROWS} required")
    elif reference_date is not None:
        age = (reference_date - d["date"].iloc[-1].date()).days
        if age > max_stale_days:
            add("stale_data", "warning", f"Latest price is {age} days old")

    usable = not any(i.severity == "error" for i in issues)
    return d, ValidationReport(rows_in=rows_in, rows_out=len(d), issues=issues, is_usable=usable)


def validate_financials(payload: dict) -> list[Issue]:
    """Flag missing or inconsistent financial statement fields."""
    issues: list[Issue] = []
    annual = payload.get("annual") or []
    if not annual:
        return [Issue(code="no_financials", severity="error", message="No annual financial statements available")]
    for field in ("revenue", "net_income", "operating_income", "total_debt", "total_equity"):
        n = sum(1 for y in annual if y.get(field) is None)
        if n:
            issues.append(Issue(code=f"missing_{field}", severity="warning",
                                message=f"{field} unavailable for {n} of {len(annual)} years", count=n))
    n = sum(1 for y in annual if (y.get("total_equity") is not None and y["total_equity"] <= 0))
    if n:
        issues.append(Issue(code="non_positive_equity", severity="warning",
                            message="Non-positive equity makes ROE and P/B unreliable", count=n))
    return issues
