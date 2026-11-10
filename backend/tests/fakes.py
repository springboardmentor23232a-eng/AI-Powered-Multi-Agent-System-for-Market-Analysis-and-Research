import numpy as np
import pandas as pd

from app.services.market_data import ProviderError


def make_ohlcv(n=120, end="2026-10-30", start_price=100.0):
    dates = pd.bdate_range(end=end, periods=n)
    close = start_price + np.arange(n) * 0.5
    return pd.DataFrame({"date": dates, "open": close - 0.2, "high": close + 1, "low": close - 1,
                         "close": close, "volume": np.full(n, 1_000_000)})


class FakeProvider:
    name = "fake"

    def __init__(self, df=None, financials=None, fail=False):
        self.df = make_ohlcv() if df is None else df
        self.financials = financials
        self.fail = fail
        self.calls = 0

    def get_ohlcv(self, symbol, period):
        self.calls += 1
        if self.fail:
            raise ProviderError("down")
        return self.df

    def get_financials(self, symbol):
        self.calls += 1
        if self.fail:
            raise ProviderError("down")
        return self.financials or {
            "profile": {"longName": "Test Co"},
            "annual": [
                {"year": 2025, "revenue": 100.0, "operating_income": 20.0, "net_income": 15.0,
                 "total_debt": 30.0, "total_equity": 80.0},
                {"year": 2024, "revenue": 90.0, "operating_income": 18.0, "net_income": 13.0,
                 "total_debt": None, "total_equity": 70.0},
            ],
        }


from datetime import datetime, timedelta, timezone

from app.services.llm import TemplateLLM
from app.services.news import Article


class FakeNews:
    name = "fake-news"

    def __init__(self, articles=None, fail=False):
        self.articles, self.fail = articles or [], fail

    def fetch(self, query, limit=15):
        if self.fail:
            raise ProviderError("news down")
        return self.articles[:limit]


def article(title, days_ago=1, url=None, now=None):
    now = now or datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
    return Article(title=title, url=url or f"https://news.test/{abs(hash(title))}", snippet="snippet text",
                   published_at=now - timedelta(days=days_ago), publisher="Test")


FIN = {
    "profile": {"longName": "Test Co", "sharesOutstanding": 5.0},
    "annual": [
        {"year": 2025, "revenue": 100.0, "operating_income": 20.0, "net_income": 15.0,
         "total_debt": 30.0, "total_equity": 80.0},
        {"year": 2024, "revenue": 90.0, "operating_income": 18.0, "net_income": 13.0,
         "total_debt": 25.0, "total_equity": 70.0},
    ],
}
