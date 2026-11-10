"""Risk metrics. Pure functions."""
import numpy as np
import pandas as pd

from app.tools._common import TRADING_DAYS, as_series


def historical_volatility(values, trading_days: int = TRADING_DAYS) -> float | None:
    """Annualised sample standard deviation (ddof=1) of daily log returns."""
    s = as_series(values)
    if len(s) < 3 or (s <= 0).any():
        return None
    returns = np.log(s).diff().dropna()
    return float(returns.std(ddof=1) * np.sqrt(trading_days))


def drawdown_series(values) -> pd.Series:
    s = as_series(values)
    return s / s.cummax() - 1.0


def max_drawdown(values) -> float | None:
    """Largest peak-to-trough decline as a negative fraction (e.g. -0.25 = -25%)."""
    s = as_series(values)
    if len(s) < 2 or (s <= 0).any():
        return None
    return float(drawdown_series(s).min())


def total_return(values) -> float | None:
    s = as_series(values)
    if len(s) < 2 or s.iloc[0] <= 0:
        return None
    return float(s.iloc[-1] / s.iloc[0] - 1.0)
