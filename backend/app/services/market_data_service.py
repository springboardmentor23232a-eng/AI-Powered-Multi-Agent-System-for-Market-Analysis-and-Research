import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

PERIOD_TO_DAYS: Dict[str, int] = {
    "1 Month": 30,
    "3 Months": 90,
    "6 Months": 180,
    "1 Year": 365,
    "5 Years": 1825,
}

PERIOD_TO_YF: Dict[str, str] = {
    "1 Month": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year": "1y",
    "5 Years": "5y",
}


def get_yf_symbol(ticker: str, market: str) -> str:
    """Convert a clean ticker and target exchange into a Yahoo Finance symbol."""
    t = ticker.strip().upper()
    m = market.strip().upper()
    if m == "NSE" and not t.endswith(".NS"):
        return f"{t}.NS"
    if m == "BSE" and not t.endswith(".BO"):
        return f"{t}.BO"
    return t


def _sha256_hash(payload: Any) -> str:
    """Compute a deterministic SHA-256 hex digest for provenance tracking."""
    serialized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def validate_ohlcv_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Validate historical OHLCV data for missing values, duplicate dates, and price/volume
    inconsistencies. Returns (cleaned_df, data_quality_report).
    """
    validated_at = datetime.now(timezone.utc).isoformat()
    if df is None or df.empty:
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"]), {
            "total_raw_rows": 0,
            "valid_rows": 0,
            "duplicate_dates_removed": 0,
            "duplicate_dates": [],
            "missing_values_count": 0,
            "missing_value_details": [],
            "inconsistent_rows_count": 0,
            "inconsistent_row_details": [],
            "date_gaps": [],
            "quality_status": "DEGRADED",
            "validated_at": validated_at,
            "notes": ["No historical OHLCV records returned by data provider."],
        }

    work = df.copy()
    required_cols = ["Open", "High", "Low", "Close", "Volume"]
    for col in required_cols:
        if col not in work.columns:
            work[col] = np.nan

    work = work[required_cols].copy()
    total_raw = len(work)

    # Normalize index to timezone-naive date strings for deduplication
    if not isinstance(work.index, pd.DatetimeIndex):
        work.index = pd.to_datetime(work.index, errors="coerce")
    work = work[~work.index.isna()]
    work.index = work.index.tz_localize(None) if work.index.tz is not None else work.index
    work = work.sort_index()

    date_strings = work.index.strftime("%Y-%m-%d")

    # 1. Duplicate date detection and removal
    dup_mask = date_strings.duplicated(keep="last")
    duplicate_dates = sorted(set(date_strings[dup_mask].tolist()))
    duplicate_count = int(dup_mask.sum())
    if duplicate_count > 0:
        work = work[~dup_mask]

    # 2. Missing value detection
    missing_details: List[str] = []
    missing_count = 0
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        col_nulls = int(work[col].isna().sum())
        if col_nulls > 0:
            missing_count += col_nulls
            null_dates = work.index[work[col].isna()].strftime("%Y-%m-%d").tolist()[:5]
            missing_details.append(f"{col}: {col_nulls} missing value(s) (e.g., {', '.join(null_dates)})")

    # Fill missing Volume with 0 when prices are valid; drop rows missing core OHLC prices
    if "Volume" in work.columns:
        work["Volume"] = work["Volume"].fillna(0)
    price_cols = ["Open", "High", "Low", "Close"]
    rows_with_missing_price = work[price_cols].isna().any(axis=1)
    if rows_with_missing_price.any():
        work = work[~rows_with_missing_price]

    # Cast to clean numeric types
    for col in price_cols:
        work[col] = pd.to_numeric(work[col], errors="coerce")
    work["Volume"] = pd.to_numeric(work["Volume"], errors="coerce").fillna(0).astype(int)

    # 3. OHLCV logical consistency checks
    inconsistent_details: List[str] = []
    inconsistent_indices = set()

    for idx, row in work.iterrows():
        d_str = idx.strftime("%Y-%m-%d")
        o, h, l, c, v = row["Open"], row["High"], row["Low"], row["Close"], row["Volume"]
        reasons: List[str] = []
        if o <= 0 or h <= 0 or l <= 0 or c <= 0:
            reasons.append("non-positive price")
        if h < l:
            reasons.append(f"High ({h:.2f}) < Low ({l:.2f})")
        if h < max(o, c) - 1e-6:
            reasons.append(f"High ({h:.2f}) < max(Open, Close)")
        if l > min(o, c) + 1e-6:
            reasons.append(f"Low ({l:.2f}) > min(Open, Close)")
        if v < 0:
            reasons.append(f"negative Volume ({v})")

        if reasons:
            inconsistent_indices.add(idx)
            if len(inconsistent_details) < 10:
                inconsistent_details.append(f"{d_str}: {', '.join(reasons)}")

    inconsistent_count = len(inconsistent_indices)

    # Repair minor High/Low envelope violations if prices are positive, otherwise drop non-positive rows
    non_positive_mask = (work["Open"] <= 0) | (work["High"] <= 0) | (work["Low"] <= 0) | (work["Close"] <= 0)
    if non_positive_mask.any():
        work = work[~non_positive_mask]

    if not work.empty:
        work["High"] = work[["Open", "High", "Low", "Close"]].max(axis=1)
        work["Low"] = work[["Open", "High", "Low", "Close"]].min(axis=1)
        work["Volume"] = work["Volume"].clip(lower=0)

    # Check extreme single-day jump anomalies (> 300% change)
    if len(work) > 1:
        pct_jumps = work["Close"].pct_change().abs()
        anomaly_dates = work.index[pct_jumps > 3.0].strftime("%Y-%m-%d").tolist()
        for ad in anomaly_dates[:5]:
            inconsistent_details.append(f"{ad}: extreme >300% single-day close change detected")
            inconsistent_count += 1

    # 4. Date gap detection (> 7 calendar days between consecutive trading sessions)
    date_gaps: List[str] = []
    if len(work) > 1:
        diffs = work.index.to_series().diff().dt.days
        gap_mask = diffs > 7
        for idx in work.index[gap_mask]:
            days = int(diffs.loc[idx])
            date_gaps.append(f"{idx.strftime('%Y-%m-%d')} ({days}d gap)")
            if len(date_gaps) >= 5:
                break

    valid_rows = len(work)
    notes: List[str] = []
    if valid_rows == 0:
        quality_status = "DEGRADED"
        notes.append("All OHLCV rows failed validation checks.")
    elif duplicate_count > 0 or missing_count > 0 or inconsistent_count > 0:
        quality_status = "VALID_WITH_WARNINGS"
        notes.append("Validation sanitized minor data anomalies; review details.")
    else:
        quality_status = "VALID"
        notes.append("All OHLCV rows passed completeness, uniqueness, and price consistency checks.")

    return work, {
        "total_raw_rows": total_raw,
        "valid_rows": valid_rows,
        "duplicate_dates_removed": duplicate_count,
        "duplicate_dates": duplicate_dates[:10],
        "missing_values_count": missing_count,
        "missing_value_details": missing_details,
        "inconsistent_rows_count": inconsistent_count,
        "inconsistent_row_details": inconsistent_details,
        "date_gaps": date_gaps,
        "quality_status": quality_status,
        "validated_at": validated_at,
        "notes": notes,
    }


def serialize_financial_statement(df: Optional[pd.DataFrame], statement_type: str, currency: str) -> Dict[str, Any]:
    """Convert a yfinance financial DataFrame into a clean, JSON-safe structure."""
    if df is None or df.empty:
        return {
            "statement_type": statement_type,
            "currency": currency,
            "periods": [],
            "rows": {},
        }

    # Sort columns newest -> oldest
    cols = sorted(list(df.columns), reverse=True)
    periods = [c.strftime("%Y-%m-%d") if hasattr(c, "strftime") else str(c)[:10] for c in cols]

    rows: Dict[str, List[Optional[float]]] = {}
    for metric_name in df.index:
        values: List[Optional[float]] = []
        has_any_valid = False
        for c in cols:
            val = df.loc[metric_name, c]
            if pd.isna(val):
                values.append(None)
            else:
                try:
                    fval = float(val)
                    if np.isfinite(fval):
                        values.append(round(fval, 4))
                        has_any_valid = True
                    else:
                        values.append(None)
                except (TypeError, ValueError):
                    values.append(None)
        if has_any_valid:
            rows[str(metric_name)] = values

    return {
        "statement_type": statement_type,
        "currency": currency,
        "periods": periods,
        "rows": rows,
    }


class MarketDataCollector:
    """
    Module 2 service responsible for collecting, validating, and recording provenance
    for historical OHLCV data, company profiles, and financial statements.
    """

    @classmethod
    def collect_market_data(
        cls,
        ticker: str,
        market: str,
        period: str = "1 Year",
        include_warmup: bool = True,
    ) -> Dict[str, Any]:
        """
        Collect OHLCV, profile, and financial statements for (ticker, market, period).
        When include_warmup=True, fetches an extended lookback window so technical
        indicators (SMA-50, SMA-200, MACD, RSI-14) are warmed up even for short windows.
        """
        import yfinance as yf

        clean_ticker = ticker.strip().upper()
        clean_market = market.strip().upper()
        yf_symbol = get_yf_symbol(clean_ticker, clean_market)
        retrieved_at = datetime.now(timezone.utc).isoformat()
        quote_url = f"https://finance.yahoo.com/quote/{yf_symbol}"

        stock = yf.Ticker(yf_symbol)
        info: Dict[str, Any] = {}
        try:
            info = stock.info or {}
        except Exception as e:
            logger.warning(f"Failed to fetch stock info for {yf_symbol}: {e}")

        # Determine fetch period (extended for indicator warmup when needed)
        requested_days = PERIOD_TO_DAYS.get(period, 365)
        if include_warmup and requested_days < 730:
            fetch_period = "2y"
        else:
            fetch_period = PERIOD_TO_YF.get(period, "1y")

        raw_hist = pd.DataFrame()
        try:
            raw_hist = stock.history(period=fetch_period, auto_adjust=False)
        except Exception as e:
            logger.warning(f"Failed to fetch history for {yf_symbol} ({fetch_period}): {e}")

        cleaned_full, _ = validate_ohlcv_dataframe(raw_hist)

        # Slice to requested period for exact period validation & reporting
        if not cleaned_full.empty:
            cutoff_date = cleaned_full.index.max() - timedelta(days=requested_days)
            raw_period = raw_hist.copy()
            if not isinstance(raw_period.index, pd.DatetimeIndex):
                raw_period.index = pd.to_datetime(raw_period.index, errors="coerce")
            raw_period = raw_period[~raw_period.index.isna()]
            if raw_period.index.tz is not None:
                raw_period.index = raw_period.index.tz_localize(None)
            raw_period_sliced = raw_period[raw_period.index >= cutoff_date]
            cleaned_period, data_quality = validate_ohlcv_dataframe(raw_period_sliced)
            if cleaned_period.empty:
                cleaned_period = cleaned_full.tail(min(len(cleaned_full), 30))
                _, data_quality = validate_ohlcv_dataframe(cleaned_period)
        else:
            cleaned_period = cleaned_full
            _, data_quality = validate_ohlcv_dataframe(raw_hist)

        # Build OHLCV bar list for requested period
        ohlcv_bars: List[Dict[str, Any]] = []
        for idx, row in cleaned_period.iterrows():
            ohlcv_bars.append({
                "date": idx.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            })

        start_price = ohlcv_bars[0]["close"] if ohlcv_bars else None
        end_price = ohlcv_bars[-1]["close"] if ohlcv_bars else None
        period_high = max((b["high"] for b in ohlcv_bars), default=None)
        period_low = min((b["low"] for b in ohlcv_bars), default=None)
        avg_volume = int(sum(b["volume"] for b in ohlcv_bars) / len(ohlcv_bars)) if ohlcv_bars else 0
        price_change_pct = (
            round(((end_price - start_price) / start_price) * 100, 2)
            if start_price and end_price and start_price > 0
            else 0.0
        )

        currency = info.get("currency") or ("INR" if clean_market in ["NSE", "BSE"] else "USD")
        current_price = info.get("currentPrice") or info.get("regularMarketPrice") or end_price

        profile: Dict[str, Any] = {
            "ticker": clean_ticker,
            "yf_symbol": yf_symbol,
            "company_name": info.get("shortName") or info.get("longName") or clean_ticker,
            "market": clean_market,
            "exchange": info.get("exchange") or clean_market,
            "currency": currency,
            "sector": info.get("sector") or "N/A",
            "industry": info.get("industry") or "N/A",
            "country": info.get("country") or ("India" if clean_market in ["NSE", "BSE"] else "United States"),
            "website": info.get("website"),
            "employees": info.get("fullTimeEmployees"),
            "market_cap": info.get("marketCap"),
            "current_price": round(float(current_price), 2) if current_price is not None else None,
            "previous_close": info.get("previousClose"),
            "day_high": info.get("dayHigh"),
            "day_low": info.get("dayLow"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "beta": info.get("beta"),
            "dividend_yield": info.get("dividendYield"),
            "shares_outstanding": info.get("sharesOutstanding"),
            "description": info.get("longBusinessSummary") or "No company summary available from data provider.",
        }

        # Collect financial statements
        income_df = None
        balance_df = None
        cashflow_df = None
        try:
            income_df = stock.financials
        except Exception as e:
            logger.warning(f"Failed to fetch income statement for {yf_symbol}: {e}")
        try:
            balance_df = stock.balance_sheet
        except Exception as e:
            logger.warning(f"Failed to fetch balance sheet for {yf_symbol}: {e}")
        try:
            cashflow_df = stock.cashflow
        except Exception as e:
            logger.warning(f"Failed to fetch cash flow for {yf_symbol}: {e}")

        financial_statements = {
            "income_statement": serialize_financial_statement(income_df, "Income Statement", currency),
            "balance_sheet": serialize_financial_statement(balance_df, "Balance Sheet", currency),
            "cash_flow": serialize_financial_statement(cashflow_df, "Cash Flow Statement", currency),
        }

        # Provenance & Source Documents
        sources: List[Dict[str, Any]] = [
            {
                "source_type": "MARKET_OHLCV",
                "title": f"Yahoo Finance Historical OHLCV ({yf_symbol}, {period})",
                "source_url": f"{quote_url}/history",
                "published_at": ohlcv_bars[-1]["date"] if ohlcv_bars else None,
                "retrieved_at": retrieved_at,
                "content_hash": _sha256_hash(ohlcv_bars),
            },
            {
                "source_type": "COMPANY_PROFILE",
                "title": f"Yahoo Finance Company Profile & Quote ({yf_symbol})",
                "source_url": quote_url,
                "published_at": None,
                "retrieved_at": retrieved_at,
                "content_hash": _sha256_hash(profile),
            },
            {
                "source_type": "FINANCIAL_STATEMENTS",
                "title": f"Yahoo Finance Financial Statements ({yf_symbol})",
                "source_url": f"{quote_url}/financials",
                "published_at": (
                    financial_statements["income_statement"]["periods"][0]
                    if financial_statements["income_statement"]["periods"]
                    else None
                ),
                "retrieved_at": retrieved_at,
                "content_hash": _sha256_hash(financial_statements),
            },
        ]

        return {
            "ticker": clean_ticker,
            "market": clean_market,
            "yf_symbol": yf_symbol,
            "period": period,
            "retrieved_at": retrieved_at,
            "profile": profile,
            "raw_info": info,
            "period_performance": {
                "period": period,
                "trading_days": len(ohlcv_bars),
                "start_date": ohlcv_bars[0]["date"] if ohlcv_bars else None,
                "end_date": ohlcv_bars[-1]["date"] if ohlcv_bars else None,
                "start_price": start_price,
                "end_price": end_price,
                "period_high": period_high,
                "period_low": period_low,
                "avg_volume": avg_volume,
                "change_percent": price_change_pct,
                "recent_history": ohlcv_bars[-10:],
            },
            "ohlcv": ohlcv_bars,
            "ohlcv_df_full": cleaned_full,
            "ohlcv_df_period": cleaned_period,
            "data_quality": data_quality,
            "financial_statements": financial_statements,
            "financial_dfs": {
                "income_statement": income_df,
                "balance_sheet": balance_df,
                "cash_flow": cashflow_df,
            },
            "sources": sources,
        }

