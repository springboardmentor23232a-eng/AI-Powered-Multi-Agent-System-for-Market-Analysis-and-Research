"""News & Sentiment Analysis Agent (Milestone 2).

Retrieves recent headlines from the configured provider, classifies each (Positive / Negative / Neutral) with the
transparent rule-based classifier in analysis/sentiment.py, detects key events (earnings, acquisitions, regulatory ...),
attaches source links and publication dates, and flags conflicting or uncertain reports.
If no real news can be retrieved the analysis is Unavailable - news is never invented.
"""
from datetime import datetime, timezone

from ..analysis.sentiment import classify
from ..news_data import NewsError, fetch_news
from .context import ResearchContext
from .schemas import Article, Finding, NewsOutput, SourceRef


def run(ctx: ResearchContext) -> NewsOutput:
    stock = ctx.stock
    base = dict(ticker=stock.ticker, market=stock.market, generated_at=datetime.now(timezone.utc))
    try:
        fetched = fetch_news(stock)
    except NewsError as exc:
        return NewsOutput(status="Unavailable", summary="News analysis is unavailable - no news could be retrieved.",
                          limitations=[str(exc), "No news was invented to fill the gap."], error=str(exc), **base)
    ctx.record("news", fetched, len(fetched.data), None)
    src = SourceRef(name=fetched.source, url=fetched.source_url, retrieved_at=fetched.retrieved_at, synthetic=fetched.synthetic)
    raw = [a for a in fetched.data if a.title]
    if not raw:
        return NewsOutput(status="Unavailable", summary=f"No recent news was found for {stock.name}.", sources=[src],
                          limitations=["The provider returned no articles; nothing was invented."], **base)

    arts: list[Article] = []
    for a in raw:
        c = classify(f"{a.title}. {a.summary or ''}")
        arts.append(Article(title=a.title, url=a.url, source=a.source, published_at=a.published_at, summary=a.summary,
                            sentiment=c["sentiment"], score=c["score"], events=c["events"], uncertain=c["uncertain"],
                            synthetic=fetched.synthetic))
    arts.sort(key=lambda x: x.published_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    counts = {k: sum(a.sentiment == k for a in arts) for k in ("Positive", "Negative", "Neutral")}
    net = sum(a.score for a in arts) / len(arts)
    tone = ("Mixed" if counts["Positive"] and counts["Negative"] and min(counts["Positive"], counts["Negative"]) / len(arts) >= 0.25
            else "Positive" if net >= 0.2 else "Negative" if net <= -0.2 else "Neutral")
    events: dict[str, list[int]] = {}
    for i, a in enumerate(arts):
        for e in a.events:
            events.setdefault(e, []).append(i)

    conflicts = []
    if counts["Positive"] and counts["Negative"]:
        conflicts.append(f"Coverage is split: {counts['Positive']} positive and {counts['Negative']} negative headline(s).")
    for e, idx in events.items():
        s = {arts[i].sentiment for i in idx}
        if "Positive" in s and "Negative" in s:
            conflicts.append(f"Reports about '{e}' disagree (both positive and negative headlines).")
    uncertain = [i for i, a in enumerate(arts) if a.uncertain]

    limitations = ["Sentiment is a rule-based reading of headline/summary wording only; it can miss nuance, sarcasm and context."]
    if fetched.synthetic:
        limitations.insert(0, "These headlines are SAMPLE data for demonstration, NOT real news. Set NEWS_PROVIDER=yahoo (no key) "
                              "or newsapi for real articles.")
    if any(a.url is None for a in arts) and not fetched.synthetic:
        limitations.append(f"{sum(a.url is None for a in arts)} article(s) have no source link.")
    if any(a.published_at is None for a in arts):
        limitations.append(f"{sum(a.published_at is None for a in arts)} article(s) have no publication date.")
    limitations.append("Only headline feeds are searched; official exchange filings and company announcements are not retrieved separately.")

    findings = [Finding(text=f"{len(arts)} recent headline(s): {counts['Positive']} positive, {counts['Negative']} negative, "
                             f"{counts['Neutral']} neutral (average sentiment score {net:+.2f}).", kind="calculated")]
    for e, idx in events.items():
        a = arts[idx[0]]
        findings.append(Finding(text=f"{e.capitalize()}: \"{a.title}\"" + (f" ({a.published_at.date()})" if a.published_at else "") +
                                (f" - {a.source}" if a.source else ""), kind="fact",
                                tone={"Positive": "positive", "Negative": "negative", "Neutral": "neutral"}[a.sentiment]))
    for c in conflicts:
        findings.append(Finding(text=c, kind="interpretation", tone="caution"))
    if uncertain:
        findings.append(Finding(text=f"{len(uncertain)} headline(s) use uncertain wording (e.g. 'may', 'reportedly'): treat as unconfirmed.",
                                kind="interpretation", tone="caution"))
    summary = f"News tone is {tone.lower()} across {len(arts)} headline(s)" + (" (SAMPLE data)." if fetched.synthetic else ".")
    return NewsOutput(summary=summary, findings=findings, limitations=limitations, sources=[src], articles=arts, counts=counts,
                      net_score=round(net, 2), tone=tone, key_events=events, conflicts=conflicts, **base)
