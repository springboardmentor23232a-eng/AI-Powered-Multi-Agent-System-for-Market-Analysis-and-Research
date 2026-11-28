from peer_analysis import analyze_peers
import time
from data_quality import assess_data_quality
import logging
from functools import lru_cache
from historical_analysis import analyze_historical_performance
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from financial_ratios import calculate_financial_ratios
from auth import get_current_user
from database import get_db
from models import User
from market_data import get_stock_info, get_financials
from provenance import SOURCE, now_utc, elapsed_ms, log_fetch

from fundamental_agent.agent import FundamentalAnalysisAgent
from fundamental_agent.errors import AnalysisError

router = APIRouter(tags=["Fundamental Analysis"])
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_agent():
    return FundamentalAnalysisAgent()


@router.get("/stocks/{ticker}/fundamental-analysis")
def fundamental_analysis(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    started = time.monotonic()
    retrieved_at = now_utc()

    stock = get_stock_info(ticker)

    if not stock:
        raise HTTPException(
            status_code=400,
            detail="Unknown or unverifiable ticker"
        )

    ticker = stock["ticker"]

    try:
        financials = get_financials(ticker, "annual")

    except Exception:
        logger.exception("Financial data retrieval failed")

        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve financial statements."
        )

    ratio_data = calculate_financial_ratios(
    ticker, financials
    )
    historical_data = analyze_historical_performance(
    financials
    )
    quality_data = assess_data_quality(
    financials,
    historical_data,
    ratio_data
    )
    try:
        agent = get_agent()

        result = agent.analyze_from_yahoo(
            financials,
            company=stock["name"]
        )

    except AnalysisError as exc:
        result = exc.to_dict()

    except Exception:
        logger.exception("Fundamental analysis failed")

        raise HTTPException(
            status_code=500,
            detail="Fundamental analysis service failed. "
                   "Check the backend logs."
        )

    log_fetch(
        db,
        user_id=current_user.user_id,
        data_type="fundamental_analysis",
        status="success" if result["status"] == "ok" else "failed",
        ticker=ticker,
        detail="Annual fundamental analysis",
        duration_ms=elapsed_ms(started),
        error=result.get("message") if result["status"] == "error" else None,
        retrieved_at=retrieved_at,
    )

    return {
    **result,
    **ratio_data,
    "historical": historical_data,
    "data_quality": quality_data,
    "ticker": ticker,
    "source": SOURCE,
    "retrieved_at": retrieved_at,
}

@router.get("/stocks/{ticker}/peer-comparison")
def peer_comparison(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    started = time.monotonic()
    retrieved_at = now_utc()

    stock = get_stock_info(ticker)

    if not stock:
        raise HTTPException(
            status_code=400,
            detail="Unknown or unverifiable ticker"
        )

    try:
        result = analyze_peers(stock["ticker"])

    except Exception:
        logger.exception("Peer comparison failed")

        raise HTTPException(
            status_code=502,
            detail="Unable to complete peer comparison."
        )

    log_fetch(
        db,
        user_id=current_user.user_id,
        data_type="peer_comparison",
        status="success" if result["status"] == "ok" else "failed",
        ticker=stock["ticker"],
        detail="Industry peer comparison",
        duration_ms=elapsed_ms(started),
        error=result.get("message"),
        retrieved_at=retrieved_at,
    )

    return {
        **result,
        "ticker": stock["ticker"],
        "source": SOURCE,
        "retrieved_at": retrieved_at,
    }
