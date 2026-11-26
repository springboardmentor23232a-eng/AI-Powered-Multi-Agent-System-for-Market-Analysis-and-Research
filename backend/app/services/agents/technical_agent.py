from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from app.services.agents.base import BaseResearchAgent
from app.services.market_data_service import PERIOD_TO_DAYS
from app.services.technical_indicators import (
    _opt_round,
    compute_indicator_dataframe,
    compute_volatility_metrics,
    evaluate_technical_conditions,
)

TECHNICAL_DISCLAIMER = (
    "Technical indicators describe historical market conditions and should not be "
    "treated as guaranteed predictions or investment advice."
)


class TechnicalAnalysisAgent(BaseResearchAgent):
    """
    Module 4 Agent: Analyzes historical OHLCV price trends, moving averages (SMA/EMA),
    momentum oscillators (RSI, MACD), historical volatility, predefined technical
    conditions, and generates chart-ready time series.
    """

    @property
    def agent_name(self) -> str:
        return "technical_analysis_agent"

    async def analyze(
        self,
        ticker: str,
        market: str,
        period: str,
        market_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        analyzed_at = datetime.now(timezone.utc).isoformat()
        profile = market_data.get("profile") or {}
        currency = profile.get("currency") or ("INR" if market in ["NSE", "BSE"] else "USD")

        df_full: pd.DataFrame = market_data.get("ohlcv_df_full")
        df_period: pd.DataFrame = market_data.get("ohlcv_df_period")

        # Fallback: construct DataFrame from ohlcv bar list if raw DataFrame not passed
        if (df_full is None or df_full.empty) and market_data.get("ohlcv"):
            bars = market_data["ohlcv"]
            df_full = pd.DataFrame(bars)
            df_full["date"] = pd.to_datetime(df_full["date"])
            df_full = df_full.set_index("date").rename(
                columns={
                    "open": "Open",
                    "high": "High",
                    "low": "Low",
                    "close": "Close",
                    "volume": "Volume",
                }
            )
            df_period = df_full

        if df_full is None or df_full.empty:
            return {
                "agent_name": self.agent_name,
                "analyzed_at": analyzed_at,
                "ticker": ticker,
                "market": market,
                "period": period,
                "currency": currency,
                "status": "INSUFFICIENT_DATA",
                "trend_summary": {
                    "overall_signal": "Unavailable",
                    "period_return_pct": None,
                },
                "latest_indicators": {},
                "volatility": compute_volatility_metrics(df_full),
                "technical_conditions": [],
                "chart_series": [],
                "data_limitations": ["No validated historical OHLCV data available for technical analysis."],
                "explanation": "Technical analysis could not be performed because no historical OHLCV bars were available.",
                "disclaimer": TECHNICAL_DISCLAIMER,
            }

        # Compute indicators over full warmup window, then slice to requested period for charts & period stats
        df_ind_full = compute_indicator_dataframe(df_full)
        if df_period is not None and not df_period.empty:
            start_dt = df_period.index.min()
            df_ind_period = df_ind_full[df_ind_full.index >= start_dt].copy()
        else:
            days = PERIOD_TO_DAYS.get(period, 365)
            cutoff = df_ind_full.index.max() - timedelta(days=days)
            df_ind_period = df_ind_full[df_ind_full.index >= cutoff].copy()
            if df_ind_period.empty:
                df_ind_period = df_ind_full.copy()

        latest = df_ind_period.iloc[-1]
        first = df_ind_period.iloc[0]

        start_close = float(first["Close"])
        end_close = float(latest["Close"])
        period_return_pct = round(((end_close - start_close) / start_close) * 100.0, 2) if start_close > 0 else 0.0
        period_high = round(float(df_ind_period["High"].max()), 2)
        period_low = round(float(df_ind_period["Low"].min()), 2)

        sma_20 = _opt_round(latest.get("sma_20"), 2)
        sma_50 = _opt_round(latest.get("sma_50"), 2)
        sma_200 = _opt_round(latest.get("sma_200"), 2)
        ema_12 = _opt_round(latest.get("ema_12"), 2)
        ema_26 = _opt_round(latest.get("ema_26"), 2)
        ema_50 = _opt_round(latest.get("ema_50"), 2)
        rsi_14 = _opt_round(latest.get("rsi_14"), 2)
        macd = _opt_round(latest.get("macd"), 4)
        macd_signal = _opt_round(latest.get("macd_signal"), 4)
        macd_hist = _opt_round(latest.get("macd_histogram"), 4)

        volatility = compute_volatility_metrics(df_ind_period)
        condition_eval = evaluate_technical_conditions(df_ind_period)

        # Build chart-ready time series
        chart_series: List[Dict[str, Any]] = []
        for idx, row in df_ind_period.iterrows():
            chart_series.append({
                "date": idx.strftime("%Y-%m-%d"),
                "open": _opt_round(row["Open"], 2),
                "high": _opt_round(row["High"], 2),
                "low": _opt_round(row["Low"], 2),
                "close": _opt_round(row["Close"], 2),
                "volume": int(row["Volume"]) if pd.notna(row["Volume"]) else 0,
                "sma_20": _opt_round(row.get("sma_20"), 2),
                "sma_50": _opt_round(row.get("sma_50"), 2),
                "sma_200": _opt_round(row.get("sma_200"), 2),
                "ema_12": _opt_round(row.get("ema_12"), 2),
                "ema_26": _opt_round(row.get("ema_26"), 2),
                "rsi_14": _opt_round(row.get("rsi_14"), 2),
                "macd": _opt_round(row.get("macd"), 4),
                "macd_signal": _opt_round(row.get("macd_signal"), 4),
                "macd_histogram": _opt_round(row.get("macd_histogram"), 4),
            })

        # Track any indicator data limitations (e.g., fewer than 200 bars for SMA-200)
        limitations: List[str] = []
        if sma_200 is None:
            limitations.append(
                f"SMA-200 requires 200 trading sessions; only {len(df_ind_full)} sessions were available."
            )
        if sma_50 is None:
            limitations.append(
                f"SMA-50 requires 50 trading sessions; only {len(df_ind_full)} sessions were available."
            )
        if rsi_14 is None:
            limitations.append("Insufficient trading bars (<15) to compute 14-period RSI.")
        if macd_signal is None:
            limitations.append("Insufficient trading bars (<35) to compute full MACD signal line.")

        # Grounded explanation
        overall_signal = condition_eval["overall_signal"]
        sym = "₹" if currency == "INR" else "$"
        sma_parts = []
        if sma_20 is not None:
            sma_parts.append(f"SMA-20 at {sym}{sma_20}")
        if sma_50 is not None:
            sma_parts.append(f"SMA-50 at {sym}{sma_50}")
        if sma_200 is not None:
            sma_parts.append(f"SMA-200 at {sym}{sma_200}")
        sma_summary = ", ".join(sma_parts) if sma_parts else "moving averages unavailable"

        rsi_clause = f"14-day RSI is {rsi_14}" if rsi_14 is not None else "RSI-14 is unavailable"
        macd_clause = (
            f"MACD ({macd}) is {'above' if macd > macd_signal else 'below'} its signal line ({macd_signal})"
            if (macd is not None and macd_signal is not None)
            else "MACD signal comparison is unavailable"
        )
        vol_clause = (
            f"Annualized historical volatility over the {period} window is {volatility['annualized_volatility_pct']}% ({volatility['volatility_regime']} regime)"
            if volatility["annualized_volatility_pct"] is not None
            else "Historical volatility could not be determined"
        )

        explanation = (
            f"Historical Trend Assessment ({period}): {ticker} moved {period_return_pct:+.2f}% from "
            f"{sym}{round(start_close, 2)} to {sym}{round(end_close, 2)} (range {sym}{period_low}–{sym}{period_high}). "
            f"Technical indicators collectively point to {overall_signal} "
            f"({condition_eval['bullish_count']} bullish vs {condition_eval['bearish_count']} bearish conditions). "
            f"Trend & Momentum: {sma_summary}; {rsi_clause}; {macd_clause}. "
            f"Volatility: {vol_clause}, with a period maximum drawdown of {volatility['max_drawdown_pct']}%. "
            f"{TECHNICAL_DISCLAIMER}"
        )

        return {
            "agent_name": self.agent_name,
            "analyzed_at": analyzed_at,
            "ticker": ticker,
            "market": market,
            "period": period,
            "currency": currency,
            "status": "COMPLETED",
            "trend_summary": {
                "overall_signal": overall_signal,
                "bullish_conditions": condition_eval["bullish_count"],
                "bearish_conditions": condition_eval["bearish_count"],
                "neutral_conditions": condition_eval["neutral_count"],
                "trading_days_analyzed": len(df_ind_period),
                "start_close": round(start_close, 2),
                "latest_close": round(end_close, 2),
                "period_return_pct": period_return_pct,
                "period_high": period_high,
                "period_low": period_low,
                "pct_from_sma_20": round(((end_close - sma_20) / sma_20) * 100.0, 2) if sma_20 else None,
                "pct_from_sma_50": round(((end_close - sma_50) / sma_50) * 100.0, 2) if sma_50 else None,
                "pct_from_sma_200": round(((end_close - sma_200) / sma_200) * 100.0, 2) if sma_200 else None,
            },
            "latest_indicators": {
                "close": round(end_close, 2),
                "sma_20": sma_20,
                "sma_50": sma_50,
                "sma_200": sma_200,
                "ema_12": ema_12,
                "ema_26": ema_26,
                "ema_50": ema_50,
                "rsi_14": rsi_14,
                "macd": macd,
                "macd_signal": macd_signal,
                "macd_histogram": macd_hist,
            },
            "volatility": volatility,
            "technical_conditions": condition_eval["conditions"],
            "chart_series": chart_series,
            "data_limitations": limitations,
            "explanation": explanation,
            "disclaimer": TECHNICAL_DISCLAIMER,
        }

