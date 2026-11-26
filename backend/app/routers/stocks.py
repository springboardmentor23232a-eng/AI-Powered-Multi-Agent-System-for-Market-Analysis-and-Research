from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.core.config import settings
from app.models.user import User
from app.schemas.stock import MarketDataCollectionResponse, StockSearchResult
from app.services.agents import FundamentalAnalysisAgent, TechnicalAnalysisAgent
from app.services.auth_service import get_current_user
from app.services.market_data_service import MarketDataCollector
from app.services.stock_data_service import StockDataService

router = APIRouter(prefix="/stocks", tags=["Stocks"])


def _validate_market_and_period(market: str, period: str) -> tuple[str, str]:
    clean_market = market.strip().upper()
    if clean_market not in settings.SUPPORTED_MARKETS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Market '{market}' is not supported. Supported markets: {settings.SUPPORTED_MARKETS}",
        )
    clean_period = period.strip()
    if clean_period not in settings.SUPPORTED_PERIODS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Period '{period}' is not supported. Supported periods: {settings.SUPPORTED_PERIODS}",
        )
    return clean_market, clean_period


@router.get("/search", response_model=List[StockSearchResult])
async def search_stocks(
    q: str = Query(..., min_length=1, description="Ticker symbol or company name"),
    market: Optional[str] = Query(None, description="Optional exchange filter (NSE, BSE, NASDAQ, NYSE)"),
    current_user: User = Depends(get_current_user),
):
    """
    Search stocks across supported exchanges (NSE, BSE, NASDAQ, NYSE)
    using validated market data provider with verified catalog fallback.
    """
    if market:
        m_upper = market.strip().upper()
        if m_upper not in settings.SUPPORTED_MARKETS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Market '{market}' is not supported.",
            )
        market = m_upper
    return await StockDataService.search_stocks(q, market=market)


@router.get("/{ticker}/market-data", response_model=MarketDataCollectionResponse)
async def get_stock_market_data(
    ticker: str,
    market: str = Query("NASDAQ", description="Target exchange (NSE, BSE, NASDAQ, NYSE)"),
    period: str = Query("1 Year", description="Analysis period"),
    current_user: User = Depends(get_current_user),
):
    """
    Module 2 endpoint: Collect and validate OHLCV historical prices, company profile,
    financial statements, data quality checks, and provenance metadata.
    """
    clean_market, clean_period = _validate_market_and_period(market, period)
    data = MarketDataCollector.collect_market_data(
        ticker=ticker,
        market=clean_market,
        period=clean_period,
        include_warmup=False,
    )
    return MarketDataCollectionResponse(
        ticker=data["ticker"],
        market=data["market"],
        yf_symbol=data["yf_symbol"],
        period=data["period"],
        retrieved_at=data["retrieved_at"],
        profile=data["profile"],
        period_performance=data["period_performance"],
        ohlcv=data["ohlcv"],
        data_quality=data["data_quality"],
        financial_statements=data["financial_statements"],
        sources=data["sources"],
    )


@router.get("/{ticker}/fundamental")
async def analyze_stock_fundamentals(
    ticker: str,
    market: str = Query("NASDAQ", description="Target exchange (NSE, BSE, NASDAQ, NYSE)"),
    period: str = Query("1 Year", description="Analysis period"),
    include_peers: bool = Query(True, description="Include sector peer comparison"),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Module 3 endpoint: Run the Fundamental Analysis Agent for a stock and return
    revenue/earnings, profitability, debt/stability, ratios (P/E, P/B, ROE),
    historical performance, peer comparison, and missing-data diagnostics.
    """
    clean_market, clean_period = _validate_market_and_period(market, period)
    market_data = MarketDataCollector.collect_market_data(
        ticker=ticker,
        market=clean_market,
        period=clean_period,
        include_warmup=False,
    )
    agent = FundamentalAnalysisAgent()
    analysis = await agent.analyze(
        ticker=market_data["ticker"],
        market=clean_market,
        period=clean_period,
        market_data=market_data,
        include_peers=include_peers,
    )
    return {
        "ticker": market_data["ticker"],
        "market": clean_market,
        "yf_symbol": market_data["yf_symbol"],
        "profile": market_data["profile"],
        "data_quality": market_data["data_quality"],
        "sources": market_data["sources"],
        "fundamental_analysis": analysis,
    }


@router.get("/{ticker}/technical")
async def analyze_stock_technical(
    ticker: str,
    market: str = Query("NASDAQ", description="Target exchange (NSE, BSE, NASDAQ, NYSE)"),
    period: str = Query("1 Year", description="Analysis period"),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Module 4 endpoint: Run the Technical Analysis Agent for a stock and return
    SMA, EMA, RSI, MACD, historical volatility, predefined technical conditions,
    and chart-ready OHLCV + indicator time series.
    """
    clean_market, clean_period = _validate_market_and_period(market, period)
    market_data = MarketDataCollector.collect_market_data(
        ticker=ticker,
        market=clean_market,
        period=clean_period,
        include_warmup=True,
    )
    agent = TechnicalAnalysisAgent()
    analysis = await agent.analyze(
        ticker=market_data["ticker"],
        market=clean_market,
        period=clean_period,
        market_data=market_data,
    )
    return {
        "ticker": market_data["ticker"],
        "market": clean_market,
        "yf_symbol": market_data["yf_symbol"],
        "profile": market_data["profile"],
        "data_quality": market_data["data_quality"],
        "sources": market_data["sources"],
        "technical_analysis": analysis,
    }
