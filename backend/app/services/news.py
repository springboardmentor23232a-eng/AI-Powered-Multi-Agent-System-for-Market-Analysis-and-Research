import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Protocol
from urllib.parse import quote_plus
from xml.etree import ElementTree

import httpx
from pydantic import BaseModel

from app.services.market_data import ProviderError


class Article(BaseModel):
    title: str
    url: str
    published_at: datetime | None = None
    snippet: str = ""
    publisher: str | None = None


class NewsProvider(Protocol):
    name: str

    def fetch(self, query: str, limit: int = 15) -> list[Article]: ...


class GoogleNewsRssProvider:
    """Public RSS search feed. Unverified live in this repo; tests use a fake provider."""

    name = "google-news-rss"

    def fetch(self, query: str, limit: int = 15) -> list[Article]:
        url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en"
        try:
            r = httpx.get(url, timeout=20, follow_redirects=True)
            r.raise_for_status()
            root = ElementTree.fromstring(r.content)
        except (httpx.HTTPError, ElementTree.ParseError) as exc:
            raise ProviderError(f"news fetch failed: {exc}") from exc
        out = []
        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            if not title or not link:
                continue
            published = None
            if item.findtext("pubDate"):
                try:
                    published = parsedate_to_datetime(item.findtext("pubDate"))
                except (TypeError, ValueError):
                    published = None
            snippet = re.sub(r"<[^>]+>", " ", item.findtext("description") or "").strip()
            src = item.find("source")
            out.append(Article(title=title, url=link, published_at=published, snippet=snippet[:300],
                               publisher=src.text if src is not None else None))
            if len(out) >= limit:
                break
        return out


def build_news_provider() -> NewsProvider:
    return GoogleNewsRssProvider()
