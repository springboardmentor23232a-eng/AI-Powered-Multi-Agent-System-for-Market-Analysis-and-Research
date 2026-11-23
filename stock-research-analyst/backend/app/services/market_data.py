from datetime import datetime, timezone
from typing import Any
import httpx
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.linear_model import LinearRegression

PERIOD_MAP = {
    "1M": "1mo",
    "3M": "3mo",
    "6M": "6mo",
    "1Y": "1y",
    "5Y": "5y",
}

MARKET_SUFFIX = {
    "NSE": ".NS",
    "BSE": ".BO",
    "NASDAQ": "",
    "NYSE": "",
}

EXCHANGE_CODES = {
    "NSE": {"NSI", "NSE"},
    "BSE": {"BSE", "BOM"},
    "NASDAQ": {"NMS", "NGM", "NCM", "NAS", "NASDAQ"},
    "NYSE": {"NYQ", "NYSE"},
}

YF_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


def utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def format_yfinance_ticker(ticker: str, market: str) -> str:
    clean = ticker.strip().upper()
    if "." in clean:
        return clean
    suffix = MARKET_SUFFIX.get(market.upper(), "")
    return f"{clean}{suffix}"


def validate_and_clean_ohlcv(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Validate and clean OHLCV data for missing values, duplicate dates, and inconsistent prices."""
    df = raw_df.copy()
    df.index = pd.to_datetime(df.index).tz_localize(None)

    dup_count = int(df.index.duplicated(keep="last").sum())
    if dup_count > 0:
        df = df[~df.index.duplicated(keep="last")]
    df = df.sort_index()

    required_cols = ["Open", "High", "Low", "Close", "Volume"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = np.nan

    missing_before = int(df[required_cols].isna().sum().sum())
    df["Volume"] = df["Volume"].fillna(0)
    df[["Open", "High", "Low", "Close"]] = df[["Open", "High", "Low", "Close"]].ffill().bfill()
    df = df.dropna(subset=["Open", "High", "Low", "Close"])

    inconsistent_mask = (
        (df["Open"] <= 0)
        | (df["High"] <= 0)
        | (df["Low"] <= 0)
        | (df["Close"] <= 0)
        | (df["Volume"] < 0)
        | (df["High"] < df["Low"])
        | (df["High"] < df[["Open", "Close"]].max(axis=1))
        | (df["Low"] > df[["Open", "Close"]].min(axis=1))
    )
    inconsistent_count = int(inconsistent_mask.sum())
    if inconsistent_count > 0:
        df = df[(df["Open"] > 0) & (df["High"] > 0) & (df["Low"] > 0) & (df["Close"] > 0)].copy()
        df["Volume"] = df["Volume"].clip(lower=0)
        df["High"] = df[["Open", "High", "Low", "Close"]].max(axis=1)
        df["Low"] = df[["Open", "High", "Low", "Close"]].min(axis=1)

    report = {
        "total_valid_rows": int(len(df)),
        "duplicate_dates_removed": dup_count,
        "missing_values_handled": missing_before,
        "inconsistent_rows_fixed": inconsistent_count,
        "validation_status": "Passed" if (dup_count == 0 and missing_before == 0 and inconsistent_count == 0) else "Cleaned",
    }
    return df, report


def _fetch_chart_api_df(yf_symbol: str, yf_period: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Direct Yahoo Finance v8 chart API fallback (uses server-side range, immune to local clock skew)."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_symbol}"
    try:
        with httpx.Client(timeout=15.0, headers=YF_HEADERS) as client:
            resp = client.get(url, params={"range": yf_period, "interval": "1d"})
            if resp.status_code != 200:
                return pd.DataFrame(), {}
            data = resp.json()
            result = (data.get("chart") or {}).get("result") or []
            if not result:
                return pd.DataFrame(), {}
            item = result[0]
            meta = item.get("meta") or {}
            timestamps = item.get("timestamp") or []
            quote = ((item.get("indicators") or {}).get("quote") or [{}])[0]
            if not timestamps or not quote.get("close"):
                return pd.DataFrame(), meta
            df = pd.DataFrame(
                {
                    "Open": quote.get("open", []),
                    "High": quote.get("high", []),
                    "Low": quote.get("low", []),
                    "Close": quote.get("close", []),
                    "Volume": quote.get("volume", []),
                },
                index=pd.to_datetime(timestamps, unit="s", utc=True),
            )
            return df.dropna(subset=["Close"]), meta
    except Exception:
        return pd.DataFrame(), {}


def _fetch_history_df(yf_symbol: str, yf_period: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    # 1. Try yfinance Ticker.history
    try:
        stock = yf.Ticker(yf_symbol)
        hist = stock.history(period=yf_period)
        if hist is not None and not hist.empty:
            return hist, {}
    except Exception:
        pass

    # 2. Try yfinance.download
    try:
        dl = yf.download(yf_symbol, period=yf_period, progress=False, auto_adjust=True)
        if dl is not None and not dl.empty:
            if isinstance(dl.columns, pd.MultiIndex):
                dl.columns = dl.columns.get_level_values(0)
            return dl, {}
    except Exception:
        pass

    # 3. Direct Yahoo Finance v8 chart API fallback
    return _fetch_chart_api_df(yf_symbol, yf_period)


def _search_yahoo_quotes(query: str) -> list[dict[str, Any]]:
    quotes: list[dict[str, Any]] = []
    try:
        search = yf.Search(query, max_results=12)
        quotes = getattr(search, "quotes", []) or []
    except Exception:
        quotes = []

    if not quotes:
        try:
            with httpx.Client(timeout=10.0, headers=YF_HEADERS) as client:
                resp = client.get(
                    "https://query1.finance.yahoo.com/v1/finance/search",
                    params={"q": query, "quotesCount": 12, "newsCount": 0},
                )
                if resp.status_code == 200:
                    quotes = resp.json().get("quotes", []) or []
        except Exception:
            quotes = []
    return quotes


def _resolve_symbol_with_fallback(ticker: str, market: str, yf_period: str) -> tuple[str, pd.DataFrame, dict[str, Any]]:
    """Try selected market first, then .NS/.BO or Yahoo Search for company names."""
    primary = format_yfinance_ticker(ticker, market)
    hist, meta = _fetch_history_df(primary, yf_period)
    if not hist.empty:
        return primary, hist, meta

    clean = ticker.strip().upper().split(".")[0]
    for candidate in (f"{clean}.NS", f"{clean}.BO", clean):
        if candidate == primary:
            continue
        hist, meta = _fetch_history_df(candidate, yf_period)
        if not hist.empty:
            return candidate, hist, meta

    for q in _search_yahoo_quotes(ticker.strip()):
        sym = (q.get("symbol") or "").upper()
        if sym:
            hist, meta = _fetch_history_df(sym, yf_period)
            if not hist.empty:
                return sym, hist, meta

    return primary, pd.DataFrame(), {}


def _serialize_statement(df: pd.DataFrame, max_cols: int = 4, max_rows: int = 12) -> list[dict[str, Any]]:
    if df is None or df.empty:
        return []
    trimmed = df.iloc[:max_rows, :max_cols]
    rows: list[dict[str, Any]] = []
    for metric, series in trimmed.iterrows():
        values = {}
        for col, val in series.items():
            col_label = col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col)
            values[col_label] = None if pd.isna(val) else float(val)
        rows.append({"metric": str(metric), "values": values})
    return rows


def search_companies(query: str, market: str) -> dict[str, Any]:
    """Search for companies by name or ticker symbol using Yahoo Finance, filtered by market."""
    retrieved_at = utc_iso_now()
    clean_query = query.strip()
    target_market = market.upper()
    allowed_exchanges = EXCHANGE_CODES.get(target_market, set())

    matches: list[dict[str, Any]] = []
    for q in _search_yahoo_quotes(clean_query):
        symbol = (q.get("symbol") or "").upper()
        exchange = (q.get("exchange") or "").upper()
        exch_disp = (q.get("exchDisp") or "").upper()
        if not symbol:
            continue

        is_match = (
            exchange in allowed_exchanges
            or exch_disp in allowed_exchanges
            or (target_market == "NSE" and symbol.endswith(".NS"))
            or (target_market == "BSE" and symbol.endswith(".BO"))
        )
        if not is_match:
            continue

        base_ticker = symbol.split(".")[0] if target_market in ("NSE", "BSE") else symbol
        matches.append(
            {
                "ticker": base_ticker,
                "yf_symbol": symbol,
                "company_name": q.get("longname") or q.get("shortname") or base_ticker,
                "market": target_market,
                "exchange": exchange or target_market,
                "quote_type": q.get("quoteType", "EQUITY"),
            }
        )

    if not matches:
        yf_symbol, hist, meta = _resolve_symbol_with_fallback(clean_query, target_market, "5d")
        if hist.empty:
            raise ValueError(f"No matching companies or tickers found for '{clean_query}'.")
        stock = yf.Ticker(yf_symbol)
        info = {}
        try:
            info = stock.info or {}
        except Exception:
            info = {}
        inferred_market = "NSE" if yf_symbol.endswith(".NS") else "BSE" if yf_symbol.endswith(".BO") else target_market
        base_ticker = yf_symbol.split(".")[0] if inferred_market in ("NSE", "BSE") else yf_symbol
        matches.append(
            {
                "ticker": base_ticker,
                "yf_symbol": yf_symbol,
                "company_name": info.get("longName") or info.get("shortName") or meta.get("longName") or meta.get("shortName") or yf_symbol,
                "market": inferred_market,
                "exchange": info.get("exchange") or meta.get("exchangeName") or inferred_market,
                "quote_type": info.get("quoteType", "EQUITY"),
                "latest_price": round(float(hist["Close"].iloc[-1]), 2),
                "currency": info.get("currency") or meta.get("currency") or ("INR" if inferred_market in ("NSE", "BSE") else "USD"),
            }
        )

    return {
        "query": clean_query,
        "market": target_market,
        "results": matches,
        "data_source": "Yahoo Finance (yfinance)",
        "source_url": f"https://finance.yahoo.com/lookup?s={clean_query}",
        "retrieved_at": retrieved_at,
    }


def fetch_company_fundamentals(ticker: str, market: str) -> dict[str, Any]:
    """Retrieve company profile and financial statements from Yahoo Finance."""
    retrieved_at = utc_iso_now()
    yf_symbol, _, meta = _resolve_symbol_with_fallback(ticker, market, "5d")
    stock = yf.Ticker(yf_symbol)

    info = {}
    try:
        info = stock.info or {}
    except Exception:
        info = {}

    if not info and not meta:
        raise ValueError(f"Company profile not available for {yf_symbol}.")

    profile = {
        "company_name": info.get("longName") or info.get("shortName") or meta.get("longName") or meta.get("shortName") or ticker.upper(),
        "yf_symbol": yf_symbol,
        "market": market.upper(),
        "exchange": info.get("exchange") or meta.get("exchangeName") or market.upper(),
        "currency": info.get("currency") or meta.get("currency") or ("INR" if yf_symbol.endswith((".NS", ".BO")) else "USD"),
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "website": info.get("website"),
        "country": info.get("country"),
        "full_time_employees": info.get("fullTimeEmployees"),
        "business_summary": info.get("longBusinessSummary"),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "fifty_two_week_high": info.get("fiftyTwoWeekHigh") or meta.get("fiftyTwoWeekHigh"),
        "fifty_two_week_low": info.get("fiftyTwoWeekLow") or meta.get("fiftyTwoWeekLow"),
    }

    financials = {
        "income_statement": _serialize_statement(getattr(stock, "income_stmt", None)),
        "balance_sheet": _serialize_statement(getattr(stock, "balance_sheet", None)),
        "cash_flow": _serialize_statement(getattr(stock, "cashflow", None)),
    }

    return {
        "profile": profile,
        "financial_statements": financials,
        "data_source": "Yahoo Finance (yfinance)",
        "source_url": f"https://finance.yahoo.com/quote/{yf_symbol}",
        "retrieved_at": retrieved_at,
    }


def fetch_stock_history(ticker: str, market: str, analysis_period: str) -> dict[str, Any]:
    """Retrieve and validate historical OHLCV data, quantitative indicators, profile, and financials."""
    retrieved_at = utc_iso_now()
    yf_period = PERIOD_MAP.get(analysis_period, "1y")
    yf_symbol, raw_hist, meta = _resolve_symbol_with_fallback(ticker, market, yf_period)
    if raw_hist is None or raw_hist.empty:
        raise ValueError(f"No historical OHLCV data found for {yf_symbol} ({yf_period}).")

    df, data_quality = validate_and_clean_ohlcv(raw_hist)
    if df.empty:
        raise ValueError(f"All OHLCV rows for {yf_symbol} failed data validation.")

    stock = yf.Ticker(yf_symbol)
    info = {}
    try:
        info = stock.info or {}
    except Exception:
        info = {}

    company_name = info.get("longName") or info.get("shortName") or meta.get("longName") or meta.get("shortName") or yf_symbol
    currency = info.get("currency") or meta.get("currency") or ("INR" if yf_symbol.endswith((".NS", ".BO")) else "USD")

    df["SMA_20"] = df["Close"].rolling(window=20, min_periods=1).mean()
    df["SMA_50"] = df["Close"].rolling(window=50, min_periods=1).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(window=14, min_periods=1).mean()
    loss = (-delta.clip(upper=0)).rolling(window=14, min_periods=1).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI_14"] = (100 - (100 / (1 + rs))).fillna(50.0)

    daily_returns = df["Close"].pct_change().dropna()
    annualized_vol = float(daily_returns.std() * np.sqrt(252) * 100) if len(daily_returns) > 1 else 0.0

    start_price = float(df["Close"].iloc[0])
    latest_price = float(df["Close"].iloc[-1])
    period_return_pct = ((latest_price - start_price) / start_price * 100.0) if start_price else 0.0

    x = np.arange(len(df)).reshape(-1, 1)
    y = df["Close"].values
    model = LinearRegression()
    model.fit(x, y)
    projected_5d_price = float(model.predict(np.array([[len(df) + 4]]))[0])
    slope_per_day = float(model.coef_[0])
    r2_score = float(model.score(x, y)) if len(df) > 2 else 0.0

    dates = [d.strftime("%Y-%m-%d") for d in df.index]

    return {
        "yf_symbol": yf_symbol,
        "company_name": company_name,
        "currency": currency,
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "website": info.get("website"),
        "business_summary": info.get("longBusinessSummary"),
        "data_source": "Yahoo Finance (yfinance)",
        "source_url": f"https://finance.yahoo.com/quote/{yf_symbol}",
        "retrieved_at": retrieved_at,
        "data_quality": data_quality,
        "metrics": {
            "latest_price": round(latest_price, 2),
            "period_high": round(float(df["High"].max()), 2),
            "period_low": round(float(df["Low"].min()), 2),
            "period_return_pct": round(period_return_pct, 2),
            "annualized_volatility_pct": round(annualized_vol, 2),
            "latest_sma_20": round(float(df["SMA_20"].iloc[-1]), 2),
            "latest_sma_50": round(float(df["SMA_50"].iloc[-1]), 2),
            "latest_rsi_14": round(float(df["RSI_14"].iloc[-1]), 2),
            "linear_trend_5d_target": round(projected_5d_price, 2),
            "linear_trend_slope": round(slope_per_day, 4),
            "linear_trend_r2": round(r2_score, 4),
        },
        "series": {
            "dates": dates,
            "open": [round(float(v), 2) for v in df["Open"].tolist()],
            "high": [round(float(v), 2) for v in df["High"].tolist()],
            "low": [round(float(v), 2) for v in df["Low"].tolist()],
            "close": [round(float(v), 2) for v in df["Close"].tolist()],
            "volume": [int(v) for v in df["Volume"].fillna(0).tolist()],
            "sma_20": [round(float(v), 2) for v in df["SMA_20"].tolist()],
            "sma_50": [round(float(v), 2) for v in df["SMA_50"].tolist()],
        },
        "financial_statements": {
            "income_statement": _serialize_statement(getattr(stock, "income_stmt", None), max_cols=3, max_rows=8),
            "balance_sheet": _serialize_statement(getattr(stock, "balance_sheet", None), max_cols=3, max_rows=8),
            "cash_flow": _serialize_statement(getattr(stock, "cashflow", None), max_cols=3, max_rows=8),
        },
    }
