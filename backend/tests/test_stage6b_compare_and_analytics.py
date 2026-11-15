import uuid
from typing import Tuple
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.main import app
from app.models.research import ResearchReport, ResearchSession
from app.models.user import User

client = TestClient(app)

TEST_RUN_ID = uuid.uuid4().hex[:6]
USER_1_EMAIL = f"stage6b_analyst_{TEST_RUN_ID}_1@fincrew.com"
USER_2_EMAIL = f"stage6b_analyst_{TEST_RUN_ID}_2@fincrew.com"
EMPTY_USER_EMAIL = f"stage6b_empty_{TEST_RUN_ID}@fincrew.com"
TEST_PASSWORD = "StrongSecurePassword@2026"

shared_state = {}


def create_session_and_report(
    user_id: int,
    ticker: str,
    company_name: str,
    status: str = "COMPLETED",
    recommendation: str = "BUY",
    confidence: float = 0.85,
    sector: str = "Technology",
    pe_ratio: float = 28.5,
    rsi_14: float = 58.0,
    has_sparse_data: bool = False,
) -> Tuple[int, int]:
    """Helper to insert a test research session and report in PostgreSQL."""
    db: Session = SessionLocal()
    try:
        session = ResearchSession(
            user_id=user_id,
            ticker=ticker,
            company_name=company_name,
            status=status,
            error_message="Provider timeout" if status == "FAILED" else None,
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        report_id = None
        if status == "COMPLETED":
            report = ResearchReport(
                session_id=session.id,
                ticker=ticker,
                company_name=company_name,
                current_price=150.00 if not has_sparse_data else None,
                target_price=175.00 if not has_sparse_data else None,
                recommendation=recommendation,
                confidence_score=confidence,
                executive_summary=f"Executive briefing for {company_name}.",
                fundamental_data={
                    "valuation_status": "FAIRLY_VALUED" if not has_sparse_data else "INSUFFICIENT_DATA",
                    "profitability_grade": "HIGH" if not has_sparse_data else "LOW",
                    "solvency_risk": "LOW",
                    "supporting_data": {
                        "pe_ratio": pe_ratio if not has_sparse_data else None,
                        "forward_pe": 24.0 if not has_sparse_data else None,
                        "price_to_book": 8.5 if not has_sparse_data else None,
                    },
                    "market_research": {
                        "sector": sector,
                        "industry": "Software",
                        "market_cap_category": "Large-Cap",
                    },
                },
                technical_data={
                    "trend_direction": "BULLISH",
                    "momentum_state": "NEUTRAL",
                    "key_support": 140.0,
                    "key_resistance": 165.0,
                    "supporting_data": {
                        "rsi_14": rsi_14 if not has_sparse_data else None,
                    },
                },
                sentiment_data={
                    "sentiment_label": "BULLISH",
                    "sentiment_score": 0.40,
                },
                risk_data={
                    "risk_level": "MODERATE",
                    "risk_score": 4.5,
                    "bear_case_scenario": "Macro slowdown",
                },
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            report_id = report.id

        return session.id, report_id
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_stage6b_users():
    """Sets up three test users: User 1 (multiple reports), User 2 (single report), Empty User."""
    # 1. Register User 1
    res1 = client.post(
        "/api/auth/register",
        json={"full_name": "Stage6B User 1", "email": USER_1_EMAIL, "password": TEST_PASSWORD, "confirm_password": TEST_PASSWORD},
    )
    assert res1.status_code == 201
    login1 = client.post("/api/auth/login", json={"email": USER_1_EMAIL, "password": TEST_PASSWORD})
    token1 = login1.json()["access_token"]
    shared_state["headers1"] = {"Authorization": f"Bearer {token1}"}

    # 2. Register User 2
    res2 = client.post(
        "/api/auth/register",
        json={"full_name": "Stage6B User 2", "email": USER_2_EMAIL, "password": TEST_PASSWORD, "confirm_password": TEST_PASSWORD},
    )
    assert res2.status_code == 201
    login2 = client.post("/api/auth/login", json={"email": USER_2_EMAIL, "password": TEST_PASSWORD})
    token2 = login2.json()["access_token"]
    shared_state["headers2"] = {"Authorization": f"Bearer {token2}"}

    # 3. Register Empty User (zero sessions)
    res3 = client.post(
        "/api/auth/register",
        json={"full_name": "Stage6B Empty User", "email": EMPTY_USER_EMAIL, "password": TEST_PASSWORD, "confirm_password": TEST_PASSWORD},
    )
    assert res3.status_code == 201
    login3 = client.post("/api/auth/login", json={"email": EMPTY_USER_EMAIL, "password": TEST_PASSWORD})
    token3 = login3.json()["access_token"]
    shared_state["headers_empty"] = {"Authorization": f"Bearer {token3}"}

    db = SessionLocal()
    u1 = db.query(User).filter(User.email == USER_1_EMAIL).first()
    u2 = db.query(User).filter(User.email == USER_2_EMAIL).first()
    shared_state["u1_id"] = u1.id
    shared_state["u2_id"] = u2.id
    db.close()

    # User 1 Sessions:
    # 1. AAPL (Technology, BUY, conf 0.85)
    s1, _ = create_session_and_report(u1.id, "AAPL", "Apple Inc.", "COMPLETED", "BUY", 0.85, "Technology", 28.5, 58.0)
    # 2. MSFT (Technology, STRONG_BUY, conf 0.90)
    s2, _ = create_session_and_report(u1.id, "MSFT", "Microsoft Corp.", "COMPLETED", "STRONG_BUY", 0.90, "Technology", 32.0, 62.0)
    # 3. PFE (Healthcare, HOLD, conf 0.70)
    s3, _ = create_session_and_report(u1.id, "PFE", "Pfizer Inc.", "COMPLETED", "HOLD", 0.70, "Healthcare", 14.5, 42.0)
    # 4. FAILED session
    s_failed, _ = create_session_and_report(u1.id, "FAIL", "Failed Corp.", "FAILED")
    # 5. Sparse data session (missing metrics)
    s_sparse, _ = create_session_and_report(u1.id, "SPARSE", "Sparse Inc.", "COMPLETED", "HOLD", 0.60, "Industrial", has_sparse_data=True)

    shared_state["u1_s1"] = s1
    shared_state["u1_s2"] = s2
    shared_state["u1_s3"] = s3
    shared_state["u1_failed"] = s_failed
    shared_state["u1_sparse"] = s_sparse

    # User 2 Session:
    u2_s1, _ = create_session_and_report(u2.id, "GOOGL", "Alphabet Inc.", "COMPLETED", "BUY", 0.88, "Communication")
    shared_state["u2_s1"] = u2_s1

    yield

    # Teardown test data
    db = SessionLocal()
    try:
        db.query(ResearchSession).filter(ResearchSession.user_id.in_([u1.id, u2.id])).delete()
        db.commit()
    finally:
        db.close()


# -------------------------------------------------------------------------
# Workspace Analytics Tests
# -------------------------------------------------------------------------

def test_01_empty_workspace_analytics():
    """Verify GET /api/research/analytics/summary handles empty workspace safely."""
    res = client.get(
        "/api/research/analytics/summary",
        headers=shared_state["headers_empty"],
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_sessions"] == 0
    assert data["average_confidence"] == 0.0
    assert data["status_counts"]["completed"] == 0
    assert data["recommendation_summary"]["buy"] == 0
    assert data["sector_allocation"] == {}
    assert data["sector_percentages"] == {}
    assert data["latest_activity_at"] is None


def test_02_workspace_analytics_with_data():
    """Verify calculations of status counts, recommendation distribution, confidence, and sector allocations."""
    res = client.get(
        "/api/research/analytics/summary",
        headers=shared_state["headers1"],
    )
    assert res.status_code == 200
    data = res.json()

    assert data["total_sessions"] == 5
    assert data["status_counts"]["completed"] == 4
    assert data["status_counts"]["failed"] == 1

    # Recommendations: 1 STRONG_BUY, 1 BUY, 2 HOLD
    assert data["recommendation_distribution"]["STRONG_BUY"] == 1
    assert data["recommendation_distribution"]["BUY"] == 1
    assert data["recommendation_distribution"]["HOLD"] == 2
    assert data["recommendation_summary"]["buy"] == 2
    assert data["recommendation_summary"]["hold"] == 2

    # Average confidence: (0.85 + 0.90 + 0.70 + 0.60) / 4 = 0.7625 -> 0.76
    assert 0.75 <= data["average_confidence"] <= 0.77

    # Sector allocation: Technology=2, Healthcare=1, Industrial=1
    assert data["sector_allocation"]["Technology"] == 2
    assert data["sector_allocation"]["Healthcare"] == 1
    assert data["sector_allocation"]["Industrial"] == 1
    assert data["sector_percentages"]["Technology"] == 50.0
    assert data["sector_percentages"]["Healthcare"] == 25.0


def test_03_workspace_analytics_user_isolation():
    """Verify User 2 sees only their own session analytics and cannot see User 1's data."""
    res = client.get(
        "/api/research/analytics/summary",
        headers=shared_state["headers2"],
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_sessions"] == 1
    assert data["status_counts"]["completed"] == 1
    assert "Communication" in data["sector_allocation"]
    assert "Technology" not in data["sector_allocation"]


def test_04_unauthenticated_analytics_rejected():
    """Verify unauthenticated GET /api/research/analytics/summary returns 401."""
    res = client.get("/api/research/analytics/summary")
    assert res.status_code == 401


# -------------------------------------------------------------------------
# Multi-Stock Comparative Analysis Tests
# -------------------------------------------------------------------------

def test_05_compare_less_than_two_sessions_rejected():
    """Verify comparing fewer than 2 sessions returns 422 Unprocessable Entity."""
    res = client.post(
        "/api/research/compare",
        json={"session_ids": [shared_state["u1_s1"]]},
        headers=shared_state["headers1"],
    )
    assert res.status_code == 422


def test_06_compare_more_than_five_sessions_rejected():
    """Verify comparing more than 5 sessions returns 422 Unprocessable Entity."""
    res = client.post(
        "/api/research/compare",
        json={"session_ids": [1, 2, 3, 4, 5, 6]},
        headers=shared_state["headers1"],
    )
    assert res.status_code == 422


def test_07_compare_duplicate_session_ids_rejected():
    """Verify submitting duplicate session IDs returns 400 Bad Request."""
    res = client.post(
        "/api/research/compare",
        json={"session_ids": [shared_state["u1_s1"], shared_state["u1_s1"]]},
        headers=shared_state["headers1"],
    )
    assert res.status_code == 400
    assert "at least 2 distinct" in res.json()["detail"].lower()


def test_08_compare_nonexistent_session_rejected():
    """Verify comparing a non-existent session ID returns 404 Not Found."""
    res = client.post(
        "/api/research/compare",
        json={"session_ids": [shared_state["u1_s1"], 999999]},
        headers=shared_state["headers1"],
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_09_compare_cross_user_forbidden():
    """Verify User 2 CANNOT compare User 1's sessions (403 Forbidden)."""
    res = client.post(
        "/api/research/compare",
        json={"session_ids": [shared_state["u1_s1"], shared_state["u2_s1"]]},
        headers=shared_state["headers2"],
    )
    assert res.status_code == 403
    assert "access denied" in res.json()["detail"].lower()


def test_10_compare_incomplete_or_failed_session_rejected():
    """Verify comparing incomplete/failed sessions returns 400 Bad Request."""
    res = client.post(
        "/api/research/compare",
        json={"session_ids": [shared_state["u1_s1"], shared_state["u1_failed"]]},
        headers=shared_state["headers1"],
    )
    assert res.status_code == 400
    assert "not completed" in res.json()["detail"].lower()


def test_11_compare_successful_multiple_stocks():
    """Verify comparing 2 to 3 valid stocks returns normalized items and side-by-side matrix."""
    sids = [shared_state["u1_s1"], shared_state["u1_s2"], shared_state["u1_s3"]]
    res = client.post(
        "/api/research/compare",
        json={"session_ids": sids},
        headers=shared_state["headers1"],
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_compared"] == 3
    assert len(data["items"]) == 3

    tickers = [item["ticker"] for item in data["items"]]
    assert tickers == ["AAPL", "MSFT", "PFE"]

    # Verify side-by-side matrix structure
    matrix = data["matrix"]
    assert len(matrix) >= 15

    categories = {row["category"] for row in matrix}
    assert "Consensus" in categories
    assert "Valuation" in categories
    assert "Technicals" in categories
    assert "Sentiment" in categories
    assert "Risk" in categories
    assert "Classification" in categories

    # Verify specific metric row
    rec_row = next(r for r in matrix if r["metric"] == "Recommendation")
    assert rec_row["values"]["AAPL"] == "BUY"
    assert rec_row["values"]["MSFT"] == "STRONG_BUY"
    assert rec_row["values"]["PFE"] == "HOLD"


def test_12_compare_missing_metrics_handled_as_null():
    """Verify missing/unavailable metrics stay None without fabricating data."""
    sids = [shared_state["u1_s1"], shared_state["u1_sparse"]]
    res = client.post(
        "/api/research/compare",
        json={"session_ids": sids},
        headers=shared_state["headers1"],
    )
    assert res.status_code == 200
    data = res.json()

    sparse_item = next(item for item in data["items"] if item["ticker"] == "SPARSE")
    assert sparse_item["current_price"] is None
    assert sparse_item["pe_ratio"] is None
    assert sparse_item["rsi_14"] is None
    assert sparse_item["valuation_status"] == "INSUFFICIENT_DATA"

    # Verify in matrix
    pe_row = next(r for r in data["matrix"] if r["metric"] == "Trailing P/E Ratio")
    assert pe_row["values"]["SPARSE"] is None
    assert pe_row["values"]["AAPL"] == 28.5
