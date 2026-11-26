"""Milestone 2: every calculation is checked against an INDEPENDENT reference (hand-worked numbers, pandas, numpy)."""
import math
import random

import numpy as np
import pandas as pd
import pytest

from app.analysis import indicators as ind
from app.analysis import ratios as rt
from app.analysis.sentiment import classify
from app.analysis.technical_rules import detect_conditions, overall_bias


def series(n=300, seed=7):
    rng = random.Random(seed)
    out, p = [], 100.0
    for _ in range(n):
        p *= math.exp(rng.gauss(0.0004, 0.015))
        out.append(round(p, 4))
    return out


def close(a, b, tol=1e-9):
    assert len(a) == len(b)
    for x, y in zip(a, b):
        if y is None or (isinstance(y, float) and math.isnan(y)):
            assert x is None
        else:
            assert x == pytest.approx(y, abs=tol, rel=1e-9)


# ------------------------------------------------------------------ hand-worked examples
def test_sma_hand_computed():
    assert ind.sma([1, 2, 3, 4, 5], 3) == [None, None, 2, 3, 4]
    assert ind.sma([1, 2], 3) == [None, None]


def test_ema_hand_computed():
    # seed = SMA(first 3) = 2; alpha = 0.5 -> 0.5*4+0.5*2 = 3 ; 0.5*5+0.5*3 = 4
    assert ind.ema([1, 2, 3, 4, 5], 3) == [None, None, 2, 3, 4]


def test_rsi_extremes_and_flat():
    assert ind.rsi(list(range(1, 40)), 14)[-1] == 100.0                 # only gains
    assert ind.rsi(list(range(40, 1, -1)), 14)[-1] == pytest.approx(0.0)  # only losses
    assert ind.rsi([10.0] * 30, 14)[-1] == 50.0                          # no movement at all -> neutral


def test_rsi_hand_computed_first_value():
    v = [44, 45, 44, 46, 45, 47]            # n = 3 -> deltas +1 -1 +2 -1 +2
    # first averages over first 3 deltas: gain (1+0+2)/3 = 1, loss (0+1+0)/3 = 1/3 -> RS 3 -> RSI 75
    out = ind.rsi(v, 3)
    assert out[3] == pytest.approx(75.0)
    # Wilder smoothing next: gain = (1*2+0)/3 = 2/3 ; loss = (1/3*2+1)/3 = 5/9 -> RS 1.2 -> RSI 54.5454...
    assert out[4] == pytest.approx(100 - 100 / (1 + (2 / 3) / (5 / 9)))


def test_volatility_drawdown_var_hand_computed():
    assert ind.max_drawdown([100, 120, 90, 110])["max_drawdown"] == pytest.approx(-0.25)
    dd = ind.max_drawdown([100, 120, 90, 130])
    assert dd["recovered"] is True and (dd["peak_index"], dd["trough_index"]) == (1, 2)
    assert ind.max_drawdown([100, 120, 90, 110])["recovered"] is False
    # 100 daily returns: five of -5 %, ninety-five of +1 %  -> 95 % VaR = 5 %
    closes, p = [100.0], 100.0
    for r in [-0.05] * 5 + [0.01] * 95:
        p *= 1 + r
        closes.append(p)
    assert ind.historical_var(closes, 0.95) == pytest.approx(0.05)
    assert ind.annualised_volatility([100, 100, 100, 100]) == pytest.approx(0.0)
    assert ind.annualised_volatility([100]) is None


# ----------------------------------------------------------------------- pandas / numpy references
@pytest.mark.parametrize("n", [5, 20, 50])
def test_sma_matches_pandas(n):
    s = series()
    close(ind.sma(s, n), pd.Series(s).rolling(n).mean().tolist())


@pytest.mark.parametrize("n", [12, 26, 50])
def test_ema_matches_pandas(n):
    s = series()
    seed = pd.Series(s[n - 1:]).copy()
    seed.iloc[0] = sum(s[:n]) / n                          # SMA seed, then the standard recursion
    ref = [None] * (n - 1) + seed.ewm(span=n, adjust=False).mean().tolist()
    close(ind.ema(s, n), ref)


@pytest.mark.parametrize("n", [7, 14])
def test_rsi_matches_pandas(n):
    s = series()
    d = pd.Series(s).diff().dropna()
    gain, loss = d.clip(lower=0), (-d).clip(lower=0)
    def wilder(x):
        seed = x.iloc[n - 1:].copy().reset_index(drop=True)
        seed.iloc[0] = x.iloc[:n].mean()
        return seed.ewm(alpha=1 / n, adjust=False).mean().tolist()
    ag, al = wilder(gain), wilder(loss)
    ref = [None] * n + [100 - 100 / (1 + g / l) for g, l in zip(ag, al)]
    close(ind.rsi(s, n), ref, tol=1e-7)


def test_macd_matches_pandas():
    s = series()
    def ema_ref(vals, n):
        v = pd.Series(vals[n - 1:]).copy().reset_index(drop=True)
        v.iloc[0] = sum(vals[:n]) / n
        return [None] * (n - 1) + v.ewm(span=n, adjust=False).mean().tolist()
    f, sl = ema_ref(s, 12), ema_ref(s, 26)
    line = [a - b if a is not None and b is not None else None for a, b in zip(f, sl)]
    first = next(i for i, x in enumerate(line) if x is not None)
    sig = [None] * first + ema_ref([x for x in line[first:]], 9)
    hist = [a - b if a is not None and b is not None else None for a, b in zip(line, sig)]
    m, g, h = ind.macd(s)
    close(m, line, 1e-7); close(g, sig, 1e-7); close(h, hist, 1e-7)
    assert len(m) == len(s) and sum(x is None for x in m) == 25


def test_volatility_drawdown_percentile_match_numpy():
    s = series(500)
    logret = np.diff(np.log(np.array(s)))
    assert ind.annualised_volatility(s) == pytest.approx(logret.std(ddof=1) * math.sqrt(252), rel=1e-9)
    arr = pd.Series(s)
    assert ind.max_drawdown(s)["max_drawdown"] == pytest.approx((arr / arr.cummax() - 1).min(), rel=1e-9)
    rolling = ind.rolling_returns_pct(s, 21)
    assert rolling == pytest.approx([(s[i + 21] / s[i] - 1) * 100 for i in range(len(s) - 21)])
    for q in (0.05, 0.5, 0.95):
        assert ind.percentile(sorted(rolling), q) == pytest.approx(np.percentile(rolling, q * 100), rel=1e-9)


def test_indicator_lengths_always_match_input():
    s = series(60)
    for out in (ind.sma(s, 20), ind.ema(s, 12), ind.rsi(s, 14), *ind.macd(s)):
        assert len(out) == len(s)


# --------------------------------------------------------------------------- technical conditions
def test_conditions_rsi_and_trend_flags():
    up = [100 + i for i in range(260)]
    codes = {c["code"]: c for c in detect_conditions(up)}
    assert codes["price_vs_sma50"]["bias"] == "bullish" and codes["rsi_overbought"]["bias"] == "bearish"
    assert overall_bias(detect_conditions(up)) in ("upward", "mixed")
    down = [400 - i for i in range(260)]
    assert {c["code"]: c for c in detect_conditions(down)}["rsi_oversold"]["bias"] == "bullish"
    assert detect_conditions([]) == [] and overall_bias([]) == "mixed"


def test_crossover_detected_within_five_sessions():
    up = [100.0] * 60 + [100 + 3 * i for i in range(1, 5)]            # SMA20 crosses above SMA50 3 sessions before the end
    gc = [c for c in detect_conditions(up) if c["code"] == "golden_cross"]
    assert gc and gc[0]["bias"] == "bullish" and "3 session(s) ago" in gc[0]["text"]
    down = [100.0] * 60 + [100 - 3 * i for i in range(1, 5)]
    dc = [c for c in detect_conditions(down) if c["code"] == "death_cross"]
    assert dc and dc[0]["bias"] == "bearish"
    old = [100.0] * 60 + [100 + 3 * i for i in range(1, 12)]          # crossed too long ago -> not reported as a fresh cross
    assert not any(c["code"] == "golden_cross" for c in detect_conditions(old))


# ------------------------------------------------------------------------------------------ ratios
M = {"revenue": [100, 121], "gross_profit": [40, 50], "operating_income": [20, 30], "net_income": [10, 18],
     "total_assets": [200, 220], "total_debt": [50, 55], "equity": [100, 110], "operating_cash_flow": [15, 24],
     "free_cash_flow": [10, 12], "eps": [1.0, 1.8], "shares_outstanding": [10, 10]}


def test_ratios_hand_computed():
    r = rt.compute_ratios(M, price=45.0, price_is_reliable=True)
    v = {k: x["value"] for k, x in r.items()}
    assert v["revenue_growth_yoy"] == pytest.approx(0.21)
    assert v["revenue_cagr"] == pytest.approx(0.21)                      # 1 year
    assert v["net_income_growth_yoy"] == pytest.approx(0.8)
    assert v["gross_margin"] == pytest.approx(50 / 121) and v["net_margin"] == pytest.approx(18 / 121)
    assert v["operating_margin"] == pytest.approx(30 / 121)
    assert v["roe"] == pytest.approx(18 / 105)                           # average equity
    assert v["roa"] == pytest.approx(18 / 220) and v["debt_to_equity"] == pytest.approx(0.5)
    assert v["free_cash_flow_margin"] == pytest.approx(12 / 121) and v["cash_conversion"] == pytest.approx(24 / 18)
    assert v["pe"] == pytest.approx(25.0)                                # 45 / 1.8
    assert v["pb"] == pytest.approx(45 / 11.0)                           # equity/shares = 11
    assert r["net_margin"]["kind"] == "calculated" and "net income / revenue" in r["net_margin"]["formula"]


def test_ratios_never_invent_values():
    r = rt.compute_ratios({"revenue": [100, 0], "net_income": [5, -3], "equity": [-10, -20]}, price=50, price_is_reliable=True)
    assert r["revenue_growth_yoy"]["value"] == pytest.approx(-1.0)
    assert r["net_margin"]["value"] is None and r["net_margin"]["reason_unavailable"]       # zero revenue
    assert r["roe"]["value"] is None and r["debt_to_equity"]["value"] is None               # negative equity
    assert r["pe"]["value"] is None and r["pb"]["value"] is None
    assert rt.compute_ratios({}, None)["gross_margin"]["value"] is None


def test_valuation_needs_reliable_price():
    r = rt.compute_ratios(M, price=45.0, price_is_reliable=False)
    assert r["pe"]["value"] is None and r["pb"]["value"] is None and r["pe"]["reason_unavailable"]
    assert rt.compute_ratios({**M, "eps": [1, -2]}, 45.0, True)["pe"]["value"] is None        # negative EPS -> no P/E


def test_reported_values_are_marked_reported():
    r = rt.compute_ratios({"revenue": [1, 2], "reported_debt_to_equity": [0.9, 1.2], "reported_current_ratio": [1.5, 1.4]})
    assert r["debt_to_equity"]["kind"] == "reported" and r["debt_to_equity"]["value"] == 1.2
    assert r["current_ratio"]["kind"] == "reported" and r["current_ratio"]["value"] == 1.4


# ---------------------------------------------------------------------------------------- sentiment
@pytest.mark.parametrize("text,expected", [
    ("Company beats earnings estimates as profit surges", "Positive"),
    ("Shares plunge after company misses forecasts and cuts guidance", "Negative"),
    ("Company to hold annual general meeting on Tuesday", "Neutral"),
    ("Company is not profitable this year", "Negative"),            # negation flips a positive word
    ("Regulator did not fine the company", "Positive"),
])
def test_sentiment_classes(text, expected):
    assert classify(text)["sentiment"] == expected


def test_sentiment_events_uncertainty_and_determinism():
    c = classify("Acquisition talks: regulator may probe Q3 earnings")
    assert {"acquisition", "regulatory", "earnings"} <= set(c["events"]) and c["uncertain"] is True
    assert classify("Profit surges") == classify("Profit surges")
    assert -1 <= classify("a b c")["score"] <= 1
