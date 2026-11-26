import logging
import math
import os
from datetime import datetime, timezone
from typing import Any

# Ensure SSL key logging doesn't fail on restricted environments
os.environ.pop("SSLKEYLOGFILE", None)

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

# Standard exchange mappings
MARKET_EXCHANGES = {
    "NSE": ("NSE", "NSI"),
    "BSE": ("BSE", "BOM"),
    "NASDAQ": ("Nasdaq", "NMS", "NGS", "NCM", "NAS"),
    "NYSE": ("NYSE", "NYQ", "PCX"),
}

PERIOD_MAP = {
    "1mo": "1mo",
    "1 month": "1mo",
    "3mo": "3mo",
    "3 months": "3mo",
    "6mo": "6mo",
    "6 months": "6mo",
    "1y": "1y",
    "1 year": "1y",
    "5y": "5y",
    "5 years": "5y",
    "max": "max",
    "5d": "5d",
}

INTERVAL_MAP = {
    "1d": "1d",
    "daily": "1d",
    "1wk": "1wk",
    "weekly": "1wk",
    "1mo": "1mo",
    "monthly": "1mo",
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
}


class StockNotFoundError(Exception):
    """Raised when a stock ticker does not exist or has no market data."""
    pass


class NoHistoricalDataError(Exception):
    """Raised when no historical price bars are returned for the given range/interval."""
    pass


class MarketDataProviderError(Exception):
    """Raised when the market data provider encounters an error or network failure."""
    pass


class RateLimitError(Exception):
    """Raised when Yahoo Finance rate limit is hit."""
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def safe_float(val: Any) -> float | None:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        if math.isnan(val) or math.isinf(val):
            return None
        return float(val)
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


def format_currency_amount(val: Any, currency: str = "USD") -> str:
    f = safe_float(val)
    if f is None:
        return "N/A"
    abs_f = abs(f)
    sign = "-" if f < 0 else ""
    sym = "₹" if currency == "INR" else "$"
    if currency == "INR":
        if abs_f >= 10_000_000:  # 1 Crore
            return f"{sign}{sym}{abs_f / 10_000_000:,.2f} Cr"
        if abs_f >= 100_000:  # 1 Lakh
            return f"{sign}{sym}{abs_f / 100_000:,.2f} L"
        return f"{sign}{sym}{abs_f:,.2f}"
    else:
        if abs_f >= 1_000_000_000_000:
            return f"{sign}{sym}{abs_f / 1_000_000_000_000:,.2f}T"
        if abs_f >= 1_000_000_000:
            return f"{sign}{sym}{abs_f / 1_000_000_000:,.2f}B"
        if abs_f >= 1_000_000:
            return f"{sign}{sym}{abs_f / 1_000_000:,.2f}M"
        return f"{sign}{sym}{abs_f:,.2f}"


def format_percent(val: Any) -> str:
    f = safe_float(val)
    if f is None:
        return "N/A"
    return f"{round(f * 100, 2)}%"


def format_ratio(val: Any) -> str:
    f = safe_float(val)
    if f is None:
        return "N/A"
    return f"{round(f, 2)}"


def get_statement_cell(df: Any, row_names: list[str], col: Any, currency: str = "USD") -> str:
    if df is None or getattr(df, "empty", True):
        return "N/A"
    for name in row_names:
        if name in df.index:
            try:
                val = df.loc[name, col]
                if hasattr(val, "iloc"):
                    val = val.iloc[0]
                if pd.isna(val):
                    continue
                return format_currency_amount(val, currency)
            except Exception:
                continue
    return "N/A"


def get_eps_cell(df: Any, row_names: list[str], col: Any, currency: str = "USD") -> str:
    if df is None or getattr(df, "empty", True):
        return "N/A"
    for name in row_names:
        if name in df.index:
            try:
                val = df.loc[name, col]
                if hasattr(val, "iloc"):
                    val = val.iloc[0]
                f = safe_float(val)
                if f is not None:
                    sym = "₹" if currency == "INR" else "$"
                    return f"{sym}{f:.2f}"
            except Exception:
                continue
    return "N/A"


class YahooFinanceClient:
    """
    Pure yfinance client for retrieving live, actual market data directly from Yahoo Finance.
    Contains strictly zero synthetic data, artificial price generators, or fallback catalogs.
    """

    def get_data_source_label(self) -> str:
        return "Yahoo Finance via yfinance"

    def normalize_ticker(self, symbol: str, market: str = "NSE") -> str:
        """
        Normalizes symbols according to exchange requirements:
          - NSE: TCS -> TCS.NS, RELIANCE -> RELIANCE.NS
          - BSE: TCS -> TCS.BO
          - NASDAQ & NYSE: AAPL, MSFT, JPM (no exchange suffixes)
        """
        sym = symbol.strip().upper()
        mkt = market.strip().upper()

        if mkt == "NSE":
            if sym.endswith(".BO"):
                sym = f"{sym[:-3]}.NS"
            elif not sym.endswith(".NS"):
                sym = f"{sym}.NS"
        elif mkt == "BSE":
            if sym.endswith(".NS"):
                sym = f"{sym[:-3]}.BO"
            elif not sym.endswith(".BO"):
                sym = f"{sym}.BO"
        elif mkt in ("NASDAQ", "NYSE"):
            if sym.endswith(".NS") or sym.endswith(".BO"):
                sym = sym.rsplit(".", 1)[0]

        return sym

    def _infer_market(self, exchange: str, symbol: str) -> str:
        s_upper = symbol.upper()
        if s_upper.endswith(".NS"):
            return "NSE"
        if s_upper.endswith(".BO"):
            return "BSE"
        ex_lower = (exchange or "").lower()
        if any(k in ex_lower for k in ("nasdaq", "nms", "ngs", "ncm", "nas")):
            return "NASDAQ"
        if any(k in ex_lower for k in ("nyse", "nyq", "pcx")):
            return "NYSE"
        return "NASDAQ"

    def _infer_currency(self, market: str, symbol: str = "") -> str:
        s_upper = symbol.upper()
        if s_upper.endswith(".NS") or s_upper.endswith(".BO") or market in ("NSE", "BSE"):
            return "INR"
        return "USD"

    def _standardize_period(self, period: str) -> str:
        p_clean = period.strip().lower()
        return PERIOD_MAP.get(p_clean, "1y")

    def _standardize_interval(self, interval: str) -> str:
        i_clean = interval.strip().lower()
        return INTERVAL_MAP.get(i_clean, "1d")

    def _validate_ticker_exists(self, ticker_obj: yf.Ticker, symbol: str) -> None:
        """
        Verifies that a ticker actually exists on Yahoo Finance.
        Raises StockNotFoundError if the symbol cannot be found.
        """
        try:
            lp = getattr(ticker_obj.fast_info, "last_price", None)
            if lp is not None and not (math.isnan(lp) or math.isinf(lp)):
                return
        except Exception:
            pass

        try:
            info = ticker_obj.info
            if info and any(k in info for k in ("regularMarketPrice", "currentPrice", "shortName", "longName", "symbol")):
                return
        except Exception:
            pass

        try:
            h = ticker_obj.history(period="5d", auto_adjust=False)
            if not h.empty:
                return
        except Exception:
            pass

        raise StockNotFoundError(f"Stock symbol '{symbol}' not found.")

    def search(self, query: str, market: str = "ALL") -> list[dict[str, Any]]:
        """
        Search for actual companies and valid ticker symbols using yf.Search.
        Returns only verified results from actual provider responses.
        """
        query_clean = query.strip()
        market_upper = market.strip().upper()
        retrieved_at = utc_now().isoformat()
        results: list[dict[str, Any]] = []

        if not query_clean:
            return results

        try:
            search_agent = yf.Search(query_clean, max_results=25)
            raw_quotes = getattr(search_agent, "quotes", []) or []

            expected_exchanges = MARKET_EXCHANGES.get(market_upper, None)

            for quote in raw_quotes:
                if not isinstance(quote, dict):
                    continue

                quote_type = quote.get("quoteType", "")
                if quote_type not in {"EQUITY", "ETF"}:
                    continue

                exchange = str(quote.get("exchange", ""))
                exchange_disp = str(quote.get("exchDisp", exchange))
                symbol = str(quote.get("symbol", "")).upper()
                name = quote.get("longname") or quote.get("shortname") or symbol

                detected_market = self._infer_market(exchange + " " + exchange_disp, symbol)

                # Match market filter if requested
                if market_upper != "ALL":
                    if expected_exchanges:
                        matches_exchange = any(
                            exp.lower() in (exchange + " " + exchange_disp).lower()
                            for exp in expected_exchanges
                        ) or (market_upper == "NSE" and symbol.endswith(".NS")) or (market_upper == "BSE" and symbol.endswith(".BO"))
                        if not matches_exchange:
                            continue
                    elif detected_market != market_upper:
                        continue

                currency = self._infer_currency(detected_market, symbol)

                results.append({
                    "ticker": symbol,
                    "company_name": name,
                    "market": detected_market if market_upper == "ALL" else market_upper,
                    "exchange": exchange_disp or exchange,
                    "quote_type": quote_type,
                    "currency": currency,
                    "data_source": self.get_data_source_label(),
                    "retrieved_at": retrieved_at,
                })

            return results[:15]

        except Exception as e:
            err_str = str(e).lower()
            if "rate" in err_str or "limit" in err_str or "429" in err_str:
                raise RateLimitError("Request limit reached. Try again later.") from e
            logger.warning("yf.Search error for query '%s': %s", query_clean, e)
            return []

    def get_historical_ohlcv(
        self,
        symbol: str,
        market: str = "NSE",
        period: str = "1y",
        interval: str = "1d",
    ) -> dict[str, Any]:
        """
        Retrieve historical stock prices and actual OHLCV data using yf.Ticker(symbol).history().
        Supports 1mo, 3mo, 6mo, 1y, 5y, max, daily, weekly, monthly, and intraday (1m, 5m, 15m).
        """
        norm_symbol = self.normalize_ticker(symbol, market)
        std_period = self._standardize_period(period)
        std_interval = self._standardize_interval(interval)
        retrieved_at = utc_now().isoformat()
        currency = self._infer_currency(market, norm_symbol)

        # Intraday period constraints enforced by Yahoo Finance API
        if std_interval == "1m" and std_period not in ("1d", "5d", "7d"):
            std_period = "5d"
        elif std_interval in ("5m", "15m") and std_period not in ("1d", "5d", "1mo"):
            std_period = "1mo"

        ticker_obj = yf.Ticker(norm_symbol)

        try:
            hist = ticker_obj.history(period=std_period, interval=std_interval, auto_adjust=False)
        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str or "rate limit" in err_str:
                raise RateLimitError("Request limit reached. Try again later.") from e
            raise MarketDataProviderError(f"Market data provider unavailable: {e}") from e

        if hist is None or hist.empty:
            self._validate_ticker_exists(ticker_obj, norm_symbol)
            raise NoHistoricalDataError(f"No historical data available for '{norm_symbol}' ({std_period}, {std_interval}).")

        ohlcv: list[dict[str, Any]] = []
        valid_closes: list[float] = []
        valid_volumes: list[int] = []

        for idx, row in hist.iterrows():
            if hasattr(idx, "to_pydatetime"):
                dt = idx.to_pydatetime()
            elif isinstance(idx, datetime):
                dt = idx
            else:
                dt = pd.to_datetime(idx).to_pydatetime()

            ts = int(dt.timestamp())
            date_str = dt.strftime("%Y-%m-%d %H:%M") if std_interval in ("1m", "5m", "15m") else dt.strftime("%Y-%m-%d")

            o = safe_float(row.get("Open"))
            h = safe_float(row.get("High"))
            l = safe_float(row.get("Low"))
            c = safe_float(row.get("Close"))
            ac = safe_float(row.get("Adj Close"))
            if ac is None:
                ac = c
            v = row.get("Volume")
            v_val = int(v) if v is not None and not pd.isna(v) else 0

            if c is None or o is None or h is None or l is None:
                continue

            valid_closes.append(round(c, 2))
            valid_volumes.append(v_val)

            ohlcv.append({
                "date": date_str,
                "timestamp": ts,
                "open": round(o, 2),
                "high": round(h, 2),
                "low": round(l, 2),
                "close": round(c, 2),
                "adj_close": round(ac, 2),
                "volume": v_val,
            })

        if not ohlcv:
            raise NoHistoricalDataError(f"No valid historical OHLCV bars returned for '{norm_symbol}'.")

        # Determine latest market price from quote information
        fast_price = None
        try:
            fp = getattr(ticker_obj.fast_info, "last_price", None)
            if fp is not None and not (math.isnan(fp) or math.isinf(fp)):
                fast_price = round(float(fp), 2)
        except Exception:
            pass

        info_price = None
        delayed_min = 15
        info: dict[str, Any] = {}
        try:
            info = ticker_obj.info or {}
            ip = info.get("regularMarketPrice") or info.get("currentPrice")
            if ip is not None and not (math.isnan(ip) or math.isinf(ip)):
                info_price = round(float(ip), 2)
            delayed_min = info.get("exchangeDataDelayedBy", 15)
        except Exception:
            pass

        latest_close = valid_closes[-1] if valid_closes else None
        current_price = fast_price or info_price or latest_close

        # Clearly identify price status
        if delayed_min == 0:
            price_status = "Live"
        elif delayed_min and delayed_min > 0:
            price_status = f"Delayed ({delayed_min} min)"
        else:
            price_status = "Latest Available Market Price"

        fast_prev = None
        try:
            pp = getattr(ticker_obj.fast_info, "previous_close", None)
            if pp is not None and not (math.isnan(pp) or math.isinf(pp)):
                fast_prev = round(float(pp), 2)
        except Exception:
            pass

        prev_close = fast_prev or (valid_closes[-2] if len(valid_closes) > 1 else current_price)
        change = round(current_price - prev_close, 2) if current_price is not None and prev_close is not None else 0.0
        pct_change = round((change / prev_close) * 100, 2) if prev_close and prev_close != 0 else 0.0

        day_high = None
        try:
            dh = getattr(ticker_obj.fast_info, "day_high", None)
            if dh is not None and not math.isnan(dh):
                day_high = round(float(dh), 2)
        except Exception:
            pass
        if day_high is None and ohlcv:
            day_high = ohlcv[-1]["high"]

        day_low = None
        try:
            dl = getattr(ticker_obj.fast_info, "day_low", None)
            if dl is not None and not math.isnan(dl):
                day_low = round(float(dl), 2)
        except Exception:
            pass
        if day_low is None and ohlcv:
            day_low = ohlcv[-1]["low"]

        fifty_two_high = None
        try:
            yh = getattr(ticker_obj.fast_info, "year_high", None)
            if yh is not None and not math.isnan(yh):
                fifty_two_high = round(float(yh), 2)
        except Exception:
            pass
        if fifty_two_high is None and valid_closes:
            fifty_two_high = max(valid_closes)

        fifty_two_low = None
        try:
            yl = getattr(ticker_obj.fast_info, "year_low", None)
            if yl is not None and not math.isnan(yl):
                fifty_two_low = round(float(yl), 2)
        except Exception:
            pass
        if fifty_two_low is None and valid_closes:
            fifty_two_low = min(valid_closes)

        avg_vol = int(sum(valid_volumes) / len(valid_volumes)) if valid_volumes else None
        company_name = info.get("longName") or info.get("shortName") or norm_symbol

        return {
            "ticker": norm_symbol,
            "company_name": company_name,
            "market": market,
            "period": period,
            "interval": interval,
            "currency": currency,
            "current_price": current_price,
            "previous_close": prev_close,
            "change": change,
            "change_percent": pct_change,
            "price_status": price_status,
            "day_high": day_high,
            "day_low": day_low,
            "fifty_two_week_high": fifty_two_high,
            "fifty_two_week_low": fifty_two_low,
            "volume": valid_volumes[-1] if valid_volumes else None,
            "average_volume": avg_vol,
            "ohlcv": ohlcv,
            "data_source": self.get_data_source_label(),
            "retrieval_timestamp": retrieved_at,
        }

    def get_company_profile(self, symbol: str, market: str = "NSE") -> dict[str, Any]:
        """
        Retrieve available company profile, executive leadership, and valuation statistics from yfinance.
        """
        norm_symbol = self.normalize_ticker(symbol, market)
        retrieved_at = utc_now().isoformat()
        currency = self._infer_currency(market, norm_symbol)
        ticker_obj = yf.Ticker(norm_symbol)

        try:
            info = ticker_obj.info or {}
        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str:
                raise RateLimitError("Request limit reached. Try again later.") from e
            if "404" in err_str or "not found" in err_str:
                raise StockNotFoundError(f"Stock symbol '{norm_symbol}' not found.") from e
            raise MarketDataProviderError(f"Market data provider unavailable: {e}") from e

        if not info or not any(k in info for k in ("symbol", "shortName", "longName", "regularMarketPrice", "currentPrice")):
            self._validate_ticker_exists(ticker_obj, norm_symbol)

        company_name = info.get("longName") or info.get("shortName") or norm_symbol

        officers_raw = info.get("companyOfficers", []) or []
        officers = []
        for off in officers_raw[:8]:
            if not isinstance(off, dict):
                continue
            pay = off.get("totalPay")
            pay_fmt = None
            if pay is not None and isinstance(pay, (int, float)) and pay > 0:
                pay_fmt = format_currency_amount(pay, currency)
            officers.append({
                "name": off.get("name", "N/A"),
                "title": off.get("title", "Executive"),
                "age": off.get("age"),
                "total_pay": pay_fmt,
            })

        mcap = info.get("marketCap")
        if mcap is None:
            try:
                mcap = getattr(ticker_obj.fast_info, "market_cap", None)
            except Exception:
                pass

        fifty_two_range = "N/A"
        low52 = info.get("fiftyTwoWeekLow")
        high52 = info.get("fiftyTwoWeekHigh")
        if low52 is not None and high52 is not None:
            fifty_two_range = f"{low52} - {high52}"

        return {
            "ticker": norm_symbol,
            "company_name": company_name,
            "market": market,
            "sector": info.get("sector") or "N/A",
            "industry": info.get("industry") or "N/A",
            "country": info.get("country") or "N/A",
            "city": info.get("city") or "N/A",
            "address": info.get("address1") or "N/A",
            "website": info.get("website") or "N/A",
            "phone": info.get("phone") or "N/A",
            "full_time_employees": info.get("fullTimeEmployees"),
            "summary": info.get("longBusinessSummary") or "No business summary available.",
            "officers": officers,
            "market_cap": format_currency_amount(mcap, currency),
            "enterprise_value": format_currency_amount(info.get("enterpriseValue"), currency),
            "trailing_pe": safe_float(info.get("trailingPE")),
            "forward_pe": safe_float(info.get("forwardPE")),
            "peg_ratio": safe_float(info.get("pegRatio")),
            "price_to_book": safe_float(info.get("priceToBook")),
            "beta": safe_float(info.get("beta")),
            "dividend_rate": safe_float(info.get("dividendRate")),
            "dividend_yield": safe_float(info.get("dividendYield")),
            "fifty_two_week_range": fifty_two_range,
            "data_source": self.get_data_source_label(),
            "retrieval_timestamp": retrieved_at,
        }

    def get_financial_statements(self, symbol: str, market: str = "NSE") -> dict[str, Any]:
        """
        Retrieve available financial statements (Income Statement, Balance Sheet, Cash Flow) and key ratios.
        Never invents missing financial values.
        """
        norm_symbol = self.normalize_ticker(symbol, market)
        retrieved_at = utc_now().isoformat()
        currency = self._infer_currency(market, norm_symbol)
        ticker_obj = yf.Ticker(norm_symbol)

        self._validate_ticker_exists(ticker_obj, norm_symbol)

        try:
            info = ticker_obj.info or {}
        except Exception:
            info = {}

        company_name = info.get("longName") or info.get("shortName") or norm_symbol

        # 1. Income Statement
        income_statement = []
        try:
            inc_df = ticker_obj.income_stmt
            if inc_df is None or getattr(inc_df, "empty", True):
                inc_df = ticker_obj.financials

            if inc_df is not None and not getattr(inc_df, "empty", True):
                for col in inc_df.columns[:5]:
                    period_str = col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col)[:10]
                    income_statement.append({
                        "period": period_str,
                        "total_revenue": get_statement_cell(inc_df, ["Total Revenue", "Operating Revenue"], col, currency),
                        "cost_of_revenue": get_statement_cell(inc_df, ["Cost Of Revenue", "Reconciled Cost Of Revenue"], col, currency),
                        "gross_profit": get_statement_cell(inc_df, ["Gross Profit"], col, currency),
                        "operating_expenses": get_statement_cell(inc_df, ["Operating Expense", "Total Expenses", "Selling General And Administration"], col, currency),
                        "operating_income": get_statement_cell(inc_df, ["Operating Income", "Total Operating Income As Reported"], col, currency),
                        "net_income": get_statement_cell(inc_df, ["Net Income", "Net Income Common Stockholders", "Net Income Continuous Operations"], col, currency),
                        "ebitda": get_statement_cell(inc_df, ["EBITDA", "Normalized EBITDA"], col, currency),
                        "diluted_eps": get_eps_cell(inc_df, ["Diluted EPS", "Basic EPS"], col, currency),
                    })
        except Exception as e:
            logger.warning("Error loading income_stmt for %s: %s", norm_symbol, e)

        # 2. Balance Sheet
        balance_sheet = []
        try:
            bal_df = ticker_obj.balance_sheet
            if bal_df is not None and not getattr(bal_df, "empty", True):
                for col in bal_df.columns[:5]:
                    period_str = col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col)[:10]
                    balance_sheet.append({
                        "period": period_str,
                        "cash_and_equivalents": get_statement_cell(bal_df, ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments", "Cash Financial"], col, currency),
                        "short_term_investments": get_statement_cell(bal_df, ["Other Short Term Investments", "Available For Sale Securities"], col, currency),
                        "total_current_assets": get_statement_cell(bal_df, ["Current Assets"], col, currency),
                        "net_ppe": get_statement_cell(bal_df, ["Net PPE", "Properties"], col, currency),
                        "total_assets": get_statement_cell(bal_df, ["Total Assets"], col, currency),
                        "total_current_liabilities": get_statement_cell(bal_df, ["Current Liabilities"], col, currency),
                        "long_term_debt": get_statement_cell(bal_df, ["Long Term Debt", "Long Term Debt And Capital Lease Obligation", "Total Debt"], col, currency),
                        "total_liabilities": get_statement_cell(bal_df, ["Total Liabilities Net Minority Interest", "Total Non Current Liabilities Net Minority Interest", "Current Liabilities"], col, currency),
                        "common_stock": get_statement_cell(bal_df, ["Common Stock", "Capital Stock", "Share Issued"], col, currency),
                        "retained_earnings": get_statement_cell(bal_df, ["Retained Earnings"], col, currency),
                        "stockholders_equity": get_statement_cell(bal_df, ["Stockholders Equity", "Common Stock Equity", "Total Capitalization"], col, currency),
                    })
        except Exception as e:
            logger.warning("Error loading balance_sheet for %s: %s", norm_symbol, e)

        # 3. Cash Flow Statement
        cash_flow = []
        try:
            cf_df = ticker_obj.cashflow
            if cf_df is not None and not getattr(cf_df, "empty", True):
                for col in cf_df.columns[:5]:
                    period_str = col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col)[:10]
                    cash_flow.append({
                        "period": period_str,
                        "operating_cash_flow": get_statement_cell(cf_df, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"], col, currency),
                        "capital_expenditures": get_statement_cell(cf_df, ["Capital Expenditure", "Purchase Of PPE"], col, currency),
                        "free_cash_flow": get_statement_cell(cf_df, ["Free Cash Flow"], col, currency),
                        "investing_cash_flow": get_statement_cell(cf_df, ["Investing Cash Flow", "Cash Flow From Continuing Investing Activities"], col, currency),
                        "financing_cash_flow": get_statement_cell(cf_df, ["Financing Cash Flow", "Cash Flow From Continuing Financing Activities"], col, currency),
                        "net_change_in_cash": get_statement_cell(cf_df, ["Changes In Cash", "End Cash Position"], col, currency),
                    })
        except Exception as e:
            logger.warning("Error loading cashflow for %s: %s", norm_symbol, e)

        # 4. Key Financial Ratios
        key_ratios = {
            "gross_margin": format_percent(info.get("grossMargins")),
            "operating_margin": format_percent(info.get("operatingMargins")),
            "profit_margin": format_percent(info.get("profitMargins")),
            "return_on_assets": format_percent(info.get("returnOnAssets")),
            "return_on_equity": format_percent(info.get("returnOnEquity")),
            "revenue_growth": format_percent(info.get("revenueGrowth")),
            "debt_to_equity": format_ratio(info.get("debtToEquity")),
            "current_ratio": format_ratio(info.get("currentRatio")),
            "quick_ratio": format_ratio(info.get("quickRatio")),
        }

        return {
            "ticker": norm_symbol,
            "company_name": company_name,
            "market": market,
            "income_statement": income_statement,
            "balance_sheet": balance_sheet,
            "cash_flow": cash_flow,
            "key_ratios": key_ratios,
            "data_source": self.get_data_source_label(),
            "retrieval_timestamp": retrieved_at,
        }

    def collect_full_market_data(
        self,
        symbol: str,
        company_name: str,
        market: str = "NSE",
        period: str = "1y",
        interval: str = "1d",
    ) -> dict[str, Any]:
        """
        Coordinates collection of actual OHLCV history, company profile, and financial statements.
        Records data source and exact retrieval timestamp.
        """
        retrieval_timestamp = utc_now().isoformat()
        ohlcv_result = self.get_historical_ohlcv(symbol, market, period, interval)
        profile_result = self.get_company_profile(symbol, market)
        financials_result = self.get_financial_statements(symbol, market)

        return {
            "ticker": ohlcv_result.get("ticker", symbol.upper()),
            "company_name": company_name or ohlcv_result.get("company_name", symbol),
            "market": market.upper(),
            "period": period,
            "interval": interval,
            "data_source": self.get_data_source_label(),
            "retrieval_timestamp": retrieval_timestamp,
            "currency": ohlcv_result.get("currency", "USD"),
            "latest_price": ohlcv_result.get("current_price"),
            "change": ohlcv_result.get("change"),
            "change_percent": ohlcv_result.get("change_percent"),
            "ohlcv_data": ohlcv_result.get("ohlcv", []),
            "profile_data": profile_result,
            "financials_data": financials_result,
        }


# Global singleton client
yahoo_finance_service = YahooFinanceClient()
