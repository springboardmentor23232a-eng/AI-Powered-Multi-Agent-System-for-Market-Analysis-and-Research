import numpy as np
import pandas as pd
from app.services.market_data import validate_ohlcv

IDX = pd.to_datetime(["2026-11-02", "2026-11-03", "2026-11-04",
                      "2026-11-05", "2026-11-06", "2026-11-09"])
TODAY = pd.Timestamp("2026-11-10")


def make_df():
    return pd.DataFrame({
        "Open": [100, 101, 102, 103, 104, 105.0],
        "High": [102, 103, 104, 105, 106, 107.0],
        "Low": [99, 100, 101, 102, 103, 104.0],
        "Close": [101, 102, 103, 104, 105, 106.0],
        "Volume": [1000] * 6,
    }, index=IDX)


def codes(rep):
    return {i["code"] for i in rep["issues"]}


def test_clean_data_has_no_errors():
    _, rep = validate_ohlcv(make_df(), "1mo", today=TODAY)
    assert rep["rows_clean"] == 6
    assert not [i for i in rep["issues"] if i["severity"] == "error"]


def test_duplicate_dates_removed():
    df = pd.concat([make_df(), make_df().iloc[[2]]])
    clean, rep = validate_ohlcv(df, "1mo", today=TODAY)
    assert len(clean) == 6 and "duplicate_dates" in codes(rep)


def test_missing_values_removed():
    df = make_df()
    df.loc[IDX[1], "Close"] = np.nan
    clean, rep = validate_ohlcv(df, "1mo", today=TODAY)
    assert len(clean) == 5 and "missing_values" in codes(rep)


def test_high_below_low_removed():
    df = make_df()
    df.loc[IDX[3], "High"] = 90
    clean, rep = validate_ohlcv(df, "1mo", today=TODAY)
    assert len(clean) == 5 and "high_below_low" in codes(rep)


def test_negative_price_removed():
    df = make_df()
    df.loc[IDX[2], "Open"] = -1
    clean, rep = validate_ohlcv(df, "1mo", today=TODAY)
    assert len(clean) == 5 and "non_positive_price" in codes(rep)