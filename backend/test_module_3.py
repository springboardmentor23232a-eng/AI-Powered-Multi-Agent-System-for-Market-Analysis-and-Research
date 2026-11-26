"""
Automated Verification Suite for Module 3:
Fundamental Analysis Agent, Financial Performance Analysis,
Ratios Calculation, Statement Trajectory, Peer Benchmarking & Audit Notices
"""

import sys
import os
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("\n" + "=" * 75)
print("MODULE 3 VERIFICATION SUITE: FUNDAMENTAL ANALYSIS AGENT & RATIOS ENGINE")
print("Features: Revenue/Earnings, Profitability, Debt/Stability, Ratios (P/E, P/B, ROE),")
print("          Historical Performance, Peer Benchmarking, Data Audit Notice")
print("=" * 75 + "\n")

# 1. Test Fundamental Analysis for Indian Equity (INFY.NS)
print("[TEST 1] Testing GET /api/stocks/INFY.NS/fundamental ...")
resp = client.get("/api/stocks/INFY.NS/fundamental")
assert resp.status_code == 200, f"Fundamental fetch failed: {resp.text}"
data = resp.json()

assert data["ticker"] == "INFY.NS"
assert data["currency"] in ["INR", "USD"]
assert "company_name" in data and len(data["company_name"]) > 0

# Check Company Profile
prof = data.get("company_profile", {})
assert "current_price" in prof and prof["current_price"] is not None
assert "fifty_two_week_high" in prof
assert "fifty_two_week_low" in prof
assert "market_cap_formatted" in prof
print(f"  --> [PASS] Company Profile: Price={prof.get('currency_symbol')}{prof.get('current_price')}, Market Cap={prof.get('market_cap_formatted')}, 52W Range={prof.get('fifty_two_week_low')} - {prof.get('fifty_two_week_high')}.\n")

# 2. Test Feature 1: Revenue and Earnings Analysis
print("[TEST 2] Verifying Feature 1: Revenue and Earnings Trajectory ...")
rev_earnings = data.get("revenue_earnings", {})
assert "yoy_growth_rate" in rev_earnings
chart = rev_earnings.get("multi_year_chart", [])
assert len(chart) >= 2, f"Multi-year chart items expected >= 2, got {len(chart)}"
for row in chart:
    assert "year" in row and "revenue" in row and "net_income" in row and "ebitda" in row
    assert "revenue_formatted" in row
print(f"  --> [PASS] Feature 1 Verified: YoY Growth={rev_earnings['yoy_growth_rate']}%, Multi-Year Statements Count={len(chart)} years.\n")

# 3. Test Feature 2: Profitability Analysis
print("[TEST 3] Verifying Feature 2: Profitability Margins (Operating, Net, ROE, ROA) ...")
profitability = data.get("profitability", {})
assert "operating_margin" in profitability and profitability["operating_margin"] is not None
assert "net_profit_margin" in profitability and profitability["net_profit_margin"] is not None
assert "roe" in profitability and profitability["roe"] is not None
assert "roa" in profitability and profitability["roa"] is not None
print(f"  --> [PASS] Feature 2 Verified: Operating Margin={profitability['operating_margin']}%, Net Margin={profitability['net_profit_margin']}%, ROE={profitability['roe']}%, ROA={profitability['roa']}%.\n")

# 4. Test Feature 3: Debt and Financial Stability Analysis
print("[TEST 4] Verifying Feature 3: Debt & Financial Stability (Debt/Equity, Current Ratio) ...")
debt_stability = data.get("debt_stability", {})
assert "debt_to_equity" in debt_stability and debt_stability["debt_to_equity"] is not None
assert "current_ratio" in debt_stability and debt_stability["current_ratio"] is not None
assert "solvency_assessment" in debt_stability and len(debt_stability["solvency_assessment"]) > 0
print(f"  --> [PASS] Feature 3 Verified: Debt-to-Equity={debt_stability['debt_to_equity']}, Current Ratio={debt_stability['current_ratio']}x ({debt_stability['solvency_assessment']}).\n")

# 5. Test Feature 4: Financial Ratios (P/E, P/B, EPS)
print("[TEST 5] Verifying Feature 4: Financial Ratios (P/E, P/B, EPS) ...")
valuation = data.get("valuation_ratios", {})
assert "pe_ratio" in valuation and valuation["pe_ratio"] is not None
assert "pb_ratio" in valuation and valuation["pb_ratio"] is not None
assert "eps" in valuation and valuation["eps"] is not None
print(f"  --> [PASS] Feature 4 Verified: P/E Ratio={valuation['pe_ratio']}x, P/B Ratio={valuation['pb_ratio']}x, EPS={valuation['eps']}.\n")

# 6. Test Feature 5: Historical Performance Comparison
print("[TEST 6] Verifying Feature 5: Historical Financial Statements Breakdown & YoY ...")
hist_comp = data.get("historical_comparison", [])
assert len(hist_comp) > 0, "Historical comparison records should be populated"
for h in hist_comp:
    assert "period" in h and "revenue_growth" in h and "status" in h
print(f"  --> [PASS] Feature 5 Verified: {len(hist_comp)} historical performance milestones tracked.\n")

# 7. Test Feature 6: Peer Comparison with Custom Peer & Narrative
print("[TEST 7] Verifying Feature 6: Peer Benchmarking (INFY.NS vs AAPL) ...")
resp_peer = client.get("/api/stocks/INFY.NS/fundamental?peer=AAPL")
assert resp_peer.status_code == 200, f"Peer comparison fetch failed: {resp_peer.text}"
data_peer = resp_peer.json()

peer_comp = data_peer.get("peer_comparison", {})
assert peer_comp.get("selected_peer") == "AAPL"
assert "narrative" in peer_comp and len(peer_comp["narrative"]) > 20
assert "comparison_table" in peer_comp and len(peer_comp["comparison_table"]) >= 5
assert "advantage_summary" in peer_comp
print(f"  --> [PASS] Feature 6 Verified: Selected Peer='{peer_comp['selected_peer']}', Table Rows={len(peer_comp['comparison_table'])}, Narrative Length={len(peer_comp['narrative'])} chars.\n")

# 8. Test Feature 7: Identification of Missing / Inconsistent Information
print("[TEST 8] Verifying Feature 7: Data Audit Notice & Missing Disclosures ...")
audit = data.get("missing_data_audit", {})
assert "notice" in audit and len(audit["notice"]) > 10
assert "missing_fields" in audit
print(f"  --> [PASS] Feature 7 Verified: Data Audit Notice: '{audit['notice'][:80]}...'.\n")

# 9. Test US Equity Fundamental Analysis (AAPL vs MSFT)
print("[TEST 9] Verifying Fundamental Analysis for US Equity (AAPL vs MSFT) ...")
resp_us = client.get("/api/stocks/AAPL/fundamental?peer=MSFT")
assert resp_us.status_code == 200, f"AAPL fundamental failed: {resp_us.text}"
data_us = resp_us.json()
assert data_us["currency"] == "USD"
assert data_us["peer_comparison"]["selected_peer"] == "MSFT"
print(f"  --> [PASS] US Equity Verified: Ticker='{data_us['ticker']}', Currency='{data_us['currency']}', Peer='{data_us['peer_comparison']['selected_peer']}'.\n")

print("=" * 75)
print("ALL MODULE 3 AUTOMATED INTEGRATION TESTS PASSED SUCCESSFULLY! (100%)")
print("=" * 75 + "\n")
