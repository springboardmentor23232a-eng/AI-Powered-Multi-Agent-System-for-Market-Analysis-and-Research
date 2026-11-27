import logging
from typing import List, Tuple, Optional
import pandas as pd

from app.schemas.dataset import ProviderAttemptLog
from app.services.dataset_providers.base import BaseMarketDataProvider, DatasetCollectionResult
from app.services.dataset_providers.yfinance_provider import YFinanceProvider
from app.services.dataset_providers.stooq_provider import StooqProvider

logger = logging.getLogger("uvicorn.error")


class ProviderRegistry:
    """
    Manages market data providers, exchange routing, health checks, and automatic fallback.
    Maintains a full provenance attempt log for auditability.
    """
    def __init__(self):
        self.providers: List[BaseMarketDataProvider] = [
            YFinanceProvider(),
            StooqProvider(),
        ]

    def collect_dataset(
        self,
        ticker: str,
        period: str = "1mo",
        market: str = "NSE"
    ) -> Tuple[Optional[pd.DataFrame], str, float, List[ProviderAttemptLog], str]:
        """
        Executes exchange-aware collection across registered providers.
        Returns:
            (raw_df, successful_provider_name, total_latency_ms, attempt_logs, retrieval_timestamp)
        """
        attempt_logs: List[ProviderAttemptLog] = []
        clean_market = (market or "NSE").strip().upper()
        clean_ticker = ticker.strip().upper()

        # Find providers claiming support for this market
        eligible_providers = [p for p in self.providers if p.supports_market(clean_market)]
        if not eligible_providers:
            # Fallback to any provider if exchange tag is unfamiliar
            eligible_providers = self.providers

        for provider in eligible_providers:
            logger.info(f"Attempting dataset retrieval for '{clean_ticker}' via {provider.name} (Market: {clean_market})...")
            result: DatasetCollectionResult = provider.fetch_ohlcv(clean_ticker, period, clean_market)

            status_str = "SUCCESS" if result.success else ("CHALLENGED" if result.status_code == 403 else "FAILED")
            log_item = ProviderAttemptLog(
                provider=provider.name,
                market=clean_market,
                status=status_str,
                http_code=result.status_code,
                latency_ms=result.latency_ms,
                records_retrieved=result.records_count,
                message=result.error_message or f"Successfully retrieved {result.records_count} records.",
                timestamp=result.retrieved_at,
            )
            attempt_logs.append(log_item)

            if result.success and result.raw_df is not None and not result.raw_df.empty:
                logger.info(f"Dataset successfully collected via {provider.name} in {result.latency_ms}ms ({result.records_count} rows).")
                return (
                    result.raw_df,
                    provider.name,
                    result.latency_ms,
                    attempt_logs,
                    result.retrieved_at,
                )

        # All providers exhausted
        logger.warning(f"All data providers failed to retrieve dataset for '{clean_ticker}' ({clean_market}).")
        latest_ts = attempt_logs[-1].timestamp if attempt_logs else ""
        return None, "none", 0.0, attempt_logs, latest_ts
