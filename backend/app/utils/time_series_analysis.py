"""
Time Series Analysis (TSA) & Frequency Distribution Engine
Module 2:
- Moving Averages (SMA 20, SMA 50)
- Daily returns and percentage changes
- Daily and annualized rolling volatility
- Trend identification (Bullish / Bearish / Neutral)
- Return distribution histogram generation with frequency bins
"""

import math
from typing import Dict, Any, List
import pandas as pd
import numpy as np


def compute_time_series_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes moving averages, volatility metrics, trend direction,
    and returns frequency histogram from a cleaned OHLCV DataFrame.
    """
    if df is None or df.empty or len(df) < 2:
        return {
            "sma_20": None,
            "sma_50": None,
            "current_price": None,
            "volatility_daily_percent": 0.0,
            "volatility_annualized_percent": 0.0,
            "trend": "Neutral",
            "trend_signal": "Insufficient historical data for time series analysis",
            "trend_color": "neutral",
            "histogram": [],
            "price_series": []
        }

    close_series = df["Close"].astype(float)

    # 1. Moving Averages
    # Use min_periods=1 so shorter sets still provide initial averages
    sma_20_series = close_series.rolling(window=20, min_periods=1).mean()
    sma_50_series = close_series.rolling(window=50, min_periods=1).mean()

    # 2. Daily Returns (percentage)
    daily_returns = close_series.pct_change().dropna() * 100.0

    # 3. Volatility Metrics
    if len(daily_returns) > 1:
        daily_vol = float(daily_returns.std())
        annual_vol = float(daily_vol * math.sqrt(252))
    else:
        daily_vol = 0.0
        annual_vol = 0.0

    # Latest values
    latest_close = float(close_series.iloc[-1])
    latest_sma_20 = float(sma_20_series.iloc[-1])
    latest_sma_50 = float(sma_50_series.iloc[-1])

    # 4. Trend Identification
    if latest_close >= latest_sma_50 and latest_sma_20 >= latest_sma_50:
        trend = "Bullish"
        trend_signal = f"Price ({latest_close:.2f}) is above 50-day SMA ({latest_sma_50:.2f}) with upward momentum."
        trend_color = "bullish"
    elif latest_close < latest_sma_50 and latest_sma_20 < latest_sma_50:
        trend = "Bearish"
        trend_signal = f"Price ({latest_close:.2f}) is below 50-day SMA ({latest_sma_50:.2f}) indicating downward pressure."
        trend_color = "bearish"
    else:
        trend = "Consolidation"
        trend_signal = f"Price ({latest_close:.2f}) is trading near moving averages showing consolidation."
        trend_color = "neutral"

    # 5. Histogram of Daily Returns
    histogram_bins = []
    if len(daily_returns) >= 5:
        # Construct 10 bins between 5th percentile and 95th percentile (or min/max bounded)
        ret_min = max(float(daily_returns.min()), -8.0)
        ret_max = min(float(daily_returns.max()), 8.0)
        
        # Ensure spread
        if ret_max <= ret_min:
            ret_min -= 1.0
            ret_max += 1.0

        num_bins = 10
        bin_edges = np.linspace(ret_min, ret_max, num_bins + 1)
        
        counts, _ = np.histogram(daily_returns, bins=bin_edges)
        total_ret_count = max(len(daily_returns), 1)

        for i in range(num_bins):
            b_start = round(float(bin_edges[i]), 2)
            b_end = round(float(bin_edges[i + 1]), 2)
            c = int(counts[i])
            pct = round((c / total_ret_count) * 100.0, 1)
            
            is_positive = (b_start >= 0)
            is_negative = (b_end <= 0)
            is_neutral = (b_start < 0 and b_end > 0)
            
            histogram_bins.append({
                "bin_index": i,
                "label": f"{b_start:+.1f}% to {b_end:+.1f}%",
                "min_return": b_start,
                "max_return": b_end,
                "count": c,
                "frequency_percent": pct,
                "tone": "green" if is_positive else ("red" if is_negative else "slate")
            })

    # 6. Formatted Price Series for Front-End Charts (Sampled to max 120 points for smooth SVG rendering)
    step = max(1, len(df) // 120)
    sampled_df = df.iloc[::step] if len(df) > 120 else df

    price_series = []
    for idx, row in sampled_df.iterrows():
        date_str = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
        c_val = round(float(row.get("Close", 0)), 2)
        s20 = round(float(sma_20_series.loc[idx]), 2) if idx in sma_20_series.index else c_val
        s50 = round(float(sma_50_series.loc[idx]), 2) if idx in sma_50_series.index else c_val
        
        price_series.append({
            "date": date_str,
            "close": c_val,
            "sma_20": s20,
            "sma_50": s50,
            "volume": int(row.get("Volume", 0))
        })

    # Ensure last actual point is included
    if price_series and len(df) > 0 and price_series[-1]["date"] != df.index[-1].strftime("%Y-%m-%d"):
        last_idx = df.index[-1]
        price_series.append({
            "date": last_idx.strftime("%Y-%m-%d"),
            "close": round(float(df["Close"].iloc[-1]), 2),
            "sma_20": round(float(sma_20_series.iloc[-1]), 2),
            "sma_50": round(float(sma_50_series.iloc[-1]), 2),
            "volume": int(df["Volume"].iloc[-1])
        })

    return {
        "current_price": round(latest_close, 2),
        "sma_20": round(latest_sma_20, 2),
        "sma_50": round(latest_sma_50, 2),
        "volatility_daily_percent": round(daily_vol, 2),
        "volatility_annualized_percent": round(annual_vol, 2),
        "trend": trend,
        "trend_signal": trend_signal,
        "trend_color": trend_color,
        "histogram": histogram_bins,
        "price_series": price_series
    }
