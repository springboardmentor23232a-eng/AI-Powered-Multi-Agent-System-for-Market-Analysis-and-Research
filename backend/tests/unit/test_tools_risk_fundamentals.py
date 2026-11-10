import math

import numpy as np
import pytest

from app.tools import (book_value_per_share, cagr, debt_to_equity, eps, growth_rate, historical_volatility,
                       margin, max_drawdown, pb_ratio, pe_ratio, roe, run_tool, total_return)

TOL = 1e-9


def test_max_drawdown_hand_value():
    # peak 120 -> trough 80 = -33.33%; later 130 is a new high
    assert max_drawdown([100, 120, 90, 110, 80, 130]) == pytest.approx(-1 / 3, abs=TOL)
    assert max_drawdown([1, 2, 3, 4]) == 0.0
    assert max_drawdown([5]) is None and max_drawdown([1, 0, 2]) is None


def test_volatility_reference():
    rng = np.random.default_rng(7)
    p = list(100 * np.exp(np.cumsum(rng.normal(0, 0.01, 300))))
    # independent pure-python reference
    r = [math.log(p[i] / p[i - 1]) for i in range(1, len(p))]
    mean = sum(r) / len(r)
    var = sum((x - mean) ** 2 for x in r) / (len(r) - 1)
    assert historical_volatility(p) == pytest.approx(math.sqrt(var) * math.sqrt(252), abs=1e-12)
    assert historical_volatility([100.0] * 50) == pytest.approx(0.0, abs=1e-12)
    assert historical_volatility([1, 2]) is None


def test_total_return():
    assert total_return([100, 150]) == pytest.approx(0.5)
    assert total_return([0, 10]) is None


def test_growth_and_cagr():
    assert growth_rate(110, 100) == pytest.approx(0.10)
    assert growth_rate(90, 100) == pytest.approx(-0.10)
    assert growth_rate(10, 0) is None and growth_rate(10, -5) is None and growth_rate(None, 5) is None
    assert cagr(100, 121, 2) == pytest.approx(0.10)
    assert cagr(100, 50, 0) is None and cagr(-1, 5, 2) is None


def test_margins_and_leverage():
    assert margin(20, 100) == pytest.approx(0.20)
    assert margin(20, 0) is None
    assert debt_to_equity(30, 80) == pytest.approx(0.375)
    assert debt_to_equity(30, 0) is None and debt_to_equity(30, -10) is None


def test_roe_end_and_average_equity():
    assert roe(15, 80) == pytest.approx(15 / 80)
    assert roe(15, 80, 70) == pytest.approx(15 / 75)
    assert roe(15, -80) is None and roe(None, 80) is None


def test_valuation_ratios():
    e = eps(15e9, 5e9)
    b = book_value_per_share(80e9, 5e9)
    assert e == pytest.approx(3.0) and b == pytest.approx(16.0)
    assert pe_ratio(60, e) == pytest.approx(20.0)
    assert pb_ratio(60, b) == pytest.approx(3.75)
    assert pe_ratio(60, -2.0) is None      # negative earnings: P/E is not meaningful
    assert pb_ratio(60, -1.0) is None
    assert eps(10, 0) is None and pe_ratio(float("nan"), 3) is None


def test_registry_for_ratio_claims():
    assert run_tool("roe", {"net_income": 15, "equity_end": 80}) == pytest.approx(0.1875)
    assert run_tool("max_drawdown", {"values": [100, 50, 75]}) == pytest.approx(-0.5)
    assert run_tool("pe_ratio", {"price": 60, "earnings_per_share": -1}) is None
