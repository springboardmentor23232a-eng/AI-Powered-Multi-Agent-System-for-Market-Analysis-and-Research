from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from app.schemas import StockQuoteResponse, HistoricalCandleResponse
from app.services.market_data import (
    get_realtime_quote,
    get_historical_candles,
    get_ticker_tape_indices,
    get_stock_comprehensive_analysis,
    POPULAR_STOCKS
)

router = APIRouter(prefix="/market", tags=["Market Data (yfinance)"])


@router.get("/ticker-tape")
def get_ticker_tape():
    """
    Returns live real-time quotes for major market indices
    (NIFTY 50, SENSEX, NASDAQ, S&P 500, Crude, Gold) for the top ticker tape.
    """
    return get_ticker_tape_indices()


@router.get("/quote/{ticker}", response_model=StockQuoteResponse)
def get_quote(ticker: str, market: str = Query("NSE", description="Market exchange e.g. NSE, BSE, NASDAQ, NYSE")):
    """
    Returns real-time stock quote from Yahoo Finance including
    LTP, day change, 52W range, P/E, P/B, ROE, and retrieval timestamp.
    """
    quote = get_realtime_quote(ticker, market)
    return quote


@router.get("/analysis/{ticker}")
def get_analysis(
    ticker: str,
    market: str = Query("NSE", description="Market exchange e.g. NSE, BSE, NASDAQ"),
    period: str = Query("1y", description="Analysis period")
):
    """
    Returns complete real-time quantitative analysis:
    - Real-time quote and valuation ratios
    - Calculated technical indicators (SMA 50, SMA 200, RSI 14, MACD, Volatility)
    - Live Yahoo Finance financial news articles
    - Quantitative risk metrics (Max Drawdown, Volatility)
    """
    return get_stock_comprehensive_analysis(ticker, market, period)


@router.get("/history/{ticker}", response_model=List[HistoricalCandleResponse])
def get_history(
    ticker: str,
    market: str = Query("NSE", description="Market exchange"),
    period: str = Query("1y", description="Analysis period e.g. 1mo, 3mo, 6mo, 1y, 5y")
):
    """
    Returns historical OHLCV candlestick data for chart plotting.
    """
    candles = get_historical_candles(ticker, market, period)
    return candles


@router.get("/popular")
def get_popular_stocks(market: str = Query("NSE")):
    """
    Returns popular preset universe for quick search / autocomplete.
    """
    market_upper = market.upper()
    return POPULAR_STOCKS.get(market_upper, POPULAR_STOCKS["NSE"])
