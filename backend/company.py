import time
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from market_data import get_company_profile, get_financials, get_stock_info
from models import User
from provenance import SOURCE, elapsed_ms, log_fetch, now_utc
from schemas import CompanyProfile, Financials

router = APIRouter(tags=["company"])


@router.get("/stocks/{ticker}/profile", response_model=CompanyProfile)
def company_profile(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.user_id
    stock = get_stock_info(ticker)
    if not stock:
        raise HTTPException(status_code=400, detail="Unknown or unverifiable ticker")

    started = time.monotonic()
    retrieved_at = now_utc()
    try:
        details = get_company_profile(stock["ticker"])
    except Exception as exc:
        log_fetch(
            db,
            user_id=user_id,
            data_type="company_profile",
            status="failed",
            ticker=stock["ticker"],
            duration_ms=elapsed_ms(started),
            error=str(exc),
            retrieved_at=retrieved_at,
        )
        raise HTTPException(status_code=502, detail="Market data provider unavailable")

    filled = sum(1 for v in details.values() if v not in (None, ""))
    log_fetch(
        db,
        user_id=user_id,
        data_type="company_profile",
        status="success" if filled > 0 else "partial",
        ticker=stock["ticker"],
        detail=f"{filled} of {len(details)} fields available",
        duration_ms=elapsed_ms(started),
        retrieved_at=retrieved_at,
    )

    return {
        "ticker": stock["ticker"],
        "name": stock["name"],
        "market": stock["market"],
        **details,
        "source": SOURCE,
        "retrieved_at": retrieved_at,
    }


@router.get("/stocks/{ticker}/financials", response_model=Financials)
def company_financials(
    ticker: str,
    frequency: Literal["annual", "quarterly"] = "annual",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.user_id
    stock = get_stock_info(ticker)
    if not stock:
        raise HTTPException(status_code=400, detail="Unknown or unverifiable ticker")

    started = time.monotonic()
    retrieved_at = now_utc()
    data = get_financials(stock["ticker"], frequency)

    statements = {
        "income statement": data["income_statement"],
        "balance sheet": data["balance_sheet"],
        "cash flow": data["cash_flow"],
    }
    missing = [name for name, s in statements.items() if not s["available"]]
    if not missing:
        outcome = "success"
    elif len(missing) < len(statements):
        outcome = "partial"
    else:
        outcome = "failed"

    all_periods = [p for s in statements.values() for p in s["periods"]]
    as_of = max(all_periods) if all_periods else None  # latest period end date
    detail = f"frequency={frequency}"
    if missing:
        detail += f"; missing: {', '.join(missing)}"

    log_fetch(
        db,
        user_id=user_id,
        data_type="financials",
        status=outcome,
        ticker=stock["ticker"],
        detail=detail,
        record_count=sum(len(s["rows"]) for s in statements.values()),
        as_of=as_of,
        duration_ms=elapsed_ms(started),
        retrieved_at=retrieved_at,
    )

    return {
        "ticker": stock["ticker"],
        "name": stock["name"],
        "frequency": frequency,
        **data,
        "source": SOURCE,
        "retrieved_at": retrieved_at,
        "as_of": as_of,
    }