"""Placeholder research workflow.

Generates a deterministic *demo* report so the workspace is fully usable.
Later modules replace `build_report` with the real multi-agent pipeline.
"""
import math
import random
import time
from datetime import datetime, timedelta, timezone

from .config import PERIODS
from .stocks import provider_symbol


def build_report(ticker: str, company: str, market: str, period: str) -> dict:
    rnd = random.Random(f"{ticker}-{market}-{period}")
    days = PERIODS[period]
    price = rnd.uniform(80, 2500)
    drift, vol = rnd.uniform(-0.0004, 0.0012), rnd.uniform(0.008, 0.022)
    series = []
    start = datetime.now(timezone.utc) - timedelta(days=int(days * 1.45))
    for i in range(days):
        price *= math.exp(drift + rnd.gauss(0, vol))
        series.append(price)
    step = max(1, days // 90)  # keep the chart light
    points = [{"i": i, "price": round(p, 2)} for i, p in enumerate(series) if i % step == 0 or i == days - 1]
    rets = [math.log(series[i] / series[i - 1]) for i in range(1, days)]
    mean = sum(rets) / len(rets)
    volat = math.sqrt(sum((r - mean) ** 2 for r in rets) / len(rets)) * math.sqrt(252)
    change = (series[-1] / series[0] - 1) * 100
    ma = sum(series[-20:]) / min(20, len(series))
    sentiment = rnd.choice(["Positive", "Neutral", "Cautious"])
    risk = "High" if volat > 0.32 else "Moderate" if volat > 0.2 else "Low"
    outlook = "Bullish" if change > 8 and sentiment != "Cautious" else "Bearish" if change < -8 else "Neutral"
    return {
        "demo": True,
        "provider_symbol": provider_symbol(ticker, market),
        "headline": f"{company} ({ticker}) shows a {outlook.lower()} outlook over {period}.",
        "metrics": {
            "last_price": round(series[-1], 2), "period_change_pct": round(change, 2),
            "high": round(max(series), 2), "low": round(min(series), 2),
            "annualised_volatility_pct": round(volat * 100, 1),
        },
        "outlook": outlook,
        "prices": points,
        "agents": [
            {"name": "Fundamental Agent", "result": f"Valuation looks {'stretched' if change > 25 else 'reasonable'} relative to the recent trend."},
            {"name": "Technical Agent", "result": f"Price is {'above' if series[-1] > ma else 'below'} its 20-day average ({ma:.2f})."},
            {"name": "Sentiment Agent", "result": f"News and social sentiment reads {sentiment.lower()}."},
            {"name": "Risk Agent", "result": f"{risk} risk: annualised volatility of {volat * 100:.1f}%."},
        ],
        "disclaimer": "Demo data for the Module 1 workspace. Not investment advice.",
    }


def run_research(task_id: int, delay: float = 2.0):
    """Background job: Pending -> Processing -> Completed/Failed."""
    from .database import SessionLocal
    from .models import ResearchTask, now

    db = SessionLocal()
    try:
        task = db.get(ResearchTask, task_id)
        if not task:
            return
        task.status = "Processing"
        db.commit()
        time.sleep(delay)
        try:
            task.report = build_report(task.ticker, task.company_name, task.market, task.analysis_period)
            task.status = "Completed"
        except Exception as exc:  # record failures clearly
            task.status, task.error = "Failed", str(exc)
        task.completed_at = now()
        db.commit()
    finally:
        db.close()
