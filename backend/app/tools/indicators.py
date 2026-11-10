"""Technical indicators. Pure functions, no I/O, no LLM.

Conventions (match TA-Lib / TradingView defaults):
- SMA: simple rolling mean; first value at index window-1.
- EMA: alpha = 2/(window+1); seeded with the SMA of the first `window` values.
- RSI: Wilder smoothing; seeded with the simple mean of the first `period` changes.
- MACD: EMA(fast) - EMA(slow); signal = EMA of the MACD line (SMA-seeded); histogram = MACD - signal.
  As in TA-Lib, the fast EMA is seeded from the `fast` bars ending where the slow EMA starts, so both
  lines begin at index slow-1 and agree exactly with TA-Lib.
Series shorter than the warm-up period yield NaN for the missing positions, never guesses.
"""
import numpy as np
import pandas as pd

from app.tools._common import as_series, check_window


def sma(values, window: int) -> pd.Series:
    check_window(window)
    return as_series(values).rolling(window=window, min_periods=window).mean()


def ema(values, window: int) -> pd.Series:
    check_window(window)
    s = as_series(values)
    out = pd.Series(np.nan, index=s.index, dtype=float)
    if len(s) < window:
        return out
    alpha = 2.0 / (window + 1)
    prev = float(s.iloc[:window].mean())
    out.iloc[window - 1] = prev
    for i in range(window, len(s)):
        prev = alpha * float(s.iloc[i]) + (1 - alpha) * prev
        out.iloc[i] = prev
    return out


def _rsi_value(avg_gain: float, avg_loss: float) -> float:
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    return 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)


def rsi(values, period: int = 14) -> pd.Series:
    check_window(period)
    s = as_series(values)
    out = pd.Series(np.nan, index=s.index, dtype=float)
    if len(s) <= period:
        return out
    delta = s.diff().to_numpy()
    gains = np.where(delta > 0, delta, 0.0)
    losses = np.where(delta < 0, -delta, 0.0)
    avg_gain = gains[1 : period + 1].mean()
    avg_loss = losses[1 : period + 1].mean()
    out.iloc[period] = _rsi_value(avg_gain, avg_loss)
    for i in range(period + 1, len(s)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        out.iloc[i] = _rsi_value(avg_gain, avg_loss)
    return out


def macd(values, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    check_window(fast), check_window(slow), check_window(signal)
    if fast >= slow:
        raise ValueError("fast window must be smaller than slow window")
    s = as_series(values)
    fast_ema = ema(s.iloc[slow - fast :], fast).reindex(s.index)
    line = fast_ema - ema(s, slow)
    sig = ema(line.dropna(), signal).reindex(s.index)
    return pd.DataFrame({"macd": line, "signal": sig, "histogram": line - sig})
