import datetime
import logging
import time
from typing import Optional, Dict, Any, List
import yfinance as yf
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Simple in-memory cache with TTL (60 seconds) to prevent Yahoo Finance rate limits
_QUOTE_CACHE: Dict[str, Dict[str, Any]] = {}
_TICKER_TAPE_CACHE: Dict[str, Any] = {"data": None, "cached_at": 0}
CACHE_TTL_SECONDS = 60

# Preset popular stock universe for immediate search / autocomplete support
POPULAR_STOCKS = {
    "NSE": [
        {"ticker": "RELIANCE", "name": "Reliance Industries Ltd", "market": "NSE"},
        {"ticker": "TCS", "name": "Tata Consultancy Services Ltd", "market": "NSE"},
        {"ticker": "INFY", "name": "Infosys Ltd", "market": "NSE"},
        {"ticker": "HDFCBANK", "name": "HDFC Bank Ltd", "market": "NSE"},
        {"ticker": "ICICIBANK", "name": "ICICI Bank Ltd", "market": "NSE"},
        {"ticker": "TATAMOTORS", "name": "Tata Motors Ltd", "market": "NSE"},
        {"ticker": "BHARTIARTL", "name": "Bharti Airtel Ltd", "market": "NSE"},
        {"ticker": "ITC", "name": "ITC Ltd", "market": "NSE"},
        {"ticker": "SBIN", "name": "State Bank of India", "market": "NSE"},
        {"ticker": "LICI", "name": "Life Insurance Corp of India", "market": "NSE"},
    ],
    "BSE": [
        {"ticker": "RELIANCE", "name": "Reliance Industries Ltd", "market": "BSE"},
        {"ticker": "TCS", "name": "Tata Consultancy Services Ltd", "market": "BSE"},
        {"ticker": "INFY", "name": "Infosys Ltd", "market": "BSE"},
        {"ticker": "HDFCBANK", "name": "HDFC Bank Ltd", "market": "BSE"},
    ],
    "NASDAQ": [
        {"ticker": "AAPL", "name": "Apple Inc.", "market": "NASDAQ"},
        {"ticker": "MSFT", "name": "Microsoft Corporation", "market": "NASDAQ"},
        {"ticker": "GOOGL", "name": "Alphabet Inc.", "market": "NASDAQ"},
        {"ticker": "NVDA", "name": "NVIDIA Corporation", "market": "NASDAQ"},
        {"ticker": "AMZN", "name": "Amazon.com, Inc.", "market": "NASDAQ"},
        {"ticker": "TSLA", "name": "Tesla, Inc.", "market": "NASDAQ"},
        {"ticker": "META", "name": "Meta Platforms, Inc.", "market": "NASDAQ"},
    ],
    "NYSE": [
        {"ticker": "JNJ", "name": "Johnson & Johnson", "market": "NYSE"},
        {"ticker": "JPM", "name": "JPMorgan Chase & Co.", "market": "NYSE"},
        {"ticker": "V", "name": "Visa Inc.", "market": "NYSE"},
        {"ticker": "WMT", "name": "Walmart Inc.", "market": "NYSE"},
    ]
}


def resolve_symbol(ticker: str, market: str = "NSE") -> str:
    """
    Normalizes stock ticker based on market exchange.
    NSE -> TICKER.NS
    BSE -> TICKER.BO
    NASDAQ / NYSE -> TICKER
    """
    clean_ticker = ticker.strip().upper()
    market_upper = market.strip().upper()

    if market_upper == "NSE":
        if not clean_ticker.endswith(".NS"):
            return f"{clean_ticker}.NS"
        return clean_ticker
    elif market_upper == "BSE":
        if not clean_ticker.endswith(".BO"):
            return f"{clean_ticker}.BO"
        return clean_ticker
    else:
        return clean_ticker.replace(".NS", "").replace(".BO", "")


def get_realtime_quote(ticker: str, market: str = "NSE") -> Dict[str, Any]:
    """
    Fetches real-time price, percentage change, financial ratios,
    and 52-week extremes from Yahoo Finance.
    """
    resolved = resolve_symbol(ticker, market)
    now = time.time()

    if resolved in _QUOTE_CACHE:
        cached_entry = _QUOTE_CACHE[resolved]
        if now - cached_entry["cached_at"] < CACHE_TTL_SECONDS:
            return cached_entry["data"]

    try:
        yf_ticker = yf.Ticker(resolved)
        fast_info = yf_ticker.fast_info
        
        last_price = float(fast_info.last_price or 0.0)
        previous_close = float(fast_info.previous_close or last_price or 1.0)
        
        change = round(last_price - previous_close, 2)
        change_percent = round((change / previous_close) * 100, 2) if previous_close else 0.0
        
        year_high = float(fast_info.year_high or (last_price * 1.15))
        year_low = float(fast_info.year_low or (last_price * 0.85))
        market_cap = float(fast_info.market_cap or 0.0)
        currency = fast_info.currency or ("INR" if "NSE" in market.upper() or "BSE" in market.upper() else "USD")

        info = {}
        try:
            info = yf_ticker.info or {}
        except Exception:
            info = {}

        name = info.get("shortName") or info.get("longName") or ticker.upper()
        pe_ratio = info.get("trailingPE") or info.get("forwardPE")
        pb_ratio = info.get("priceToBook")
        roe = info.get("returnOnEquity")
        debt_to_equity = info.get("debtToEquity")
        volume = info.get("regularMarketVolume") or fast_info.last_volume or 0
        day_high = info.get("dayHigh") or fast_info.day_high or last_price
        day_low = info.get("dayLow") or fast_info.day_low or last_price
        sector = info.get("sector") or "Diversified"
        industry = info.get("industry") or "Equities"

        quote_data = {
            "ticker": ticker.upper(),
            "resolved_symbol": resolved,
            "company_name": name,
            "market": market.upper(),
            "currency": currency,
            "price": round(last_price, 2),
            "change": change,
            "change_percent": change_percent,
            "previous_close": round(previous_close, 2),
            "day_high": round(float(day_high), 2),
            "day_low": round(float(day_low), 2),
            "fifty_two_week_high": round(year_high, 2),
            "fifty_two_week_low": round(year_low, 2),
            "volume": int(volume),
            "market_cap": round(market_cap, 2),
            "pe_ratio": round(float(pe_ratio), 2) if pe_ratio else None,
            "pb_ratio": round(float(pb_ratio), 2) if pb_ratio else None,
            "roe": round(float(roe) * 100, 2) if roe else None,
            "debt_to_equity": round(float(debt_to_equity), 2) if debt_to_equity else None,
            "sector": sector,
            "industry": industry,
            "data_source": "Live Exchange Feed",
            "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

        _QUOTE_CACHE[resolved] = {"data": quote_data, "cached_at": now}
        return quote_data

    except Exception as e:
        logger.error(f"Failed to fetch real-time quote for {resolved}: {e}")
        return {
            "ticker": ticker.upper(),
            "resolved_symbol": resolved,
            "company_name": ticker.upper(),
            "market": market.upper(),
            "currency": "INR" if market.upper() in ["NSE", "BSE"] else "USD",
            "price": 0.0,
            "change": 0.0,
            "change_percent": 0.0,
            "previous_close": 0.0,
            "day_high": 0.0,
            "day_low": 0.0,
            "fifty_two_week_high": 0.0,
            "fifty_two_week_low": 0.0,
            "volume": 0,
            "market_cap": 0.0,
            "pe_ratio": None,
            "pb_ratio": None,
            "roe": None,
            "debt_to_equity": None,
            "sector": "N/A",
            "industry": "N/A",
            "data_source": "Market Feed",
            "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "error": str(e)
        }


def get_ticker_tape_indices() -> List[Dict[str, Any]]:
    """
    Fetches real-time live prices for major market indices for the top ticker tape.
    """
    global _TICKER_TAPE_CACHE
    now = time.time()
    if _TICKER_TAPE_CACHE["data"] and (now - _TICKER_TAPE_CACHE["cached_at"] < 90):
        return _TICKER_TAPE_CACHE["data"]

    symbols = [
        {"name": "NIFTY 50", "symbol": "^NSEI", "currency": "₹"},
        {"name": "SENSEX", "symbol": "^BSESN", "currency": "₹"},
        {"name": "NASDAQ", "symbol": "^IXIC", "currency": "$"},
        {"name": "S&P 500", "symbol": "^GSPC", "currency": "$"},
        {"name": "BRENT CRUDE", "symbol": "BZ=F", "currency": "$"},
        {"name": "GOLD (10G)", "symbol": "GC=F", "currency": "$"},
    ]

    tape_items = []
    for item in symbols:
        try:
            t = yf.Ticker(item["symbol"])
            fi = t.fast_info
            price = float(fi.last_price or 0.0)
            prev = float(fi.previous_close or price or 1.0)
            chg_pct = round(((price - prev) / prev) * 100, 2) if prev else 0.0
            
            tape_items.append({
                "symbol": item["name"],
                "value": f"{item['currency']}{price:,.2f}",
                "change": f"{chg_pct:+.2f}%",
                "isPositive": chg_pct >= 0
            })
        except Exception:
            tape_items.append({
                "symbol": item["name"],
                "value": f"{item['currency']}--",
                "change": "0.00%",
                "isPositive": True
            })

    _TICKER_TAPE_CACHE = {"data": tape_items, "cached_at": now}
    return tape_items


def get_stock_comprehensive_analysis(ticker: str, market: str = "NSE", period: str = "1y") -> Dict[str, Any]:
    """
    Combines real-time quotes, calculated technical indicators (SMA, RSI, MACD),
    real financial news from Yahoo Finance, and calculated risk metrics (Max Drawdown)
    for the dynamically requested analysis period (1 Month, 3 Months, 6 Months, 1 Year, 5 Years).
    """
    quote = get_realtime_quote(ticker, market)
    resolved = resolve_symbol(ticker, market)

    # Map user timeframe string to yfinance interval
    period_map = {
        "1 month": "1mo",
        "1m": "1mo",
        "1mo": "1mo",
        "3 months": "3mo",
        "3m": "3mo",
        "3mo": "3mo",
        "6 months": "6mo",
        "6m": "6mo",
        "6mo": "6mo",
        "1 year": "1y",
        "1y": "1y",
        "5 years": "5y",
        "5y": "5y"
    }
    cleaned_period = str(period).lower().strip()
    yf_period = period_map.get(cleaned_period, "1y")
    display_period = {
        "1mo": "1 Month",
        "3mo": "3 Months",
        "6mo": "6 Months",
        "1y": "1 Year",
        "5y": "5 Years"
    }.get(yf_period, "1 Year")

    # 1. Fetch historical candles for calculations
    yf_ticker = yf.Ticker(resolved)
    
    # Technical & Risk calculations
    tech_signals = {
        "sma_50": "N/A",
        "sma_200": "N/A",
        "rsi_14": "N/A",
        "macd": "N/A",
        "volatility": "N/A",
        "trend_summary": "Neutral",
        "crossover": "Neutral",
        "period_analyzed": display_period
    }
    
    risk_metrics = {
        "max_drawdown": "-0.00%",
        "volatility_annualized": "N/A",
        "conflict_status": "CONVERGENT",
        "risk_level": "MODERATE",
        "period_analyzed": display_period,
        "period_return": "0.00%",
        "period_high": 0.0,
        "period_low": 0.0
    }

    try:
        hist = yf_ticker.history(period=yf_period)
        if not hist.empty and len(hist) >= 5:
            close = hist["Close"]
            
            # Period Performance & Price Range
            start_price = float(close.iloc[0])
            end_price = float(close.iloc[-1])
            period_return_pct = round(((end_price - start_price) / (start_price if start_price else 1.0)) * 100, 2)
            period_high = float(hist["High"].max())
            period_low = float(hist["Low"].min())

            # SMAs adjusted for window length
            w50 = min(50, len(close))
            w200 = min(200, len(close))
            s50 = close.rolling(window=w50).mean().iloc[-1]
            s200 = close.rolling(window=w200).mean().iloc[-1]
            tech_signals["sma_50"] = f"{round(s50, 2)}"
            tech_signals["sma_200"] = f"{round(s200, 2)}"
            
            # RSI 14 (or dynamic window if short period)
            rsi_window = min(14, max(5, len(close) - 1))
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_window).mean()
            rs = gain / (loss.replace(0, 0.0001))
            rsi_val = 100 - (100 / (1 + rs)).iloc[-1]
            tech_signals["rsi_14"] = f"{round(rsi_val, 2)}"
            
            # MACD
            span_fast = min(12, max(3, len(close) // 2))
            span_slow = min(26, max(6, len(close)))
            ema12 = close.ewm(span=span_fast, adjust=False).mean()
            ema26 = close.ewm(span=span_slow, adjust=False).mean()
            macd_val = (ema12 - ema26).iloc[-1]
            tech_signals["macd"] = f"{round(macd_val, 2)}"
            
            # Volatility in requested period
            vol_val = (close.pct_change().std() * np.sqrt(min(252, len(close)))) * 100
            tech_signals["volatility"] = f"{round(vol_val, 2)}%"
            risk_metrics["volatility_annualized"] = f"{round(vol_val, 2)}%"

            # Max Drawdown across this specific timeframe
            peak = close.cummax()
            dd = (close - peak) / peak
            max_dd = dd.min() * 100
            risk_metrics["max_drawdown"] = f"{round(max_dd, 2)}%"
            risk_metrics["period_analyzed"] = display_period
            risk_metrics["period_return"] = f"{period_return_pct:+.2f}%"
            risk_metrics["period_high"] = round(period_high, 2)
            risk_metrics["period_low"] = round(period_low, 2)

            if s50 >= s200:
                tech_signals["crossover"] = "Golden Cross (Bullish)"
                tech_signals["trend_summary"] = "Bullish Accumulation"
            else:
                tech_signals["crossover"] = "Death Cross (Bearish)"
                tech_signals["trend_summary"] = "Bearish Distribution"

            if abs(max_dd) > 25:
                risk_metrics["risk_level"] = "HIGH"
            elif abs(max_dd) > 12:
                risk_metrics["risk_level"] = "MODERATE"
            else:
                risk_metrics["risk_level"] = "LOW"
    except Exception as e:
        logger.error(f"Error calculating technical/risk indicators: {e}")

    # 2. Fetch real live news from Yahoo Finance
    real_news = []
    try:
        raw_news = yf_ticker.news or []
        for item in raw_news[:5]:
            title = item.get("title")
            if not title and "content" in item:
                title = item["content"].get("title")
            publisher = item.get("publisher")
            if not publisher and "content" in item and "provider" in item["content"]:
                publisher = item["content"]["provider"].get("displayName")
            link = item.get("link")
            if not link and "content" in item:
                link = item["content"].get("canonicalUrl", {}).get("url") or item["content"].get("clickThroughUrl", {}).get("url")
            pub_time = item.get("providerPublishTime")
            time_str = "Recent"
            if pub_time:
                time_str = datetime.datetime.fromtimestamp(pub_time, datetime.timezone.utc).strftime("%d %b, %H:%M UTC")

            if title:
                real_news.append({
                    "title": title,
                    "publisher": publisher or "Financial Wire",
                    "link": link or "https://finance.yahoo.com",
                    "published_at": time_str,
                    "sentiment": "POSITIVE" if any(w in title.lower() for w in ["gain", "rise", "invest", "expand", "profit", "bull", "growth"]) else ("NEGATIVE" if any(w in title.lower() for w in ["fall", "drop", "cut", "loss", "bear", "down"]) else "NEUTRAL")
                })
    except Exception as e:
        logger.error(f"Error fetching live news: {e}")

    return {
        "quote": quote,
        "technical": tech_signals,
        "risk": risk_metrics,
        "news": real_news
    }


def get_historical_candles(ticker: str, market: str = "NSE", period: str = "1y") -> List[Dict[str, Any]]:
    """
    Fetches historical OHLCV candles (Open, High, Low, Close, Volume)
    for requested period (1mo, 3mo, 6mo, 1y, 5y).
    """
    resolved = resolve_symbol(ticker, market)
    
    period_map = {
        "1 month": "1mo",
        "1m": "1mo",
        "3 months": "3mo",
        "3m": "3mo",
        "6 months": "6mo",
        "6m": "6mo",
        "1 year": "1y",
        "1y": "1y",
        "5 years": "5y",
        "5y": "5y"
    }
    yf_period = period_map.get(period.lower().strip(), "1y")

    try:
        yf_ticker = yf.Ticker(resolved)
        hist = yf_ticker.history(period=yf_period)

        if hist.empty:
            return []

        candles = []
        for index, row in hist.iterrows():
            candles.append({
                "date": index.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            })
        return candles

    except Exception as e:
        logger.error(f"Failed to fetch historical candles for {resolved}: {e}")
        return []
