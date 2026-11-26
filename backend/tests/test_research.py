from unittest.mock import patch
import numpy as np
import pandas as pd

from app.models.research_task import ResearchTask
from app.services.research_engine import execute_research_task_background


def get_auth_token(client, email):
    client.post("/api/auth/register", json={
        "full_name": "Research User",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    res = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    return res.json()["access_token"]


def test_research_task_creation_and_isolation(client):
    token1 = get_auth_token(client, "res_user1@example.com")
    token2 = get_auth_token(client, "res_user2@example.com")

    h1 = {"Authorization": f"Bearer {token1}"}
    h2 = {"Authorization": f"Bearer {token2}"}

    # Patch background execution so creation test stays fast & offline
    with patch("app.routers.research.execute_research_task_background"):
        create_res = client.post(
            "/api/research",
            headers=h1,
            json={"ticker": "MSFT", "market": "NASDAQ", "analysis_period": "1 Year"}
        )
    assert create_res.status_code == 201
    task_id = create_res.json()["task_id"]
    assert create_res.json()["status"] == "Pending"

    # User 1 can view task details
    detail_res = client.get(f"/api/research/{task_id}", headers=h1)
    assert detail_res.status_code == 200
    assert detail_res.json()["ticker"] == "MSFT"

    # User 2 is forbidden from accessing task
    u2_view = client.get(f"/api/research/{task_id}", headers=h2)
    assert u2_view.status_code == 403

    # History filtering
    hist_res = client.get("/api/research/history?search=MSFT", headers=h1)
    assert hist_res.status_code == 200
    assert len(hist_res.json()) >= 1

    # Dashboard overview
    dash_res = client.get("/api/research/dashboard/overview", headers=h1)
    assert dash_res.status_code == 200
    assert dash_res.json()["total_research"] >= 1


def test_full_multi_agent_pipeline_and_exports(client, db_session):
    token = get_auth_token(client, "pipeline_e2e@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    with patch("app.routers.research.execute_research_task_background"):
        create_res = client.post(
            "/api/research",
            headers=headers,
            json={"ticker": "INFY", "company_name": "Infosys Limited", "market": "NSE", "analysis_period": "6 Months"},
        )
    assert create_res.status_code == 201
    task_id = create_res.json()["task_id"]

    # Build deterministic mock MarketDataCollector payload
    dates = pd.date_range("2026-01-01", periods=60, freq="B")
    close = np.linspace(1400.0, 1650.0, 60)
    df = pd.DataFrame({
        "Open": close - 5.0,
        "High": close + 10.0,
        "Low": close - 10.0,
        "Close": close,
        "Volume": [2_000_000] * 60,
    }, index=dates)

    fake_md = {
        "ticker": "INFY",
        "market": "NSE",
        "yf_symbol": "INFY.NS",
        "period": "6 Months",
        "retrieved_at": "2026-11-26T10:00:00+00:00",
        "profile": {
            "ticker": "INFY",
            "yf_symbol": "INFY.NS",
            "company_name": "Infosys Limited",
            "market": "NSE",
            "currency": "INR",
            "sector": "Technology",
            "industry": "IT Services",
            "current_price": 1650.0,
            "market_cap": 6.8e12,
            "fifty_two_week_high": 1700.0,
            "fifty_two_week_low": 1350.0,
            "description": "Infosys Limited provides consulting and IT services globally.",
        },
        "raw_info": {},
        "period_performance": {
            "period": "6 Months",
            "trading_days": 60,
            "start_price": 1400.0,
            "end_price": 1650.0,
            "change_percent": 17.86,
            "recent_history": [],
        },
        "ohlcv": [],
        "ohlcv_df_full": df,
        "ohlcv_df_period": df,
        "data_quality": {
            "total_raw_rows": 60,
            "valid_rows": 60,
            "duplicate_dates_removed": 0,
            "duplicate_dates": [],
            "missing_values_count": 0,
            "missing_value_details": [],
            "inconsistent_rows_count": 0,
            "inconsistent_row_details": [],
            "date_gaps": [],
            "quality_status": "VALID",
            "validated_at": "2026-11-26T10:00:00+00:00",
            "notes": ["All OHLCV rows passed completeness, uniqueness, and price consistency checks."],
        },
        "financial_statements": {
            "income_statement": {
                "statement_type": "Income Statement",
                "currency": "INR",
                "periods": ["2026-03-31", "2025-03-31"],
                "rows": {
                    "Total Revenue": [1.6e12, 1.5e12],
                    "Gross Profit": [4.8e11, 4.5e11],
                    "Operating Income": [3.3e11, 3.1e11],
                    "Net Income": [2.6e11, 2.4e11],
                    "Diluted EPS": [62.5, 58.0],
                },
            },
            "balance_sheet": {
                "statement_type": "Balance Sheet",
                "currency": "INR",
                "periods": ["2026-03-31"],
                "rows": {
                    "Total Debt": [8.0e10],
                    "Cash And Cash Equivalents": [2.5e11],
                    "Stockholders Equity": [8.8e11],
                    "Total Assets": [1.3e12],
                    "Current Assets": [7.0e11],
                    "Current Liabilities": [3.5e11],
                },
            },
            "cash_flow": {
                "statement_type": "Cash Flow Statement",
                "currency": "INR",
                "periods": ["2026-03-31"],
                "rows": {
                    "Operating Cash Flow": [2.9e11],
                    "Capital Expenditure": [-3.0e10],
                },
            },
        },
        "sources": [
            {
                "source_type": "MARKET_OHLCV",
                "title": "Yahoo Finance Historical OHLCV (INFY.NS, 6 Months)",
                "source_url": "https://finance.yahoo.com/quote/INFY.NS/history",
                "published_at": "2026-03-26",
                "retrieved_at": "2026-11-26T10:00:00+00:00",
                "content_hash": "hash123",
            }
        ],
    }

    # Execute pipeline synchronously against the test db_session
    class _SessionWrapper:
        def __init__(self, s):
            self._s = s

        def __getattr__(self, name):
            return getattr(self._s, name)

        def close(self):
            pass  # Keep test fixture session open

    with patch("app.services.research_engine.MarketDataCollector.collect_market_data", return_value=fake_md):
        execute_research_task_background(
            task_id,
            session_factory=lambda: _SessionWrapper(db_session),
            include_peers=False,
        )

    # Verify task status & completed_at
    task_res = client.get(f"/api/research/{task_id}", headers=headers)
    assert task_res.status_code == 200
    assert task_res.json()["status"] == "Completed"
    assert task_res.json()["completed_at"] is not None
    assert task_res.json()["has_report"] is True

    # Verify Report
    rep_res = client.get(f"/api/research/{task_id}/report", headers=headers)
    assert rep_res.status_code == 200
    rep_body = rep_res.json()
    assert rep_body["summary"] is not None
    content = rep_body["report_content"]
    assert "fundamental_analysis" in content
    assert "technical_analysis" in content
    assert content["fundamental_analysis"]["financial_ratios"]["pe_ratio"]["value"] == 26.4
    assert content["technical_analysis"]["trend_summary"]["overall_signal"] == "Upward Trend"

    # Verify AgentResult rows
    agents_res = client.get(f"/api/research/{task_id}/agents", headers=headers)
    assert agents_res.status_code == 200
    agent_names = [a["agent_name"] for a in agents_res.json()]
    assert "market_data_collector" in agent_names
    assert "fundamental_analysis_agent" in agent_names
    assert "technical_analysis_agent" in agent_names
    assert "synthesis_officer" in agent_names

    # Verify SourceDocument rows
    src_res = client.get(f"/api/research/{task_id}/sources", headers=headers)
    assert src_res.status_code == 200
    assert len(src_res.json()) == 1
    assert src_res.json()[0]["source_type"] == "MARKET_OHLCV"

    # Verify Markdown export
    md_res = client.get(f"/api/research/{task_id}/export/markdown", headers=headers)
    assert md_res.status_code == 200
    assert "text/markdown" in md_res.headers["content-type"]
    assert "# Stock Research Report: Infosys Limited (INFY)" in md_res.text
