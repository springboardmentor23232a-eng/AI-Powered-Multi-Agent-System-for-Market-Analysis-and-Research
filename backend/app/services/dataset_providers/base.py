from abc import ABC, abstractmethod
from typing import List, Optional, Any
import pandas as pd
from pydantic import BaseModel, ConfigDict


class DatasetCollectionResult(BaseModel):
    """
    Standardized result returned by a market data provider.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    provider_name: str
    ticker: str
    market: str
    period: str
    success: bool
    status_code: int = 200
    latency_ms: float = 0.0
    raw_df: Optional[Any] = None
    records_count: int = 0
    error_message: Optional[str] = None
    retrieved_at: str


class BaseMarketDataProvider(ABC):
    """
    Abstract Base Class for modular market data providers.
    Supports pluggable data sources with capability matrices and health verification.
    """
    name: str = "base"
    supported_markets: List[str] = []

    @abstractmethod
    def fetch_ohlcv(self, ticker: str, period: str, market: str) -> DatasetCollectionResult:
        """
        Retrieves raw historical OHLCV dataset for the given symbol and period.
        """
        pass

    @abstractmethod
    def supports_market(self, market: str) -> bool:
        """
        Checks whether this provider supports the given exchange/market.
        """
        pass
