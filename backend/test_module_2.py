"""
Automated Verification Suite for Module 2:
Market Analytics, Historical OHLCV, Time Series Analysis (TSA),
Data Quality Validation, Company Profile & Financial Statements
"""

import sys
import os
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("\n" + "=" * 75)
print("MODULE 2 VERIFICATION SUITE: FINANCIAL ANALYTICS & TIME SERIES ENGINE")
print("Data Source: yfinance API | Ingesting OHLCV, TSA, Histograms & Market Feeds")
print("=" * 75 + "\n")

# 1. Test Historical OHLCV & TSA for Indian Stock (INFY.NS)
print("[TEST 1] Testing GET /api/stocks/INFY.NS/historical?period=1y ...")
resp = client.get("/api/stocks/INFY.NS/historical?period=1y")
assert resp.status_code == 200, f"Historical fetch failed: {resp.text}"
data = resp.json()

assert data["ticker"] == "INFY.NS"
assert data["currency"] == "INR"
assert data["currency_symbol"] == "₹"
assert data["is_us_market"] is False
assert data["data_source"] == "yfinance API"

# Verify timestamp format contains hours, minutes, and seconds
ts = data["retrieved_at"]
assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", ts), f"Timestamp '{ts}' missing HH:mm:ss"
print(f"  --> [PASS] OHLCV retrieved. Data Source: '{data['data_source']}', Timestamp: '{ts}'.\n")

# 2. Test Time Series Analysis (TSA) & Frequency Histogram
print("[TEST 2] Verifying Time Series Analysis (SMA 20, SMA 50, Volatility, Trend, Histogram) ...")
tsa = data["time_series_analysis"]
assert tsa["sma_20"] is not None and tsa["sma_20"] > 0
assert tsa["sma_50"] is not None and tsa["sma_50"] > 0
assert tsa["volatility_annualized_percent"] >= 0
assert tsa["trend"] in ["Bullish", "Bearish", "Consolidation"]
assert len(tsa["histogram"]) > 0
print(f"  --> [PASS] TSA Verified: SMA20=₹{tsa['sma_20']}, SMA50=₹{tsa['sma_50']}, Volatility={tsa['volatility_annualized_percent']}%, Trend={tsa['trend']}.")
print(f"  --> [PASS] Histogram: Generated {len(tsa['histogram'])} return frequency bins.\n")

# 3. Test US Market Equity (AAPL)
print("[TEST 3] Testing GET /api/stocks/AAPL/historical?period=6mo (US Stock) ...")
resp_us = client.get("/api/stocks/AAPL/historical?period=6mo")
assert resp_us.status_code == 200, f"AAPL fetch failed: {resp_us.text}"
data_us = resp_us.json()
assert data_us["currency"] == "USD"
assert data_us["currency_symbol"] == "$"
assert data_us["is_us_market"] is True
assert data_us["data_source"] == "yfinance API"
print(f"  --> [PASS] US Market Support Verified: AAPL on {data_us['exchange']} with USD ($) currency.\n")

# 4. Test Company Profile
print("[TEST 4] Testing GET /api/stocks/INFY.NS/profile ...")
resp_prof = client.get("/api/stocks/INFY.NS/profile")
assert resp_prof.status_code == 200, f"Profile fetch failed: {resp_prof.text}"
prof = resp_prof.json()
assert prof["ticker"] == "INFY.NS"
assert prof["data_source"] == "yfinance API"
assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", prof["retrieved_at"])
assert prof["sector"] is not None
assert prof["summary"] is not None
print(f"  --> [PASS] Profile: Sector='{prof['sector']}', Industry='{prof['industry']}', Market Cap={prof['market_cap_formatted']}.\n")

# 5. Test Financial Statements
print("[TEST 5] Testing GET /api/stocks/INFY.NS/financials ...")
resp_fin = client.get("/api/stocks/INFY.NS/financials")
assert resp_fin.status_code == 200, f"Financials fetch failed: {resp_fin.text}"
fin = resp_fin.json()
assert fin["ticker"] == "INFY.NS"
assert fin["data_source"] == "yfinance API"
assert len(fin["income_statement"]) > 0
assert len(fin["balance_sheet"]) > 0
assert len(fin["cash_flow"]) > 0
print(f"  --> [PASS] Financials: Income Statement ({len(fin['income_statement'])} items), Balance Sheet ({len(fin['balance_sheet'])} items), Cash Flow ({len(fin['cash_flow'])} items).\n")

# 6. Test Structured Multi-Tier Research Report Generation (Section 8 of Document)
print("[TEST 6] Testing Structured Multi-Tier Research Report Generation ...")
from app.routes.dashboard_routes import generate_synthesis_report

cname, summary, content, limitations = generate_synthesis_report(
    ticker="INFY.NS",
    market="NSE",
    requested_period="6 Months"
)

assert "Company Overview" in content, "Missing Section 1: Company Overview"
assert "Fundamental Analysis" in content, "Missing Section 2: Fundamental Analysis"
assert "Technical Analysis" in content, "Missing Section 3: Technical Analysis"
assert "News and Sentiment Summary" in content, "Missing Section 4: News & Sentiment"
assert "Risk Assessment" in content, "Missing Section 5: Risk Assessment"
assert "Conflicting Findings" in content, "Missing Section 6: Conflicting Findings"
assert "Supporting Source Links and Timestamps" in content, "Missing Section 7: Source Links & Timestamps"
assert "Data Limitations and Uncertainty" in content, "Missing Section 8: Data Limitations"

# Structure validation
assert "yfinance" in content, "Report missing yfinance data source provider"
assert "Coming Soon" in content, "Report missing scheduled agent notices"
print(f"  --> [PASS] 8 Research Report Sections Verified with Real yfinance Data & Scheduled Agents.\n")

print("=" * 75)
print("ALL MODULE 2 AUTOMATED INTEGRATION TESTS PASSED SUCCESSFULLY! (100%)")
print("=" * 75 + "\n")
