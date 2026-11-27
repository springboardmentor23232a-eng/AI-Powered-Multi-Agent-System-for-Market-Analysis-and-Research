import time
import io
import logging
import urllib.request
from datetime import datetime, timezone
from typing import List, Optional
import pandas as pd

from app.services.dataset_providers.base import BaseMarketDataProvider, DatasetCollectionResult

logger = logging.getLogger("uvicorn.error")


class StooqProvider(BaseMarketDataProvider):
    """
    Secondary public provider for US equities.
    Supports modular fallback for NASDAQ and NYSE.
    Explicitly checks for anti-bot challenges and records failures accurately.
    """
    name: str = "stooq"
    supported_markets: List[str] = ["NASDAQ", "NYSE"]

    def supports_market(self, market: str) -> bool:
        if not market:
            return False
        return market.strip().upper() in self.supported_markets

    def fetch_ohlcv(self, ticker: str, period: str, market: str) -> DatasetCollectionResult:
        start_time = time.perf_counter()
        now_str = datetime.now(timezone.utc).isoformat()
        clean_ticker = ticker.strip().lower()

        # Reject Indian market tickers directly
        if clean_ticker.endswith(".ns") or clean_ticker.endswith(".bo") or market in {"NSE", "BSE"}:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return DatasetCollectionResult(
                provider_name=self.name,
                ticker=ticker,
                market=market,
                period=period,
                success=False,
                status_code=400,
                latency_ms=latency_ms,
                raw_df=None,
                records_count=0,
                error_message=f"{self.name} does not support Indian market symbols ({market}).",
                retrieved_at=now_str,
            )

        # Normalize US symbol for Stooq (e.g. aapl.us)
        stooq_symbol = clean_ticker if clean_ticker.endswith(".us") else f"{clean_ticker}.us"
        url = f"https://stooq.com/q/d/l/?s={stooq_symbol}&i=d"

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SAI-Analysis/1.0"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                content = response.read().decode("utf-8")
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

                # Check for anti-bot / JavaScript challenge response
                if "<html" in content.lower() or "javascript" in content.lower() or "verify your browser" in content.lower():
                    return DatasetCollectionResult(
                        provider_name=self.name,
                        ticker=ticker,
                        market=market,
                        period=period,
                        success=False,
                        status_code=403,
                        latency_ms=latency_ms,
                        raw_df=None,
                        records_count=0,
                        error_message="Provider challenged request with automated anti-bot browser verification.",
                        retrieved_at=now_str,
                    )

                df = pd.read_csv(io.StringIO(content))
                if df.empty or "Date" not in df.columns:
                    return DatasetCollectionResult(
                        provider_name=self.name,
                        ticker=ticker,
                        market=market,
                        period=period,
                        success=False,
                        status_code=404,
                        latency_ms=latency_ms,
                        raw_df=None,
                        records_count=0,
                        error_message=f"No tabular OHLCV data found for symbol '{stooq_symbol}' on {self.name}.",
                        retrieved_at=now_str,
                    )

                # Set Date index for standard OHLCV alignment
                df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
                df = df.dropna(subset=["Date"]).set_index("Date")

                return DatasetCollectionResult(
                    provider_name=self.name,
                    ticker=ticker,
                    market=market,
                    period=period,
                    success=True,
                    status_code=200,
                    latency_ms=latency_ms,
                    raw_df=df,
                    records_count=len(df),
                    error_message=None,
                    retrieved_at=now_str,
                )

        except Exception as exc:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.warning(f"{self.name} provider attempt failed for {ticker}: {exc}")
            return DatasetCollectionResult(
                provider_name=self.name,
                ticker=ticker,
                market=market,
                period=period,
                success=False,
                status_code=502,
                latency_ms=latency_ms,
                raw_df=None,
                records_count=0,
                error_message=f"Provider request failure: {str(exc)}",
                retrieved_at=now_str,
            )
