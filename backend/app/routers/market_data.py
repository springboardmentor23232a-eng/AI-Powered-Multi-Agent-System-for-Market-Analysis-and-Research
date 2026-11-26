from datetime import datetime, timezone
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..dependencies import get_current_user, require_csrf_for_cookie_auth
from ..models import (
    AgentResult,
    MarketDataRecord,
    ResearchTask,
    SourceDocument,
    User,
)
from ..schemas import (
    MARKETS,
    PERIODS,
    CompanyProfileResponse,
    FinancialStatementsResponse,
    HistoricalDataResponse,
    MarketDataCollectRequest,
    MarketDataFullResponse,
    MarketDataRecordResponse,
    StockSearchItem,
)
from ..services.yahoo_finance import (
    MarketDataProviderError,
    NoHistoricalDataError,
    RateLimitError,
    StockNotFoundError,
    yahoo_finance_service,
)

router = APIRouter(
    prefix="/api/market",
    tags=["stock market data"],
    dependencies=[Depends(require_csrf_for_cookie_auth)],
)


def _clean_param(val: Any, default: str = "") -> str:
    if hasattr(val, "default"):
        return str(val.default)
    return str(val) if val is not None else default


@router.get("/config")
def get_market_api_config(current_user: User = Depends(get_current_user)):
    """
    Returns the current Yahoo Finance API configuration status.
    """
    return {
        "provider": "Yahoo Finance (via yfinance)",
        "has_api_key": False,
        "mode": "Python yfinance Library",
        "data_source": "Yahoo Finance via yfinance",
        "requires_api_key": False,
        "status": "ready",
    }


@router.get("/search", response_model=list[StockSearchItem])
def search_stocks(
    q: str = Query(min_length=1, max_length=80, description="Company name or ticker symbol"),
    market: str = Query(default="ALL", description="Market filter: NSE, BSE, NASDAQ, NYSE, or ALL"),
    current_user: User = Depends(get_current_user),
):
    """
    Search for companies using their name or ticker symbol.
    """
    market_clean = _clean_param(market, "ALL").strip().upper()
    if market_clean != "ALL" and market_clean not in MARKETS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported market '{market}'. Choose from NSE, BSE, NASDAQ, NYSE, or ALL.",
        )

    try:
        results = yahoo_finance_service.search(_clean_param(q), market=market_clean)
        return results
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Market data provider unavailable: {e}")


@router.get("/historical/{ticker}", response_model=HistoricalDataResponse)
def get_historical_prices(
    ticker: str,
    market: str = Query(default="NSE"),
    period: str = Query(default="1y", description="Time range (1mo, 3mo, 6mo, 1y, 5y, max)"),
    interval: str = Query(default="1d", description="Bar interval (1d, 1wk, 1mo, 1m, 5m, 15m)"),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve historical stock prices and OHLCV data.
    """
    market_clean = _clean_param(market, "NSE").strip().upper()
    period_clean = _clean_param(period, "1y").strip()
    interval_clean = _clean_param(interval, "1d").strip()

    try:
        data = yahoo_finance_service.get_historical_ohlcv(
            symbol=ticker,
            market=market_clean,
            period=period_clean,
            interval=interval_clean,
        )
        return data
    except StockNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NoHistoricalDataError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except MarketDataProviderError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Market data provider unavailable: {e}")


@router.get("/profile/{ticker}", response_model=CompanyProfileResponse)
def get_company_profile(
    ticker: str,
    market: str = Query(default="NSE"),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve available company profile, executive leadership, and valuation statistics.
    """
    market_clean = _clean_param(market, "NSE").strip().upper()
    try:
        data = yahoo_finance_service.get_company_profile(symbol=ticker, market=market_clean)
        return data
    except StockNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except MarketDataProviderError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Market data provider unavailable: {e}")


@router.get("/financials/{ticker}", response_model=FinancialStatementsResponse)
def get_financial_statements(
    ticker: str,
    market: str = Query(default="NSE"),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve available financial statements (Income Statement, Balance Sheet, Cash Flow) and key ratios.
    """
    market_clean = _clean_param(market, "NSE").strip().upper()
    try:
        data = yahoo_finance_service.get_financial_statements(symbol=ticker, market=market_clean)
        return data
    except StockNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except MarketDataProviderError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Market data provider unavailable: {e}")


@router.post("/collect", response_model=MarketDataFullResponse, status_code=status.HTTP_201_CREATED)
def collect_market_data(
    payload: MarketDataCollectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Collect comprehensive market data (OHLCV, profile, and financials).
    Records data sources and exact retrieval timestamps in PostgreSQL.
    Optionally links to an existing research task as a source document and agent result.
    """
    ticker_clean = payload.ticker.strip().upper()
    market_clean = payload.market.strip().upper()

    try:
        collected = yahoo_finance_service.collect_full_market_data(
            symbol=ticker_clean,
            company_name=payload.company_name.strip(),
            market=market_clean,
            period=payload.period,
            interval=payload.interval,
        )
    except StockNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NoHistoricalDataError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except MarketDataProviderError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Market data provider unavailable: {e}")

    now = datetime.now(timezone.utc)
    record = MarketDataRecord(
        user_id=current_user.user_id,
        task_id=payload.task_id,
        ticker=ticker_clean,
        company_name=collected["company_name"],
        market=market_clean,
        data_source=collected["data_source"],
        retrieval_timestamp=datetime.fromisoformat(collected["retrieval_timestamp"]),
        period=payload.period,
        interval=payload.interval,
        currency=collected.get("currency"),
        latest_price=collected.get("latest_price"),
        change=collected.get("change"),
        change_percent=collected.get("change_percent"),
        ohlcv_data=collected.get("ohlcv_data", []),
        profile_data=collected.get("profile_data", {}),
        financials_data=collected.get("financials_data", {}),
        created_at=now,
    )
    db.add(record)

    # If linked to a ResearchTask, populate SourceDocument and AgentResult
    if payload.task_id:
        task = db.scalar(
            select(ResearchTask).where(
                ResearchTask.task_id == payload.task_id,
                ResearchTask.user_id == current_user.user_id,
            )
        )
        if task:
            # Create Source Document
            ohlcv_count = len(collected.get("ohlcv_data", []))
            doc_content = (
                f"Yahoo Finance Market Intelligence for {ticker_clean} ({task.company_name}).\n"
                f"Data Source: {collected['data_source']}\n"
                f"Retrieved At (UTC): {collected['retrieval_timestamp']}\n"
                f"Latest Close: {collected.get('currency')} {collected.get('latest_price')}\n"
                f"OHLCV Series: {ohlcv_count} bars collected for period {payload.period} ({payload.interval}).\n"
                f"Sector: {collected.get('profile_data', {}).get('sector')}\n"
                f"Industry: {collected.get('profile_data', {}).get('industry')}\n"
                f"Market Cap: {collected.get('profile_data', {}).get('market_cap')}\n"
                f"Summary: {collected.get('profile_data', {}).get('summary')[:300]}..."
            )

            source_doc = SourceDocument(
                task_id=task.task_id,
                source_name=f"Yahoo Finance Market Data — {ticker_clean}",
                source_url=f"https://finance.yahoo.com/quote/{ticker_clean}",
                document_content=doc_content,
                document_metadata={
                    "data_source": collected["data_source"],
                    "retrieval_timestamp": collected["retrieval_timestamp"],
                    "ticker": ticker_clean,
                    "market": market_clean,
                    "period": payload.period,
                    "currency": collected.get("currency"),
                    "latest_price": collected.get("latest_price"),
                    "ohlcv_count": ohlcv_count,
                },
                created_at=now,
            )
            db.add(source_doc)

            # Create Agent Result
            agent_res = AgentResult(
                task_id=task.task_id,
                agent_name="MarketDataCollectorAgent",
                status="Completed",
                result={
                    "data_source": collected["data_source"],
                    "retrieval_timestamp": collected["retrieval_timestamp"],
                    "ticker": ticker_clean,
                    "company_name": task.company_name,
                    "latest_price": collected.get("latest_price"),
                    "change": collected.get("change"),
                    "change_percent": collected.get("change_percent"),
                    "currency": collected.get("currency"),
                    "ohlcv_summary": {
                        "total_bars": ohlcv_count,
                        "start_date": collected["ohlcv_data"][0]["date"] if collected["ohlcv_data"] else None,
                        "end_date": collected["ohlcv_data"][-1]["date"] if collected["ohlcv_data"] else None,
                    },
                    "key_ratios": collected.get("financials_data", {}).get("key_ratios", {}),
                    "profile_highlights": {
                        "sector": collected.get("profile_data", {}).get("sector"),
                        "industry": collected.get("profile_data", {}).get("industry"),
                        "market_cap": collected.get("profile_data", {}).get("market_cap"),
                        "pe_ratio": collected.get("profile_data", {}).get("trailing_pe"),
                    },
                },
                created_at=now,
            )
            db.add(agent_res)

            # Update task status to Data Collected
            task.status = "Data Collected"
            task.updated_at = now

    db.commit()
    db.refresh(record)
    return record


@router.get("/records", response_model=list[MarketDataRecordResponse])
def get_recorded_market_data_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve previously recorded market data collections for the current user.
    """
    records = list(
        db.scalars(
            select(MarketDataRecord)
            .where(MarketDataRecord.user_id == current_user.user_id)
            .order_by(MarketDataRecord.created_at.desc())
        ).all()
    )

    out = []
    for r in records:
        out.append(
            MarketDataRecordResponse(
                record_id=r.record_id,
                user_id=r.user_id,
                task_id=r.task_id,
                ticker=r.ticker,
                company_name=r.company_name,
                market=r.market,
                period=r.period,
                interval=r.interval,
                currency=r.currency,
                latest_price=r.latest_price,
                change=r.change,
                change_percent=r.change_percent,
                data_source=r.data_source,
                retrieval_timestamp=r.retrieval_timestamp,
                created_at=r.created_at,
                ohlcv_count=len(r.ohlcv_data) if r.ohlcv_data else 0,
            )
        )
    return out


@router.get("/records/{record_id}", response_model=MarketDataFullResponse)
def get_single_recorded_market_data(
    record_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve full details of a saved market data collection.
    """
    record = db.scalar(
        select(MarketDataRecord).where(
            MarketDataRecord.record_id == record_id,
            MarketDataRecord.user_id == current_user.user_id,
        )
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Market data record not found.")
    return record


@router.delete("/records/{record_id}", response_model=dict)
def delete_recorded_market_data(
    record_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a saved market data collection.
    """
    record = db.scalar(
        select(MarketDataRecord).where(
            MarketDataRecord.record_id == record_id,
            MarketDataRecord.user_id == current_user.user_id,
        )
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Market data record not found.")

    db.delete(record)
    db.commit()
    return {"message": "Market data record deleted successfully."}
