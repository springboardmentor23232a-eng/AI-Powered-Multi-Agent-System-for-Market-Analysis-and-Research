import abc
import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.agent_result import AgentResult
from app.models.research_report import ResearchReport
from app.models.research_task import ResearchTask
from app.models.source_document import SourceDocument
from app.services.agents import (
    BaseResearchAgent,
    FundamentalAnalysisAgent,
    TechnicalAnalysisAgent,
)
from app.services.market_data_service import MarketDataCollector

logger = logging.getLogger(__name__)


class MultiAgentResearchCoordinatorInterface(abc.ABC):
    """
    Orchestration interface for the multi-agent stock analysis system.
    """

    @abc.abstractmethod
    def register_agent(self, agent: BaseResearchAgent) -> None:
        pass

    @abc.abstractmethod
    async def run_pipeline(self, task: ResearchTask) -> Dict[str, Any]:
        pass


class DefaultResearchEngine(MultiAgentResearchCoordinatorInterface):
    """
    Multi-Agent Research Coordinator executing:
    1. Market Data Collection & Validation (Module 2)
    2. Fundamental Analysis Agent (Module 3)
    3. Technical Analysis Agent (Module 4)
    4. Structured Report Synthesis with Provenance & Limitations
    """

    def __init__(self):
        self._agents: Dict[str, BaseResearchAgent] = {}
        self.register_agent(FundamentalAnalysisAgent())
        self.register_agent(TechnicalAnalysisAgent())

    def register_agent(self, agent: BaseResearchAgent) -> None:
        self._agents[agent.agent_name] = agent

    async def run_pipeline(self, task: ResearchTask, include_peers: bool = True) -> Dict[str, Any]:
        agent_records: List[Dict[str, Any]] = []

        # Step 1: Market Data Collection & Validation
        t0 = time.perf_counter()
        market_data = MarketDataCollector.collect_market_data(
            ticker=task.ticker,
            market=task.market,
            period=task.analysis_period,
            include_warmup=True,
        )
        collector_ms = int((time.perf_counter() - t0) * 1000)

        profile = market_data["profile"]
        perf = market_data["period_performance"]
        data_quality = market_data["data_quality"]
        sources = market_data["sources"]

        agent_records.append({
            "agent_id": "market_data_collector",
            "role": "Market Data Collection & Validation",
            "status": "COMPLETED",
            "execution_time_ms": collector_ms,
            "summary": (
                f"Collected {data_quality['valid_rows']} validated OHLCV bars, company profile, and "
                f"financial statements ({data_quality['quality_status']})."
            ),
            "output": {
                "profile": profile,
                "period_performance": perf,
                "data_quality": data_quality,
            },
        })

        # Step 2: Fundamental Analysis Agent
        fundamental_agent: FundamentalAnalysisAgent = self._agents["fundamental_analysis_agent"]
        t1 = time.perf_counter()
        fundamental_result: Dict[str, Any] = {}
        fund_status = "COMPLETED"
        fund_err: Optional[str] = None
        try:
            fundamental_result = await fundamental_agent.analyze(
                ticker=task.ticker,
                market=task.market,
                period=task.analysis_period,
                market_data=market_data,
                include_peers=include_peers,
            )
        except Exception as e:
            logger.exception(f"Fundamental agent failed for {task.ticker}: {e}")
            fund_status = "FAILED"
            fund_err = str(e)
        fund_ms = int((time.perf_counter() - t1) * 1000)

        agent_records.append({
            "agent_id": fundamental_agent.agent_name,
            "role": "Fundamental Analysis Agent",
            "status": fund_status,
            "execution_time_ms": fund_ms,
            "error_message": fund_err,
            "summary": (
                fundamental_result.get("explanation")
                if fund_status == "COMPLETED"
                else f"Fundamental analysis encountered an error: {fund_err}"
            ),
            "output": fundamental_result if fund_status == "COMPLETED" else None,
        })

        # Step 3: Technical Analysis Agent
        technical_agent: TechnicalAnalysisAgent = self._agents["technical_analysis_agent"]
        t2 = time.perf_counter()
        technical_result: Dict[str, Any] = {}
        tech_status = "COMPLETED"
        tech_err: Optional[str] = None
        try:
            technical_result = await technical_agent.analyze(
                ticker=task.ticker,
                market=task.market,
                period=task.analysis_period,
                market_data=market_data,
            )
        except Exception as e:
            logger.exception(f"Technical agent failed for {task.ticker}: {e}")
            tech_status = "FAILED"
            tech_err = str(e)
        tech_ms = int((time.perf_counter() - t2) * 1000)

        agent_records.append({
            "agent_id": technical_agent.agent_name,
            "role": "Technical Analysis Agent",
            "status": tech_status,
            "execution_time_ms": tech_ms,
            "error_message": tech_err,
            "summary": (
                technical_result.get("explanation")
                if tech_status == "COMPLETED"
                else f"Technical analysis encountered an error: {tech_err}"
            ),
            "output": technical_result if tech_status == "COMPLETED" else None,
        })

        # Step 4: Compile limitations & executive summary
        all_limitations: List[str] = []
        all_limitations.extend(data_quality.get("notes", []))
        all_limitations.extend(fundamental_result.get("data_gaps", []))
        all_limitations.extend(technical_result.get("data_limitations", []))
        if technical_result.get("disclaimer"):
            all_limitations.append(technical_result["disclaimer"])

        exec_summary_parts = [
            f"{profile.get('company_name', task.ticker)} ({task.ticker}, {task.market}) — {task.analysis_period} Analysis:",
        ]
        if perf.get("change_percent") is not None:
            exec_summary_parts.append(f"Period return: {perf['change_percent']:+.2f}%.")
        if fundamental_result.get("explanation"):
            exec_summary_parts.append(fundamental_result["explanation"])
        if technical_result.get("trend_summary", {}).get("overall_signal"):
            exec_summary_parts.append(
                f"Technical posture: {technical_result['trend_summary']['overall_signal']}."
            )
        executive_summary = " ".join(exec_summary_parts)

        agent_records.append({
            "agent_id": "synthesis_officer",
            "role": "Report Synthesizer",
            "status": "COMPLETED",
            "execution_time_ms": 1,
            "summary": "Compiled market data, fundamental analysis, technical indicators, and source provenance.",
            "output": {"summary": executive_summary, "limitations_count": len(all_limitations)},
        })

        pe_val = (fundamental_result.get("financial_ratios") or {}).get("pe_ratio", {}).get("value")
        report_payload = {
            "meta": {
                "task_id": task.task_id,
                "ticker": task.ticker,
                "yf_symbol": market_data.get("yf_symbol"),
                "company_name": profile.get("company_name", task.company_name),
                "market": task.market,
                "analysis_period": task.analysis_period,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "pipeline_version": "Modules-1-4",
            },
            "executive_summary": executive_summary,
            "market_metrics": {
                "current_price": profile.get("current_price"),
                "currency": profile.get("currency"),
                "period_change_pct": perf.get("change_percent"),
                "pe_ratio": pe_val if pe_val is not None else "N/A",
                "market_cap": profile.get("market_cap"),
                "fifty_two_week_high": profile.get("fifty_two_week_high"),
                "fifty_two_week_low": profile.get("fifty_two_week_low"),
                "sector": profile.get("sector"),
                "industry": profile.get("industry"),
                "beta": profile.get("beta"),
            },
            "company_overview": profile.get("description"),
            "period_performance": perf,
            "data_quality": data_quality,
            "financial_statements": market_data.get("financial_statements"),
            "fundamental_analysis": fundamental_result,
            "technical_analysis": technical_result,
            "sources": sources,
            "limitations": all_limitations,
            "multi_agent_pipeline": {
                "coordinator": "DefaultResearchEngine",
                "active_agents": [
                    {k: v for k, v in rec.items() if k != "output"}
                    for rec in agent_records
                ],
            },
            "_agent_records": agent_records,
            "_sources": sources,
        }

        return report_payload


def render_markdown_report(task: ResearchTask, content: Dict[str, Any]) -> str:
    """Render a clean downloadable Markdown report from a structured ResearchReport payload."""
    meta = content.get("meta", {})
    metrics = content.get("market_metrics", {})
    fund = content.get("fundamental_analysis", {})
    tech = content.get("technical_analysis", {})
    dq = content.get("data_quality", {})
    sources = content.get("sources", [])
    limitations = content.get("limitations", [])

    rev = fund.get("revenue_and_earnings", {})
    prof = fund.get("profitability", {})
    stab = fund.get("debt_and_stability", {})
    ratios = fund.get("financial_ratios", {})
    trend = tech.get("trend_summary", {})
    ind = tech.get("latest_indicators", {})
    vol = tech.get("volatility", {})

    lines = [
        f"# Stock Research Report: {meta.get('company_name', task.company_name)} ({task.ticker})",
        "",
        f"- **Market:** {task.market}",
        f"- **Analysis Period:** {task.analysis_period}",
        f"- **Generated At:** {meta.get('generated_at', '')}",
        f"- **Current Price:** {metrics.get('currency', '')} {metrics.get('current_price', 'N/A')} ({metrics.get('period_change_pct', 'N/A')}% period change)",
        "",
        "## Executive Summary",
        content.get("executive_summary", ""),
        "",
        "## Company Overview",
        content.get("company_overview", "N/A"),
        "",
        "## Fundamental Analysis",
        fund.get("explanation", "Unavailable"),
        "",
        "### Key Financial Metrics & Ratios",
        f"- **Latest Revenue:** {rev.get('latest_revenue', 'N/A')} (YoY: {rev.get('revenue_yoy_growth_pct', 'N/A')}%)",
        f"- **Latest Net Income:** {rev.get('latest_net_income', 'N/A')} (YoY: {rev.get('earnings_yoy_growth_pct', 'N/A')}%)",
        f"- **Gross / Operating / Net Margins:** {prof.get('gross_margin_pct', 'N/A')}% / {prof.get('operating_margin_pct', 'N/A')}% / {prof.get('net_margin_pct', 'N/A')}%",
        f"- **ROA:** {prof.get('roa_pct', 'N/A')}%",
        f"- **P/E Ratio:** {(ratios.get('pe_ratio') or {}).get('value', 'N/A')}",
        f"- **P/B Ratio:** {(ratios.get('pb_ratio') or {}).get('value', 'N/A')}",
        f"- **ROE:** {(ratios.get('roe_pct') or {}).get('value', 'N/A')}%",
        f"- **Debt-to-Equity:** {stab.get('debt_to_equity', 'N/A')}x | **Current Ratio:** {stab.get('current_ratio', 'N/A')}x | **Free Cash Flow:** {stab.get('free_cash_flow', 'N/A')}",
        "",
        "## Technical Analysis",
        tech.get("explanation", "Unavailable"),
        "",
        f"- **Overall Signal:** {trend.get('overall_signal', 'N/A')}",
        f"- **SMA (20 / 50 / 200):** {ind.get('sma_20', 'N/A')} / {ind.get('sma_50', 'N/A')} / {ind.get('sma_200', 'N/A')}",
        f"- **EMA (12 / 26):** {ind.get('ema_12', 'N/A')} / {ind.get('ema_26', 'N/A')}",
        f"- **RSI (14):** {ind.get('rsi_14', 'N/A')}",
        f"- **MACD / Signal / Histogram:** {ind.get('macd', 'N/A')} / {ind.get('macd_signal', 'N/A')} / {ind.get('macd_histogram', 'N/A')}",
        f"- **Annualized Volatility:** {vol.get('annualized_volatility_pct', 'N/A')}% ({vol.get('volatility_regime', 'N/A')})",
        "",
        "## Data Quality & Validation",
        f"- **Status:** {dq.get('quality_status', 'N/A')}",
        f"- **Valid OHLCV Rows:** {dq.get('valid_rows', 0)} / {dq.get('total_raw_rows', 0)}",
        f"- **Duplicate Dates Removed:** {dq.get('duplicate_dates_removed', 0)}",
        f"- **Missing Values Detected:** {dq.get('missing_values_count', 0)}",
        f"- **Inconsistent Rows Detected:** {dq.get('inconsistent_rows_count', 0)}",
        "",
        "## Data Sources & Provenance",
    ]
    for s in sources:
        lines.append(f"- **{s.get('title')}** — {s.get('source_url', 'N/A')} (Retrieved: {s.get('retrieved_at', '')})")

    lines.extend(["", "## Data Limitations & Disclaimers"])
    for lim in limitations:
        lines.append(f"- {lim}")

    return "\n".join(lines)


# Singleton Engine Instance
research_engine = DefaultResearchEngine()


def execute_research_task_background(
    task_id: int,
    session_factory: Callable[[], Session] = SessionLocal,
    include_peers: bool = True,
) -> None:
    """
    Background worker that transitions task status:
    Pending -> Processing -> Completed (or Failed on error)
    and persists AgentResult, SourceDocument, and ResearchReport rows.
    """
    db: Session = session_factory()
    try:
        task = db.query(ResearchTask).filter(ResearchTask.task_id == task_id).first()
        if not task:
            logger.error(f"Research task {task_id} not found in background worker.")
            return

        # 1. Transition to Processing
        task.status = "Processing"
        task.updated_at = datetime.now(timezone.utc)
        db.commit()

        # 2. Run Coordinator pipeline
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            report_data = loop.run_until_complete(
                research_engine.run_pipeline(task, include_peers=include_peers)
            )

            agent_records = report_data.pop("_agent_records", [])
            source_records = report_data.pop("_sources", [])

            if report_data.get("meta", {}).get("company_name"):
                task.company_name = report_data["meta"]["company_name"]

            # Persist AgentResult rows
            for rec in agent_records:
                db.add(AgentResult(
                    task_id=task.task_id,
                    agent_name=rec["agent_id"],
                    status=rec["status"],
                    output_json=json.dumps(rec.get("output"), default=str) if rec.get("output") is not None else None,
                    error_message=rec.get("error_message"),
                    execution_time_ms=rec.get("execution_time_ms"),
                ))

            # Persist SourceDocument rows
            for src in source_records:
                pub_dt = None
                if src.get("published_at"):
                    try:
                        pub_dt = datetime.fromisoformat(src["published_at"])
                    except Exception:
                        pub_dt = None
                db.add(SourceDocument(
                    task_id=task.task_id,
                    source_type=src["source_type"],
                    title=src["title"],
                    source_url=src.get("source_url"),
                    published_at=pub_dt,
                    content_hash=src.get("content_hash"),
                ))

            # Persist ResearchReport
            report = ResearchReport(
                task_id=task.task_id,
                report_content=json.dumps(report_data, default=str),
                summary=report_data.get("executive_summary"),
                limitations="\n".join(report_data.get("limitations", [])),
            )
            db.add(report)

            # Transition to Completed
            now_utc = datetime.now(timezone.utc)
            task.status = "Completed"
            task.completed_at = now_utc
            task.updated_at = now_utc
            db.commit()
            logger.info(f"Research task {task_id} successfully completed.")
        except Exception as exec_err:
            logger.exception(f"Error during research execution for task {task_id}: {exec_err}")
            task.status = "Failed"
            task.error_message = f"Analysis pipeline failed: {str(exec_err)}"
            task.updated_at = datetime.now(timezone.utc)
            db.commit()
        finally:
            loop.close()

    except Exception as db_err:
        logger.exception(f"Database error in background research worker for task {task_id}: {db_err}")
    finally:
        db.close()
