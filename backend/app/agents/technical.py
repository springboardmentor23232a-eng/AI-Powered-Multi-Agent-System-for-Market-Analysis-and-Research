import math

import pandas as pd

from app.agents.base import AgentContext, ClaimBuilder, num, pct
from app.schemas.agents import AgentResult, AgentStatus, Signal, TechnicalOutput
from app.services import market_data as md
from app.tools import macd, rsi, sma

FLAT_BAND = 1e-4  # |MACD histogram| below this fraction of price counts as flat
HISTORY = 260  # trading sessions used for indicators (covers the 200-day SMA with warm-up)


def _clean(series) -> list:
    return [None if (v is None or (isinstance(v, float) and math.isnan(v))) else round(float(v), 4) for v in series]


class TechnicalAgent:
    name = "technical"

    def run(self, ctx: AgentContext) -> AgentResult:
        prices = md.get_prices(ctx.db, ctx.market, ctx.ticker, ctx.market_code, ctx.period, ctx.as_of,
                               task_id=ctx.task_id, now=ctx.now)
        limitations = [i.message for i in prices.validation.issues]
        if not prices.validation.is_usable:
            return AgentResult(agent=self.name, status=AgentStatus.unavailable, limitations=limitations)
        rows = prices.rows[-HISTORY:]
        closes = [float(r["close"]) for r in rows]
        last = rows[-1]
        b, ind = ClaimBuilder(self.name), {}

        b.fact(f"Latest close was {last['close']:,.2f} on {last['date']}", prices.source.content_hash,
               md.last_close_line(last["date"], last["close"]), key="price_fact")
        v = {"values": closes}
        ind["sma50"] = b.calc("50-day simple moving average", "sma", {**v, "window": 50}, "sma50")
        ind["sma200"] = b.calc("200-day simple moving average", "sma", {**v, "window": 200}, "sma200")
        ind["rsi14"] = b.calc("14-day RSI", "rsi", {**v, "period": 14}, "rsi14")
        mac = b.calc("MACD (12, 26, 9)", "macd", {**v, "fast": 12, "slow": 26, "signal": 9}, "macd")
        ind["macd"], ind["macd_signal"], ind["macd_histogram"] = (
            (mac["macd"], mac["signal"], mac["histogram"]) if mac else (None, None, None))
        ind["volatility"] = b.calc("Annualised historical volatility", "historical_volatility", v, "volatility")

        close, s50, s200, hist = closes[-1], ind["sma50"], ind["sma200"], ind["macd_histogram"]
        conditions, score = [], 0
        if s50 is not None:
            conditions.append(f"Close is {'above' if close > s50 else 'below'} the 50-day SMA")
            score += 1 if close > s50 else -1
        if s50 is not None and s200 is not None:
            conditions.append(f"50-day SMA is {'above' if s50 > s200 else 'below'} the 200-day SMA")
            score += 1 if s50 > s200 else -1
        if hist is not None:
            if abs(hist) < FLAT_BAND * close:  # dead band: ignore numerical noise around zero
                conditions.append("MACD histogram is flat")
            else:
                conditions.append(f"MACD histogram is {'positive' if hist > 0 else 'negative'}")
                score += 1 if hist > 0 else -1
        r = ind["rsi14"]
        if r is not None:
            conditions.append("RSI above 70 (overbought)" if r > 70 else "RSI below 30 (oversold)" if r < 30
                              else "RSI between 30 and 70 (no extreme)")
        for name, label in (("sma50", "50-day SMA"), ("sma200", "200-day SMA"), ("rsi14", "RSI"), ("macd", "MACD")):
            if ind.get(name) is None and not (name == "macd" and mac):
                limitations.append(f"{label} not computed: insufficient price history")
        limitations.append("Indicators describe historical conditions and are not predictions")

        signal = Signal.bullish if score >= 2 else Signal.bearish if score <= -2 else Signal.neutral
        facts = {"RSI": num(r), "50-day SMA": num(s50), "200-day SMA": num(s200), "MACD histogram": num(hist, 3),
                 "volatility": pct(ind["volatility"])}
        facts = {k: v for k, v in facts.items() if v != "n/a"}
        summary = ctx.llm.summarize(self.name, facts)
        if conditions:
            summary += " " + "; ".join(conditions) + "."
        b.interpret(summary, key="summary")

        ser = pd.Series(closes)
        mac_df = macd(ser)
        chart = {"dates": [r["date"] for r in rows], "close": closes, "sma50": _clean(sma(ser, 50)),
                 "sma200": _clean(sma(ser, 200)), "rsi14": _clean(rsi(ser, 14)),
                 "macd": _clean(mac_df["macd"]), "macd_signal": _clean(mac_df["signal"])}
        out = TechnicalOutput(indicators=ind, conditions=conditions, signal=signal, summary=summary, chart=chart)
        return AgentResult(agent=self.name, status=AgentStatus.success,
                           data={**out.model_dump(mode="json"), "claim_ids": b.index}, claims=b.claims,
                           limitations=limitations)
