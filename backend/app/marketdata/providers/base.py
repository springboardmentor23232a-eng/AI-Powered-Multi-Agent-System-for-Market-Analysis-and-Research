import pandas as pd


class ProviderError(Exception):
    """The data source could not be reached or returned something unusable."""


class SymbolNotFound(ProviderError):
    """The data source has no data for the requested symbol."""


class MarketDataProvider:
    name = ""   # shown to users and stored with every collection
    kind = ""   # "sample" or "yfinance"

    def history(self, symbol: str, period: str) -> pd.DataFrame:
        """Raw OHLCV rows with columns: date, open, high, low, close, volume.

        Rows are returned as received, so duplicates, gaps and bad values are
        still present. Cleaning happens in validation.validate_and_clean.
        """
        raise NotImplementedError

    def profile(self, symbol: str) -> dict | None:
        raise NotImplementedError

    def financials(self, symbol: str) -> dict:
        """{statement: {fiscal_year_end: {line_item: value}}}"""
        raise NotImplementedError

    def symbols(self) -> list[dict] | None:
        """Symbols this source can serve, or None when it is open-ended."""
        return None
