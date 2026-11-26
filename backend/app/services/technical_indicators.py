from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


def compute_sma(series: pd.Series, window: int) -> pd.Series:
    """Simple Moving Average over `window` trading bars."""
    return series.rolling(window=window, min_periods=window).mean()


def compute_ema(series: pd.Series, span: int) -> pd.Series:
    """Exponential Moving Average over `span` trading bars."""
    return series.ewm(span=span, adjust=False, min_periods=span).mean()


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Wilder's Relative Strength Index (RSI) over `period` bars (default 14).
    First valid RSI appears at index `period` using SMA seed of initial gains/losses,
    followed by Wilder's exponential smoothing.
    """
    values = series.astype(float).values
    n = len(values)
    rsi = np.full(n, np.nan, dtype=float)
    if n <= period:
        return pd.Series(rsi, index=series.index)

    deltas = np.diff(values)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    avg_gain = float(np.mean(gains[:period]))
    avg_loss = float(np.mean(losses[:period]))

    if avg_loss == 0.0:
        rsi[period] = 50.0 if avg_gain == 0.0 else 100.0
    else:
        rs = avg_gain / avg_loss
        rsi[period] = 100.0 - (100.0 / (1.0 + rs))

    for i in range(period, len(deltas)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period
        if avg_loss == 0.0:
            rsi[i + 1] = 50.0 if avg_gain == 0.0 else 100.0
        else:
            rs = avg_gain / avg_loss
            rsi[i + 1] = 100.0 - (100.0 / (1.0 + rs))

    return pd.Series(rsi, index=series.index)


def compute_macd(
    series: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> pd.DataFrame:
    """
    Moving Average Convergence Divergence (MACD 12, 26, 9).
    Returns DataFrame with columns: macd, macd_signal, macd_histogram.
    """
    ema_fast = compute_ema(series.astype(float), fast_period)
    ema_slow = compute_ema(series.astype(float), slow_period)
    macd_line = ema_fast - ema_slow

    valid_macd = macd_line.dropna()
    signal_line = pd.Series(np.nan, index=series.index, dtype=float)
    if len(valid_macd) >= signal_period:
        computed_sig = valid_macd.ewm(span=signal_period, adjust=False, min_periods=signal_period).mean()
        signal_line.loc[computed_sig.index] = computed_sig

    histogram = macd_line - signal_line
    return pd.DataFrame(
        {
            "macd": macd_line,
            "macd_signal": signal_line,
            "macd_histogram": histogram,
        },
        index=series.index,
    )


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range (ATR-14) using Wilder's smoothing."""
    if df is None or len(df) < period + 1:
        return pd.Series(np.nan, index=df.index if df is not None else [])
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    prev_close = df["Close"].astype(float).shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def compute_volatility_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate daily return standard deviation, annualized historical volatility,
    20-day rolling volatility, max drawdown, and ATR-14.
    """
    if df is None or len(df) < 2:
        return {
            "daily_volatility_pct": None,
            "annualized_volatility_pct": None,
            "rolling_20d_volatility_pct": None,
            "max_drawdown_pct": None,
            "atr_14": None,
            "volatility_regime": "Insufficient Data",
        }

    close = df["Close"].astype(float)
    daily_returns = close.pct_change().dropna()
    if daily_returns.empty:
        return {
            "daily_volatility_pct": None,
            "annualized_volatility_pct": None,
            "rolling_20d_volatility_pct": None,
            "max_drawdown_pct": None,
            "atr_14": None,
            "volatility_regime": "Insufficient Data",
        }

    daily_std = float(daily_returns.std(ddof=1))
    annual_vol = daily_std * np.sqrt(252.0) * 100.0

    rolling_20 = daily_returns.rolling(20, min_periods=20).std(ddof=1) * np.sqrt(252.0) * 100.0
    latest_rolling_20 = (
        round(float(rolling_20.iloc[-1]), 2)
        if not rolling_20.empty and np.isfinite(rolling_20.iloc[-1])
        else None
    )

    cummax = close.cummax()
    drawdown = ((close / cummax) - 1.0) * 100.0
    max_dd = round(float(drawdown.min()), 2)

    atr_series = compute_atr(df, period=14)
    latest_atr = (
        round(float(atr_series.iloc[-1]), 2)
        if not atr_series.empty and np.isfinite(atr_series.iloc[-1])
        else None
    )

    if annual_vol < 20.0:
        regime = "Low"
    elif annual_vol <= 35.0:
        regime = "Moderate"
    else:
        regime = "High"

    return {
        "daily_volatility_pct": round(daily_std * 100.0, 2),
        "annualized_volatility_pct": round(annual_vol, 2),
        "rolling_20d_volatility_pct": latest_rolling_20,
        "max_drawdown_pct": max_dd,
        "atr_14": latest_atr,
        "volatility_regime": regime,
    }


def _opt_round(val: Any, digits: int = 2) -> Optional[float]:
    if val is None:
        return None
    try:
        f = float(val)
        return round(f, digits) if np.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def compute_indicator_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Attach SMA (20, 50, 200), EMA (12, 26, 50), RSI (14), MACD (12, 26, 9), and ATR (14)."""
    work = df.copy()
    close = work["Close"].astype(float)
    work["sma_20"] = compute_sma(close, 20)
    work["sma_50"] = compute_sma(close, 50)
    work["sma_200"] = compute_sma(close, 200)
    work["ema_12"] = compute_ema(close, 12)
    work["ema_26"] = compute_ema(close, 26)
    work["ema_50"] = compute_ema(close, 50)
    work["rsi_14"] = compute_rsi(close, 14)

    macd_df = compute_macd(close, 12, 26, 9)
    work["macd"] = macd_df["macd"]
    work["macd_signal"] = macd_df["macd_signal"]
    work["macd_histogram"] = macd_df["macd_histogram"]
    work["atr_14"] = compute_atr(work, 14)
    work["vol_sma_20"] = work["Volume"].astype(float).rolling(20, min_periods=5).mean()
    return work


def evaluate_technical_conditions(df_ind: pd.DataFrame) -> Dict[str, Any]:
    """
    Identify predefined technical conditions and classify overall historical trend
    into Upward Trend, Downward Trend, or Mixed Signals.
    """
    if df_ind is None or df_ind.empty:
        return {
            "overall_signal": "Unavailable",
            "bullish_count": 0,
            "bearish_count": 0,
            "neutral_count": 0,
            "conditions": [],
        }

    latest = df_ind.iloc[-1]
    prev = df_ind.iloc[-2] if len(df_ind) > 1 else latest
    close = _opt_round(latest["Close"], 2)
    sma20 = _opt_round(latest.get("sma_20"), 2)
    sma50 = _opt_round(latest.get("sma_50"), 2)
    sma200 = _opt_round(latest.get("sma_200"), 2)
    ema12 = _opt_round(latest.get("ema_12"), 2)
    ema26 = _opt_round(latest.get("ema_26"), 2)
    rsi14 = _opt_round(latest.get("rsi_14"), 2)
    macd = _opt_round(latest.get("macd"), 4)
    macd_sig = _opt_round(latest.get("macd_signal"), 4)
    vol = _opt_round(latest.get("Volume"), 0)
    vol_avg = _opt_round(latest.get("vol_sma_20"), 0)

    conditions: List[Dict[str, Any]] = []

    # 1. Price vs SMA-20
    if close is not None and sma20 is not None:
        above = close > sma20
        conditions.append({
            "id": "price_vs_sma20",
            "name": "Short-Term Trend (Price vs SMA-20)",
            "category": "Moving Average",
            "signal": "Bullish" if above else "Bearish",
            "triggered": True,
            "description": f"Close ({close}) is {'above' if above else 'below'} SMA-20 ({sma20}).",
        })

    # 2. Price vs SMA-50
    if close is not None and sma50 is not None:
        above = close > sma50
        conditions.append({
            "id": "price_vs_sma50",
            "name": "Medium-Term Trend (Price vs SMA-50)",
            "category": "Moving Average",
            "signal": "Bullish" if above else "Bearish",
            "triggered": True,
            "description": f"Close ({close}) is {'above' if above else 'below'} SMA-50 ({sma50}).",
        })

    # 3. Golden Cross / Death Cross (SMA-50 vs SMA-200)
    if sma50 is not None and sma200 is not None:
        golden = sma50 > sma200
        # Check if crossover occurred within last 5 bars
        recent_cross = False
        lookback = df_ind.tail(6)
        if len(lookback) >= 2 and lookback["sma_50"].notna().all() and lookback["sma_200"].notna().all():
            diff = lookback["sma_50"] - lookback["sma_200"]
            recent_cross = bool((diff.iloc[0] <= 0 < diff.iloc[-1]) or (diff.iloc[0] >= 0 > diff.iloc[-1]))

        label = "Golden Cross Alignment (SMA-50 > SMA-200)" if golden else "Death Cross Alignment (SMA-50 < SMA-200)"
        if recent_cross:
            label = "Recent Golden Cross" if golden else "Recent Death Cross"
        conditions.append({
            "id": "sma_50_200_cross",
            "name": label,
            "category": "Trend Crossover",
            "signal": "Bullish" if golden else "Bearish",
            "triggered": True,
            "description": f"SMA-50 ({sma50}) is {'above' if golden else 'below'} SMA-200 ({sma200}).",
        })

    # 4. EMA-12 vs EMA-26
    if ema12 is not None and ema26 is not None:
        bull_ema = ema12 > ema26
        conditions.append({
            "id": "ema_12_26",
            "name": "EMA Momentum (EMA-12 vs EMA-26)",
            "category": "Exponential Moving Average",
            "signal": "Bullish" if bull_ema else "Bearish",
            "triggered": True,
            "description": f"EMA-12 ({ema12}) is {'above' if bull_ema else 'below'} EMA-26 ({ema26}).",
        })

    # 5. RSI-14 Condition
    if rsi14 is not None:
        if rsi14 >= 70.0:
            sig = "Bearish"
            cond_name = "RSI Overbought (>= 70)"
            desc = f"RSI-14 at {rsi14} indicates overbought historical momentum."
        elif rsi14 <= 30.0:
            sig = "Bullish"
            cond_name = "RSI Oversold (<= 30)"
            desc = f"RSI-14 at {rsi14} indicates oversold territory."
        elif rsi14 >= 55.0:
            sig = "Bullish"
            cond_name = "RSI Bullish Zone (55–70)"
            desc = f"RSI-14 at {rsi14} reflects positive momentum without overbought extremes."
        elif rsi14 <= 45.0:
            sig = "Bearish"
            cond_name = "RSI Weak Zone (30–45)"
            desc = f"RSI-14 at {rsi14} reflects subdued / downward momentum."
        else:
            sig = "Neutral"
            cond_name = "RSI Neutral Zone (45–55)"
            desc = f"RSI-14 at {rsi14} sits in neutral balance."
        conditions.append({
            "id": "rsi_14_state",
            "name": cond_name,
            "category": "Momentum Oscillator",
            "signal": sig,
            "triggered": True,
            "description": desc,
        })

    # 6. MACD Signal Crossover
    if macd is not None and macd_sig is not None:
        prev_macd = _opt_round(prev.get("macd"), 4)
        prev_sig = _opt_round(prev.get("macd_signal"), 4)
        bullish_cross = (
            prev_macd is not None and prev_sig is not None
            and prev_macd <= prev_sig and macd > macd_sig
        )
        bearish_cross = (
            prev_macd is not None and prev_sig is not None
            and prev_macd >= prev_sig and macd < macd_sig
        )
        above_sig = macd > macd_sig
        if bullish_cross:
            c_name = "MACD Bullish Crossover"
        elif bearish_cross:
            c_name = "MACD Bearish Crossover"
        else:
            c_name = "MACD Above Signal Line" if above_sig else "MACD Below Signal Line"
        conditions.append({
            "id": "macd_signal",
            "name": c_name,
            "category": "MACD",
            "signal": "Bullish" if above_sig else "Bearish",
            "triggered": True,
            "description": f"MACD ({macd}) is {'above' if above_sig else 'below'} Signal ({macd_sig}).",
        })

    # 7. Volume Surge Check
    if vol is not None and vol_avg is not None and vol_avg > 0:
        ratio = round(vol / vol_avg, 2)
        if ratio >= 1.5:
            conditions.append({
                "id": "volume_spike",
                "name": f"Volume Surge ({ratio}x 20-Day Avg)",
                "category": "Volume",
                "signal": "Neutral",
                "triggered": True,
                "description": f"Latest volume ({int(vol):,}) is {ratio}x the 20-day average ({int(vol_avg):,}).",
            })

    bullish_count = sum(1 for c in conditions if c["signal"] == "Bullish")
    bearish_count = sum(1 for c in conditions if c["signal"] == "Bearish")
    neutral_count = sum(1 for c in conditions if c["signal"] == "Neutral")

    total_directional = bullish_count + bearish_count
    if total_directional == 0:
        overall = "Mixed Signals"
    elif bullish_count >= bearish_count + 2 and bullish_count / total_directional >= 0.65:
        overall = "Upward Trend"
    elif bearish_count >= bullish_count + 2 and bearish_count / total_directional >= 0.65:
        overall = "Downward Trend"
    else:
        overall = "Mixed Signals"

    return {
        "overall_signal": overall,
        "bullish_count": bullish_count,
        "bearish_count": bearish_count,
        "neutral_count": neutral_count,
        "conditions": conditions,
    }

