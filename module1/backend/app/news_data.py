"""Financial-news providers for the News & Sentiment agent (Milestone 2).

demo    : a few clearly-labelled SAMPLE headlines so the pipeline can be demonstrated offline. They are NOT real news,
          carry no link, and are flagged `synthetic` everywhere (agent output, API, UI).
yahoo   : Yahoo Finance headline RSS for the ticker - free, no API key (needs internet).
newsapi : https://newsapi.org (set NEWSAPI_KEY) - company-name query, newest first.

A provider returns raw articles; it never summarises or "fills gaps". When a real provider has nothing or fails,
the News agent reports the analysis as Unavailable instead of inventing anything.
"""
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import httpx

from .catalog import Stock, provider_symbol
from .config import settings
from .market_data import Fetched

YAHOO_RSS = "https://feeds.finance.yahoo.com/rss/2.0/headline"
NEWSAPI = "https://newsapi.org/v2/everything"
_HEADERS = {"User-Agent": "Mozilla/5.0"}
MAX_ARTICLES = 15


class NewsError(Exception):
    pass


@dataclass(frozen=True)
class RawArticle:
    title: str
    url: str | None
    source: str | None
    published_at: datetime | None
    summary: str | None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_date(text: str | None) -> datetime | None:
    if not text:
        return None
    try:
        d = parsedate_to_datetime(text)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _demo(stock: Stock) -> Fetched:
    now = _now()
    n = stock.name
    samples = [
        (f"[SAMPLE] {n} beats quarterly earnings estimates as revenue growth accelerates", 2),
        (f"[SAMPLE] {n} announces acquisition of a smaller rival to expand its product range", 5),
        (f"[SAMPLE] Regulator opens investigation into {n} over disclosure practices", 9),
        (f"[SAMPLE] Analysts say {n} outlook is uncertain as demand may slow", 12),
        (f"[SAMPLE] {n} declares dividend and approves share buyback", 20),
    ]
    arts = [RawArticle(t, None, "Sample data (not real news)", now - timedelta(days=d), None) for t, d in samples]
    return Fetched(arts, "Demo news provider (SAMPLE headlines - not real news)", None, True, now)


def _yahoo(stock: Stock) -> Fetched:
    symbol = provider_symbol(stock)
    try:
        r = httpx.get(YAHOO_RSS, params={"s": symbol, "region": "US", "lang": "en-US"}, headers=_HEADERS, timeout=10)
        r.raise_for_status()
        root = ET.fromstring(r.text if hasattr(r, "text") else r.content)
        arts = []
        for item in root.iterfind(".//item"):
            title = (item.findtext("title") or "").strip()
            if not title:
                continue
            arts.append(RawArticle(title, (item.findtext("link") or "").strip() or None, "Yahoo Finance",
                                   _parse_date(item.findtext("pubDate")), (item.findtext("description") or "").strip() or None))
    except Exception as exc:
        raise NewsError(f"Could not fetch news for {symbol} from Yahoo Finance: {exc}") from exc
    return Fetched(arts[:MAX_ARTICLES], "Yahoo Finance headline RSS", f"https://finance.yahoo.com/quote/{symbol}/news", False, _now())


def _newsapi(stock: Stock) -> Fetched:
    if not settings.newsapi_key:
        raise NewsError("NEWS_PROVIDER=newsapi but NEWSAPI_KEY is not set in backend/.env.")
    try:
        r = httpx.get(NEWSAPI, params={"q": f'"{stock.name}"', "language": "en", "sortBy": "publishedAt",
                                       "pageSize": MAX_ARTICLES, "apiKey": settings.newsapi_key}, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "ok":
            raise ValueError(data.get("message", "unexpected response"))
        arts = [RawArticle((a.get("title") or "").strip(), a.get("url"), (a.get("source") or {}).get("name"),
                           _parse_date(a.get("publishedAt")), a.get("description"))
                for a in data.get("articles", []) if (a.get("title") or "").strip()]
    except Exception as exc:
        raise NewsError(f"Could not fetch news for {stock.name} from NewsAPI: {exc}") from exc
    return Fetched(arts, "NewsAPI.org", "https://newsapi.org", False, _now())


def fetch_news(stock: Stock) -> Fetched:
    provider = settings.news_provider
    if provider == "yahoo":
        return _yahoo(stock)
    if provider == "newsapi":
        return _newsapi(stock)
    return _demo(stock)
