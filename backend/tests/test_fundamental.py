import pandas as pd
import pytest

from app.agents import fundamental as fa
from app.services import market_data as md

D = ["2025-03-31", "2024-03-31", "2023-03-31"]


def tb(rows, cols=D):
    return {"columns": list(cols), "rows": [{"item": k, "values": v} for k, v in rows.items()]}


def make_statements(**over):
    inc = {"Total Revenue": [1100.0, 1000.0, 800.0], "Gross Profit": [440.0, 380.0, 280.0],
           "Operating Income": [220.0, 180.0, 120.0], "Net Income": [165.0, 130.0, 80.0],
           "Diluted EPS": [16.5, 13.0, 8.0], "Interest Expense": [-20.0, -20.0, -20.0]}
    bal = {"Total Assets": [2000.0, 1800.0, 1500.0], "Total Liabilities Net Minority Interest": [1000.0, 950.0, 800.0],
           "Total Equity Gross Minority Interest": [1000.0, 850.0, 700.0], "Stockholders Equity": [1000.0, 850.0, 700.0],
           "Total Debt": [400.0, 450.0, 400.0], "Cash And Cash Equivalents": [150.0, 100.0, 90.0],
           "Current Assets": [600.0, 500.0, 400.0], "Current Liabilities": [300.0, 280.0, 250.0]}
    cf = {"Operating Cash Flow": [250.0, 200.0, 150.0], "Capital Expenditure": [-100.0, -90.0, -80.0],
          "Free Cash Flow": [150.0, 110.0, 70.0]}
    for k, v in over.items():
        stmt, item = k.split("__")
        {"inc": inc, "bal": bal, "cf": cf}[stmt][item.replace("_", " ")] = v
    return {"income_statement": tb(inc), "balance_sheet": tb(bal), "cash_flow": tb(cf)}


PROFILE = {"company_name": "Test Co", "sector": "Industrials", "currency": "INR",
           "trailing_pe": None, "price_to_book": None, "return_on_equity": None, "market_cap": 20000.0}


def report(statements=None, profile=None, price=330.0):
    return fa.build_report("TEST.NS", "NSE", statements or make_statements(), profile or PROFILE, price,
                           "2025-06-01", today=pd.Timestamp("2025-06-01").date())


def test_growth_and_margins():
    h = report()["history"]
    assert h[0]["revenue_growth"] == pytest.approx(0.10)
    assert h[0]["net_income_growth"] == pytest.approx(0.2692, abs=1e-4)
    assert h[0]["net_margin"] == pytest.approx(0.15)
    assert h[0]["gross_margin"] == pytest.approx(0.40)
    assert h[0]["operating_margin"] == pytest.approx(0.20)
    assert h[-1]["revenue_growth"] is None          # oldest year has no previous year


def test_return_and_debt_ratios():
    y = report()["history"][0]
    assert y["roe"] == pytest.approx(0.165)
    assert y["roa"] == pytest.approx(0.0825)
    assert y["debt_to_equity"] == pytest.approx(0.4)
    assert y["current_ratio"] == pytest.approx(2.0)
    assert y["interest_coverage"] == pytest.approx(11.0)
    assert y["net_debt"] == pytest.approx(250.0)
    assert y["fcf_margin"] == pytest.approx(150 / 1100, abs=1e-4)


def test_cagr_over_history():
    t = report()["trend"]
    assert t["periods"] == 2
    assert t["revenue_cagr"] == pytest.approx((1100 / 800) ** 0.5 - 1, abs=1e-4)
    assert t["net_margin_change_pp"] == pytest.approx(5.0)
    assert t["revenue_up_years"] == {"up": 2, "of": 2}


def test_valuation_from_price():
    v = report()["valuation"]
    assert v["pe"] == pytest.approx(20.0)           # 330 / 16.5
    assert v["pb"] == pytest.approx(20.0)           # 20000 / 1000


def test_valuation_not_meaningful_for_loss_or_negative_equity():
    st = make_statements(inc__Diluted_EPS=[-2.0, 13.0, 8.0], bal__Stockholders_Equity=[-50.0, 850.0, 700.0])
    r = report(st)
    y = r["history"][0]
    assert r["valuation"]["pe"] is None and r["valuation"]["pb"] is None
    assert y["roe"] is None and y["debt_to_equity"] is None
    codes = {i["code"] for i in r["data_quality"]["issues"]}
    assert {"negative_equity", "loss_making"} <= codes


def test_growth_off_negative_base_is_none():
    st = make_statements(inc__Net_Income=[100.0, -50.0, 80.0])
    assert report(st)["history"][0]["net_income_growth"] is None


def test_inconsistent_data_is_flagged():
    st = make_statements(inc__Gross_Profit=[1500.0, 380.0, 280.0],
                         bal__Total_Liabilities_Net_Minority_Interest=[1500.0, 950.0, 800.0],
                         cf__Free_Cash_Flow=[900.0, 110.0, 70.0])
    q = report(st)["data_quality"]
    codes = {i["code"] for i in q["issues"]}
    assert {"gross_profit_above_revenue", "balance_sheet_mismatch", "fcf_mismatch"} <= codes
    assert q["confidence"] == "low" and q["is_reliable"] is False


def test_missing_items_are_reported():
    st = make_statements()
    st["balance_sheet"]["rows"] = [r for r in st["balance_sheet"]["rows"] if r["item"] != "Current Assets"]
    r = report(st)
    assert any(i["code"] == "missing_item" and "Current assets" in i["message"] for i in r["data_quality"]["issues"])
    assert r["history"][0]["current_ratio"] is None


def test_core_item_missing_makes_report_unreliable():
    st = make_statements()
    st["income_statement"]["rows"] = [r for r in st["income_statement"]["rows"] if r["item"] != "Net Income"]
    q = report(st)["data_quality"]
    assert q["is_reliable"] is False and q["confidence"] == "low"


def test_provider_mismatch_flagged_but_close_values_are_not():
    far = dict(PROFILE, trailing_pe=40.0, price_to_book=20.5, return_on_equity=0.165)
    msgs = [i["message"] for i in report(profile=far)["data_quality"]["issues"] if i["code"] == "provider_mismatch"]
    assert len(msgs) == 1 and msgs[0].startswith("P/E")


def test_stale_and_short_history():
    r = fa.build_report("T", "NSE", make_statements(), PROFILE, 330.0, today=pd.Timestamp("2027-01-01").date())
    assert "stale_statements" in {i["code"] for i in r["data_quality"]["issues"]}
    one = {k: tb({r_["item"]: r_["values"][:1] for r_ in v["rows"]}, D[:1]) for k, v in make_statements().items()}
    assert "short_history" in {i["code"] for i in report(one)["data_quality"]["issues"]}


def test_period_gap_skips_growth():
    st = make_statements()
    for t in st.values():
        t["columns"] = ["2025-03-31", "2023-03-31", "2022-03-31"]
    r = report(st)
    assert r["history"][0]["revenue_growth"] is None
    assert "period_gap" in {i["code"] for i in r["data_quality"]["issues"]}


def test_assessment_ratings():
    s = report()["assessment"]["sections"]
    assert s["revenue_earnings"]["rating"] == "positive"
    assert s["profitability"]["rating"] == "positive"
    assert s["financial_stability"]["rating"] == "positive"
    assert s["valuation"]["rating"] == "neutral"
    weak = make_statements(inc__Total_Revenue=[900.0, 1000.0, 800.0], inc__Net_Income=[10.0, 130.0, 80.0])
    w = report(weak)["assessment"]["sections"]
    assert w["revenue_earnings"]["rating"] == "negative" and w["profitability"]["rating"] == "negative"


def test_financial_sector_skips_debt_rating():
    r = report(profile=dict(PROFILE, sector="Financial Services"))
    assert r["assessment"]["sections"]["financial_stability"]["rating"] == "unknown"


def test_no_usable_statements_raises():
    with pytest.raises(md.DataUnavailable):
        fa.build_report("X", "NSE", {"income_statement": {"columns": [], "rows": []}}, {}, None)


def test_peer_comparison_median_and_position():
    me = fa.snapshot(report())
    mk = lambda t, nm, pe: dict(me, ticker=t, net_margin=nm, pe=pe)
    out = fa.compare_peers(me, [mk("A", 0.05, 10.0), mk("B", 0.25, 30.0), mk("C", 0.10, None)], [])
    m = {x["key"]: x for x in out["metrics"]}
    assert m["net_margin"]["peer_median"] == pytest.approx(0.10) and m["net_margin"]["position"] == "above"
    assert m["pe"]["peer_median"] == pytest.approx(20.0) and m["pe"]["peers_with_data"] == 2
    assert fa.compare_peers(me, [], [{"ticker": "Z", "reason": "x"}])["available"] is False


def test_analyze_survives_failing_peer(monkeypatch):
    def fake_report(ticker, market):
        if ticker == "BAD.NS":
            raise md.DataUnavailable("No financial statements found for 'BAD.NS'.")
        return fa.build_report(ticker, market, make_statements(), dict(PROFILE, company_name=ticker), 330.0, "2025-06-01")
    monkeypatch.setattr(fa, "_report_for", fake_report)
    r = fa.analyze("TEST.NS", "NSE", ["PEER.NS", "BAD.NS", "TEST.NS", "PEER.NS"])
    assert r["peers"]["available"] is True and len(r["peers"]["companies"]) == 2
    assert r["peers"]["unavailable"][0]["ticker"] == "BAD.NS"
    assert fa.analyze("TEST.NS", "NSE")["peers"]["available"] is False


def test_provider_names_without_spaces_still_match():
    """Newer yfinance returns 'TotalRevenue' / 'DilutedEPS' instead of 'Total Revenue' / 'Diluted EPS'."""
    camel = {k: {"columns": v["columns"],
                 "rows": [{"item": r["item"].replace(" ", ""), "values": r["values"]} for r in v["rows"]]}
             for k, v in make_statements().items()}
    a, b = report(camel), report()
    assert a["history"][0]["revenue"] == 1100.0 and a["history"][0]["eps"] == 16.5
    assert a["history"][0]["roe"] == b["history"][0]["roe"]
    assert a["valuation"]["pe"] == b["valuation"]["pe"]
    assert a["data_quality"]["counts"] == b["data_quality"]["counts"]
