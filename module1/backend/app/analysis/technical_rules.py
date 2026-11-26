"""Predefined technical conditions (Milestone 2) - rule-based, descriptive of HISTORY only, never a prediction."""
from .indicators import ema, macd, rsi, sma


def detect_conditions(closes: list[float]) -> list[dict]:
    """Predefined technical conditions. Descriptive of HISTORY only - never a prediction."""
    out: list[dict] = []
    if not closes:
        return out
    price = closes[-1]
    s20, s50, s200 = sma(closes, 20), sma(closes, 50), sma(closes, 200)
    e12, e26 = ema(closes, 12), ema(closes, 26)
    r = rsi(closes, 14)
    m, sg, _ = macd(closes)

    def add(code, bias, text):
        out.append({"code": code, "bias": bias, "text": text})

    if s50[-1] is not None:
        add("price_vs_sma50", "bullish" if price > s50[-1] else "bearish",
            f"Price is {'above' if price > s50[-1] else 'below'} its 50-day SMA ({s50[-1]:.2f}).")
    if s20[-1] is not None and s50[-1] is not None:
        add("sma20_vs_sma50", "bullish" if s20[-1] > s50[-1] else "bearish",
            f"20-day SMA is {'above' if s20[-1] > s50[-1] else 'below'} the 50-day SMA.")
    # crossovers within the last 5 sessions (k = 1 is the latest session)
    for name, fast, slow in (("SMA 20/50", s20, s50), ("SMA 50/200", s50, s200)):
        for k in range(1, 6):
            if len(fast) > k and None not in (fast[-k], slow[-k], fast[-k - 1], slow[-k - 1]):
                when = "on the latest session" if k == 1 else f"{k - 1} session(s) ago"
                if fast[-k - 1] <= slow[-k - 1] and fast[-k] > slow[-k]:
                    add("golden_cross", "bullish", f"{name} bullish crossover {when}.")
                    break
                if fast[-k - 1] >= slow[-k - 1] and fast[-k] < slow[-k]:
                    add("death_cross", "bearish", f"{name} bearish crossover {when}.")
                    break
    if r[-1] is not None:
        if r[-1] >= 70:
            add("rsi_overbought", "bearish", f"RSI(14) is {r[-1]:.1f} (>= 70, overbought zone).")
        elif r[-1] <= 30:
            add("rsi_oversold", "bullish", f"RSI(14) is {r[-1]:.1f} (<= 30, oversold zone).")
        else:
            add("rsi_neutral", "neutral", f"RSI(14) is {r[-1]:.1f} (between 30 and 70).")
    if m[-1] is not None and sg[-1] is not None:
        add("macd_vs_signal", "bullish" if m[-1] > sg[-1] else "bearish",
            f"MACD line is {'above' if m[-1] > sg[-1] else 'below'} its signal line.")
    if e12[-1] is not None and e26[-1] is not None:
        add("ema12_vs_ema26", "bullish" if e12[-1] > e26[-1] else "bearish",
            f"12-day EMA is {'above' if e12[-1] > e26[-1] else 'below'} the 26-day EMA.")
    return out


def overall_bias(conditions: list[dict]) -> str:
    """'upward' / 'downward' / 'mixed' from the count of bullish vs bearish conditions (>= 2/3 agreement needed)."""
    b = sum(1 for c in conditions if c["bias"] == "bullish")
    s = sum(1 for c in conditions if c["bias"] == "bearish")
    total = b + s
    if total == 0:
        return "mixed"
    if b / total >= 2 / 3:
        return "upward"
    if s / total >= 2 / 3:
        return "downward"
    return "mixed"
