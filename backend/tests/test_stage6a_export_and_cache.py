import threading
import time
import uuid
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
from app.services.market_data_cache import MarketDataCache, get_cached_stock_market_data
from app.services.report_exporter import ReportExporter

client = TestClient(app)

TEST_RUN_ID = uuid.uuid4().hex[:6]
USER_1_EMAIL = f"stage6a_analyst_{TEST_RUN_ID}_1@fincrew.com"
USER_2_EMAIL = f"stage6a_analyst_{TEST_RUN_ID}_2@fincrew.com"
TEST_PASSWORD = "StrongSecurePassword@2026"

shared_state = {}


def get_mock_market_data(ticker: str = "AAPL", current_price: float = 185.50) -> StockMarketData:
    """Creates a deterministic StockMarketData fixture for testing."""
    return StockMarketData(
        ticker=ticker,
        company_name=f"{ticker} Technologies",
        fetched_at="2026-11-15T10:00:00Z",
        profile=CompanyProfile(
            ticker=ticker,
            company_name=f"{ticker} Technologies",
            sector="Technology",
            industry="Consumer Electronics",
            country="United States",
            beta=1.1,
            business_summary="Leading electronics company.",
        ),
        price=PriceSummary(
            current_price=current_price,
            previous_close=180.00,
            day_change=5.50,
            day_change_percent=3.05,
            fifty_two_week_high=195.00,
            fifty_two_week_low=145.00,
            market_cap=2800000000000,
            currency="USD",
        ),
        fundamentals=FundamentalMetrics(
            pe_ratio=28.5,
            forward_pe=24.0,
            price_to_book=15.0,
            profit_margins=0.25,
            total_debt=100000000000,
            total_cash=60000000000,
        ),
        technicals=TechnicalIndicators(
            sma_50=182.0,
            sma_200=175.0,
            rsi_14=58.0,
            trend_signal="BULLISH",
            support_level=178.0,
            resistance_level=192.0,
        ),
        news=[
            NewsArticle(
                title=f"{ticker} Announces Record Quarterly Revenue",
                publisher="WSJ",
                link="https://wsj.com/article",
            )
        ],
        has_full_data=True,
    )


def create_mock_report_in_db(user_id: int, ticker: str = "AAPL") -> Tuple[int, int]:
    """Helper to insert a completed research session and report in PostgreSQL."""
    db: Session = SessionLocal()
    try:
        session = ResearchSession(
            user_id=user_id,
            ticker=ticker,
            company_name=f"{ticker} Technologies",
            status="COMPLETED",
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        report = ResearchReport(
            session_id=session.id,
            ticker=ticker,
            company_name=session.company_name,
            current_price=185.50,
            target_price=195.00,
            recommendation="BUY",
            confidence_score=0.85,
            executive_summary=(
                f"FinCrew Investment Committee report for {session.company_name} ({ticker}).\n\n"
                "Consensus recommendation is BUY with 85% confidence score.\n\n"
                "Strong technical setup and robust cash flows support a 12-month target of $195.00."
            ),
            fundamental_data={
                "valuation_status": "FAIRLY_VALUED",
                "profitability_grade": "HIGH",
                "solvency_risk": "LOW",
                "key_findings": ["High gross margin of 45%", "Stable balance sheet with strong cash reserves"],
                "market_research": {
                    "sector": "Technology",
                    "industry": "Consumer Electronics",
                    "market_cap_category": "Mega-Cap",
                    "key_findings": ["Dominant global ecosystem"],
                },
            },
            technical_data={
                "trend_direction": "BULLISH",
                "momentum_state": "NEUTRAL",
                "key_support": 178.0,
                "key_resistance": 192.0,
                "key_findings": ["Trading above 50-day and 200-day moving averages"],
            },
            sentiment_data={
                "sentiment_label": "BULLISH",
                "sentiment_score": 0.45,
                "news_sample_size": 1,
                "key_findings": ["Favorable earnings coverage"],
            },
            risk_data={
                "risk_level": "LOW",
                "risk_score": 2.5,
                "bear_case_scenario": "Consumer discretionary spending contraction",
                "key_findings": ["Supply chain concentration"],
            },
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return session.id, report.id
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_stage6a_users():
    """Sets up two isolated test users and shared tokens."""
    # Register User 1
    res1 = client.post(
        "/api/auth/register",
        json={"full_name": "Stage6A User 1", "email": USER_1_EMAIL, "password": TEST_PASSWORD, "confirm_password": TEST_PASSWORD},
    )
    assert res1.status_code == 201
    login1 = client.post("/api/auth/login", json={"email": USER_1_EMAIL, "password": TEST_PASSWORD})
    token1 = login1.json()["access_token"]
    shared_state["headers1"] = {"Authorization": f"Bearer {token1}"}

    # Register User 2
    res2 = client.post(
        "/api/auth/register",
        json={"full_name": "Stage6A User 2", "email": USER_2_EMAIL, "password": TEST_PASSWORD, "confirm_password": TEST_PASSWORD},
    )
    assert res2.status_code == 201
    login2 = client.post("/api/auth/login", json={"email": USER_2_EMAIL, "password": TEST_PASSWORD})
    token2 = login2.json()["access_token"]
    shared_state["headers2"] = {"Authorization": f"Bearer {token2}"}

    db = SessionLocal()
    u1 = db.query(User).filter(User.email == USER_1_EMAIL).first()
    shared_state["user_1_id"] = u1.id
    db.close()

    # Create completed research session and report for User 1
    session_id, report_id = create_mock_report_in_db(u1.id, ticker="AAPL")
    shared_state["session_1_id"] = session_id
    shared_state["report_1_id"] = report_id

    yield

    # Clean up test sessions created for User 1
    db = SessionLocal()
    try:
        db.query(ResearchSession).filter(ResearchSession.user_id == u1.id).delete()
        db.commit()
    finally:
        db.close()


# -------------------------------------------------------------------------
# Unit Tests: Market Data Cache
# -------------------------------------------------------------------------

def test_cache_set_and_get():
    """Verify storing and retrieving data from MarketDataCache."""
    cache = MarketDataCache(default_ttl_seconds=10)
    data = get_mock_market_data("TSLA", 220.00)

    assert cache.get("TSLA") is None
    cache.set("TSLA", data)
    retrieved = cache.get("TSLA")

    assert retrieved is not None
    assert retrieved.ticker == "TSLA"
    assert retrieved.price.current_price == 220.00
    assert cache.size() == 1


def test_cache_expiration():
    """Verify expired cache entries return None and are evicted."""
    cache = MarketDataCache(default_ttl_seconds=1)
    data = get_mock_market_data("NVDA", 130.00)

    cache.set("NVDA", data, ttl_seconds=1)
    assert cache.get("NVDA") is not None

    time.sleep(1.05)
    assert cache.get("NVDA") is None
    assert cache.size() == 0


def test_cache_never_caches_invalid_data():
    """Verify cache rejects None or incomplete market data."""
    cache = MarketDataCache()
    cache.set("BAD", None)  # type: ignore
    assert cache.get("BAD") is None

    # Missing current_price
    incomplete = get_mock_market_data("INC")
    incomplete.price.current_price = None
    cache.set("INC", incomplete)
    assert cache.get("INC") is None


def test_cache_thread_safety_concurrent_access():
    """Verify thread-safety of MarketDataCache under concurrent multi-threaded reads/writes."""
    cache = MarketDataCache(default_ttl_seconds=60)
    data = get_mock_market_data("GOOGL", 175.00)

    errors = []

    def worker(idx: int):
        try:
            for i in range(25):
                ticker = f"TICK{idx}_{i % 5}"
                cache.set(ticker, data)
                res = cache.get(ticker)
                assert res is not None
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Concurrent cache operations produced errors: {errors}"
    assert cache.size() > 0


# -------------------------------------------------------------------------
# Unit Tests: Report Exporter
# -------------------------------------------------------------------------

def test_report_exporter_json():
    """Verify ReportExporter.export_json returns structured, serializable metadata."""
    db: Session = SessionLocal()
    try:
        report = db.query(ResearchReport).filter(ResearchReport.id == shared_state["report_1_id"]).first()
        data = ReportExporter.export_json(report)

        assert "metadata" in data
        assert data["metadata"]["ticker"] == "AAPL"
        assert "summary" in data
        assert data["summary"]["recommendation"] == "BUY"
        assert data["summary"]["confidence_score"] == 0.85
        assert "specialist_analyses" in data
        assert "market_research" in data["specialist_analyses"]
        assert "fundamental_analysis" in data["specialist_analyses"]
        assert "technical_analysis" in data["specialist_analyses"]
        assert "sentiment_analysis" in data["specialist_analyses"]
        assert "risk_analysis" in data["specialist_analyses"]
        assert "disclaimer" in data
    finally:
        db.close()


def test_report_exporter_markdown():
    """Verify ReportExporter.export_markdown generates clean Markdown with all 5 sections and disclaimer."""
    db: Session = SessionLocal()
    try:
        report = db.query(ResearchReport).filter(ResearchReport.id == shared_state["report_1_id"]).first()
        md = ReportExporter.export_markdown(report)

        assert "# Institutional Equity Research: AAPL Technologies (AAPL)" in md
        assert "Consensus Recommendation" in md
        assert "1. Market Positioning & Industry Dynamics" in md
        assert "2. Fundamental Health & Valuation Assessment" in md
        assert "3. Technical Momentum & Key Levels" in md
        assert "4. Market Sentiment & Media Digest" in md
        assert "5. Downside Risk Analysis & Bear Case" in md
        assert "Regulatory & Investment Disclaimer" in md
    finally:
        db.close()


def test_report_exporter_html_sanitization():
    """Verify ReportExporter.export_html properly sanitizes dynamic content against XSS/HTML injection."""
    db: Session = SessionLocal()
    try:
        report = db.query(ResearchReport).filter(ResearchReport.id == shared_state["report_1_id"]).first()
        # Test with potentially unsafe company name
        report.company_name = "<script>alert('xss')</script> Test Corp"
        html_out = ReportExporter.export_html(report)

        assert "<!DOCTYPE html>" in html_out
        assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in html_out
        assert "<script>alert" not in html_out  # Script tag must not exist unescaped
        assert "Legal Notice" in html_out
    finally:
        db.close()


def test_report_exporter_pdf_genuine_generation():
    """Verify ReportExporter.export_pdf creates a genuine binary PDF conforming to PDF-1.7 standard."""
    db: Session = SessionLocal()
    try:
        report = db.query(ResearchReport).filter(ResearchReport.id == shared_state["report_1_id"]).first()
        pdf_bytes = ReportExporter.export_pdf(report)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000
        assert pdf_bytes.startswith(b"%PDF-")
        assert b"%%EOF" in pdf_bytes
    finally:
        db.close()


# -------------------------------------------------------------------------
# Integration Tests: GET /api/research/sessions/{id}/export API
# -------------------------------------------------------------------------

def test_api_export_all_formats_authenticated():
    """Verify GET /api/research/sessions/{id}/export delivers Markdown, JSON, HTML, and PDF."""
    session_id = shared_state["session_1_id"]

    # 1. Markdown
    res_md = client.get(
        f"/api/research/sessions/{session_id}/export?format=markdown",
        headers=shared_state["headers1"],
    )
    assert res_md.status_code == 200
    assert "text/markdown" in res_md.headers["content-type"]
    assert "attachment" in res_md.headers["content-disposition"]
    assert "# Institutional Equity Research" in res_md.text

    # 2. JSON
    res_json = client.get(
        f"/api/research/sessions/{session_id}/export?format=json",
        headers=shared_state["headers1"],
    )
    assert res_json.status_code == 200
    assert "application/json" in res_json.headers["content-type"]
    assert res_json.json()["summary"]["recommendation"] == "BUY"

    # 3. HTML
    res_html = client.get(
        f"/api/research/sessions/{session_id}/export?format=html",
        headers=shared_state["headers1"],
    )
    assert res_html.status_code == 200
    assert "text/html" in res_html.headers["content-type"]
    assert "<!DOCTYPE html>" in res_html.text

    # 4. PDF
    res_pdf = client.get(
        f"/api/research/sessions/{session_id}/export?format=pdf",
        headers=shared_state["headers1"],
    )
    assert res_pdf.status_code == 200
    assert "application/pdf" in res_pdf.headers["content-type"]
    assert "attachment" in res_pdf.headers["content-disposition"]
    assert res_pdf.content.startswith(b"%PDF-")


def test_api_export_unauthenticated_rejected():
    """Verify export endpoint strictly rejects unauthenticated calls with 401."""
    session_id = shared_state["session_1_id"]
    res = client.get(f"/api/research/sessions/{session_id}/export?format=pdf")
    assert res.status_code == 401


def test_api_export_cross_user_isolation():
    """Verify User 2 CANNOT export User 1's research reports (403 Forbidden)."""
    user1_session_id = shared_state["session_1_id"]
    res = client.get(
        f"/api/research/sessions/{user1_session_id}/export?format=pdf",
        headers=shared_state["headers2"],
    )
    assert res.status_code == 403
    assert "do not own" in res.json()["detail"].lower()


def test_api_export_pending_session_rejected():
    """Verify export endpoint rejects sessions that are not COMPLETED (400 Bad Request)."""
    # Create pending session
    res_create = client.post(
        "/api/research/sessions",
        json={"ticker": "AMD"},
        headers=shared_state["headers1"],
    )
    assert res_create.status_code == 201
    pending_id = res_create.json()["id"]

    res_exp = client.get(
        f"/api/research/sessions/{pending_id}/export?format=markdown",
        headers=shared_state["headers1"],
    )
    assert res_exp.status_code == 400
    assert "only completed reports can be exported" in res_exp.json()["detail"].lower()
