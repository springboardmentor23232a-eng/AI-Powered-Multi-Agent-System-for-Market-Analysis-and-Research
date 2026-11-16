import logging
import threading
import time
from typing import Callable, Dict, Optional, Tuple
from app.schemas.market_data import StockMarketData

logger = logging.getLogger("fincrew.cache")


class MarketDataCache:
    """
    Thread-safe, in-memory TTL (Time-To-Live) cache for stock market data.
    Protects upstream market data providers (e.g. yfinance) against IP rate limits,
    especially during rapid re-queries and multi-stock peer comparisons.

    Guarantees:
    - Thread-safe reads and writes using threading.RLock.
    - Automatic eviction of expired entries based on TTL.
    - Never caches failed, incomplete, or invalid data.
    """

    def __init__(self, default_ttl_seconds: int = 600):
        self._cache: Dict[str, Tuple[StockMarketData, float]] = {}
        self._lock = threading.RLock()
        self._default_ttl = max(1, default_ttl_seconds)

    def get(self, ticker: str) -> Optional[StockMarketData]:
        """Retrieves cached market data for ticker if present and not expired."""
        if not ticker:
            return None

        clean_ticker = ticker.strip().upper()
        now = time.time()

        with self._lock:
            entry = self._cache.get(clean_ticker)
            if entry is None:
                return None

            data, expiry = entry
            if now >= expiry:
                # Expired: evict immediately
                del self._cache[clean_ticker]
                logger.debug("Evicted expired market data cache for '%s'", clean_ticker)
                return None

            logger.debug("Market data cache HIT for '%s'", clean_ticker)
            return data

    def set(
        self,
        ticker: str,
        data: StockMarketData,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """
        Stores validated StockMarketData in the cache.
        Rejects invalid or incomplete data.
        """
        if not ticker or not isinstance(data, StockMarketData):
            return

        # Defensive check: do not cache empty or invalid market data
        if not data.price or data.price.current_price is None:
            logger.warning("Refusing to cache incomplete market data without current_price for '%s'", ticker)
            return

        clean_ticker = ticker.strip().upper()
        ttl = max(1, ttl_seconds if ttl_seconds is not None else self._default_ttl)
        expiry = time.time() + ttl

        with self._lock:
            self._cache[clean_ticker] = (data, expiry)
            logger.debug("Market data cached for '%s' (TTL: %ds)", clean_ticker, ttl)

    def invalidate(self, ticker: str) -> bool:
        """Removes a specific ticker from the cache."""
        clean_ticker = ticker.strip().upper()
        with self._lock:
            if clean_ticker in self._cache:
                del self._cache[clean_ticker]
                return True
        return False

    def clear(self) -> None:
        """Purges all entries from the cache."""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """Returns the number of active, unexpired cached entries."""
        now = time.time()
        with self._lock:
            # Clean expired on inspect
            expired_keys = [k for k, (_, exp) in self._cache.items() if now >= exp]
            for k in expired_keys:
                del self._cache[k]
            return len(self._cache)


# Global singleton cache instance with 10-minute default TTL
market_data_cache = MarketDataCache(default_ttl_seconds=600)


def get_cached_stock_market_data(
    ticker: str,
    fetcher: Optional[Callable[[str], StockMarketData]] = None,
    ttl_seconds: Optional[int] = None,
) -> StockMarketData:
    """
    Helper function that returns cached data if available;
    otherwise executes fetcher, caches valid results, and returns.
    """
    cached = market_data_cache.get(ticker)
    if cached is not None:
        return cached

    if fetcher is None:
        from app.services.market_data import fetch_stock_market_data
        fetcher = fetch_stock_market_data

    # Execute fetcher (raises exception on failure without caching)
    data = fetcher(ticker)

    # Only cache successful, complete responses
    market_data_cache.set(ticker, data, ttl_seconds=ttl_seconds)
    return data
