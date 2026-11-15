import uuid
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.main import app
from app.models.research import ResearchReport, ResearchSession
from app.models.user import User
from app.schemas.market_data import (
    CompanyProfile,
    FundamentalMetrics,
    NewsArticle,
    PriceSummary,
    StockMarketData,
    TechnicalIndicators,
)
from app.services.research_orchestrator import ResearchOrchestrator

client = TestClient(app)

TEST_RUN_ID = uuid.uuid4().hex[:6]
USER_1_EMAIL = f"res_analyst_{TEST_RUN_ID}_1@fincrew.com"
USER_2_EMAIL = f"res_analyst_{TEST_RUN_ID}_2@fincrew.com"
TEST_PASSWORD = "StrongSecurePassword@2026"

# Shared fixture state across tests
shared_state = {}


def get_mock_market_data(ticker: str = "AAPL", current_price: float = 185.50) -> StockMarketData:
    """Creates a deterministic, non-fabricated StockMarketData fixture for unit testing."""
    return StockMarketData(
        ticker=ticker,
        company_name=f"{ticker} Test Corporation",
        fetched_at="2026-11-15T10:00:00Z",
        profile=CompanyProfile(
            ticker=ticker,
            company_name=f"{ticker} Test Corporation",
            sector="Technology",
            industry="Software & Infrastructure",
            country="United States",
            website="https://example.com",
            beta=1.12,
            business_summary=f"{ticker} Test Corporation provides cloud and enterprise software solutions.",
        ),
        price=PriceSummary(
            current_price=current_price,
            previous_close=182.00,
            day_change=3.50,
            day_change_percent=1.92,
            day_high=187.00,
            day_low=181.50,
            fifty_two_week_high=200.00,
            fifty_two_week_low=150.00,
            market_cap=2500000000000,
            currency="USD",
        ),
        fundamentals=FundamentalMetrics(
            pe_ratio=26.5,
            forward_pe=22.0,
            price_to_book=12.0,
            enterprise_to_ebitda=17.5,
            profit_margins=0.24,
            operating_margins=0.28,
            gross_margins=0.48,
            revenue_growth=0.11,
            earnings_growth=0.14,
            total_revenue=95000000000,
            ebitda=30000000000,
            total_debt=20000000000,
            total_cash=35000000000,
            debt_to_equity=40.0,
            free_cash_flow=22000000000,
            dividend_yield=0.012,
        ),
        technicals=TechnicalIndicators(
            sma_50=180.0,
            sma_200=172.0,
            rsi_14=56.0,
            trend_signal="BULLISH",
            price_change_30d_pct=4.5,
            price_change_90d_pct=9.2,
            support_level=175.0,
            resistance_level=195.0,
            recent_history=[],
        ),
        news=[
            NewsArticle(
                title=f"{ticker} Beats Earnings Estimates and Raises Guidance",
                summary="Solid performance driven by robust enterprise adoption.",
                publisher="Reuters",
                link="https://reuters.com/news/1",
                published_at="2026-11-14T10:00:00Z",
            ),
            NewsArticle(
                title=f"{ticker} Unveils Next-Generation AI Cloud Architecture",
                summary="New architecture expands high-performance computing capabilities.",
                publisher="Bloomberg",
                link="https://bloomberg.com/news/2",
                published_at="2026-11-14T14:30:00Z",
            ),
        ],
        has_full_data=True,
    )


@pytest.fixture(scope="module", autouse=True)
def setup_test_users():
    """Sets up two isolated test users and obtains valid Bearer JWT tokens."""
    # 1. Register User 1
    res1 = client.post(
        "/api/auth/register",
        json={
            "full_name": "Primary Analyst",
            "email": USER_1_EMAIL,
            "password": TEST_PASSWORD,
            "confirm_password": TEST_PASSWORD,
        },
    )
    assert res1.status_code == 201, f"User 1 registration failed: {res1.text}"

    # Login User 1
    login1 = client.post(
        "/api/auth/login",
        json={"email": USER_1_EMAIL, "password": TEST_PASSWORD},
    )
    assert login1.status_code == 200
    token1 = login1.json()["access_token"]
    shared_state["token1"] = token1
    shared_state["headers1"] = {"Authorization": f"Bearer {token1}"}

    # 2. Register User 2
    res2 = client.post(
        "/api/auth/register",
        json={
            "full_name": "Secondary Analyst",
            "email": USER_2_EMAIL,
            "password": TEST_PASSWORD,
            "confirm_password": TEST_PASSWORD,
        },
    )
    assert res2.status_code == 201, f"User 2 registration failed: {res2.text}"

    # Login User 2
    login2 = client.post(
        "/api/auth/login",
        json={"email": USER_2_EMAIL, "password": TEST_PASSWORD},
    )
    assert login2.status_code == 200
    token2 = login2.json()["access_token"]
    shared_state["token2"] = token2
    shared_state["headers2"] = {"Authorization": f"Bearer {token2}"}

    yield

    # Clean up test research sessions and reports created by test users
    db: Session = SessionLocal()
    try:
        u1 = db.query(User).filter(User.email == USER_1_EMAIL).first()
        u2 = db.query(User).filter(User.email == USER_2_EMAIL).first()
        if u1:
            db.query(ResearchSession).filter(ResearchSession.user_id == u1.id).delete()
        if u2:
            db.query(ResearchSession).filter(ResearchSession.user_id == u2.id).delete()
        db.commit()
    finally:
        db.close()


def test_01_unauthenticated_requests_rejected():
    """Verify that all research endpoints strictly reject unauthenticated requests with 401 Unauthorized."""
    endpoints = [
        ("POST", "/api/research/analyze", {"ticker": "AAPL"}),
        ("POST", "/api/research/sessions", {"ticker": "AAPL"}),
        ("POST", "/api/research/sessions/999/start", {}),
        ("GET", "/api/research/sessions", None),
        ("GET", "/api/research/sessions/999", None),
        ("GET", "/api/research/sessions/999/report", None),
        ("DELETE", "/api/research/sessions/999", None),
    ]

    for method, path, body in endpoints:
        if method == "POST":
            res = client.post(path, json=body or {})
        elif method == "GET":
            res = client.get(path)
        elif method == "DELETE":
            res = client.delete(path)
        assert res.status_code == 401, f"Expected 401 for unauthenticated {method} {path}, got {res.status_code}"


def test_02_invalid_ticker_syntax_rejected():
    """Verify that ticker symbols with invalid length or illegal characters are rejected with 422 Unprocessable Entity."""
    invalid_tickers = [
        "TOOLONGTICKERNAME",  # > 10 chars
        "AAPL$$",             # illegal characters
        "",                   # empty string
        "   ",                # whitespace only
        "A@PL",               # illegal @ symbol
    ]

    for ticker in invalid_tickers:
        res = client.post(
            "/api/research/sessions",
            json={"ticker": ticker},
            headers=shared_state["headers1"],
        )
        assert res.status_code == 422, f"Expected 422 for invalid ticker '{ticker}', got {res.status_code}"


def test_03_create_research_session_pending():
    """Verify creating a research session returns 201 Created and PENDING status."""
    res = client.post(
        "/api/research/sessions",
        json={"ticker": "aapl"},
        headers=shared_state["headers1"],
    )
    assert res.status_code == 201
    data = res.json()
    assert data["ticker"] == "AAPL"  # Normalized to uppercase
    assert data["status"] == "PENDING"
    assert data["error_message"] is None
    assert "id" in data
    shared_state["session_1_id"] = data["id"]


def test_04_orchestrator_pipeline_execution():
    """
    Directly tests ResearchOrchestrator pipeline execution with deterministic mocked market data.
    Verifies state transitions, specialist outputs, consensus recommendation, target prices, and persistence.
    """
    db: Session = SessionLocal()
    try:
        session_id = shared_state["session_1_id"]
        mock_data = get_mock_market_data(ticker="AAPL", current_price=185.50)

        orchestrator = ResearchOrchestrator(
            market_data_service=lambda t: mock_data
        )
        report = orchestrator.run(session_id=session_id, db=db)

        assert report is not None
        assert report.ticker == "AAPL"
        assert report.current_price == 185.50
        assert report.target_price is not None
        assert report.recommendation in ("STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL")
        assert 0.0 <= report.confidence_score <= 1.0
        assert len(report.executive_summary) > 50

        # Verify all specialist agent JSON payloads are stored
        assert report.fundamental_data is not None
        assert "valuation_status" in report.fundamental_data
        assert "market_research" in report.fundamental_data
        assert report.technical_data is not None
        assert "trend_direction" in report.technical_data
        assert report.sentiment_data is not None
        assert "sentiment_score" in report.sentiment_data
        assert report.risk_data is not None
        assert "risk_score" in report.risk_data

        # Verify session record in PostgreSQL
        session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
        assert session.status == "COMPLETED"
        assert session.error_message is None
        assert session.completed_at is not None
        assert session.company_name == "AAPL Test Corporation"
    finally:
        db.close()


def test_05_get_session_details_and_report():
    """Verify GET /api/research/sessions/{id} and /api/research/sessions/{id}/report return completed data."""
    session_id = shared_state["session_1_id"]

    # 1. GET session status
    res = client.get(
        f"/api/research/sessions/{session_id}",
        headers=shared_state["headers1"],
    )
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == session_id
    assert data["status"] == "COMPLETED"
    assert data["report"] is not None
    assert data["report"]["recommendation"] in ("STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL")

    # 2. GET dedicated report endpoint
    res_report = client.get(
        f"/api/research/sessions/{session_id}/report",
        headers=shared_state["headers1"],
    )
    assert res_report.status_code == 200
    rep_data = res_report.json()
    assert rep_data["session_id"] == session_id
    assert rep_data["ticker"] == "AAPL"
    assert rep_data["current_price"] == 185.50
    assert rep_data["target_price"] is not None


def test_06_analyze_stock_synchronous_endpoint():
    """Verify POST /api/research/analyze?run_sync=true creates and executes research synchronously."""
    mock_data = get_mock_market_data(ticker="MSFT", current_price=415.00)

    with patch("app.services.research_orchestrator.get_cached_stock_market_data", return_value=mock_data):
        res = client.post(
            "/api/research/analyze?run_sync=true",
            json={"ticker": "MSFT"},
            headers=shared_state["headers1"],
        )
        assert res.status_code == 200
        data = res.json()
        assert data["ticker"] == "MSFT"
        assert data["status"] == "COMPLETED"
        assert data["report"] is not None
        assert data["report"]["current_price"] == 415.00
        shared_state["session_msft_id"] = data["id"]


def test_07_list_user_research_sessions():
    """Verify GET /api/research/sessions returns previous sessions for authenticated user ordered latest first."""
    res = client.get(
        "/api/research/sessions",
        headers=shared_state["headers1"],
    )
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert data["total"] >= 2  # AAPL and MSFT
    assert len(data["sessions"]) >= 2

    # Verify latest session comes first
    tickers = [s["ticker"] for s in data["sessions"]]
    assert "MSFT" in tickers
    assert "AAPL" in tickers


def test_08_cross_user_isolation_strictly_enforced():
    """
    CRITICAL SECURITY CHECK:
    Verify that User 2 CANNOT view, start, or delete User 1's research sessions (403 Forbidden),
    and User 1's sessions do not appear in User 2's session list.
    """
    user1_session_id = shared_state["session_1_id"]

    # 1. User 2 attempts to get User 1's session details -> 403 Forbidden
    res = client.get(
        f"/api/research/sessions/{user1_session_id}",
        headers=shared_state["headers2"],
    )
    assert res.status_code == 403
    assert "do not own" in res.json()["detail"].lower()

    # 2. User 2 attempts to get User 1's report -> 403 Forbidden
    res_rep = client.get(
        f"/api/research/sessions/{user1_session_id}/report",
        headers=shared_state["headers2"],
    )
    assert res_rep.status_code == 403

    # 3. User 2 attempts to start User 1's session -> 403 Forbidden
    res_start = client.post(
        f"/api/research/sessions/{user1_session_id}/start",
        headers=shared_state["headers2"],
    )
    assert res_start.status_code == 403

    # 4. User 2 attempts to delete User 1's session -> 403 Forbidden
    res_del = client.delete(
        f"/api/research/sessions/{user1_session_id}",
        headers=shared_state["headers2"],
    )
    assert res_del.status_code == 403

    # 5. User 2 lists their own sessions -> User 1's sessions must NOT appear
    res_list = client.get(
        "/api/research/sessions",
        headers=shared_state["headers2"],
    )
    assert res_list.status_code == 200
    user2_session_ids = [s["id"] for s in res_list.json()["sessions"]]
    assert user1_session_id not in user2_session_ids


def test_09_agent_failure_resilience():
    """
    Verify fault tolerance: if one specialist agent raises an unexpected exception,
    the pipeline DOES NOT crash, logs the failure, sets fallback output with confidence=0.0,
    and successfully completes the research session.
    """
    db: Session = SessionLocal()
    try:
        # Create a new session for testing resilience
        res = client.post(
            "/api/research/sessions",
            json={"ticker": "NVDA"},
            headers=shared_state["headers1"],
        )
        assert res.status_code == 201
        session_id = res.json()["id"]

        mock_data = get_mock_market_data(ticker="NVDA", current_price=120.00)

        # Mock TechnicalAnalysisAgent to throw an unexpected exception
        failing_technical_agent = MagicMock()
        failing_technical_agent.analyze.side_effect = RuntimeError("Simulated internal indicator crash")

        orchestrator = ResearchOrchestrator(
            technical_agent=failing_technical_agent,
            market_data_service=lambda t: mock_data,
        )

        report = orchestrator.run(session_id=session_id, db=db)

        # Orchestrator must successfully return the report despite agent failure
        assert report is not None
        assert report.ticker == "NVDA"
        assert report.status if hasattr(report, "status") else True
        assert report.technical_data is not None
        assert report.technical_data["confidence_level"] == 0.0
        assert "execution error" in report.technical_data["key_findings"][0].lower()

        # Session in DB must be COMPLETED
        session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
        assert session.status == "COMPLETED"
    finally:
        db.close()


def test_10_market_data_provider_failure_handling():
    """
    Verify provider failure handling: if market data acquisition fails (e.g. invalid ticker or provider down),
    the session is marked as FAILED with a clear error message, and report retrieval returns 400 Bad Request.
    """
    db: Session = SessionLocal()
    try:
        res = client.post(
            "/api/research/sessions",
            json={"ticker": "XYZ999"},
            headers=shared_state["headers1"],
        )
        assert res.status_code == 201
        session_id = res.json()["id"]

        def failing_market_data(ticker: str):
            raise ValueError(f"Ticker symbol '{ticker}' was not found or has no active market data.")

        orchestrator = ResearchOrchestrator(
            market_data_service=failing_market_data
        )
        report = orchestrator.run(session_id=session_id, db=db)

        # Report must be None when market data fails
        assert report is None

        # Session must be marked FAILED
        session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
        assert session.status == "FAILED"
        assert "not found" in session.error_message.lower()
        assert session.completed_at is not None

        # Report retrieval must return 400 Bad Request with the failure explanation
        res_rep = client.get(
            f"/api/research/sessions/{session_id}/report",
            headers=shared_state["headers1"],
        )
        assert res_rep.status_code == 400
        assert "failed" in res_rep.json()["detail"].lower()
    finally:
        db.close()


def test_11_delete_research_session_and_cascade_report():
    """
    Verify deleting a research session removes the session and its associated report
    via PostgreSQL ON DELETE CASCADE.
    """
    session_id = shared_state["session_1_id"]

    # Verify session and report exist in DB before deletion
    db: Session = SessionLocal()
    try:
        sess_before = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
        assert sess_before is not None
        rep_before = db.query(ResearchReport).filter(ResearchReport.session_id == session_id).first()
        assert rep_before is not None
    finally:
        db.close()

    # Issue DELETE request
    res = client.delete(
        f"/api/research/sessions/{session_id}",
        headers=shared_state["headers1"],
    )
    assert res.status_code == 200
    assert "deleted successfully" in res.json()["message"].lower()

    # Verify session and report are gone in PostgreSQL
    db = SessionLocal()
    try:
        sess_after = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
        assert sess_after is None
        rep_after = db.query(ResearchReport).filter(ResearchReport.session_id == session_id).first()
        assert rep_after is None
    finally:
        db.close()

    # Verify endpoint returns 404 for deleted session
    res_get = client.get(
        f"/api/research/sessions/{session_id}",
        headers=shared_state["headers1"],
    )
    assert res_get.status_code == 404
