import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional
from sqlalchemy.orm import Session
from app.models.research import ResearchReport, ResearchSession
from app.schemas.agent_outputs import (
    FinancialAnalysisOutput,
    MarketResearchOutput,
    RiskAnalysisOutput,
    SentimentAnalysisOutput,
    TechnicalAnalysisOutput,
)
from app.schemas.market_data import StockMarketData
from app.services.agents import (
    FinancialAnalysisAgent,
    MarketResearchAgent,
    RiskAnalysisAgent,
    SentimentAnalysisAgent,
    TechnicalAnalysisAgent,
)
from app.services.market_data import fetch_stock_market_data
from app.services.market_data_cache import get_cached_stock_market_data

logger = logging.getLogger("fincrew.orchestrator")


class ResearchOrchestrator:
    """
    Coordinates the multi-agent stock research pipeline.
    
    Responsibilities:
    1. Orchestrates market data retrieval without data fabrication.
    2. Runs five independent specialist AI agents:
       - Market Research Agent
       - Financial Analysis Agent
       - Technical Analysis Agent
       - Sentiment Analysis Agent
       - Risk Analysis Agent
    3. Handles individual agent failures gracefully without crashing the pipeline.
    4. Synthesizes consensus recommendation, target price, confidence score, and executive narrative.
    5. Persists research sessions and reports to PostgreSQL.
    """

    def __init__(
        self,
        market_agent: Optional[MarketResearchAgent] = None,
        financial_agent: Optional[FinancialAnalysisAgent] = None,
        technical_agent: Optional[TechnicalAnalysisAgent] = None,
        sentiment_agent: Optional[SentimentAnalysisAgent] = None,
        risk_agent: Optional[RiskAnalysisAgent] = None,
        market_data_service: Optional[Callable[[str], StockMarketData]] = None,
    ):
        self.market_agent = market_agent or MarketResearchAgent()
        self.financial_agent = financial_agent or FinancialAnalysisAgent()
        self.technical_agent = technical_agent or TechnicalAnalysisAgent()
        self.sentiment_agent = sentiment_agent or SentimentAnalysisAgent()
        self.risk_agent = risk_agent or RiskAnalysisAgent()
        self.market_data_service = market_data_service or get_cached_stock_market_data

    def run(self, session_id: int, db: Session) -> Optional[ResearchReport]:
        """
        Executes the full stock research pipeline for an existing ResearchSession.
        Updates session status through IN_PROGRESS to COMPLETED or FAILED.
        """
        session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
        if not session:
            raise ValueError(f"Research session with ID {session_id} not found.")

        ticker = session.ticker

        # 1. Update session status to IN_PROGRESS
        session.status = "IN_PROGRESS"
        session.error_message = None
        db.commit()
        db.refresh(session)
        logger.info("Started research pipeline for session %d (Ticker: %s)", session.id, ticker)

        # 2. Acquire real market data
        try:
            market_data = self.market_data_service(ticker)
        except Exception as exc:
            error_msg = f"Failed to acquire market data: {str(exc)}"
            logger.error("Market data retrieval failed for session %d (%s): %s", session.id, ticker, exc)
            session.status = "FAILED"
            session.error_message = error_msg
            session.completed_at = datetime.now(timezone.utc)
            db.commit()
            return None

        # Record verified company name
        session.company_name = market_data.profile.company_name or ticker
        db.commit()

        # 3. Execute Specialist Agents with Independent Fault Tolerance
        market_output = self._run_market_agent(market_data, ticker, session.company_name)
        financial_output = self._run_financial_agent(market_data, ticker)
        technical_output = self._run_technical_agent(market_data, ticker)
        sentiment_output = self._run_sentiment_agent(market_data, ticker)
        risk_output = self._run_risk_agent(market_data, ticker)

        # 4. Synthesize Consensus Investment Decision
        recommendation = self._synthesize_recommendation(
            financial_output, technical_output, sentiment_output, risk_output
        )

        current_price = market_data.price.current_price
        target_price = self._calculate_target_price(
            current_price=current_price,
            recommendation=recommendation,
            technical_output=technical_output,
        )

        confidence_score = self._calculate_consensus_confidence([
            market_output.confidence_level,
            financial_output.confidence_level,
            technical_output.confidence_level,
            sentiment_output.confidence_level,
            risk_output.confidence_level,
        ])

        executive_summary = self._generate_executive_summary(
            session=session,
            market_data=market_data,
            recommendation=recommendation,
            target_price=target_price,
            confidence_score=confidence_score,
            market_output=market_output,
            financial_output=financial_output,
            technical_output=technical_output,
            sentiment_output=sentiment_output,
            risk_output=risk_output,
        )

        # 5. Persist Research Report in PostgreSQL
        # Remove any stale report for this session if rerun
        existing_report = (
            db.query(ResearchReport)
            .filter(ResearchReport.session_id == session.id)
            .first()
        )
        if existing_report:
            db.delete(existing_report)
            db.flush()

        # Bundle fundamental data with market research payload
        fundamental_payload = financial_output.model_dump()
        fundamental_payload["market_research"] = market_output.model_dump()

        report = ResearchReport(
            session_id=session.id,
            ticker=ticker,
            company_name=session.company_name or ticker,
            current_price=current_price,
            target_price=target_price,
            recommendation=recommendation,
            confidence_score=confidence_score,
            executive_summary=executive_summary,
            fundamental_data=fundamental_payload,
            technical_data=technical_output.model_dump(),
            sentiment_data=sentiment_output.model_dump(),
            risk_data=risk_output.model_dump(),
        )
        db.add(report)

        # 6. Mark Session COMPLETED
        session.status = "COMPLETED"
        session.error_message = None
        session.completed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(session)
        db.refresh(report)

        logger.info(
            "Research pipeline completed successfully for session %d (%s): %s",
            session.id,
            ticker,
            recommendation,
        )
        return report

    # -------------------------------------------------------------------------
    # Fault-tolerant Agent Runners
    # -------------------------------------------------------------------------

    def _run_market_agent(
        self, market_data: StockMarketData, ticker: str, company_name: str
    ) -> MarketResearchOutput:
        try:
            return self.market_agent.analyze(market_data)
        except Exception as exc:
            logger.warning("MarketResearchAgent failed for %s: %s", ticker, exc)
            return MarketResearchOutput(
                agent_name="Market Research Specialist",
                ticker=ticker,
                company_name=company_name or ticker,
                sector=market_data.profile.sector,
                industry=market_data.profile.industry,
                market_cap_category="Unknown",
                analysis=f"Market research analysis could not be completed: {str(exc)}",
                key_findings=["Agent encountered an execution error."],
                supporting_data={"error": str(exc)},
                warnings_and_limitations=["Analysis incomplete due to agent failure."],
                confidence_level=0.0,
            )

    def _run_financial_agent(
        self, market_data: StockMarketData, ticker: str
    ) -> FinancialAnalysisOutput:
        try:
            return self.financial_agent.analyze(market_data)
        except Exception as exc:
            logger.warning("FinancialAnalysisAgent failed for %s: %s", ticker, exc)
            return FinancialAnalysisOutput(
                agent_name="Financial Analysis Specialist",
                valuation_status="INSUFFICIENT_DATA",
                profitability_grade="LOW",
                solvency_risk="INSUFFICIENT_DATA",
                analysis=f"Financial fundamental analysis could not be completed: {str(exc)}",
                key_findings=["Agent encountered an execution error."],
                supporting_data={"error": str(exc)},
                warnings_and_limitations=["Analysis incomplete due to agent failure."],
                confidence_level=0.0,
            )

    def _run_technical_agent(
        self, market_data: StockMarketData, ticker: str
    ) -> TechnicalAnalysisOutput:
        try:
            return self.technical_agent.analyze(market_data)
        except Exception as exc:
            logger.warning("TechnicalAnalysisAgent failed for %s: %s", ticker, exc)
            return TechnicalAnalysisOutput(
                agent_name="Technical Analysis Specialist",
                trend_direction="NEUTRAL",
                momentum_state="NEUTRAL",
                key_support=None,
                key_resistance=None,
                analysis=f"Technical analysis could not be completed: {str(exc)}",
                key_findings=["Agent encountered an execution error."],
                supporting_data={"error": str(exc)},
                warnings_and_limitations=["Analysis incomplete due to agent failure."],
                confidence_level=0.0,
            )

    def _run_sentiment_agent(
        self, market_data: StockMarketData, ticker: str
    ) -> SentimentAnalysisOutput:
        try:
            return self.sentiment_agent.analyze(market_data)
        except Exception as exc:
            logger.warning("SentimentAnalysisAgent failed for %s: %s", ticker, exc)
            return SentimentAnalysisOutput(
                agent_name="Sentiment Analysis Specialist",
                sentiment_score=0.0,
                sentiment_label="NEUTRAL",
                positive_catalysts=[],
                negative_concerns=[],
                news_sample_size=0,
                analysis=f"Sentiment analysis could not be completed: {str(exc)}",
                key_findings=["Agent encountered an execution error."],
                supporting_data={"error": str(exc)},
                warnings_and_limitations=["Analysis incomplete due to agent failure."],
                confidence_level=0.0,
            )

    def _run_risk_agent(
        self, market_data: StockMarketData, ticker: str
    ) -> RiskAnalysisOutput:
        try:
            return self.risk_agent.analyze(market_data)
        except Exception as exc:
            logger.warning("RiskAnalysisAgent failed for %s: %s", ticker, exc)
            return RiskAnalysisOutput(
                agent_name="Risk Analysis Specialist",
                risk_level="HIGH",
                risk_score=7.0,
                primary_risk_factors=["Risk analysis execution failed."],
                bear_case_scenario="Risk assessment could not be finalized due to agent execution error.",
                analysis=f"Risk analysis could not be completed: {str(exc)}",
                key_findings=["Agent encountered an execution error."],
                supporting_data={"error": str(exc)},
                warnings_and_limitations=["Analysis incomplete due to agent failure."],
                confidence_level=0.0,
            )

    # -------------------------------------------------------------------------
    # Consensus Synthesis Logic
    # -------------------------------------------------------------------------

    def _synthesize_recommendation(
        self,
        fin: FinancialAnalysisOutput,
        tech: TechnicalAnalysisOutput,
        sent: SentimentAnalysisOutput,
        risk: RiskAnalysisOutput,
    ) -> str:
        """
        Synthesizes a consensus equity recommendation across fundamental, technical,
        sentiment, and risk vectors with capital preservation guardrails.
        """
        score = 0.0

        # 1. Valuation weighting
        if fin.valuation_status == "UNDERVALUED":
            score += 2.0
        elif fin.valuation_status == "FAIRLY_VALUED":
            score += 0.5
        elif fin.valuation_status == "OVERVALUED":
            score -= 1.5
        elif fin.valuation_status == "SPECULATIVE":
            score -= 1.0

        # 2. Profitability weighting
        if fin.profitability_grade == "HIGH":
            score += 1.0
        elif fin.profitability_grade == "MODERATE":
            score += 0.2
        elif fin.profitability_grade == "NEGATIVE":
            score -= 1.0

        # 3. Technical Momentum weighting
        if tech.trend_direction == "BULLISH":
            score += 1.5
        elif tech.trend_direction == "BEARISH":
            score -= 1.5

        # 4. Sentiment weighting (-1.0 to 1.0 scaled)
        score += round(sent.sentiment_score * 1.5, 2)

        # 5. Risk deduction
        if risk.risk_level == "LOW":
            score += 0.5
        elif risk.risk_level == "HIGH":
            score -= 1.0
        elif risk.risk_level == "CRITICAL":
            score -= 2.5

        # Map composite score to recommendation
        if score >= 3.0:
            rec = "STRONG_BUY"
        elif score >= 1.0:
            rec = "BUY"
        elif score >= -1.0:
            rec = "HOLD"
        elif score >= -3.0:
            rec = "SELL"
        else:
            rec = "STRONG_SELL"

        # Capital preservation guardrail: critical risk downgrades aggressive buys
        if risk.risk_level == "CRITICAL" and rec in ("STRONG_BUY", "BUY"):
            rec = "HOLD"

        return rec

    def _calculate_target_price(
        self,
        current_price: Optional[float],
        recommendation: str,
        technical_output: TechnicalAnalysisOutput,
    ) -> Optional[float]:
        """
        Calculates an objective price target grounded in real technical levels
        or standard scenario thresholds. Never fabricates figures.
        """
        if current_price is None or current_price <= 0:
            return None

        if recommendation in ("STRONG_BUY", "BUY"):
            if technical_output.key_resistance and technical_output.key_resistance > current_price:
                return round(technical_output.key_resistance, 2)
            return round(current_price * 1.15, 2)
        elif recommendation == "HOLD":
            return round(current_price, 2)
        elif recommendation in ("SELL", "STRONG_SELL"):
            if technical_output.key_support and technical_output.key_support < current_price:
                return round(technical_output.key_support, 2)
            return round(current_price * 0.85, 2)

        return round(current_price, 2)

    def _calculate_consensus_confidence(self, confidences: list[float]) -> float:
        """Calculates arithmetic mean confidence across all specialists."""
        if not confidences:
            return 0.5
        return round(sum(confidences) / len(confidences), 2)

    def _generate_executive_summary(
        self,
        session: ResearchSession,
        market_data: StockMarketData,
        recommendation: str,
        target_price: Optional[float],
        confidence_score: float,
        market_output: MarketResearchOutput,
        financial_output: FinancialAnalysisOutput,
        technical_output: TechnicalAnalysisOutput,
        sentiment_output: SentimentAnalysisOutput,
        risk_output: RiskAnalysisOutput,
    ) -> str:
        """Compiles a synthesized executive committee briefing."""
        current_price = market_data.price.current_price
        price_str = f"${current_price:.2f}" if current_price is not None else "N/A"
        target_str = f"${target_price:.2f}" if target_price is not None else "N/A"
        confidence_pct = int(confidence_score * 100)

        parts = [
            f"FinCrew Investment Committee Consensus for {session.company_name} ({session.ticker}).",
            f"Consensus Rating: {recommendation} | Confidence Level: {confidence_pct}% | Current Price: {price_str} | Target Price: {target_str}.",
            f"1. Market Profile: {market_output.market_cap_category} capitalisation in the {market_output.sector or 'General'} sector ({market_output.industry or 'Diversified'}).",
            f"2. Fundamental Health: Evaluated as {financial_output.valuation_status.replace('_', ' ')} with {financial_output.profitability_grade} profitability margins and {financial_output.solvency_risk} solvency risk.",
            f"3. Technical Posture: Primary trend is {technical_output.trend_direction} with {technical_output.momentum_state} momentum (RSI-14: {market_data.technicals.rsi_14 or 'N/A'}).",
            f"4. Market Sentiment: Media tone is {sentiment_output.sentiment_label.replace('_', ' ')} based on {sentiment_output.news_sample_size} financial publications.",
            f"5. Risk Assessment: {risk_output.risk_level} risk classification (Score: {risk_output.risk_score:.1f}/10). Key vulnerability: {risk_output.bear_case_scenario}",
        ]

        if current_price and target_price:
            implied_pct = round(((target_price - current_price) / current_price) * 100, 1)
            parts.append(
                f"Investment Thesis: A 12-month target of {target_str} offers an implied price potential of {implied_pct:+.1f}%."
            )

        return "\n\n".join(parts)


def run_research_background(session_id: int) -> None:
    """
    Background worker task executed by FastAPI BackgroundTasks.
    Spawns an isolated database session, triggers the orchestrator,
    and guarantees proper database connection cleanup.
    """
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        orchestrator = ResearchOrchestrator()
        orchestrator.run(session_id=session_id, db=db)
    except Exception as exc:
        logger.exception("Unexpected background research failure for session %d: %s", session_id, exc)
        try:
            session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
            if session:
                session.status = "FAILED"
                session.error_message = f"Background execution error: {str(exc)}"
                session.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()

