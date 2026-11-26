from unittest.mock import patch
import numpy as np
import pandas as pd
import pytest

from app.services.agents.technical_agent import TECHNICAL_DISCLAIMER, TechnicalAnalysisAgent
from app.services.technical_indicators import (
    compute_ema,
    compute_macd,
    compute_rsi,
    compute_sma,
    compute_volatility_metrics,
)


def _get_auth_headers(client, email="tech_user@example.com"):
    client.post("/api/auth/register", json={
        "full_name": "Tech Tester",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!",
    })
    res = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_independent_reference_technical_indicators():
    # 1. SMA & EMA independent reference check
    prices = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0])
    sma3 = compute_sma(prices, 3)
    assert pd.isna(sma3.iloc[1])
    assert pytest.approx(sma3.iloc[2], rel=1e-6) == 11.0
    assert pytest.approx(sma3.iloc[6], rel=1e-6) == 15.0

    # EMA manual reference: alpha = 2/(3+1) = 0.5, ewm(span=3, adjust=False)
    ema3 = compute_ema(prices, 3)
    manual = prices.iloc[0]
    alpha = 2.0 / (3.0 + 1.0)
    for idx in range(1, len(prices)):
        manual = alpha * prices.iloc[idx] + (1.0 - alpha) * manual
    assert pytest.approx(ema3.iloc[-1], rel=1e-6) == manual

    # 2. Wilder's RSI-14 reference check: monotonically increasing series -> RSI = 100.0
    up_series = pd.Series([float(100 + i) for i in range(25)])
    rsi_up = compute_rsi(up_series, 14)
    assert pd.isna(rsi_up.iloc[13])
    assert rsi_up.iloc[14] == 100.0
    assert rsi_up.iloc[-1] == 100.0

    # Mixed series manual Wilder RSI verification
    mixed = pd.Series([44.0, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08,
                       45.89, 46.03, 45.61, 46.28, 46.28, 46.00, 46.03, 46.41, 46.22, 45.64])
    rsi_mixed = compute_rsi(mixed, 14)
    # First seed at index 14: manual calculation
    deltas = np.diff(mixed.values[:15])
    avg_g = np.mean(np.where(deltas > 0, deltas, 0.0))
    avg_l = np.mean(np.where(deltas < 0, -deltas, 0.0))
    expected_seed = 100.0 - (100.0 / (1.0 + (avg_g / avg_l)))
    assert pytest.approx(rsi_mixed.iloc[14], rel=1e-6) == expected_seed

    # 3. MACD(12, 26, 9) reference check
    long_series = pd.Series([100.0 + i * 0.5 + np.sin(i / 3.0) for i in range(60)])
    macd_df = compute_macd(long_series, 12, 26, 9)
    expected_macd = compute_ema(long_series, 12) - compute_ema(long_series, 26)
    assert pytest.approx(macd_df["macd"].iloc[-1], rel=1e-6) == expected_macd.iloc[-1]
    assert pytest.approx(macd_df["macd_histogram"].iloc[-1], rel=1e-6) == (
        macd_df["macd"].iloc[-1] - macd_df["macd_signal"].iloc[-1]
    )

    # 4. Volatility reference check
    dates = pd.date_range("2025-01-01", periods=30, freq="B")
    ohlcv = pd.DataFrame({
        "Open": long_series.iloc[:30].values,
        "High": long_series.iloc[:30].values + 1.0,
        "Low": long_series.iloc[:30].values - 1.0,
        "Close": long_series.iloc[:30].values,
        "Volume": [100_000] * 30,
    }, index=dates)
    vol = compute_volatility_metrics(ohlcv)
    ret = ohlcv["Close"].pct_change().dropna()
    expected_ann_vol = float(ret.std(ddof=1) * np.sqrt(252.0) * 100.0)
    assert pytest.approx(vol["annualized_volatility_pct"], abs=0.02) == expected_ann_vol


@pytest.mark.asyncio
async def test_technical_agent_uptrend_and_downtrend_classification():
    dates = pd.date_range("2025-01-01", periods=240, freq="B")

    # Strong Uptrend series
    close_up = np.linspace(100.0, 220.0, 240)
    df_up = pd.DataFrame({
        "Open": close_up - 0.5,
        "High": close_up + 1.0,
        "Low": close_up - 1.0,
        "Close": close_up,
        "Volume": [500_000] * 240,
    }, index=dates)

    agent = TechnicalAnalysisAgent()
    res_up = await agent.analyze(
        "UPCO",
        "NASDAQ",
        "1 Year",
        {"profile": {"currency": "USD"}, "ohlcv_df_full": df_up, "ohlcv_df_period": df_up},
    )
    assert res_up["trend_summary"]["overall_signal"] == "Upward Trend"
    assert res_up["latest_indicators"]["sma_200"] is not None
    assert len(res_up["chart_series"]) == 240
    assert res_up["disclaimer"] == TECHNICAL_DISCLAIMER

    # Strong Downtrend series
    close_down = np.linspace(220.0, 100.0, 240)
    df_down = pd.DataFrame({
        "Open": close_down + 0.5,
        "High": close_down + 1.0,
        "Low": close_down - 1.0,
        "Close": close_down,
        "Volume": [500_000] * 240,
    }, index=dates)

    res_down = await agent.analyze(
        "DNCO",
        "NASDAQ",
        "1 Year",
        {"profile": {"currency": "USD"}, "ohlcv_df_full": df_down, "ohlcv_df_period": df_down},
    )
    assert res_down["trend_summary"]["overall_signal"] == "Downward Trend"
    assert res_down["trend_summary"]["period_return_pct"] < 0


def test_technical_endpoint(client):
    headers = _get_auth_headers(client, "tech_ep@example.com")
    dates = pd.date_range("2026-01-01", periods=45, freq="B")
    close = np.linspace(100.0, 140.0, 45)
    df = pd.DataFrame({
        "Open": close - 0.5,
        "High": close + 1.0,
        "Low": close - 1.0,
        "Close": close,
        "Volume": [200_000] * 45,
    }, index=dates)

    fake_md = {
        "ticker": "NVDA",
        "market": "NASDAQ",
        "yf_symbol": "NVDA",
        "profile": {"ticker": "NVDA", "company_name": "NVIDIA Corporation", "currency": "USD"},
        "data_quality": {"total_raw_rows": 45, "valid_rows": 45, "quality_status": "VALID", "validated_at": "2026-11-26T10:00:00Z"},
        "sources": [],
        "ohlcv_df_full": df,
        "ohlcv_df_period": df,
    }
    with patch("app.routers.stocks.MarketDataCollector.collect_market_data", return_value=fake_md):
        res = client.get("/api/stocks/NVDA/technical?market=NASDAQ&period=3%20Months", headers=headers)
        assert res.status_code == 200
        ta = res.json()["technical_analysis"]
        assert ta["status"] == "COMPLETED"
        assert len(ta["chart_series"]) == 45
        assert ta["latest_indicators"]["sma_20"] is not None
        assert ta["latest_indicators"]["rsi_14"] is not None

