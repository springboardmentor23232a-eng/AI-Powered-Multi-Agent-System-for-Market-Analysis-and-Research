"""Independent reference calculations for the evaluation harness.

Deliberately written with plain Python lists and `math` only (no pandas, numpy or app.tools) so that agreement
with app.tools is evidence of correctness rather than a shared bug. Conventions follow TA-Lib.
"""
import math


def _mean(xs):
    return sum(xs) / len(xs)


def ema_series(values, window):
    """SMA-seeded EMA; entries before index window-1 are None."""
    out = [None] * len(values)
    if len(values) < window:
        return out
    k = 2.0 / (window + 1)
    prev = _mean(values[:window])
    out[window - 1] = prev
    for i in range(window, len(values)):
        prev = values[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def ref_sma(values, window):
    return _mean(values[-window:]) if len(values) >= window else None


def ref_ema(values, window):
    return ema_series(values, window)[-1]


def ref_rsi(values, period=14):
    if len(values) <= period:
        return None
    ch = [values[i] - values[i - 1] for i in range(1, len(values))]
    gain = [max(c, 0.0) for c in ch]
    loss = [max(-c, 0.0) for c in ch]
    ag, al = _mean(gain[:period]), _mean(loss[:period])
    for i in range(period, len(ch)):
        ag = (ag * (period - 1) + gain[i]) / period
        al = (al * (period - 1) + loss[i]) / period
    if al == 0:
        return 100.0 if ag > 0 else 50.0
    return 100.0 - 100.0 / (1.0 + ag / al)


def ref_macd(values, fast=12, slow=26, signal=9):
    if len(values) < slow + signal - 1:
        return {"macd": None, "signal": None, "histogram": None} if len(values) < slow else \
            {"macd": ema_series(values[slow - fast:], fast)[-1] - ema_series(values, slow)[-1],
             "signal": None, "histogram": None}
    slow_e = ema_series(values, slow)
    fast_e = [None] * (slow - fast) + ema_series(values[slow - fast:], fast)  # TA-Lib seeding of the fast EMA
    line = [f - s for f, s in zip(fast_e[slow - 1:], slow_e[slow - 1:])]
    sig = ema_series(line, signal)[-1]
    return {"macd": line[-1], "signal": sig, "histogram": line[-1] - sig}


def ref_volatility(values, trading_days=252):
    if len(values) < 3 or min(values) <= 0:
        return None
    r = [math.log(values[i] / values[i - 1]) for i in range(1, len(values))]
    m = _mean(r)
    var = sum((x - m) ** 2 for x in r) / (len(r) - 1)
    return math.sqrt(var) * math.sqrt(trading_days)


def ref_max_drawdown(values):
    if len(values) < 2 or min(values) <= 0:
        return None
    peak, worst = values[0], 0.0
    for v in values:
        peak = max(peak, v)
        worst = min(worst, v / peak - 1.0)
    return worst


def ref_total_return(values):
    return values[-1] / values[0] - 1.0 if len(values) >= 2 and values[0] > 0 else None


def _ok(*xs):
    return all(x is not None and math.isfinite(x) for x in xs)


def reference_value(function: str, inputs: dict):
    """Recompute a CALCULATED claim from its stored inputs. Raises KeyError for unknown functions."""
    i = inputs
    if function == "sma":
        return ref_sma(i["values"], i["window"])
    if function == "ema":
        return ref_ema(i["values"], i["window"])
    if function == "rsi":
        return ref_rsi(i["values"], i.get("period", 14))
    if function == "macd":
        return ref_macd(i["values"], i.get("fast", 12), i.get("slow", 26), i.get("signal", 9))
    if function == "historical_volatility":
        return ref_volatility(i["values"])
    if function == "max_drawdown":
        return ref_max_drawdown(i["values"])
    if function == "total_return":
        return ref_total_return(i["values"])
    if function == "growth_rate":
        c, p = i["current"], i["previous"]
        return (c - p) / p if _ok(c, p) and p > 0 else None
    if function == "cagr":
        b, e, y = i["begin"], i["end"], i["years"]
        return (e / b) ** (1 / y) - 1 if _ok(b, e, y) and b > 0 and e > 0 and y > 0 else None
    if function == "margin":
        n, r = i["numerator"], i["revenue"]
        return n / r if _ok(n, r) and r > 0 else None
    if function == "debt_to_equity":
        d, e = i["total_debt"], i["total_equity"]
        return d / e if _ok(d, e) and e > 0 else None
    if function == "roe":
        n, e, b = i["net_income"], i["equity_end"], i.get("equity_begin")
        if b is not None:
            return n / ((e + b) / 2) if _ok(n, e, b) and (e + b) > 0 else None
        return n / e if _ok(n, e) and e > 0 else None
    if function == "eps":
        n, s = i["net_income"], i["shares"]
        return n / s if _ok(n, s) and s > 0 else None
    if function == "book_value_per_share":
        e, s = i["total_equity"], i["shares"]
        return e / s if _ok(e, s) and s > 0 else None
    if function == "pe_ratio":
        p, e = i["price"], i["earnings_per_share"]
        return p / e if _ok(p, e) and e > 0 else None
    if function == "pb_ratio":
        p, b = i["price"], i["book_value_ps"]
        return p / b if _ok(p, b) and b > 0 else None
    raise KeyError(function)
