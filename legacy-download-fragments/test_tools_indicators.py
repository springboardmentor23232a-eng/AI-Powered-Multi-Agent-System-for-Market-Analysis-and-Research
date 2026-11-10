import math

import numpy as np
import pandas as pd
import pytest

from app.tools import ema, macd, rsi, run_tool, sma

TOL = 1e-6


@pytest.fixture(scope="module")
def prices():
    rng = np.random.default_rng(42)
    return pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.015, 500))))


def assert_close(actual: pd.Series, expected: np.ndarray):
    mask = ~np.isnan(expected)
    assert not np.isnan(actual.to_numpy()[mask]).any()
    assert np.nanmax(np.abs(actual.to_numpy()[mask] - expected[mask])) < TOL


# ---- hand-computed values -------------------------------------------------
def test_sma_hand_values():
    out = sma([1, 2, 3, 4, 5], 3)
    assert out.isna().tolist() == [True, True, False, False, False]
    assert out.iloc[2:].tolist() == [2.0, 3.0, 4.0]


def test_ema_hand_values():
    # window 3: alpha 0.5, seed = mean(1,2,3) = 2
    out = ema([1, 2, 3, 4, 5], 3)
    assert out.iloc[2:].tolist() == [2.0, 3.0, 4.0]
    assert ema([5.0] * 10, 4).dropna().eq(5.0).all()


def test_rsi_hand_values():
    out = rsi([10, 11, 10, 12, 13], period=3)
    assert out.iloc[3] == pytest.approx(75.0, abs=1e-9)           # RS = (1)/(1/3) = 3
    assert out.iloc[4] == pytest.approx(100 - 100 / 5.5, abs=1e-9)  # RS = 1 / (2/9) = 4.5


def test_rsi_extremes():
    assert rsi(list(range(1, 30))).dropna().eq(100.0).all()
    assert rsi([5.0] * 30).dropna().eq(50.0).all()
    assert rsi(list(range(30, 1, -1))).dropna().eq(0.0).all()


def test_short_series_gives_nan_not_guesses():
    assert sma([1, 2], 5).isna().all()
    assert ema([1, 2], 5).isna().all()
    assert rsi([1, 2, 3], 14).isna().all()
    assert macd([1.0] * 10).isna().all().all()


def test_invalid_windows():
    with pytest.raises(ValueError):
        sma([1, 2, 3], 0)
    with pytest.raises(ValueError):
        macd([1.0] * 50, fast=26, slow=12)


def test_macd_identity(prices):
    m = macd(prices)
    both = m.dropna()
    assert (both["histogram"] - (both["macd"] - both["signal"])).abs().max() < 1e-12
    assert m["macd"].first_valid_index() == 25 and m["signal"].first_valid_index() == 33


# ---- independent reference: TA-Lib ----------------------------------------
talib = pytest.importorskip("talib")


def test_sma_matches_talib(prices):
    assert_close(sma(prices, 20), talib.SMA(prices.to_numpy(), 20))


def test_ema_matches_talib(prices):
    for w in (5, 12, 26, 50):
        assert_close(ema(prices, w), talib.EMA(prices.to_numpy(), w))


def test_rsi_matches_talib(prices):
    for p in (7, 14, 21):
        assert_close(rsi(prices, p), talib.RSI(prices.to_numpy(), p))


def test_macd_matches_talib(prices):
    t_macd, t_sig, t_hist = talib.MACD(prices.to_numpy(), 12, 26, 9)
    ours = macd(prices)
    sl = slice(33, None)  # first index where the signal line exists
    for name, ref in (("macd", t_macd), ("signal", t_sig), ("histogram", t_hist)):
        assert np.abs(ours[name].to_numpy()[sl] - ref[sl]).max() < TOL, name


def test_registry_scalarizes(prices):
    assert run_tool("rsi", {"values": prices.tolist(), "period": 14}) == pytest.approx(
        float(talib.RSI(prices.to_numpy(), 14)[-1]), abs=TOL)
    out = run_tool("macd", {"values": prices.tolist()})
    assert set(out) == {"macd", "signal", "histogram"} and all(math.isfinite(v) for v in out.values())
    with pytest.raises(KeyError):
        run_tool("nope", {})
