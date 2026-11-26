"""Technical indicators + risk statistics (Milestone 2). Pure Python, no third-party maths library.

Every function returns a list the SAME LENGTH as its input, with `None` where there is not enough history yet, so the
results line up with the dates for charting. The tests check each one against an independent reference implementation.
"""
import math
from datetime import date

TRADING_DAYS = 252


def sma(values: list[float], n: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    if n < 1 or len(values) < n:
        return out
    window = sum(values[:n])
    out[n - 1] = window / n
    for i in range(n, len(values)):
        window += values[i] - values[i - n]
        out[i] = window / n
    return out


def ema(values: list[float], n: int) -> list[float | None]:
    """Exponential moving average, k = 2/(n+1), seeded with the SMA of the first n values (textbook convention)."""
    out: list[float | None] = [None] * len(values)
    if n < 1 or len(values) < n:
        return out
    k = 2 / (n + 1)
    prev = sum(values[:n]) / n
    out[n - 1] = prev
    for i in range(n, len(values)):
        prev = values[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def rsi(values: list[float], n: int = 14) -> list[float | None]:
    """Wilder's RSI: first averages are simple means of the first n changes, then Wilder smoothing."""
    out: list[float | None] = [None] * len(values)
    if len(values) <= n:
        return out
    gains = [max(values[i] - values[i - 1], 0.0) for i in range(1, len(values))]
    losses = [max(values[i - 1] - values[i], 0.0) for i in range(1, len(values))]
    avg_gain, avg_loss = sum(gains[:n]) / n, sum(losses[:n]) / n

    def value(g: float, l: float) -> float:
        if l == 0:
            return 100.0 if g > 0 else 50.0   # no losses: fully overbought; no movement at all: neutral
        return 100 - 100 / (1 + g / l)

    out[n] = value(avg_gain, avg_loss)
    for i in range(n + 1, len(values)):
        avg_gain = (avg_gain * (n - 1) + gains[i - 1]) / n
        avg_loss = (avg_loss * (n - 1) + losses[i - 1]) / n
        out[i] = value(avg_gain, avg_loss)
    return out


def macd(values: list[float], fast: int = 12, slow: int = 26, signal: int = 9):
    """Returns (macd_line, signal_line, histogram). macd = EMA(fast) - EMA(slow); signal = EMA(signal) of macd."""
    f, s = ema(values, fast), ema(values, slow)
    line = [(a - b) if a is not None and b is not None else None for a, b in zip(f, s)]
    sig: list[float | None] = [None] * len(values)
    first = next((i for i, v in enumerate(line) if v is not None), None)
    if first is not None:
        tail = [v for v in line[first:]]
        for j, v in enumerate(ema(tail, signal)):
            sig[first + j] = v
    hist = [(m - g) if m is not None and g is not None else None for m, g in zip(line, sig)]
    return line, sig, hist


def log_returns(values: list[float]) -> list[float]:
    return [math.log(b / a) for a, b in zip(values, values[1:]) if a > 0 and b > 0]


def annualised_volatility(values: list[float]) -> float | None:
    """Sample standard deviation of daily log returns x sqrt(252), as a fraction (0.25 = 25 %)."""
    r = log_returns(values)
    if len(r) < 2:
        return None
    mean = sum(r) / len(r)
    return math.sqrt(sum((x - mean) ** 2 for x in r) / (len(r) - 1)) * math.sqrt(TRADING_DAYS)


def max_drawdown(values: list[float], dates: list[date] | None = None) -> dict | None:
    """Largest peak-to-trough fall. Returns fraction (negative), peak/trough index (+dates) and whether it recovered."""
    if len(values) < 2:
        return None
    peak_i, worst, worst_peak_i, worst_trough_i = 0, 0.0, 0, 0
    for i, v in enumerate(values):
        if v > values[peak_i]:
            peak_i = i
        dd = v / values[peak_i] - 1
        if dd < worst:
            worst, worst_peak_i, worst_trough_i = dd, peak_i, i
    recovered = any(v >= values[worst_peak_i] for v in values[worst_trough_i:]) if worst < 0 else True
    out = {"max_drawdown": worst, "peak_index": worst_peak_i, "trough_index": worst_trough_i, "recovered": recovered}
    if dates:
        out["peak_date"], out["trough_date"] = dates[worst_peak_i].isoformat(), dates[worst_trough_i].isoformat()
    return out


def historical_var(values: list[float], confidence: float = 0.95) -> float | None:
    """1-day historical-simulation Value at Risk as a positive fraction of value (loss not exceeded `confidence` of days)."""
    r = sorted((b / a - 1) for a, b in zip(values, values[1:]) if a > 0)
    if len(r) < 20:
        return None
    idx = max(int(math.floor((1 - confidence) * len(r))) - 1, 0)
    return max(-r[idx], 0.0)


def last(series: list[float | None]) -> float | None:
    return next((v for v in reversed(series) if v is not None), None)


def percentile(sorted_values: list[float], q: float) -> float:
    """Linear-interpolated percentile (q in 0..1) of an ALREADY SORTED list (same as numpy's default)."""
    if not sorted_values:
        raise ValueError("empty")
    pos = (len(sorted_values) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (pos - lo)


def rolling_returns_pct(closes: list[float], window: int) -> list[float]:
    return [(closes[i + window] / closes[i] - 1) * 100 for i in range(len(closes) - window) if closes[i] > 0]
