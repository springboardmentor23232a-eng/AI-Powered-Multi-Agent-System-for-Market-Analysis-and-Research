from functools import lru_cache

from ..config import DATA_SOURCE
from .providers.base import MarketDataProvider


@lru_cache(maxsize=1)
def get_provider() -> MarketDataProvider:
    """The data source chosen by DATA_SOURCE: 'sample' (default) or 'yfinance'."""
    if DATA_SOURCE == "yfinance":
        from .providers.yf import YFinanceProvider
        return YFinanceProvider()
    from .providers.sample import SampleProvider
    return SampleProvider()
