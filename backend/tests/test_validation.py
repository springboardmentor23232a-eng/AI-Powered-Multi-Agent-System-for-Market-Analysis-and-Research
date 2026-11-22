import json

import pandas as pd
import pytest

from app.marketdata.providers.sample import DATA_DIR, SampleProvider
from app.marketdata.validation import validate_and_clean

MANIFEST = json.loads((DATA_DIR / "defects.json").read_text())
provider = SampleProvider()


def frame(rows):
    return pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume"])


def counts(report):
    return {i["check"]: i["count"] for i in report["issues"]}


GOOD = [("2026-01-05", 10, 12, 9, 11, 100), ("2026-01-06", 11, 13, 10, 12, 120), ("2026-01-07", 12, 14, 11, 13, 90)]


def test_clean_data_passes_unchanged():
    clean, report = validate_and_clean(frame(GOOD))
    assert len(clean) == 3 and report["issues"] == []


def test_missing_prices_are_removed():
    rows = GOOD + [("2026-01-08", 12, 14, 11, None, 90), ("2026-01-09", None, 14, 11, 13, 90)]
    clean, report = validate_and_clean(frame(rows))
    assert len(clean) == 3 and counts(report) == {"missing_prices": 2}


def test_duplicate_dates_keep_the_last_row():
    rows = GOOD + [("2026-01-06", 11, 13, 10, 12.5, 130)]
    clean, report = validate_and_clean(frame(rows))
    assert len(clean) == 3 and counts(report) == {"duplicate_dates": 1}
    assert clean.loc[clean["date"].astype(str) == "2026-01-06", "close"].item() == 12.5


def test_inconsistent_ohlc_is_removed():
    rows = GOOD + [("2026-01-08", 12, 9, 11, 10, 90), ("2026-01-09", 12, 14, 11, 15, 90)]  # high<low, close>high
    clean, report = validate_and_clean(frame(rows))
    assert len(clean) == 3 and counts(report) == {"inconsistent_ohlc": 2}


def test_non_positive_values_are_removed():
    rows = GOOD + [("2026-01-08", 12, 14, 11, 0, 90), ("2026-01-09", 12, 14, 11, 13, -5)]
    clean, report = validate_and_clean(frame(rows))
    assert len(clean) == 3 and counts(report) == {"non_positive": 2}


def test_missing_volume_is_filled_with_zero():
    rows = GOOD + [("2026-01-08", 12, 14, 11, 13, None)]
    clean, report = validate_and_clean(frame(rows))
    assert len(clean) == 4 and counts(report) == {"missing_volume": 1}
    assert clean["volume"].iloc[-1] == 0


def test_invalid_dates_are_removed():
    clean, report = validate_and_clean(frame(GOOD + [("not a date", 12, 14, 11, 13, 90)]))
    assert len(clean) == 3 and counts(report) == {"invalid_dates": 1}


def test_output_is_sorted_with_one_row_per_date():
    clean, _ = validate_and_clean(frame(list(reversed(GOOD))))
    assert list(clean["date"]) == sorted(clean["date"]) and clean["date"].is_unique


@pytest.mark.parametrize("symbol", sorted(MANIFEST))
def test_model_dataset_defects_are_found_exactly(symbol):
    raw = provider.history(symbol, "5Y")
    clean, report = validate_and_clean(raw)
    assert counts(report) == MANIFEST[symbol]
    removed = sum(i["count"] for i in report["issues"] if i["check"] != "missing_volume")
    assert report["rows_in"] - report["rows_out"] == removed


@pytest.mark.parametrize("symbol", [s["symbol"] for s in provider.symbols() if s["symbol"] not in MANIFEST])
def test_model_dataset_clean_symbols_have_no_issues(symbol):
    _, report = validate_and_clean(provider.history(symbol, "5Y"))
    assert report["issues"] == []


@pytest.mark.parametrize("symbol", [s["symbol"] for s in provider.symbols()])
def test_cleaned_output_is_internally_consistent(symbol):
    clean, _ = validate_and_clean(provider.history(symbol, "5Y"))
    assert clean["date"].is_unique and clean["date"].is_monotonic_increasing
    assert (clean[["open", "high", "low", "close"]] > 0).all().all()
    assert (clean["high"] >= clean[["open", "close", "low"]].max(axis=1)).all()
    assert (clean["low"] <= clean[["open", "close", "high"]].min(axis=1)).all()
    assert clean.notna().all().all()
