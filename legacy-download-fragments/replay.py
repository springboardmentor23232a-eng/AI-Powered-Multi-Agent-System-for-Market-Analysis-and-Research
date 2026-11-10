"""Time-travel replay calibration: run research as of past dates, then score the technical signal against what
happened next. Only the technical signal is scored: financial statements are not point-in-time, so the fundamental
signal would leak the future."""
import math
from datetime import timedelta

import pandas as pd
from sqlalchemy import select

from app.models import AgentResult


def wilson_interval(hits: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    if n == 0:
        return None
    p = hits / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return round(100 * (centre - half), 1), round(100 * (centre + half), 1)


def forward_return(closes: pd.Series, as_of, horizon_days: int) -> float | None:
    """Return from the last close on/before as_of to the last close on/before as_of + horizon. None if not observable."""
    end = pd.Timestamp(as_of) + timedelta(days=horizon_days)
    if closes.index[-1] < end:
        return None
    start_px = closes[:pd.Timestamp(as_of)]
    end_px = closes[:end]
    if start_px.empty:
        return None
    return float(end_px.iloc[-1] / start_px.iloc[-1] - 1.0)


def score_calls(calls: list[tuple[str, float]]) -> dict:
    """calls = [(signal, realised forward return)]. Neutral calls are excluded from the hit rate."""
    directional = [(s, r) for s, r in calls if s in ("bullish", "bearish")]
    hits = sum((s == "bullish" and r > 0) or (s == "bearish" and r < 0) for s, r in directional)
    base_up = sum(r > 0 for _, r in calls)
    return {"windows": len(calls), "directional_calls": len(directional), "hits": hits,
            "hit_rate_percent": round(100 * hits / len(directional), 1) if directional else None,
            "hit_rate_ci95": wilson_interval(hits, len(directional)),
            "base_rate_up_percent": round(100 * base_up / len(calls), 1) if calls else None}


def technical_signal(db, task_id) -> str | None:
    row = db.scalar(select(AgentResult).where(AgentResult.task_id == task_id, AgentResult.agent_name == "technical"))
    if row is None or row.status.value != "success":
        return None
    return (row.output_json or {}).get("data", {}).get("signal")
