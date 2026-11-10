"""Deterministic offline providers. Used to test the harness and for CI.
Results produced with these are NOT evaluation results: they only show the pipeline works."""
import zlib
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd

from app.services.market_data import _period_days
from app.services.news import Article


def _rng(symbol: str) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32(symbol.encode()))


class SyntheticMarket:
    name = "synthetic"

    def get_ohlcv(self, symbol: str, period: str) -> pd.DataFrame:
        rng = _rng(symbol)
        n = 800
        dates = pd.bdate_range(end=date.today(), periods=n)
        drift = rng.normal(0.0003, 0.0004)
        close = 500 * np.exp(np.cumsum(rng.normal(drift, 0.014, n)))
        df = pd.DataFrame({"date": dates, "open": close * 0.999, "high": close * 1.01, "low": close * 0.99,
                           "close": close, "volume": rng.integers(1_000_000, 5_000_000, n)})
        days = _period_days(period)
        return df if days is None else df.tail(int(days * 252 / 365) + 5).reset_index(drop=True)

    def get_financials(self, symbol: str) -> dict:
        rng = _rng(symbol + "fin")
        rev = float(rng.uniform(5e10, 5e11))
        annual = []
        for k, year in enumerate((2022, 2023, 2024, 2025)):
            r = rev * (1 + rng.normal(0.08, 0.05)) ** k
            annual.append({"year": year, "revenue": r, "operating_income": r * rng.uniform(0.1, 0.3),
                           "net_income": r * rng.uniform(0.05, 0.2), "total_debt": r * rng.uniform(0.05, 0.6),
                           "total_equity": r * rng.uniform(0.4, 1.2)})
        return {"profile": {"longName": symbol, "sharesOutstanding": float(rng.uniform(5e8, 5e9))}, "annual": annual}


class SyntheticNews:
    name = "synthetic-news"
    TEMPLATES = ["{t} profit rises as quarterly results beat estimates", "{t} shares fall on regulatory probe",
                 "{t} wins large contract", "{t} to acquire smaller rival in all-cash deal",
                 "{t} announces dividend, outlook steady", "Analysts downgrade {t} on weak demand"]

    def fetch(self, query: str, limit: int = 15):
        t = query.split()[0]
        rng = _rng(query)
        now = datetime.now(timezone.utc)
        idx = rng.permutation(len(self.TEMPLATES))[: int(rng.integers(3, 6))]
        return [Article(title=self.TEMPLATES[i].format(t=t), url=f"https://news.synthetic/{t}/{i}",
                        published_at=now - timedelta(days=int(rng.integers(1, 20))), snippet="synthetic snippet",
                        publisher="Synthetic Wire") for i in idx][:limit]
