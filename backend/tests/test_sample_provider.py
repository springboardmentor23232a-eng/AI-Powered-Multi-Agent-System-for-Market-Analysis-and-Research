import pandas as pd
import pytest

from app.marketdata.providers.base import SymbolNotFound
from app.marketdata.providers.sample import SampleProvider

p = SampleProvider()


def span_days(df):
    d = pd.to_datetime(df["date"])
    return (d.max() - d.min()).days


@pytest.mark.parametrize("period,days", [("1M", 30), ("3M", 91), ("6M", 182), ("1Y", 365), ("5Y", 1826)])
def test_period_windows(period, days):
    assert 0 <= days - span_days(p.history("MSFT", period)) <= 4


def test_unknown_symbol_is_reported():
    with pytest.raises(SymbolNotFound):
        p.history("NOSUCH.NS", "1Y")


def test_every_market_is_covered():
    assert {s["market"] for s in p.symbols()} == {"NSE", "BSE", "NASDAQ", "NYSE"}


def test_profile_and_statements_exist_for_every_symbol():
    for s in p.symbols():
        prof, fin = p.profile(s["symbol"]), p.financials(s["symbol"])
        assert prof["name"] and prof["currency"] and prof["sector"]
        assert set(fin) == {"income_statement", "balance_sheet", "cash_flow"}


def test_statements_add_up():
    for s in p.symbols():
        fin = p.financials(s["symbol"])
        for fy, inc in fin["income_statement"].items():
            assert abs(inc["Total Revenue"] - inc["Cost Of Revenue"] - inc["Gross Profit"]) <= 2
            assert abs(inc["Gross Profit"] - inc["Operating Expense"] - inc["Operating Income"]) <= 2
        for bs in fin["balance_sheet"].values():
            assert abs(bs["Total Assets"] - bs["Total Liabilities"] - bs["Stockholders Equity"]) <= 2
        for cf in fin["cash_flow"].values():
            assert abs(cf["Operating Cash Flow"] + cf["Capital Expenditure"] - cf["Free Cash Flow"]) <= 2
