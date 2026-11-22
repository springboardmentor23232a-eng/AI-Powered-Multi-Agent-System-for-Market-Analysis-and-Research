import json
from functools import lru_cache
from pathlib import Path

import pandas as pd

from .base import MarketDataProvider, SymbolNotFound

DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "sample"
PERIOD_DAYS = {"1M": 30, "3M": 91, "6M": 182, "1Y": 365, "5Y": 1826}


@lru_cache(maxsize=1)
def _prices() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "prices.csv")


@lru_cache(maxsize=1)
def _json(name: str) -> dict:
    return json.loads((DATA_DIR / name).read_text())


class SampleProvider(MarketDataProvider):
    """Serves the bundled model dataset in backend/data/sample (synthetic data)."""

    name = "Sample dataset (synthetic)"
    kind = "sample"

    def history(self, symbol, period):
        df = _prices()
        rows = df[df["symbol"] == symbol]
        if rows.empty:
            raise SymbolNotFound(
                f"{symbol} is not in the sample dataset. Set DATA_SOURCE=yfinance in backend/.env to use live data."
            )
        # The dataset is static, so the window is measured back from its last date, not from today.
        end = pd.to_datetime(rows["date"]).max()
        start = end - pd.Timedelta(days=PERIOD_DAYS[period])
        keep = pd.to_datetime(rows["date"]) >= start
        return rows.loc[keep, ["date", "open", "high", "low", "close", "volume"]].reset_index(drop=True)

    def profile(self, symbol):
        return _json("profiles.json").get(symbol)

    def financials(self, symbol):
        return _json("financials.json").get(symbol, {})

    def symbols(self):
        return [{"symbol": s, "name": p["name"], "market": p["market"]} for s, p in _json("profiles.json").items()]
