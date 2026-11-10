"""Name -> function registry. The Verifier re-runs CALCULATED claims through `run_tool`."""
from typing import Any

import numpy as np
import pandas as pd

from app.tools import fundamentals as f
from app.tools import indicators as ind
from app.tools import risk as r

TOOLS = {
    "sma": ind.sma, "ema": ind.ema, "rsi": ind.rsi, "macd": ind.macd,
    "historical_volatility": r.historical_volatility, "max_drawdown": r.max_drawdown,
    "total_return": r.total_return,
    "growth_rate": f.growth_rate, "cagr": f.cagr, "margin": f.margin,
    "debt_to_equity": f.debt_to_equity, "roe": f.roe, "eps": f.eps,
    "book_value_per_share": f.book_value_per_share, "pe_ratio": f.pe_ratio, "pb_ratio": f.pb_ratio,
}


def _last(s: pd.Series) -> float | None:
    s = s.dropna()
    return float(s.iloc[-1]) if len(s) else None


def scalarize(result: Any) -> float | dict | None:
    """Latest value of a series, or a dict of latest values for MACD."""
    if isinstance(result, pd.DataFrame):
        return {c: _last(result[c]) for c in result.columns}
    if isinstance(result, pd.Series):
        return _last(result)
    if result is None:
        return None
    return float(result) if np.isfinite(result) else None


def run_tool(name: str, inputs: dict) -> float | dict | None:
    if name not in TOOLS:
        raise KeyError(f"Unknown tool: {name}")
    return scalarize(TOOLS[name](**inputs))
