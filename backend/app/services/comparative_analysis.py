import logging
from typing import Any, Dict, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.research import ResearchReport, ResearchSession
from app.schemas.comparison import (
    ComparisonItem,
    ComparisonMatrixRow,
    ComparisonResponse,
)

logger = logging.getLogger("fincrew.comparative_analysis")


class ComparativeAnalysisService:
    """
    Evaluates and compares 2 to 5 completed equity research sessions side-by-side.
    Handles missing metrics as None without data fabrication.
    Enforces user data isolation and never initiates unwanted queries.
    """

    @classmethod
    def compare_sessions(
        cls,
        session_ids: List[int],
        user_id: int,
        db: Session,
    ) -> ComparisonResponse:
        # 1. Validate session count constraint (2 to 5)
        if not session_ids or len(session_ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Comparative analysis requires at least 2 research sessions to compare.",
            )
        if len(session_ids) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Comparative analysis supports a maximum of 5 research sessions simultaneously.",
            )

        # Preserve order while deduplicating
        unique_ids = list(dict.fromkeys(session_ids))
        if len(unique_ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Comparative analysis requires at least 2 distinct research session IDs.",
            )

        # 2. Query sessions from database
        sessions = (
            db.query(ResearchSession)
            .filter(ResearchSession.id.in_(unique_ids))
            .all()
        )
        found_map = {s.id: s for s in sessions}

        # Check for missing session IDs
        missing_ids = [sid for sid in unique_ids if sid not in found_map]
        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Research session(s) {missing_ids} not found.",
            )

        # 3. Enforce user ownership strictly
        foreign_ids = [sid for sid in unique_ids if found_map[sid].user_id != user_id]
        if foreign_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: You do not own research session(s) {foreign_ids}.",
            )

        # 4. Enforce session completion
        incomplete_ids = [
            sid
            for sid in unique_ids
            if found_map[sid].status != "COMPLETED" or not found_map[sid].report
        ]
        if incomplete_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Session(s) {incomplete_ids} are not completed. "
                    "Only successfully completed research reports can be compared."
                ),
            )

        # 5. Extract normalized metrics (preserving order of request)
        items: List[ComparisonItem] = []
        ordered_sessions = [found_map[sid] for sid in unique_ids]

        for s in ordered_sessions:
            rep: ResearchReport = s.report
            fun: Dict[str, Any] = rep.fundamental_data or {}
            mr: Dict[str, Any] = fun.get("market_research", {})
            tech: Dict[str, Any] = rep.technical_data or {}
            sent: Dict[str, Any] = rep.sentiment_data or {}
            risk: Dict[str, Any] = rep.risk_data or {}

            # Extract supporting figures if present without fabricating
            fun_sup = fun.get("supporting_data") or {}
            tech_sup = tech.get("supporting_data") or {}

            implied_upside = None
            if rep.target_price and rep.current_price and rep.current_price > 0:
                implied_upside = round(
                    ((rep.target_price - rep.current_price) / rep.current_price) * 100, 1
                )

            item = ComparisonItem(
                session_id=s.id,
                ticker=rep.ticker,
                company_name=rep.company_name,
                current_price=rep.current_price,
                target_price=rep.target_price,
                implied_upside_percent=implied_upside,
                recommendation=rep.recommendation,
                confidence_score=rep.confidence_score,
                valuation_status=fun.get("valuation_status"),
                pe_ratio=fun_sup.get("pe_ratio"),
                forward_pe=fun_sup.get("forward_pe"),
                price_to_book=fun_sup.get("price_to_book"),
                profitability_grade=fun.get("profitability_grade"),
                solvency_risk=fun.get("solvency_risk"),
                profit_margins=fun_sup.get("profit_margins"),
                operating_margins=fun_sup.get("operating_margins"),
                debt_to_equity=fun_sup.get("debt_to_equity"),
                total_cash=fun_sup.get("total_cash"),
                total_debt=fun_sup.get("total_debt"),
                free_cash_flow=fun_sup.get("free_cash_flow"),
                trend_direction=tech.get("trend_direction"),
                momentum_state=tech.get("momentum_state"),
                rsi_14=tech_sup.get("rsi_14"),
                key_support=tech.get("key_support"),
                key_resistance=tech.get("key_resistance"),
                sentiment_label=sent.get("sentiment_label"),
                sentiment_score=sent.get("sentiment_score"),
                risk_level=risk.get("risk_level"),
                risk_score=risk.get("risk_score"),
                sector=mr.get("sector"),
                industry=mr.get("industry"),
            )
            items.append(item)

        # 6. Build comparative side-by-side matrix
        matrix: List[ComparisonMatrixRow] = cls._build_matrix(items)

        logger.info(
            "Comparative analysis synthesized for %d equities (User: %d)",
            len(items),
            user_id,
        )
        return ComparisonResponse(
            total_compared=len(items),
            items=items,
            matrix=matrix,
        )

    @classmethod
    def _build_matrix(cls, items: List[ComparisonItem]) -> List[ComparisonMatrixRow]:
        """Constructs formatted side-by-side metric rows grouped by category."""
        rows: List[ComparisonMatrixRow] = []

        def make_row(cat: str, metric: str, attr: str, fmt: str = "raw") -> ComparisonMatrixRow:
            val_map = {}
            for item in items:
                v = getattr(item, attr, None)
                if v is None:
                    val_map[item.ticker] = None
                elif fmt == "currency":
                    val_map[item.ticker] = f"${v:,.2f}"
                elif fmt == "large_currency":
                    abs_v = abs(v)
                    sign = "-" if v < 0 else ""
                    if abs_v >= 1e12:
                        val_map[item.ticker] = f"{sign}${abs_v / 1e12:.2f}T USD"
                    elif abs_v >= 1e9:
                        val_map[item.ticker] = f"{sign}${abs_v / 1e9:.2f}B USD"
                    elif abs_v >= 1e6:
                        val_map[item.ticker] = f"{sign}${abs_v / 1e6:.2f}M USD"
                    elif abs_v >= 1e3:
                        val_map[item.ticker] = f"{sign}${abs_v / 1e3:.2f}K USD"
                    else:
                        val_map[item.ticker] = f"{sign}${abs_v:,.2f} USD"
                elif fmt == "margin_pct":
                    val_map[item.ticker] = f"{v * 100:.1f}%"
                elif fmt == "ratio_pct":
                    val_map[item.ticker] = f"{v:.2f}%"
                elif fmt == "multiple":
                    val_map[item.ticker] = f"{v:.2f}x"
                elif fmt == "percent":
                    val_map[item.ticker] = f"{v:+.1f}%"
                elif fmt == "confidence":
                    val_map[item.ticker] = f"{int(v * 100)}%"
                elif fmt == "score_10":
                    val_map[item.ticker] = f"{v:.1f}/10"
                else:
                    val_map[item.ticker] = v
            return ComparisonMatrixRow(category=cat, metric=metric, values=val_map)

        # Category 1: Committee Consensus
        rows.append(make_row("Consensus", "Recommendation", "recommendation"))
        rows.append(make_row("Consensus", "Confidence Level", "confidence_score", fmt="confidence"))
        rows.append(make_row("Consensus", "Current Price", "current_price", fmt="currency"))
        rows.append(make_row("Consensus", "12-Mo Target Price", "target_price", fmt="currency"))
        rows.append(make_row("Consensus", "Implied Change %", "implied_upside_percent", fmt="percent"))

        # Category 2: Market Classification
        rows.append(make_row("Classification", "Sector", "sector"))
        rows.append(make_row("Classification", "Industry", "industry"))

        # Category 3: Valuation & Fundamentals
        rows.append(make_row("Valuation", "Valuation Status", "valuation_status"))
        rows.append(make_row("Valuation", "Profitability Grade", "profitability_grade"))
        rows.append(make_row("Valuation", "Solvency Risk", "solvency_risk"))
        rows.append(make_row("Valuation", "Trailing P/E Ratio", "pe_ratio"))
        rows.append(make_row("Valuation", "Forward P/E Ratio", "forward_pe"))
        rows.append(make_row("Valuation", "Price to Book (P/B)", "price_to_book"))
        rows.append(make_row("Valuation", "Free Cash Flow", "free_cash_flow", fmt="large_currency"))
        rows.append(make_row("Valuation", "Total Cash", "total_cash", fmt="large_currency"))
        rows.append(make_row("Valuation", "Total Debt", "total_debt", fmt="large_currency"))
        rows.append(make_row("Valuation", "Debt to Equity", "debt_to_equity", fmt="ratio_pct"))
        rows.append(make_row("Valuation", "Profit Margin", "profit_margins", fmt="margin_pct"))
        rows.append(make_row("Valuation", "Operating Margin", "operating_margins", fmt="margin_pct"))

        # Category 4: Technical Posture
        rows.append(make_row("Technicals", "Trend Direction", "trend_direction"))
        rows.append(make_row("Technicals", "Momentum State", "momentum_state"))
        rows.append(make_row("Technicals", "RSI (14-Day)", "rsi_14"))
        rows.append(make_row("Technicals", "Support Level", "key_support", fmt="currency"))
        rows.append(make_row("Technicals", "Resistance Level", "key_resistance", fmt="currency"))

        # Category 5: Sentiment & Media
        rows.append(make_row("Sentiment", "Media Tone", "sentiment_label"))
        rows.append(make_row("Sentiment", "Sentiment Score (-1 to +1)", "sentiment_score"))

        # Category 6: Risk Profile
        rows.append(make_row("Risk", "Risk Classification", "risk_level"))
        rows.append(make_row("Risk", "Risk Severity Score", "risk_score", fmt="score_10"))

        return rows
