from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from app.dependencies import get_current_user
from app.models import User

router = APIRouter(prefix="/stocks", tags=["Stock search"])
SUFFIX = {"NSE": ".NS", "BSE": ".BO", "NASDAQ": "", "NYSE": ""}

def provider_symbol(ticker: str, market: str) -> str:
    clean = ticker.strip().upper().replace(".NS", "").replace(".BO", "")
    return clean + SUFFIX[market]

@router.get("/search")
def search_stocks(q: str = Query(min_length=1, max_length=80), market: str = Query(pattern="^(NSE|BSE|NASDAQ|NYSE)$"), user: User = Depends(get_current_user)):
    """Search Yahoo Finance's symbol catalogue. Results depend on provider coverage and rate limits."""
    try:
        import yfinance as yf
        query = q.strip()
        search = yf.Search(query, max_results=10, news_count=0)
        quotes = search.quotes or []
        results = []
        for item in quotes:
            symbol = item.get("symbol", "")
            exchange = (item.get("exchange") or "").upper()
            quote_type = item.get("quoteType", "")
            if quote_type and quote_type not in ("EQUITY", "ETF"):
                continue
            if market == "NSE" and not symbol.endswith(".NS"):
                continue
            if market == "BSE" and not symbol.endswith(".BO"):
                continue
            if market in ("NASDAQ", "NYSE"):
                if symbol.endswith((".NS", ".BO")):
                    continue
                if market == "NASDAQ" and exchange not in ("NMS", "NGM", "NCM", "NASDAQ"):
                    continue
                if market == "NYSE" and exchange not in ("NYQ", "NYSE"):
                    continue
            clean = symbol.replace(".NS", "").replace(".BO", "")
            results.append({
                "company_name": item.get("longname") or item.get("shortname") or clean,
                "ticker": clean,
                "market": market,
                "provider_symbol": symbol,
                "price": item.get("regularMarketPrice"),
                "change_percent": item.get("regularMarketChangePercent"),
                "currency": item.get("currency"),
            })
        return {"results": results, "source": "Yahoo Finance search", "note": "Search coverage and availability are provided by the market-data provider."}
    except Exception as exc:
        raise HTTPException(502, f"Stock search provider is temporarily unavailable: {type(exc).__name__}")

@router.get("/quote")
def quote(ticker: str = Query(min_length=1, max_length=30), market: str = Query(pattern="^(NSE|BSE|NASDAQ|NYSE)$"), user: User = Depends(get_current_user)):
    try:
        import yfinance as yf
        symbol = provider_symbol(ticker, market)
        info = yf.Ticker(symbol).fast_info
        price = info.get("last_price")
        previous = info.get("previous_close")
        change_percent = ((price - previous) / previous * 100) if price is not None and previous else None
        return {"ticker": ticker.strip().upper(), "market": market, "provider_symbol": symbol, "price": price, "previous_close": previous, "change_percent": change_percent, "currency": info.get("currency")}
    except Exception as exc:
        raise HTTPException(502, f"Quote provider is temporarily unavailable: {type(exc).__name__}")

@router.get("/analytics")
def analytics(ticker: str = Query(min_length=1, max_length=30), market: str = Query(pattern="^(NSE|BSE|NASDAQ|NYSE)$"), period: str = Query(default="1 Year", pattern="^(1 Month|3 Months|6 Months|1 Year|5 Years)$"), user: User = Depends(get_current_user)):
    periods = {"1 Month": "1mo", "3 Months": "3mo", "6 Months": "6mo", "1 Year": "1y", "5 Years": "5y"}
    try:
        import yfinance as yf
        import pandas as pd
        symbol = provider_symbol(ticker, market)
        frame = yf.Ticker(symbol).history(period=periods[period], auto_adjust=False)
        if frame.empty or "Close" not in frame:
            raise HTTPException(404, "No historical data is available for this ticker and period.")
        close = frame["Close"].dropna()
        returns = close.pct_change().dropna()
        delta = close.diff()
        gains = delta.clip(lower=0).rolling(14).mean()
        losses = (-delta.clip(upper=0)).rolling(14).mean()
        rsi_series = pd.Series(50.0, index=close.index)
        active = losses > 0
        rsi_series.loc[active] = 100 - (100 / (1 + gains.loc[active] / losses.loc[active]))
        rsi_series.loc[(losses == 0) & (gains > 0)] = 100
        rsi = rsi_series.iloc[-1]
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        rolling_peak = close.cummax()
        drawdown = (close - rolling_peak) / rolling_peak
        return {
            "ticker": ticker.strip().upper(), "market": market, "provider_symbol": symbol, "period": period,
            "period_high": float(close.max()), "period_low": float(close.min()),
            "horizon_return": float((close.iloc[-1] / close.iloc[0] - 1) * 100),
            "maximum_drawdown": float(drawdown.min() * 100),
            "annualized_volatility": float(returns.std() * (252 ** 0.5) * 100) if len(returns) > 1 else None,
            "sma_50": float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None,
            "sma_200": float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None,
            "rsi_14": None if pd.isna(rsi) else float(rsi),
            "macd": float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else None,
            "macd_signal": float(signal.iloc[-1]) if not pd.isna(signal.iloc[-1]) else None,
            "as_of": datetime.now(timezone.utc),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Analytics provider is temporarily unavailable: {type(exc).__name__}")

@router.get("/indices")
def indices(user: User = Depends(get_current_user)):
    try:
        import yfinance as yf
        symbols = {"S&P 500": "^GSPC", "Nasdaq": "^IXIC", "Dow Jones": "^DJI", "Nifty 50": "^NSEI"}
        output = []
        for name, symbol in symbols.items():
            info = yf.Ticker(symbol).fast_info
            price = info.get("last_price")
            previous = info.get("previous_close")
            output.append({"name": name, "symbol": symbol, "price": price, "change_percent": ((price - previous) / previous * 100) if price is not None and previous else None})
        return output
    except Exception as exc:
        raise HTTPException(502, f"Index provider is temporarily unavailable: {type(exc).__name__}")
