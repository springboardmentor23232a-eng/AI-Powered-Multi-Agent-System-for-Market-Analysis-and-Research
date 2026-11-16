from typing import List
from app.schemas.agent_outputs import TechnicalAnalysisOutput
from app.schemas.market_data import StockMarketData


class TechnicalAnalysisAgent:
    """
    Specialist Agent responsible for quantitative price action, moving average trends,
    RSI oscillator momentum, support/resistance barriers, and short-to-medium term chart dynamics.
    """
    AGENT_NAME = "Technical Analysis Specialist"

    @classmethod
    def analyze(cls, data: StockMarketData) -> TechnicalAnalysisOutput:
        ticker = data.ticker
        tech = data.technicals
        price = data.price

        key_findings: List[str] = []
        warnings: List[str] = []
        confidence = 0.90

        current_price = price.current_price
        sma_50 = tech.sma_50
        sma_200 = tech.sma_200
        rsi = tech.rsi_14

        # 1. Moving Average & Trend Direction
        trend_direction = tech.trend_signal or "NEUTRAL"
        if current_price and sma_50 and sma_200:
            if current_price > sma_50 > sma_200:
                trend_direction = "BULLISH"
                key_findings.append(
                    f"Strong bullish alignment: Price (${current_price:.2f}) trades above both the 50-day (${sma_50:.2f}) and 200-day (${sma_200:.2f}) SMAs."
                )
            elif current_price < sma_50 < sma_200:
                trend_direction = "BEARISH"
                key_findings.append(
                    f"Bearish breakdown: Price (${current_price:.2f}) trades below both the 50-day (${sma_50:.2f}) and 200-day (${sma_200:.2f}) SMAs."
                )
            elif current_price > sma_200:
                trend_direction = "NEUTRAL"
                key_findings.append(
                    f"Mixed trend structure: Price (${current_price:.2f}) holds above the 200-day SMA (${sma_200:.2f}) but shows near-term consolidation."
                )
            else:
                trend_direction = "BEARISH"
                key_findings.append(
                    f"Weak trend: Price (${current_price:.2f}) trades below key 200-day long-term benchmark (${sma_200:.2f})."
                )
        elif sma_50:
            trend_direction = "BULLISH" if current_price and current_price > sma_50 else "BEARISH"
            warnings.append("200-day moving average is unavailable due to insufficient historical trading days.")
            confidence -= 0.15
        else:
            trend_direction = "NEUTRAL"
            warnings.append("Insufficient moving average data available for trend confirmation.")
            confidence -= 0.30

        # 2. RSI Momentum Oscillator
        if rsi is not None:
            if rsi >= 70:
                momentum_state = "OVERBOUGHT"
                key_findings.append(
                    f"14-day RSI stands at {rsi:.1f}, placing the stock in overbought territory where mean-reversion pullbacks are common."
                )
            elif rsi <= 30:
                momentum_state = "OVERSOLD"
                key_findings.append(
                    f"14-day RSI stands at {rsi:.1f}, indicating oversold exhaustion where technical bounces frequently occur."
                )
            else:
                momentum_state = "NEUTRAL"
                key_findings.append(f"14-day RSI is balanced at {rsi:.1f}, indicating sustainable momentum.")
        else:
            momentum_state = "NEUTRAL"
            warnings.append("14-day RSI could not be calculated due to limited price history.")
            confidence -= 0.15

        # 3. Support and Resistance Levels
        supp = tech.support_level
        res = tech.resistance_level
        if supp is not None and res is not None:
            key_findings.append(
                f"Established 6-month trading channel: Support at ${supp:.2f} | Resistance at ${res:.2f}."
            )
        else:
            warnings.append("Support and resistance channel boundaries are uncalculated.")

        # 4. Multi-timeframe Returns
        ret_30d = tech.price_change_30d_pct
        ret_90d = tech.price_change_90d_pct
        if ret_30d is not None:
            key_findings.append(f"Trailing 30-day price performance: {ret_30d:+.2f}%.")
        if ret_90d is not None:
            key_findings.append(f"Trailing 90-day price performance: {ret_90d:+.2f}%.")

        # Narrative Synthesis
        supp_str = f"${supp:.2f}" if supp is not None else "unestablished"
        res_str = f"${res:.2f}" if res is not None else "unestablished"
        narrative = (
            f"Technical evaluation for {ticker} indicates a {trend_direction.lower()} primary trend "
            f"with a {momentum_state.lower()} momentum oscillator profile. "
            f"Key support rests at {supp_str} and resistance at {res_str}."
        )

        supporting_data = {
            "current_price": current_price,
            "sma_50": sma_50,
            "sma_200": sma_200,
            "rsi_14": rsi,
            "price_change_30d_pct": ret_30d,
            "price_change_90d_pct": ret_90d,
            "support_level": supp,
            "resistance_level": res,
            "history_bars_analyzed": len(tech.recent_history),
        }

        return TechnicalAnalysisOutput(
            agent_name=cls.AGENT_NAME,
            trend_direction=trend_direction,
            momentum_state=momentum_state,
            key_support=supp,
            key_resistance=res,
            analysis=narrative,
            key_findings=key_findings,
            supporting_data=supporting_data,
            warnings_and_limitations=warnings,
            confidence_level=round(max(0.1, min(1.0, confidence)), 2),
        )
