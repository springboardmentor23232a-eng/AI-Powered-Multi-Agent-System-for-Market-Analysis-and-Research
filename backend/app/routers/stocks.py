import math
import re
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
import pandas as pd
from app.dependencies import get_current_user
from app.models import User
from app.schemas import (
    StockSearchResponse,
    StockSearchResult,
    StockQuoteOut,
    StockHistoryOut,
    StockHistoryRow,
    StockProfileOut,
    StockFinancialsOut,
    StockAnalyticsOut,
    FinancialStatementData,
    FinancialMetricRow,
    FinancialStatementsGroup,
)

router = APIRouter(prefix="/stocks", tags=["Stock search and market data"])

SUFFIX = {"NSE": ".NS", "BSE": ".BO", "NASDAQ": "", "NYSE": ""}
PERIOD_MAP = {
    "1 Day": "1d",
    "5 Days": "5d",
    "1 Month": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year": "1y",
    "5 Years": "5y",
    "Max": "max",
    "Maximum": "max",
}

def provider_symbol(ticker: str, market: str) -> str:
    clean = ticker.strip().upper().replace(".NS", "").replace(".BO", "")
    return clean + SUFFIX[market]

def clean_num(val) -> float | None:
    if val is None or pd.isna(val):
        return None
    try:
        num = float(val)
        if math.isnan(num) or math.isinf(num):
            return None
        return num
    except (TypeError, ValueError):
        return None

def clean_int(val) -> int | None:
    if val is None or pd.isna(val):
        return None
    try:
        num = int(val)
        return num
    except (TypeError, ValueError):
        return None

def clean_url(url: str | None) -> str | None:
    if not url or pd.isna(url):
        return None
    s = str(url).strip()
    if not s or s.lower() in ("none", "null", "n/a", "not available"):
        return None
    if not re.match(r"^https?://", s, re.I):
        s = "https://" + s
    # Ensure there's a domain structure
    parts = s.split("/")
    if len(parts) >= 3 and "." in parts[2]:
        return s
    return None

def format_metric_name(name: str) -> str:
    s = str(name).strip()
    if " " in s:
        return s
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)
    spaced = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", spaced)
    return spaced

def get_fast_info_val(fast_info, key: str):
    try:
        if hasattr(fast_info, "get"):
            v = fast_info.get(key)
            if v is not None:
                return v
        if hasattr(fast_info, key):
            return getattr(fast_info, key)
        if isinstance(fast_info, dict):
            return fast_info.get(key)
    except Exception:
        pass
    return None

def check_exchange_mismatch(market: str, exchange: str | None, symbol: str) -> str | None:
    if not exchange:
        return None
    exch = str(exchange).upper().strip()
    nasdaq_exchanges = {"NMS", "NGM", "NCM", "NASDAQ", "NAS", "NBI"}
    nyse_exchanges = {"NYQ", "NYSE", "ASE", "AMEX", "ARCA"}
    nse_exchanges = {"NSI", "NSE"}
    bse_exchanges = {"BSE", "BOM"}

    if market == "NASDAQ":
        if symbol.endswith((".NS", ".BO")):
            return f"Symbol {symbol} carries an Indian exchange suffix and is not listed on NASDAQ."
        if exch in nyse_exchanges:
            return "This company is listed on the New York Stock Exchange (NYSE), not NASDAQ. Please select NYSE to view this stock."
        if exch in nse_exchanges:
            return "This company is listed on the National Stock Exchange of India (NSE), not NASDAQ. Please select NSE to view this stock."
        if exch in bse_exchanges:
            return "This company is listed on the Bombay Stock Exchange (BSE), not NASDAQ. Please select BSE to view this stock."

    elif market == "NYSE":
        if symbol.endswith((".NS", ".BO")):
            return f"Symbol {symbol} carries an Indian exchange suffix and is not listed on NYSE."
        if exch in nasdaq_exchanges:
            return "This company is listed on NASDAQ, not NYSE. Please select NASDAQ to view this stock."
        if exch in nse_exchanges:
            return "This company is listed on the National Stock Exchange of India (NSE), not NYSE. Please select NSE to view this stock."
        if exch in bse_exchanges:
            return "This company is listed on the Bombay Stock Exchange (BSE), not NYSE. Please select BSE to view this stock."

    elif market == "NSE":
        if not symbol.endswith(".NS"):
            return "NSE listings require a .NS symbol suffix on Yahoo Finance."
        if exch in nasdaq_exchanges:
            return "This company is listed on NASDAQ, not NSE. Please select NASDAQ."
        if exch in nyse_exchanges:
            return "This company is listed on NYSE, not NSE. Please select NYSE."
        if exch in bse_exchanges:
            return "This company is listed on the Bombay Stock Exchange (BSE), not NSE. Please select BSE to view this stock."

    elif market == "BSE":
        if not symbol.endswith(".BO"):
            return "BSE listings require a .BO symbol suffix on Yahoo Finance."
        if exch in nasdaq_exchanges:
            return "This company is listed on NASDAQ, not BSE. Please select NASDAQ."
        if exch in nyse_exchanges:
            return "This company is listed on NYSE, not BSE. Please select NYSE."
        if exch in nse_exchanges:
            return "This company is listed on the National Stock Exchange of India (NSE), not BSE. Please select NSE to view this stock."

    return None

def get_statement_df(stock, *attr_names):
    for attr in attr_names:
        try:
            val = getattr(stock, attr, None)
            if val is not None and isinstance(val, pd.DataFrame) and not val.empty:
                return val
        except Exception:
            continue
    return None

def serialize_statement(df: pd.DataFrame | None, is_annual: bool = True) -> FinancialStatementData:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return FinancialStatementData(periods=[], metrics=[])

    raw_cols = list(df.columns)
    try:
        raw_cols = sorted(raw_cols, reverse=True)
    except Exception:
        pass

    def col_title(c) -> str:
        if hasattr(c, "strftime"):
            return c.strftime("%Y") if is_annual else c.strftime("%Y-%m-%d")
        s = str(c).split(" ")[0]
        if is_annual and len(s) >= 4 and s[:4].isdigit():
            return s[:4]
        return s

    period_labels = []
    seen = {}
    for c in raw_cols:
        lbl = col_title(c)
        if lbl in seen:
            seen[lbl] += 1
            lbl = f"{lbl} ({seen[lbl]})"
        else:
            seen[lbl] = 1
        period_labels.append(lbl)

    metrics: list[FinancialMetricRow] = []
    for idx_label, row in df.iterrows():
        name = format_metric_name(str(idx_label))
        row_values: dict[str, float | None] = {}
        for c, lbl in zip(raw_cols, period_labels):
            val = row.get(c)
            row_values[lbl] = clean_num(val)
        metrics.append(FinancialMetricRow(name=name, values=row_values))

    return FinancialStatementData(periods=period_labels, metrics=metrics)

@router.get("/search", response_model=StockSearchResponse)
def search_stocks(
    q: str = Query(min_length=1, max_length=80),
    market: str = Query(pattern="^(NSE|BSE|NASDAQ|NYSE)$"),
    user: User = Depends(get_current_user),
):
    """Search Yahoo Finance symbol catalogue for companies and tickers in the selected market."""
    try:
        import yfinance as yf
        query = q.strip()
        search = yf.Search(query, max_results=15, news_count=0)
        quotes = search.quotes or []
        results = []
        found_symbols = set()

        for item in quotes:
            symbol = (item.get("symbol") or "").strip()
            if not symbol:
                continue
            exchange = (item.get("exchange") or "").upper()
            quote_type = item.get("quoteType", "")
            if quote_type and quote_type not in ("EQUITY", "ETF"):
                continue

            # Strict market filtering
            if market == "NSE" and not symbol.endswith(".NS"):
                continue
            if market == "BSE" and not symbol.endswith(".BO"):
                continue
            if market in ("NASDAQ", "NYSE"):
                if symbol.endswith((".NS", ".BO")):
                    continue
                if market == "NASDAQ" and exchange not in ("NMS", "NGM", "NCM", "NASDAQ", "NAS", "NBI"):
                    continue
                if market == "NYSE" and exchange not in ("NYQ", "NYSE", "ASE", "AMEX", "ARCA"):
                    continue

            clean = symbol.replace(".NS", "").replace(".BO", "")
            found_symbols.add(clean.upper())
            results.append(StockSearchResult(
                company_name=item.get("longname") or item.get("shortname") or clean,
                ticker=clean,
                market=market,
                provider_symbol=symbol,
                price=clean_num(item.get("regularMarketPrice")),
                change_percent=clean_num(item.get("regularMarketChangePercent")),
                currency=item.get("currency"),
            ))

        # Direct ticker symbol resolution fallback
        clean_query = query.upper().replace(".NS", "").replace(".BO", "")
        if clean_query not in found_symbols and len(clean_query) <= 12 and re.match(r"^[A-Z0-9\.\-]+$", clean_query):
            direct_sym = provider_symbol(clean_query, market)
            try:
                probe = yf.Ticker(direct_sym)
                f_info = probe.fast_info
                probe_price = clean_num(get_fast_info_val(f_info, "last_price"))
                probe_exch = get_fast_info_val(f_info, "exchange")
                mismatch = check_exchange_mismatch(market, probe_exch, direct_sym)
                if probe_price is not None and not mismatch:
                    probe_prev = clean_num(get_fast_info_val(f_info, "previous_close"))
                    probe_change = ((probe_price - probe_prev) / probe_prev * 100) if probe_prev else None
                    info = {}
                    try:
                        info = probe.info or {}
                    except Exception:
                        pass
                    comp_name = info.get("longName") or info.get("shortName") or clean_query
                    results.insert(0, StockSearchResult(
                        company_name=comp_name,
                        ticker=clean_query,
                        market=market,
                        provider_symbol=direct_sym,
                        price=probe_price,
                        change_percent=clean_num(probe_change),
                        currency=get_fast_info_val(f_info, "currency") or info.get("currency"),
                    ))
            except Exception:
                pass

        return StockSearchResponse(
            results=results,
            source="Yahoo Finance",
            market=market,
            retrieval_timestamp=datetime.now(timezone.utc),
            note="Search results depend on Yahoo Finance provider coverage and delay tiers."
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Stock search provider is temporarily unavailable: {type(exc).__name__}")

@router.get("/quote", response_model=StockQuoteOut)
def quote(
    ticker: str = Query(min_length=1, max_length=30),
    market: str = Query(pattern="^(NSE|BSE|NASDAQ|NYSE)$"),
    user: User = Depends(get_current_user),
):
    """Retrieve the latest quote for a ticker on the selected market."""
    try:
        import yfinance as yf
        clean_ticker = ticker.strip().upper()
        symbol = provider_symbol(clean_ticker, market)
        stock = yf.Ticker(symbol)
        info = stock.fast_info
        price = clean_num(get_fast_info_val(info, "last_price"))

        # Verify listing
        exchange = get_fast_info_val(info, "exchange")
        mismatch = check_exchange_mismatch(market, exchange, symbol)
        if mismatch:
            raise HTTPException(404, mismatch)

        if price is None:
            # Fallback check history
            hist = stock.history(period="5d")
            if hist.empty or "Close" not in hist:
                raise HTTPException(404, f"No quote data is available for '{clean_ticker}' on {market}.")
            price = clean_num(hist["Close"].dropna().iloc[-1])

        previous = clean_num(get_fast_info_val(info, "previous_close"))
        change_percent = ((price - previous) / previous * 100) if price is not None and previous else None

        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return StockQuoteOut(
            ticker=clean_ticker,
            market=market,
            provider_symbol=symbol,
            price=price,
            previous_close=previous,
            change_percent=clean_num(change_percent),
            currency=get_fast_info_val(info, "currency"),
            source="Yahoo Finance",
            retrieval_timestamp=datetime.now(timezone.utc),
            as_of=today_str,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Quote provider is temporarily unavailable: {type(exc).__name__}")

@router.get("/history", response_model=StockHistoryOut)
def history(
    ticker: str = Query(min_length=1, max_length=30),
    market: str = Query(pattern="^(NSE|BSE|NASDAQ|NYSE)$"),
    period: str = Query(default="1 Year", pattern="^(1 Day|5 Days|1 Month|3 Months|6 Months|1 Year|5 Years|Max|Maximum)$"),
    user: User = Depends(get_current_user),
):
    """Retrieve historical OHLCV data for the given period."""
    if period not in PERIOD_MAP:
        raise HTTPException(400, f"Unsupported period: {period}")

    try:
        import yfinance as yf
        clean_ticker = ticker.strip().upper()
        symbol = provider_symbol(clean_ticker, market)
        stock = yf.Ticker(symbol)

        # Verify market listing
        info = stock.fast_info
        exchange = get_fast_info_val(info, "exchange")
        mismatch = check_exchange_mismatch(market, exchange, symbol)
        if mismatch:
            raise HTTPException(404, mismatch)

        frame = pd.DataFrame()
        try:
            # actions=False prevents yfinance dividend parsing crashes on weekly intervals
            frame = stock.history(period=PERIOD_MAP[period], auto_adjust=False, actions=False)
        except Exception:
            try:
                frame = yf.download(symbol, period=PERIOD_MAP[period], auto_adjust=False, progress=False)
                if isinstance(frame.columns, pd.MultiIndex):
                    frame.columns = [col[0] if isinstance(col, tuple) else col for col in frame.columns]
            except Exception:
                frame = pd.DataFrame()

        if frame.empty or "Close" not in frame:
            raise HTTPException(404, f"No historical OHLCV data available for '{clean_ticker}' on {market}.")

        # Filter out dividend-only rows or rows without valid positive Close & Open
        frame = frame.dropna(subset=["Close", "Open"])
        frame = frame[(frame["Close"] > 0) & (frame["Open"] > 0)]

        if frame.empty:
            raise HTTPException(404, f"No valid OHLCV price records found for '{clean_ticker}' on {market}.")

        # Handle timezone-aware and timezone-naive dates consistently; deduplicate by date string
        date_keys = []
        for idx in frame.index:
            if hasattr(idx, "strftime"):
                date_keys.append(idx.strftime("%Y-%m-%d"))
            else:
                date_keys.append(str(idx).split(" ")[0])
        frame["_date_key"] = date_keys
        frame = frame.drop_duplicates(subset=["_date_key"], keep="last")
        frame = frame.drop(columns=["_date_key"])

        # Sort chronologically ascending
        frame = frame.sort_index(ascending=True)

        currency = get_fast_info_val(info, "currency")
        rows: list[StockHistoryRow] = []

        # Convert index to sorted descending rows (latest first for tabular presentation)
        sorted_frame = frame.sort_index(ascending=False)
        for idx, row in sorted_frame.iterrows():
            date_str = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx).split(" ")[0]
            fmt_date = idx.strftime("%d %b %Y") if hasattr(idx, "strftime") else date_str
            rows.append(StockHistoryRow(
                date=date_str,
                formatted_date=fmt_date,
                open=clean_num(row.get("Open")),
                high=clean_num(row.get("High")),
                low=clean_num(row.get("Low")),
                close=clean_num(row.get("Close")),
                volume=clean_int(row.get("Volume")),
            ))

        latest_date = rows[0].formatted_date if rows else None
        as_of_date = rows[0].date if rows else None

        provider_note = None
        if market == "BSE":
            provider_note = (
                f"Yahoo Finance data limitation: BSE ({symbol}) historical daily data has {len(rows)} record(s) "
                f"for '{period}'. Yahoo Finance provides limited historical daily depth on BSE compared to NSE. "
                "Only genuine exchange records are displayed without artificial interpolation or fabrication."
            )

        return StockHistoryOut(
            ticker=clean_ticker,
            market=market,
            provider_symbol=symbol,
            currency=currency,
            period=period,
            latest_trading_date=latest_date,
            source="Yahoo Finance",
            retrieval_timestamp=datetime.now(timezone.utc),
            as_of=as_of_date,
            count=len(rows),
            provider_note=provider_note,
            history=rows,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Historical market data provider is temporarily unavailable: {type(exc).__name__}")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Historical market data provider is temporarily unavailable: {type(exc).__name__}")

@router.get("/profile", response_model=StockProfileOut)
def profile(
    ticker: str = Query(min_length=1, max_length=30),
    market: str = Query(pattern="^(NSE|BSE|NASDAQ|NYSE)$"),
    user: User = Depends(get_current_user),
):
    """Retrieve full company profile information."""
    try:
        import yfinance as yf
        clean_ticker = ticker.strip().upper()
        symbol = provider_symbol(clean_ticker, market)
        stock = yf.Ticker(symbol)

        fast_info = stock.fast_info
        exchange = get_fast_info_val(fast_info, "exchange")
        mismatch = check_exchange_mismatch(market, exchange, symbol)
        if mismatch:
            raise HTTPException(404, mismatch)

        info = {}
        try:
            info = stock.info or {}
        except Exception:
            pass

        company_name = info.get("longName") or info.get("shortName") or clean_ticker
        sector = info.get("sector")
        industry = info.get("industry")
        description = info.get("longBusinessSummary") or info.get("description")
        country = info.get("country")
        city = info.get("city")
        website = clean_url(info.get("website"))
        market_cap = clean_num(info.get("marketCap") or get_fast_info_val(fast_info, "market_cap"))
        full_time_employees = clean_int(info.get("fullTimeEmployees"))
        currency = info.get("currency") or get_fast_info_val(fast_info, "currency")
        exch_label = info.get("exchange") or str(exchange) if exchange else market

        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return StockProfileOut(
            ticker=clean_ticker,
            company_name=company_name,
            market=market,
            provider_symbol=symbol,
            exchange=exch_label,
            sector=sector,
            industry=industry,
            description=description,
            country=country,
            city=city,
            website=website,
            market_cap=market_cap,
            full_time_employees=full_time_employees,
            currency=currency,
            source="Yahoo Finance",
            retrieval_timestamp=datetime.now(timezone.utc),
            as_of=today_str,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Company profile provider is temporarily unavailable: {type(exc).__name__}")

@router.get("/financials", response_model=StockFinancialsOut)
def financials(
    ticker: str = Query(min_length=1, max_length=30),
    market: str = Query(pattern="^(NSE|BSE|NASDAQ|NYSE)$"),
    user: User = Depends(get_current_user),
):
    """Retrieve annual and quarterly financial statements (Income Statement, Balance Sheet, Cash Flow)."""
    try:
        import yfinance as yf
        clean_ticker = ticker.strip().upper()
        symbol = provider_symbol(clean_ticker, market)
        stock = yf.Ticker(symbol)

        fast_info = stock.fast_info
        exchange = get_fast_info_val(fast_info, "exchange")
        mismatch = check_exchange_mismatch(market, exchange, symbol)
        if mismatch:
            raise HTTPException(404, mismatch)

        currency = get_fast_info_val(fast_info, "currency")

        # Annual statements
        ann_income = get_statement_df(stock, "income_stmt", "financials")
        ann_balance = get_statement_df(stock, "balance_sheet", "balancesheet")
        ann_cash = get_statement_df(stock, "cashflow", "cash_flow")

        # Quarterly statements
        qtr_income = get_statement_df(stock, "quarterly_income_stmt", "quarterly_financials")
        qtr_balance = get_statement_df(stock, "quarterly_balance_sheet", "quarterly_balancesheet")
        qtr_cash = get_statement_df(stock, "quarterly_cashflow", "quarterly_cash_flow")

        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return StockFinancialsOut(
            ticker=clean_ticker,
            market=market,
            provider_symbol=symbol,
            currency=currency,
            source="Yahoo Finance",
            retrieval_timestamp=datetime.now(timezone.utc),
            as_of=today_str,
            annual=FinancialStatementsGroup(
                income_statement=serialize_statement(ann_income, is_annual=True),
                balance_sheet=serialize_statement(ann_balance, is_annual=True),
                cash_flow=serialize_statement(ann_cash, is_annual=True),
            ),
            quarterly=FinancialStatementsGroup(
                income_statement=serialize_statement(qtr_income, is_annual=False),
                balance_sheet=serialize_statement(qtr_balance, is_annual=False),
                cash_flow=serialize_statement(qtr_cash, is_annual=False),
            ),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Financial statements provider is temporarily unavailable: {type(exc).__name__}")

@router.get("/analytics", response_model=StockAnalyticsOut)
def analytics(
    ticker: str = Query(min_length=1, max_length=30),
    market: str = Query(pattern="^(NSE|BSE|NASDAQ|NYSE)$"),
    period: str = Query(default="1 Year", pattern="^(1 Day|5 Days|1 Month|3 Months|6 Months|1 Year|5 Years|Max|Maximum)$"),
    user: User = Depends(get_current_user),
):
    """Retrieve technical and market analytics for the selected stock and period with Bullish/Bearish/Neutral status."""
    if period not in PERIOD_MAP:
        raise HTTPException(400, f"Unsupported period: {period}")

    try:
        import yfinance as yf
        clean_ticker = ticker.strip().upper()
        symbol = provider_symbol(clean_ticker, market)
        stock = yf.Ticker(symbol)

        fast_info = stock.fast_info
        exchange = get_fast_info_val(fast_info, "exchange")
        mismatch = check_exchange_mismatch(market, exchange, symbol)
        if mismatch:
            raise HTTPException(404, mismatch)

        frame = pd.DataFrame()
        try:
            frame = stock.history(period=PERIOD_MAP[period], auto_adjust=False, actions=False)
        except Exception:
            try:
                frame = yf.download(symbol, period=PERIOD_MAP[period], auto_adjust=False, progress=False)
                if isinstance(frame.columns, pd.MultiIndex):
                    frame.columns = [col[0] for col in frame.columns]
            except Exception:
                frame = pd.DataFrame()

        if frame.empty or "Close" not in frame:
            raise HTTPException(404, f"No historical analytics data is available for '{clean_ticker}' on {market}.")

        # Handle timezone-aware and timezone-naive dates consistently; deduplicate by date string
        date_keys = []
        for idx in frame.index:
            if hasattr(idx, "strftime"):
                date_keys.append(idx.strftime("%Y-%m-%d"))
            else:
                date_keys.append(str(idx).split(" ")[0])
        frame["_date_key"] = date_keys
        frame = frame.drop_duplicates(subset=["_date_key"], keep="last")
        frame = frame.drop(columns=["_date_key"])
        frame = frame.sort_index(ascending=True)

        close = frame["Close"].dropna()
        if close.empty:
            raise HTTPException(404, f"No closing prices available for '{clean_ticker}'.")

        returns = close.pct_change().dropna()
        delta = close.diff()
        gains = delta.clip(lower=0).rolling(14).mean()
        losses = (-delta.clip(upper=0)).rolling(14).mean()
        rsi_series = pd.Series(50.0, index=close.index)
        active = losses > 0
        rsi_series.loc[active] = 100 - (100 / (1 + gains.loc[active] / losses.loc[active]))
        rsi_series.loc[(losses == 0) & (gains > 0)] = 100
        rsi = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else None

        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        rolling_peak = close.cummax()
        drawdown = (close - rolling_peak) / rolling_peak

        last_date = frame.index[-1].strftime("%Y-%m-%d") if hasattr(frame.index[-1], "strftime") else str(frame.index[-1])

        sma50_val = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 and not pd.isna(close.rolling(50).mean().iloc[-1]) else None
        sma200_val = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 and not pd.isna(close.rolling(200).mean().iloc[-1]) else None
        macd_val = float(macd.iloc[-1]) if not macd.empty and not pd.isna(macd.iloc[-1]) else None
        signal_val = float(signal.iloc[-1]) if not signal.empty and not pd.isna(signal.iloc[-1]) else None
        curr_price = float(close.iloc[-1])

        # Technical Signal Evaluation (Bullish / Bearish / Neutral)
        score = 0
        evaluations_count = 0
        signals_list = []
        reasons_list = []

        # 1. RSI-14 momentum
        if rsi is not None:
            evaluations_count += 1
            if rsi >= 60:
                score += 1
                signals_list.append(f"RSI-14 ({rsi:.1f}) in strong bullish territory")
                reasons_list.append(f"RSI-14 momentum is bullish at {rsi:.1f}")
            elif rsi <= 40:
                score -= 1
                signals_list.append(f"RSI-14 ({rsi:.1f}) in oversold/bearish territory")
                reasons_list.append(f"RSI-14 momentum is bearish at {rsi:.1f}")
            else:
                reasons_list.append(f"RSI-14 is neutral at {rsi:.1f}")

        # 2. MACD Histogram / Crossover
        if macd_val is not None and signal_val is not None:
            evaluations_count += 1
            if macd_val > signal_val:
                score += 1
                signals_list.append(f"MACD line ({macd_val:.2f}) above signal line ({signal_val:.2f})")
                reasons_list.append("MACD is above signal line (bullish momentum)")
            elif macd_val < signal_val:
                score -= 1
                signals_list.append(f"MACD line ({macd_val:.2f}) below signal line ({signal_val:.2f})")
                reasons_list.append("MACD is below signal line (bearish momentum)")

        # 3. Price vs SMA-50
        if sma50_val is not None:
            evaluations_count += 1
            if curr_price >= sma50_val:
                score += 1
                signals_list.append(f"Price ({curr_price:.2f}) trading above 50-day SMA ({sma50_val:.2f})")
                reasons_list.append("Price is trading above 50-day moving average")
            else:
                score -= 1
                signals_list.append(f"Price ({curr_price:.2f}) trading below 50-day SMA ({sma50_val:.2f})")
                reasons_list.append("Price is trading below 50-day moving average")

        # 4. SMA-50 vs SMA-200 (Golden/Death Cross)
        if sma50_val is not None and sma200_val is not None:
            evaluations_count += 1
            if sma50_val >= sma200_val:
                score += 1
                signals_list.append("50-day SMA above 200-day SMA (Golden Cross)")
                reasons_list.append("Medium-term trend is above long-term trend")
            else:
                score -= 1
                signals_list.append("50-day SMA below 200-day SMA (Death Cross)")
                reasons_list.append("Medium-term trend is below long-term trend")

        # Classification
        if score >= 1:
            sentiment = "Bullish"
            confidence = min(92, max(55, int(50 + (score / max(1, evaluations_count)) * 42)))
            explanation = "Technical indicators suggest net positive upward momentum. " + "; ".join(reasons_list) + "."
        elif score <= -1:
            sentiment = "Bearish"
            confidence = min(92, max(55, int(50 + (abs(score) / max(1, evaluations_count)) * 42)))
            explanation = "Technical indicators reflect net downward pressure. " + "; ".join(reasons_list) + "."
        else:
            sentiment = "Neutral"
            confidence = 50
            explanation = "Technical indicators are mixed or consolidating. " + "; ".join(reasons_list) + "."

        return StockAnalyticsOut(
            ticker=clean_ticker,
            market=market,
            provider_symbol=symbol,
            period=period,
            period_high=clean_num(close.max()),
            period_low=clean_num(close.min()),
            horizon_return=clean_num((close.iloc[-1] / close.iloc[0] - 1) * 100) if len(close) > 0 and close.iloc[0] != 0 else None,
            maximum_drawdown=clean_num(drawdown.min() * 100) if not drawdown.empty else None,
            annualized_volatility=clean_num(returns.std() * (252 ** 0.5) * 100) if len(returns) > 1 else None,
            sma_50=clean_num(sma50_val),
            sma_200=clean_num(sma200_val),
            rsi_14=clean_num(rsi),
            macd=clean_num(macd_val),
            macd_signal=clean_num(signal_val),
            sentiment=sentiment,
            confidence=confidence,
            explanation=explanation,
            signals=signals_list,
            disclaimer="Technical analysis signals are computed from historical price indicators. Informational only, not financial or investment advice.",
            source="Yahoo Finance",
            retrieval_timestamp=datetime.now(timezone.utc),
            as_of=last_date,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Analytics provider is temporarily unavailable: {type(exc).__name__}")

@router.get("/indices")
def indices(user: User = Depends(get_current_user)):
    """Retrieve market indices benchmark prices."""
    try:
        import yfinance as yf
        symbols = {"S&P 500": "^GSPC", "Nasdaq": "^IXIC", "Dow Jones": "^DJI", "Nifty 50": "^NSEI"}
        output = []
        for name, symbol in symbols.items():
            info = yf.Ticker(symbol).fast_info
            price = clean_num(get_fast_info_val(info, "last_price"))
            previous = clean_num(get_fast_info_val(info, "previous_close"))
            output.append({
                "name": name,
                "symbol": symbol,
                "price": price,
                "change_percent": clean_num(((price - previous) / previous * 100)) if price is not None and previous else None,
            })
        return output
    except Exception as exc:
        raise HTTPException(502, f"Index provider is temporarily unavailable: {type(exc).__name__}")
