from unittest.mock import patch
import pytest

from app.services.agents.fundamental_agent import FundamentalAnalysisAgent
from app.services.financial_calculations import (
    compute_cagr_pct,
    compute_growth_pct,
    compute_margin_pct,
    compute_pb_ratio,
    compute_pe_ratio,
    compute_roa_pct,
    compute_roe_pct,
    compute_stability_metrics,
)


def _get_auth_headers(client, email="fund_user@example.com"):
    client.post("/api/auth/register", json={
        "full_name": "Fundamental Tester",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!",
    })
    res = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_independent_reference_financial_ratios():
    # P/E reference: price=200, eps=8 -> 25.0
    pe = compute_pe_ratio(current_price=200.0, diluted_eps=8.0)
    assert pe["value"] == 25.0
    assert pe["status"] == "COMPUTED"

    # Negative EPS -> unavailable
    pe_neg = compute_pe_ratio(current_price=200.0, diluted_eps=-2.5)
    assert pe_neg["value"] is None
    assert pe_neg["status"] == "UNAVAILABLE"

    # P/B reference: market_cap=1_000_000, equity=250_000 -> 4.0
    pb = compute_pb_ratio(market_cap=1_000_000.0, stockholders_equity=250_000.0)
    assert pb["value"] == 4.0
    assert pb["status"] == "COMPUTED"

    # Negative equity -> unavailable
    pb_neg = compute_pb_ratio(market_cap=1_000_000.0, stockholders_equity=-10_000.0)
    assert pb_neg["value"] is None
    assert pb_neg["status"] == "UNAVAILABLE"

    # ROE reference: net_income=50_000, equity=250_000 -> 20.0%
    roe = compute_roe_pct(net_income=50_000.0, stockholders_equity=250_000.0)
    assert roe["value"] == 20.0
    assert roe["status"] == "COMPUTED"

    # ROA, margins, growth, CAGR
    assert compute_roa_pct(50_000.0, 500_000.0) == 10.0
    assert compute_margin_pct(150.0, 500.0) == 30.0
    assert compute_growth_pct(120.0, 100.0) == 20.0
    # CAGR from 100 to 121 over 2 years -> 10.0%
    assert compute_cagr_pct(121.0, 100.0, 2) == 10.0

    # Stability metrics
    stab = compute_stability_metrics(
        total_debt=100.0,
        cash_and_equivalents=40.0,
        stockholders_equity=200.0,
        current_assets=150.0,
        current_liabilities=75.0,
        inventory=30.0,
        operating_income=60.0,
        interest_expense=10.0,
        operating_cash_flow=80.0,
        capex=-20.0,
    )
    assert stab["net_debt"] == 60.0
    assert stab["debt_to_equity"] == 0.5
    assert stab["current_ratio"] == 2.0
    assert stab["quick_ratio"] == 1.6
    assert stab["interest_coverage"] == 6.0
    assert stab["free_cash_flow"] == 60.0


@pytest.mark.asyncio
async def test_fundamental_agent_full_analysis_and_data_gaps():
    synthetic_market_data = {
        "profile": {
            "ticker": "TESTCO",
            "company_name": "Test Corp",
            "market": "NASDAQ",
            "currency": "USD",
            "sector": "Technology",
            "current_price": 150.0,
            "market_cap": 1_500_000_000.0,
        },
        "raw_info": {},
        "financial_statements": {
            "income_statement": {
                "statement_type": "Income Statement",
                "currency": "USD",
                "periods": ["2025-12-31", "2024-12-31", "2023-12-31"],
                "rows": {
                    "Total Revenue": [1_210_000_000.0, 1_100_000_000.0, 1_000_000_000.0],
                    "Gross Profit": [605_000_000.0, 528_000_000.0, 470_000_000.0],
                    "Operating Income": [242_000_000.0, 200_000_000.0, 180_000_000.0],
                    "Net Income": [181_500_000.0, 150_000_000.0, 130_000_000.0],
                    "Diluted EPS": [5.0, 4.1, 3.5],
                },
            },
            "balance_sheet": {
                "statement_type": "Balance Sheet",
                "currency": "USD",
                "periods": ["2025-12-31", "2024-12-31"],
                "rows": {
                    "Total Debt": [250_000_000.0, 260_000_000.0],
                    "Cash And Cash Equivalents": [300_000_000.0, 220_000_000.0],
                    "Stockholders Equity": [500_000_000.0, 420_000_000.0],
                    "Total Assets": [1_000_000_000.0, 900_000_000.0],
                    "Current Assets": [450_000_000.0, 380_000_000.0],
                    "Current Liabilities": [225_000_000.0, 200_000_000.0],
                },
            },
            "cash_flow": {
                "statement_type": "Cash Flow Statement",
                "currency": "USD",
                "periods": ["2025-12-31"],
                "rows": {
                    "Operating Cash Flow": [220_000_000.0],
                    "Capital Expenditure": [-40_000_000.0],
                },
            },
        },
    }

    agent = FundamentalAnalysisAgent()
    result = await agent.analyze("TESTCO", "NASDAQ", "1 Year", synthetic_market_data, include_peers=False)

    assert result["revenue_and_earnings"]["revenue_yoy_growth_pct"] == 10.0
    assert result["revenue_and_earnings"]["revenue_cagr_pct"] == 10.0
    assert result["revenue_and_earnings"]["earnings_yoy_growth_pct"] == 21.0
    assert result["profitability"]["gross_margin_pct"] == 50.0
    assert result["profitability"]["operating_margin_pct"] == 20.0
    assert result["profitability"]["net_margin_pct"] == 15.0
    assert result["profitability"]["roa_pct"] == 18.15
    assert result["financial_ratios"]["pe_ratio"]["value"] == 30.0
    assert result["financial_ratios"]["pb_ratio"]["value"] == 3.0
    assert result["financial_ratios"]["roe_pct"]["value"] == 36.3
    assert result["debt_and_stability"]["debt_to_equity"] == 0.5
    assert result["debt_and_stability"]["current_ratio"] == 2.0
    assert result["debt_and_stability"]["free_cash_flow"] == 180_000_000.0
    assert result["debt_and_stability"]["stability_rating"] == "Strong"
    assert len(result["historical_comparison"]) == 3
    # Interest expense was omitted -> should appear in data_gaps
    assert any("Interest expense" in g for g in result["data_gaps"])


def test_fundamental_endpoint(client):
    headers = _get_auth_headers(client, "fund_ep@example.com")
    fake_md = {
        "ticker": "MSFT",
        "market": "NASDAQ",
        "yf_symbol": "MSFT",
        "profile": {"ticker": "MSFT", "company_name": "Microsoft", "currency": "USD", "current_price": 400.0, "market_cap": 3e12, "sector": "Technology"},
        "raw_info": {},
        "data_quality": {"total_raw_rows": 10, "valid_rows": 10, "quality_status": "VALID", "validated_at": "2026-11-26T10:00:00Z"},
        "sources": [],
        "financial_statements": {
            "income_statement": {"periods": ["2025-06-30"], "rows": {"Total Revenue": [2.5e11], "Net Income": [9.0e10], "Diluted EPS": [12.0]}},
            "balance_sheet": {"periods": ["2025-06-30"], "rows": {"Stockholders Equity": [3.0e11]}},
            "cash_flow": {"periods": [], "rows": {}},
        },
    }
    with patch("app.routers.stocks.MarketDataCollector.collect_market_data", return_value=fake_md):
        res = client.get("/api/stocks/MSFT/fundamental?market=NASDAQ&period=1%20Year&include_peers=false", headers=headers)
        assert res.status_code == 200
        fa = res.json()["fundamental_analysis"]
        assert fa["financial_ratios"]["pe_ratio"]["value"] == round(400.0 / 12.0, 2)
        assert fa["financial_ratios"]["pb_ratio"]["value"] == 10.0
        assert fa["financial_ratios"]["roe_pct"]["value"] == 30.0

