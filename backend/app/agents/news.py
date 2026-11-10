import hashlib
from datetime import datetime, timedelta, timezone

from app.agents.base import AgentContext, ClaimBuilder
from app.data.universe import UNIVERSE
from app.models import SourceDocument
from app.schemas.agents import AgentResult, AgentStatus, NewsItem, NewsOutput, Signal
from app.services.market_data import normalize_ticker

MAX_AGE_DAYS = 30
EVENT_KEYWORDS = {
    "earnings": ("earnings", "results", "profit", "revenue", "quarter", "q1", "q2", "q3", "q4"),
    "acquisition": ("acquire", "acquisition", "merger", "takeover", "stake", "buyout"),
    "regulatory": ("sebi", "rbi", "regulator", "penalty", "fine", "probe", "investigation", "ban", "tax notice"),
}


def event_type(title: str) -> str:
    low = title.lower()
    for event, words in EVENT_KEYWORDS.items():
        if any(w in low for w in words):
            return event
    return "other"


def article_hash(title: str, url: str, published: datetime | None) -> str:
    return hashlib.sha256(f"{title}|{url}|{published.isoformat() if published else ''}".encode()).hexdigest()


class NewsAgent:
    name = "news"

    def run(self, ctx: AgentContext) -> AgentResult:
        if ctx.as_of:
            return AgentResult(agent=self.name, status=AgentStatus.unavailable,
                               limitations=["News is not point-in-time and is skipped in replay mode"])
        now = ctx.now or datetime.now(timezone.utc)
        ticker = normalize_ticker(ctx.ticker)
        company = UNIVERSE.get(ticker, ticker)
        articles = ctx.news.fetch(f"{company} {ticker} NSE stock", limit=15)  # ProviderError propagates (supervisor retries)

        seen, kept = set(), []
        for a in articles:
            key = a.url or a.title
            pub = a.published_at
            if pub is not None and pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            if key in seen or (pub is not None and pub < now - timedelta(days=MAX_AGE_DAYS)):
                continue
            seen.add(key)
            kept.append(a)
        if not kept:
            return AgentResult(agent=self.name, status=AgentStatus.unavailable,
                               limitations=[f"No news found for {ticker} in the last {MAX_AGE_DAYS} days"])

        labels = ctx.llm.classify_sentiment([a.title for a in kept])
        if len(labels) != len(kept):
            labels = ["neutral"] * len(kept)
        b, items = ClaimBuilder(self.name), []
        for a, label in zip(kept, labels):
            h = article_hash(a.title, a.url, a.published_at)
            if ctx.task_id is not None:
                ctx.db.add(SourceDocument(task_id=ctx.task_id, source_type="news", title=a.title, source_url=a.url,
                                          published_at=a.published_at, retrieved_at=now, content_hash=h,
                                          content_excerpt=f"{a.title} {a.snippet}".strip()))
            date = a.published_at.date().isoformat() if a.published_at else "undated"
            b.fact(f"{date}: {a.title}", h, a.title, url=a.url)
            items.append(NewsItem(title=a.title, url=a.url, published_at=a.published_at, sentiment=label,
                                  event_type=event_type(a.title), content_hash=h))
        if ctx.task_id is not None:
            ctx.db.commit()

        pos, neg = labels.count("positive"), labels.count("negative")
        net = (pos - neg) / len(items)
        signal = Signal.bullish if net >= 0.3 else Signal.bearish if net <= -0.3 else Signal.neutral
        limitations = ["Sentiment labels are AI-classified from headlines and snippets, not full articles"]
        for ev in ("earnings", "acquisition", "regulatory"):
            sent = {i.sentiment for i in items if i.event_type == ev}
            if {"positive", "negative"} <= sent:
                limitations.append(f"Conflicting reports on {ev} events: both positive and negative coverage")
        summary = ctx.llm.summarize(self.name, {"headlines reviewed": str(len(items)), "positive": str(pos),
                                                "negative": str(neg), "neutral": str(len(items) - pos - neg)})
        b.interpret(summary, key="summary")
        out = NewsOutput(items=items, signal=signal, summary=summary)
        return AgentResult(agent=self.name, status=AgentStatus.success, data=out.model_dump(mode="json"),
                           claims=b.claims, limitations=limitations)
