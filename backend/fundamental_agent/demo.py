"""Run:  python -m fundamental_agent.demo
Shows one good analysis and the error notices for bad input. Also acts as a self-test."""
import json

from .agent import FundamentalAnalysisAgent
from .errors import AnalysisError

agent = FundamentalAnalysisAgent()

# Apple, financial year 2022, in USD millions (from its 10-K)
APPLE = dict(revenue=394328, prev_revenue=365817, gross_profit=170782, net_income=99803, prev_net_income=94680,
             ebitda=130541, operating_cash_flow=122151, current_assets=135405, current_liabilities=153982,
             total_debt=120069, equity=50672, total_assets=352755)

# An illustrative struggling retailer
WEAK = dict(revenue=20000, prev_revenue=24000, gross_profit=4500, net_income=-1500, prev_net_income=-800,
            ebitda=-200, operating_cash_flow=-600, current_assets=5200, current_liabilities=5600,
            total_debt=4000, equity=-1200, total_assets=7000)


def run(title, raw, expect_codes=None, **kw):
    print("=" * 78)
    print(title)
    print("-" * 78)
    try:
        res = agent.analyze(raw, **kw)
        print(f"Classification: {res['classification']}  (confidence {res['confidence']:.0%}, "
              f"probabilities { {k: round(v, 2) for k, v in res['probabilities'].items()} })")
        for section, text in res["explanation"].items():
            print(f"  [{section}] {text}")
        assert expect_codes is None, f"expected an error {expect_codes} but the analysis succeeded"
        return res
    except AnalysisError as e:
        codes = [r.code for r in e.reasons]
        for r in e.reasons:
            print(f"  ERROR [{r.code}] ({r.field}): {r.message}")
        if expect_codes is not None:
            assert set(expect_codes) <= set(codes), f"expected {expect_codes}, got {codes}"
        else:
            raise


run("1. Apple FY2022 (valid input; note this year is also one of the training rows)", APPLE, company="Apple", currency="USD", amount_unit=1e6)
run("2. Struggling retailer (valid input)", WEAK, company="Illustrative retailer", currency="USD", amount_unit=1e6)

bad = {**APPLE, "net_income": None, "equity": float("nan")}
run("3. Missing values", bad, ["missing_value"])

run("4. Text instead of a number", {**APPLE, "revenue": "abc"}, ["invalid_value"])
run("5. Negative revenue", {**APPLE, "revenue": -5}, ["invalid_value"])
run("6. Gross profit larger than revenue", {**APPLE, "gross_profit": 500000}, ["inconsistent_data"])
run("7. Absurd growth (revenue x30)", {**APPLE, "prev_revenue": 13000}, ["outside_training_range"])

# every ratio inside its training range, but an unusual combination
S = agent.stats
def at(name, frac):  # frac 0..1 between the training min and max
    return S[name]["min"] + frac * (S[name]["max"] - S[name]["min"])
rev = 1000.0
fr = dict(gross_margin=0.95, net_margin=0.05, ebitda_margin=0.05, ocf_margin=0.95,
          current_ratio=0.95, debt_equity=0.05, roa=0.05, rev_growth=0.95)
ni = rev * at("net_margin", fr["net_margin"]) / 100
odd = dict(revenue=rev, prev_revenue=rev / (1 + at("rev_growth", fr["rev_growth"]) / 100),
           gross_profit=rev * at("gross_margin", fr["gross_margin"]) / 100, net_income=ni,
           ebitda=rev * at("ebitda_margin", fr["ebitda_margin"]) / 100,
           operating_cash_flow=rev * at("ocf_margin", fr["ocf_margin"]) / 100,
           current_liabilities=1000.0, current_assets=1000.0 * at("current_ratio", fr["current_ratio"]),
           total_debt=1000.0 * at("debt_equity", fr["debt_equity"]), equity=1000.0,
           total_assets=ni / (at("roa", fr["roa"]) / 100))
run("8. Every ratio is inside its training range, but the combination is unlike any company in training", odd, ["unlike_training_data"])

# ---- Yahoo-style input (what market_data.get_financials returns) ----
def stmt(rows, periods=("2024-12-31", "2023-12-31")):
    return {"available": True, "periods": list(periods),
            "rows": [{"item": k, "values": list(v)} for k, v in rows.items()]}

yahoo_ok = {
    "currency": "USD",
    "income_statement": stmt({"Total Revenue": (394328e6, 365817e6), "Gross Profit": (170782e6, 152836e6),
                              "Net Income": (99803e6, 94680e6), "EBITDA": (130541e6, 120233e6)}),
    "balance_sheet": stmt({"Current Assets": (135405e6, 143566e6), "Current Liabilities": (153982e6, 145308e6),
                           "Total Debt": (120069e6, 124719e6), "Stockholders Equity": (50672e6, 63090e6),
                           "Total Assets": (352755e6, 351002e6)}),
    "cash_flow": stmt({"Operating Cash Flow": (122151e6, 104038e6)}),
}
print("=" * 78)
print("9. Yahoo-style input (full units, as the app collects it)")
print("-" * 78)
res = agent.analyze_from_yahoo(yahoo_ok, company="Apple (Yahoo format)")
print(f"Classification: {res['classification']}  | {res['explanation']['revenue_growth']}")

bank = json.loads(json.dumps(yahoo_ok))
bank["income_statement"]["rows"] = [r for r in bank["income_statement"]["rows"] if r["item"] != "Gross Profit"]
bank["balance_sheet"]["rows"] = [r for r in bank["balance_sheet"]["rows"]
                                 if r["item"] not in ("Current Assets", "Current Liabilities")]
print("=" * 78)
print("10. Bank-like Yahoo data (no gross profit, no current assets or liabilities)")
print("-" * 78)
try:
    agent.analyze_from_yahoo(bank)
    raise SystemExit("expected an error")
except AnalysisError as e:
    for r in e.reasons:
        print(f"  ERROR [{r.code}] ({r.field}): {r.message}")
    assert {"not_reported"} <= {r.code for r in e.reasons}

no_cf = json.loads(json.dumps(yahoo_ok)); no_cf["cash_flow"] = {"available": False, "periods": [], "rows": []}
print("=" * 78)
print("11. Yahoo returned no cash flow statement")
print("-" * 78)
try:
    agent.analyze_from_yahoo(no_cf)
    raise SystemExit("expected an error")
except AnalysisError as e:
    for r in e.reasons:
        print(f"  ERROR [{r.code}] ({r.field}): {r.message}")
    assert e.reasons[0].code == "statement_unavailable"

print("=" * 78)
print("All checks behaved as expected.")
