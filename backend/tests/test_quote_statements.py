import numpy as np
import pandas as pd
from app.services.market_data import HistoryResult, _table, build_quote


def make_history(n=300):
    idx = pd.bdate_range("2025-09-01", periods=n)
    close = pd.Series(np.linspace(100, 160, n), index=idx)
    df = pd.DataFrame({"Open": close - 1, "High": close + 2, "Low": close - 2,
                       "Close": close, "Volume": 1000}, index=idx)
    return HistoryResult(df, {"provider": "test"}, {"issues": []})


def test_build_quote_numbers():
    h = make_history()
    q = build_quote("AAPL", "NASDAQ", h, {"company_name": "Apple", "currency": "USD", "trailing_pe": 30.0})
    last, prev = float(h.df["Close"].iloc[-1]), float(h.df["Close"].iloc[-2])
    assert q["price"] == round(last, 4)
    assert q["change_pct"] == round((last / prev - 1) * 100, 2)
    assert q["day_high"] == round(last + 2, 4)
    assert q["week52_low"] == round(float(h.df["Low"].tail(252).min()), 4)
    assert len(q["spark"]) == 30
    assert q["pe_ratio"] == 30.0 and q["company_name"] == "Apple"


def test_build_quote_without_profile():
    q = build_quote("TCS.NS", "NSE", make_history(), None)
    assert q["company_name"] is None and q["pe_ratio"] is None


def test_table_sorts_newest_first_and_drops_empty_rows():
    cols = pd.to_datetime(["2023-09-30", "2025-09-30", "2024-09-30"])
    df = pd.DataFrame(
        {cols[0]: [10.0, np.nan], cols[1]: [30.0, np.nan], cols[2]: [20.0, np.nan]},
        index=["Total Revenue", "Empty Row"],
    )
    t = _table(df)
    assert t["columns"] == ["2025-09-30", "2024-09-30", "2023-09-30"]
    assert t["rows"] == [{"item": "Total Revenue", "values": [30.0, 20.0, 10.0]}]


def test_table_handles_missing_dataframe():
    assert _table(None) == {"columns": [], "rows": []}
    assert _table(pd.DataFrame()) == {"columns": [], "rows": []}
