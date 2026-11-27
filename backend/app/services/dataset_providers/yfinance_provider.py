import time
import logging
from datetime import datetime, timezone
from typing import List, Optional
import yfinance as yf
import pandas as pd

from app.services.dataset_providers.base import BaseMarketDataProvider, DatasetCollectionResult

logger = logging.getLogger("uvicorn.error")


class YFinanceProvider(BaseMarketDataProvider):
    """
    Primary production provider for verified global and Indian equity coverage.
    Supports NSE, BSE, NASDAQ, and NYSE daily historical OHLCV data.
    """
    name: str = "yfinance"
    supported_markets: List[str] = ["NSE", "BSE", "NASDAQ", "NYSE"]

    def supports_market(self, market: str) -> bool:
        if not market:
            return True
        return market.strip().upper() in self.supported_markets

    def fetch_ohlcv(self, ticker: str, period: str, market: str) -> DatasetCollectionResult:
        start_time = time.perf_counter()
        now_str = datetime.now(timezone.utc).isoformat()
        clean_ticker = ticker.strip().upper()

        valid_periods = {"1mo", "3mo", "6mo", "1y", "2y", "5y", "max"}
        clean_period = period.strip() if period in valid_periods else "1mo"

        try:
            t = yf.Ticker(clean_ticker)
            raw_df = t.history(period=clean_period, interval="1d")
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            if raw_df is None or not isinstance(raw_df, pd.DataFrame) or raw_df.empty:
                return DatasetCollectionResult(
                    provider_name=self.name,
                    ticker=clean_ticker,
                    market=market,
                    period=clean_period,
                    success=False,
                    status_code=404,
                    latency_ms=latency_ms,
                    raw_df=None,
                    records_count=0,
                    error_message=f"No data returned by {self.name} for ticker '{clean_ticker}'.",
                    retrieved_at=now_str,
                )

            return DatasetCollectionResult(
                provider_name=self.name,
                ticker=clean_ticker,
                market=market,
                period=clean_period,
                success=True,
                status_code=200,
                latency_ms=latency_ms,
                raw_df=raw_df,
                records_count=len(raw_df),
                error_message=None,
                retrieved_at=now_str,
            )

        except Exception as exc:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.warning(f"{self.name} provider error for {clean_ticker}: {exc}")
            return DatasetCollectionResult(
                provider_name=self.name,
                ticker=clean_ticker,
                market=market,
                period=clean_period,
                success=False,
                status_code=502,
                latency_ms=latency_ms,
                raw_df=None,
                records_count=0,
                error_message=f"Provider network/API failure: {str(exc)}",
                retrieved_at=now_str,
            )
