import pandas as pd
import yfinance as yf

from ..providers.base import MarketDataProvider, ProviderError, SymbolNotFound

PERIODS = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "5Y": "5y"}
STATEMENTS = {"income_statement": "income_stmt", "balance_sheet": "balance_sheet", "cash_flow": "cashflow"}


class YFinanceProvider(MarketDataProvider):
    name = "Yahoo Finance (yfinance)"
    kind = "yfinance"

    def history(self, symbol, period):
        try:
            raw = yf.Ticker(symbol).history(period=PERIODS[period], auto_adjust=False)
        except Exception as e:
            raise ProviderError("Yahoo Finance could not be reached right now") from e
        if raw.empty:
            raise SymbolNotFound(f"Yahoo Finance has no price data for {symbol}")
        raw = raw.reset_index()
        dates = pd.to_datetime(raw.iloc[:, 0]).dt.tz_localize(None).dt.strftime("%Y-%m-%d")
        return pd.DataFrame({
            "date": dates, "open": raw["Open"], "high": raw["High"],
            "low": raw["Low"], "close": raw["Close"], "volume": raw["Volume"],
        })

    def profile(self, symbol):
        try:
            info = yf.Ticker(symbol).get_info()
        except Exception as e:
            raise ProviderError("Company profile unavailable") from e
        fields = {
            "name": info.get("longName") or info.get("shortName"), "exchange": info.get("fullExchangeName") or info.get("exchange"),
            "currency": info.get("currency"), "country": info.get("country"), "sector": info.get("sector"),
            "industry": info.get("industry"), "website": info.get("website"), "summary": info.get("longBusinessSummary"),
            "employees": info.get("fullTimeEmployees"), "market_cap": info.get("marketCap"),
        }
        fields = {k: v for k, v in fields.items() if v not in (None, "")}
        return fields or None

    def financials(self, symbol):
        ticker = yf.Ticker(symbol)
        out = {}
        for key, attr in STATEMENTS.items():
            try:
                frame = getattr(ticker, attr)
            except Exception:
                continue
            if frame is None or frame.empty:
                continue
            out[key] = {
                str(col.date()): {str(item): float(v) for item, v in frame[col].items() if pd.notna(v)}
                for col in frame.columns
            }
        return out
