import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.research_task import ResearchTask, ResearchReport
from app.models.user import User
from app.schemas.research import ResearchTaskCreate
from app.services.stock_service import (
    get_company_overview,
    get_historical_ohlcv,
    get_financial_statements,
)

logger = logging.getLogger("uvicorn.error")

VALID_MARKETS = {"NSE", "BSE", "NASDAQ", "NYSE"}
VALID_PERIODS = {"1mo", "3mo", "6mo", "1y", "5y", "2y", "max"}

KNOWN_NYSE_TICKERS = {
    "IBM", "JPM", "DIS", "KO", "WMT", "GE", "BRK.A", "BRK.B",
    "V", "UNH", "XOM", "CVX", "PG", "MA", "HD", "BAC", "PFE", "ABBV"
}
KNOWN_US_TICKERS = {
    "AAPL", "MSFT", "NVDA", "TSLA", "GOOGL", "AMZN", "META",
    "IBM", "JPM", "DIS", "KO", "WMT", "GE", "BRK.A", "BRK.B",
    "V", "UNH", "XOM", "CVX", "PG", "MA", "HD", "BAC", "PFE", "ABBV"
}


def determine_market_from_ticker(ticker: str, explicit_market: Optional[str] = None) -> str:
    """
    Infers exchange market name from ticker symbol unless explicitly provided.
    Preserves canonical market names: NSE, BSE, NASDAQ, NYSE.
    """
    upper = ticker.strip().upper()

    if explicit_market:
        clean_market = explicit_market.strip().upper()
        if clean_market in VALID_MARKETS:
            return clean_market
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported market '{explicit_market}'. Supported markets are: {', '.join(sorted(VALID_MARKETS))}.",
        )

    if upper.endswith(".NS"):
        return "NSE"
    if upper.endswith(".BO"):
        return "BSE"
    if upper in KNOWN_NYSE_TICKERS:
        return "NYSE"
    return "NASDAQ"


def validate_market_and_ticker(market: str, ticker: str) -> str:
    """
    Validates ticker symbol against the selected market.
    Returns normalized ticker symbol ready for upstream data retrieval.
    Rejects incompatible market/ticker combinations with clear validation errors.
    """
    clean_ticker = ticker.strip().upper()

    if market == "NSE":
        if clean_ticker.endswith(".BO"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ticker '{clean_ticker}' has a BSE suffix (.BO) which is incompatible with selected market 'NSE'.",
            )
        if clean_ticker in KNOWN_US_TICKERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ticker '{clean_ticker}' is a US equity and cannot be researched under market 'NSE'.",
            )
        # Normalize Indian ticker for NSE provider lookup
        if not clean_ticker.endswith(".NS") and "." not in clean_ticker:
            known_nse = {"INFY": "INFY.NS", "TCS": "TCS.NS", "RELIANCE": "RELIANCE.NS", "HDFCBANK": "HDFCBANK.NS"}
            clean_ticker = known_nse.get(clean_ticker, f"{clean_ticker}.NS")

    elif market == "BSE":
        if clean_ticker.endswith(".NS"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ticker '{clean_ticker}' has an NSE suffix (.NS) which is incompatible with selected market 'BSE'.",
            )
        if clean_ticker in KNOWN_US_TICKERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ticker '{clean_ticker}' is a US equity and cannot be researched under market 'BSE'.",
            )
        if not clean_ticker.endswith(".BO") and "." not in clean_ticker:
            clean_ticker = f"{clean_ticker}.BO"

    elif market in {"NASDAQ", "NYSE"}:
        if clean_ticker.endswith(".NS") or clean_ticker.endswith(".BO"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ticker '{clean_ticker}' is an Indian market symbol and cannot be researched under US market '{market}'.",
            )

    return clean_ticker


def execute_research_workflow(
    db: Session,
    user: User,
    request: ResearchTaskCreate,
) -> Tuple[ResearchTask, Optional[ResearchReport]]:
    """
    Executes the research task lifecycle:
    1. Initial save with 'Pending' status.
    2. Transition to 'Processing'.
    3. Validate market, ticker format, and provider-supported historical period.
    4. Fetch company overview and validated historical OHLCV data.
    5. If successful, persist ResearchReport and mark task 'Completed'.
    6. If failed, record 'Failed' status and appropriate timestamps.
    """
    clean_ticker = request.ticker.strip().upper()
    clean_period = request.period.strip()
    market = determine_market_from_ticker(clean_ticker, request.market)

    # 1. Create task with initial Pending status
    task = ResearchTask(
        user_id=user.user_id,
        ticker=clean_ticker,
        company_name=clean_ticker,  # Initial placeholder before overview fetch
        market=market,
        requested_period=clean_period,
        status="Pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    logger.info(f"Created ResearchTask #{task.task_id} for user #{user.user_id} with status 'Pending'")

    # 2. Transition to Processing
    task.status = "Processing"
    db.commit()
    db.refresh(task)

    try:
        # Validate market/ticker compatibility and provider period support
        lookup_ticker = validate_market_and_ticker(market, clean_ticker)
        if clean_period not in VALID_PERIODS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requested period '{clean_period}' is not supported by the market data provider. Valid periods: 1mo, 3mo, 6mo, 1y, 5y.",
            )

        # 3. Fetch real market overview & historical data
        overview = get_company_overview(ticker=lookup_ticker)
        history = get_historical_ohlcv(ticker=lookup_ticker, period=clean_period)

        # 4. Fetch financial statements (resilient: financial statement failure does not abort research task)
        financials = None
        financials_dict = None
        try:
            financials = get_financial_statements(ticker=lookup_ticker)
            financials_dict = financials.model_dump()
        except Exception as fin_exc:
            logger.warning(f"Could not load financial statements for {lookup_ticker}: {fin_exc}")

        # Module 3: Fundamental Analysis Agent (resilient: failures do not abort research task)
        fundamental_dict = None
        try:
            from app.services.fundamental_service import run_fundamental_analysis
            fundamental_analysis = run_fundamental_analysis(
                ticker=lookup_ticker,
                financials=financials,
                overview=overview,
            )
            fundamental_dict = fundamental_analysis.model_dump()
        except Exception as fund_exc:
            logger.warning(f"Could not execute fundamental analysis for {lookup_ticker}: {fund_exc}")

        # 5. Populate real company name and preserve standard market (do not overwrite with NSI/NMS)
        task.company_name = overview.company_name or clean_ticker
        task.market = market
        task.status = "Completed"
        task.completed_at = datetime.now(timezone.utc)

        # Convert Pydantic models to serializable dicts
        overview_dict = overview.model_dump()
        history_dict = history.model_dump()

        # Build consolidated report_content directly from real data
        summary_text = overview.business_summary or f"Research report for {clean_ticker}"
        report_content = {
            "overview": overview_dict,
            "history": history_dict,
            "financial_statements": financials_dict,
            "fundamental_analysis": fundamental_dict,
            "summary": summary_text,
            "metadata": {
                "task_id": task.task_id,
                "ticker": clean_ticker,
                "company_name": task.company_name,
                "market": market,
                "provider_exchange": overview.exchange,
                "requested_period": clean_period,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "data_source": overview.data_source,
                "retrieved_at": overview.retrieved_at,
            },
        }

        # Build factual limitations describing provider, data range, cleaning, and market uncertainty
        val = history_dict.get("validation", {})
        stats = history_dict.get("stats", {})
        total_raw = val.get("total_raw_records", 0)
        cleaned = val.get("cleaned_records", 0)
        dups = val.get("duplicates_removed", 0)
        start_d = stats.get("start_date", "N/A")
        end_d = stats.get("end_date", "N/A")
        trading_days = stats.get("total_trading_days", 0)

        limitations_text = (
            f"Market data retrieved from {overview.data_source} for {clean_ticker} across the requested period '{clean_period}' "
            f"(covering {trading_days} trading sessions from {start_d} to {end_d}). Data quality verification processed "
            f"{total_raw} raw records, filtered {dups} duplicates, and validated {cleaned} chronological sessions. "
            f"Market prices and valuation metrics are historical or point-in-time reflections provided by the upstream source "
            f"and do not constitute financial advice or predict future performance."
        )

        # 5. Save report
        report = ResearchReport(
            task_id=task.task_id,
            report_content=report_content,
            overview_data=overview_dict,
            history_data=history_dict,
            summary=summary_text,
            limitations=limitations_text,
        )
        db.add(report)
        db.commit()
        db.refresh(task)
        db.refresh(report)

        logger.info(f"ResearchTask #{task.task_id} completed successfully for '{clean_ticker}' on market '{market}'")
        return task, report

    except Exception as exc:
        # 6. Mark task as Failed and commit failure state to PostgreSQL
        task.status = "Failed"
        task.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(task)
        logger.error(f"ResearchTask #{task.task_id} failed: {exc}", exc_info=True)
        error_msg = str(getattr(exc, "detail", exc))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Research task failed for {clean_ticker}: {error_msg}. Status has been recorded as Failed.",
        )


def list_user_research_history(db: Session, user_id: int) -> List[ResearchTask]:
    """
    Returns all research tasks belonging strictly to the authenticated user,
    ordered newest first.
    """
    return (
        db.query(ResearchTask)
        .filter(ResearchTask.user_id == user_id)
        .order_by(ResearchTask.created_at.desc())
        .all()
    )


def get_user_research_task_and_report(
    db: Session, task_id: int, user_id: int
) -> Tuple[ResearchTask, Optional[ResearchReport]]:
    """
    Retrieves a research task and its report for the authenticated user.
    Returns HTTP 404 if the task doesn't exist or belongs to another user.
    Automatically enriches legacy reports with multi-period data integrity audits
    if stored data lacks Task 7 enhancements.
    """
    task = db.query(ResearchTask).filter(ResearchTask.task_id == task_id).first()

    if not task or task.user_id != user_id:
        # Strict isolation: 404 prevents enumeration of other users' tasks
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research task not found.",
        )

    report = db.query(ResearchReport).filter(ResearchReport.task_id == task_id).first()
    if report and report.report_content:
        try:
            rc = report.report_content
            fa = rc.get("fundamental_analysis")
            fin_data = rc.get("financial_statements")
            ov_data = rc.get("overview")
            if isinstance(fa, dict) and fin_data and ov_data:
                audit_dict = fa.get("data_integrity_audit")
                # Auto-enrich if legacy audit lacks multi-period balance audits or currency detection
                if not audit_dict or not audit_dict.get("multi_period_balance_audits") or not audit_dict.get("periods_audited") or not audit_dict.get("trading_currency"):
                    from sqlalchemy.orm.attributes import flag_modified
                    from app.services.fundamental_service import audit_data_integrity
                    from app.schemas.stock import FinancialStatementsResponse, StockOverviewResponse
                    fin_obj = FinancialStatementsResponse.model_validate(fin_data)
                    ov_obj = StockOverviewResponse.model_validate(ov_data)
                    fresh_audit = audit_data_integrity(fin_obj, ov_obj)
                    fa["data_integrity_audit"] = fresh_audit.model_dump()
                    rc["fundamental_analysis"] = fa
                    report.report_content = dict(rc)
                    flag_modified(report, "report_content")
                    db.commit()
                    db.refresh(report)
        except Exception as enrich_exc:
            logger.warning(f"Failed to auto-enrich legacy research report #{task_id}: {enrich_exc}")

    return task, report
