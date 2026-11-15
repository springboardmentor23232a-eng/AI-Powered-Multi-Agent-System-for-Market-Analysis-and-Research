import logging
from collections import Counter
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.research import ResearchReport, ResearchSession
from app.schemas.analytics import WorkspaceSummaryResponse

logger = logging.getLogger("fincrew.analytics")


class WorkspaceAnalyticsService:
    """
    Computes portfolio and research workspace analytics for the authenticated user.
    Safely handles empty workspaces without division by zero or runtime errors.
    Strictly queries data belonging to the requested user_id.
    """

    @classmethod
    def get_user_summary(cls, user_id: int, db: Session) -> WorkspaceSummaryResponse:
        # 1. Fetch all research sessions for the authenticated user
        sessions = (
            db.query(ResearchSession)
            .filter(ResearchSession.user_id == user_id)
            .order_by(ResearchSession.created_at.desc())
            .all()
        )

        total_sessions = len(sessions)
        if total_sessions == 0:
            logger.info("Computed workspace summary for user %d (Empty workspace)", user_id)
            return WorkspaceSummaryResponse()

        # 2. Status counts
        status_counts = {"pending": 0, "in_progress": 0, "completed": 0, "failed": 0}
        for s in sessions:
            st = (s.status or "").lower()
            if st in status_counts:
                status_counts[st] += 1
            else:
                status_counts[st] = 1

        # 3. Analyze completed reports
        completed_sessions = [s for s in sessions if s.status == "COMPLETED" and s.report]
        
        rec_dist = {
            "STRONG_BUY": 0,
            "BUY": 0,
            "HOLD": 0,
            "SELL": 0,
            "STRONG_SELL": 0,
        }
        rec_summary = {"buy": 0, "hold": 0, "sell": 0}
        confidence_values: List[float] = []
        sector_counter: Counter = Counter()

        for s in completed_sessions:
            rep: ResearchReport = s.report

            # Recommendation
            rec = (rep.recommendation or "").upper()
            if rec in rec_dist:
                rec_dist[rec] += 1

            if "BUY" in rec:
                rec_summary["buy"] += 1
            elif "SELL" in rec:
                rec_summary["sell"] += 1
            elif "HOLD" in rec:
                rec_summary["hold"] += 1

            # Confidence score
            if rep.confidence_score is not None:
                confidence_values.append(float(rep.confidence_score))

            # Sector
            fun = rep.fundamental_data or {}
            mr = fun.get("market_research") or {}
            sec = mr.get("sector")
            if sec and str(sec).strip():
                sector_counter[str(sec).strip()] += 1
            else:
                sector_counter["Unclassified"] += 1

        # 4. Averages and percentages
        avg_confidence = 0.0
        if confidence_values:
            avg_confidence = round(sum(confidence_values) / len(confidence_values), 2)

        sector_allocation = dict(sector_counter.most_common())
        total_sectors = sum(sector_allocation.values())
        sector_percentages = {}
        if total_sectors > 0:
            for sec_name, count in sector_allocation.items():
                sector_percentages[sec_name] = round((count / total_sectors) * 100, 1)

        latest_activity = sessions[0].created_at if sessions else None

        logger.info(
            "Computed workspace summary for user %d (%d total sessions, %d completed)",
            user_id,
            total_sessions,
            len(completed_sessions),
        )

        return WorkspaceSummaryResponse(
            total_sessions=total_sessions,
            status_counts=status_counts,
            recommendation_distribution=rec_dist,
            recommendation_summary=rec_summary,
            average_confidence=avg_confidence,
            sector_allocation=sector_allocation,
            sector_percentages=sector_percentages,
            latest_activity_at=latest_activity,
        )
