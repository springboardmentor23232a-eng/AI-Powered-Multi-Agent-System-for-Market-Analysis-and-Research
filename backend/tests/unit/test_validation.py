from datetime import date

import pandas as pd

from app.services.validation import validate_financials, validate_ohlcv
from tests.fakes import make_ohlcv


def codes(report):
    return {i.code for i in report.issues}


def test_clean_data_passes():
    df, rep = validate_ohlcv(make_ohlcv(), reference_date=date(2026, 11, 2))
    assert rep.is_usable and rep.rows_out == 120 and not rep.issues


def test_duplicates_nulls_and_inconsistent_rows_are_dropped_and_reported():
    base = make_ohlcv(60)
    dup = pd.concat([base, base.iloc[[10]]])
    dup.loc[dup.index[5], "close"] = None
    dup.loc[dup.index[7], ["high", "low"]] = [90.0, 95.0]          # high < low
    dup.loc[dup.index[9], "open"] = -1.0                              # non-positive
    df, rep = validate_ohlcv(dup)
    assert {"duplicate_dates", "null_prices", "high_below_low", "non_positive_values"} <= codes(rep)
    assert df["date"].is_unique and rep.rows_out < rep.rows_in
    assert (df["high"] >= df["low"]).all()


def test_too_few_rows_is_unusable():
    _, rep = validate_ohlcv(make_ohlcv(10))
    assert not rep.is_usable and "insufficient_history" in codes(rep)


def test_missing_columns_is_unusable():
    _, rep = validate_ohlcv(make_ohlcv().drop(columns=["volume"]))
    assert not rep.is_usable and "missing_columns" in codes(rep)


def test_stale_gap_and_extreme_move_flags():
    df = make_ohlcv(60, end="2026-09-01")
    df.loc[30:, ["open", "high", "low", "close"]] *= 2   # 100% jump
    df.loc[40:, "date"] = df.loc[40:, "date"] + pd.Timedelta(days=30)  # gap
    _, rep = validate_ohlcv(df, reference_date=date(2026, 11, 2))
    assert {"stale_data", "extreme_move", "date_gap"} <= codes(rep)


def test_financial_issues():
    iss = validate_financials({"annual": [{"year": 2025, "revenue": 1, "net_income": 1, "total_equity": -5}]})
    assert {"missing_total_debt", "non_positive_equity"} <= {i.code for i in iss}
    assert validate_financials({"annual": []})[0].code == "no_financials"
