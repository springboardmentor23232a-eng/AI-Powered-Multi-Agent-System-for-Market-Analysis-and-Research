from datetime import datetime, timezone
import pandas as pd
import yfinance as yf

MARKET_SUFFIX = {"NSE": ".NS", "BSE": ".BO", "NASDAQ": "", "NYSE": ""}
PERIODS = {"1mo": "1mo", "3mo": "3mo", "6mo": "6mo", "1y": "1y", "5y": "5y"}

class MarketDataError(Exception):
    pass

def yahoo_symbol(symbol: str, market: str):
    if market not in MARKET_SUFFIX:
        raise MarketDataError("Unsupported market")
    base = symbol.strip().upper()
    suffix = MARKET_SUFFIX[market]
    return base if not suffix or base.endswith(suffix) else base + suffix

def search_stocks(query: str, market: str):
    # Yahoo Finance search is used for discovery; no result is fabricated.
    try:
        results = yf.Search(query, max_results=12).quotes
    except Exception as exc:
        raise MarketDataError(f"Yahoo Finance search unavailable: {exc}")
    output = []
    for item in results:
        symbol = item.get("symbol", "")
        quote_type = item.get("quoteType", "")
        if not symbol or quote_type not in ("EQUITY", "ETF"):
            continue
        if market == "NSE" and not symbol.endswith(".NS"): continue
        if market == "BSE" and not symbol.endswith(".BO"): continue
        if market in ("NASDAQ", "NYSE") and symbol.endswith((".NS", ".BO")): continue
        output.append({"symbol": symbol, "name": item.get("shortname") or item.get("longname") or symbol,
                       "market": market, "exchange": item.get("exchange", "")})
    return output

def fetch_history(symbol: str, market: str, period: str):
    if period not in PERIODS:
        raise MarketDataError("Unsupported analysis period")
    ticker_symbol = yahoo_symbol(symbol, market)
    try:
        df = yf.Ticker(ticker_symbol).history(period=period, auto_adjust=False)
    except Exception as exc:
        raise MarketDataError(f"Yahoo Finance retrieval failed: {exc}")
    if df.empty:
        raise MarketDataError("No historical price data was returned by Yahoo Finance")
    df = df.reset_index()
    date_col = "Date" if "Date" in df.columns else "Datetime"
    warnings = []
    required = ["Open", "High", "Low", "Close", "Volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise MarketDataError(f"Yahoo Finance response is missing columns: {', '.join(missing)}")
    before = len(df)
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    if len(df) != before: warnings.append(f"{before-len(df)} rows dropped due to missing OHLC values")
    duplicate_count = int(df[date_col].duplicated().sum())
    if duplicate_count:
        df = df.drop_duplicates(subset=[date_col], keep="last")
        warnings.append(f"{duplicate_count} duplicate date rows removed")
    invalid = (df["High"] < df["Low"]) | (df["High"] < df[["Open","Close"]].max(axis=1)) | (df["Low"] > df[["Open","Close"]].min(axis=1))
    if invalid.any():
        warnings.append(f"{int(invalid.sum())} rows contain inconsistent OHLC values")
        df = df.loc[~invalid]
    rows = []
    for _, r in df.iterrows():
        dt = pd.Timestamp(r[date_col]).to_pydatetime()
        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
        rows.append({"date": dt.isoformat(), "open": float(r.Open), "high": float(r.High),
                     "low": float(r.Low), "close": float(r.Close),
                     "volume": int(r.Volume) if pd.notna(r.Volume) else None})
    return {"symbol": ticker_symbol, "market": market, "period": period, "source": "Yahoo Finance via yfinance",
            "retrieved_at": datetime.now(timezone.utc).isoformat(), "data": rows, "warnings": warnings}

def fetch_profile(symbol: str, market: str):
    info = yf.Ticker(yahoo_symbol(symbol, market)).get_info()
    if not info:
        raise MarketDataError("Company profile is not available")
    keys = ["longName", "symbol", "sector", "industry", "website", "longBusinessSummary",
            "country", "currency", "fullTimeEmployees", "marketCap"]
    return {k: info.get(k) for k in keys if info.get(k) is not None}

def fetch_financials(symbol: str, market: str):
    t = yf.Ticker(yahoo_symbol(symbol, market))
    def records(frame):
        if frame is None or frame.empty: return []
        return [{"metric": str(idx), **{str(col.date()): (None if pd.isna(val) else float(val))
                    for col, val in row.items()}} for idx, row in frame.iterrows()]
    return {"income_statement": records(t.income_stmt), "balance_sheet": records(t.balance_sheet),
            "cash_flow": records(t.cashflow), "source": "Yahoo Finance via yfinance"}
