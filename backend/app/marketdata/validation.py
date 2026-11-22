"""Validation and cleaning of raw OHLCV data.

Checks run in this order, each on the rows that survived the previous one, so a
row is only ever counted under the first problem found in it:

1. invalid_dates       date cannot be read                      -> row removed
2. missing_prices      open, high, low or close is empty        -> row removed
3. duplicate_dates     same date appears more than once         -> last row kept
4. non_positive        a price <= 0 or a negative volume        -> row removed
5. inconsistent_ohlc   high below low, or open/close outside
                       the high-low range                       -> row removed
6. missing_volume      volume is empty                          -> filled with 0
"""
import pandas as pd

PRICE_COLS = ["open", "high", "low", "close"]
LABELS = {
    "invalid_dates": "Invalid dates",
    "missing_prices": "Missing price values",
    "duplicate_dates": "Duplicate dates",
    "non_positive": "Non-positive prices or negative volume",
    "inconsistent_ohlc": "Inconsistent OHLC values",
    "missing_volume": "Missing volume",
}


def _examples(dates) -> list[str]:
    return [d.strftime("%Y-%m-%d") for d in list(dates)[:5]]


def validate_and_clean(raw: pd.DataFrame):
    """Returns (clean_frame, report). The clean frame has one row per date, sorted."""
    df = raw.copy()
    rows_in = len(df)
    issues = []

    def record(check, mask, action, remove=True):
        count = int(mask.sum())
        if count:
            issues.append({"check": check, "label": LABELS[check], "count": count,
                           "action": action, "examples": _examples(df.loc[mask, "date"])})
        return df[~mask] if remove else df

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in PRICE_COLS + ["volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Invalid dates have no date to show as an example, so they are counted separately.
    bad_date = df["date"].isna()
    if bad_date.any():
        issues.append({"check": "invalid_dates", "label": LABELS["invalid_dates"], "count": int(bad_date.sum()),
                       "action": "Rows removed", "examples": []})
        df = df[~bad_date]
    df = df.reset_index(drop=True)

    df = record("missing_prices", df[PRICE_COLS].isna().any(axis=1), "Rows removed").reset_index(drop=True)
    df = record("duplicate_dates", df.duplicated("date", keep="last"), "Kept the last row for each date").reset_index(drop=True)
    bad = (df[PRICE_COLS] <= 0).any(axis=1) | (df["volume"] < 0)
    df = record("non_positive", bad, "Rows removed").reset_index(drop=True)
    top, bottom = df[["open", "close"]].max(axis=1), df[["open", "close"]].min(axis=1)
    bad = (df["high"] < df["low"]) | (df["high"] < top) | (df["low"] > bottom)
    df = record("inconsistent_ohlc", bad, "Rows removed").reset_index(drop=True)

    missing_vol = df["volume"].isna()
    record("missing_volume", missing_vol, "Filled with 0", remove=False)
    df["volume"] = df["volume"].fillna(0)

    df = df.sort_values("date", ignore_index=True)
    df["volume"] = df["volume"].astype("int64")
    df["date"] = df["date"].dt.date
    report = {"rows_in": rows_in, "rows_out": len(df), "issues": issues}
    return df, report
