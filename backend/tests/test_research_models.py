from datetime import datetime, timezone
import pytest
from sqlalchemy import text
from app.database import SessionLocal
from app.models.research import ResearchReport, ResearchSession
from app.models.user import User


def test_research_models_crud_and_cascade():
    """Verify ResearchSession and ResearchReport models, relationships, and cascade operations."""
    db = SessionLocal()
    try:
        # 1. Fetch an existing user (e.g., Demo Trader or Sarah Market)
        user = db.query(User).filter(User.id == 8).first()
        if not user:
            user = db.query(User).first()
        assert user is not None, "At least one user must exist in the database."

        # 2. Create a ResearchSession
        session = ResearchSession(
            user_id=user.id,
            ticker="AAPL",
            company_name="Apple Inc.",
            status="PENDING",
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        assert session.id is not None
        assert session.status == "PENDING"
        assert session.ticker == "AAPL"
        assert session.user_id == user.id
        session_id = session.id

        # 3. Create a ResearchReport linked to the session
        report = ResearchReport(
            session_id=session.id,
            ticker="AAPL",
            company_name="Apple Inc.",
            current_price=225.50,
            target_price=260.00,
            recommendation="BUY",
            confidence_score=0.88,
            executive_summary="Strong ecosystem with expanding service revenue and solid balance sheet.",
            fundamental_data={
                "pe_ratio": 32.4,
                "revenue_growth": 0.06,
                "gross_margin": 0.46,
                "valuation_status": "Fairly Valued",
            },
            technical_data={
                "rsi_14": 58.2,
                "above_200_sma": True,
                "trend": "Bullish",
            },
            sentiment_data={
                "sentiment_index": 0.65,
                "news_count": 15,
                "catalysts": ["AI product expansion", "Services segment growth"],
            },
            risk_data={
                "risk_level": "Medium",
                "bear_case_target": 190.00,
                "critical_risks": ["China hardware competition", "Regulatory app store scrutiny"],
            },
        )
        db.add(report)

        # Update session status to COMPLETED
        session.status = "COMPLETED"
        session.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(report)
        db.refresh(session)

        assert report.id is not None
        assert report.session_id == session_id
        assert report.recommendation == "BUY"
        assert report.fundamental_data["pe_ratio"] == 32.4
        assert report.technical_data["trend"] == "Bullish"
        assert report.sentiment_data["sentiment_index"] == 0.65
        assert report.risk_data["risk_level"] == "Medium"

        # 4. Test relationship navigation
        assert session.report.id == report.id
        assert report.session.id == session.id

        # 5. Test query by user_id
        user_sessions = db.query(ResearchSession).filter(ResearchSession.user_id == user.id).all()
        assert any(s.id == session_id for s in user_sessions)

        # 6. Test Cascade Delete: deleting session must automatically delete the report
        report_id = report.id
        db.delete(session)
        db.commit()

        # Verify session is deleted
        deleted_session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
        assert deleted_session is None

        # Verify report was automatically cascade-deleted
        deleted_report = db.query(ResearchReport).filter(ResearchReport.id == report_id).first()
        assert deleted_report is None

    finally:
        db.close()

