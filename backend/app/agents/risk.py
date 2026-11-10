from app.agents.base import AgentContext, ClaimBuilder, pct
from app.agents.contradictions import detect_contradictions
from app.schemas.agents import AgentResult, AgentStatus, RiskOutput
from app.services import market_data as md

MAX_HISTORY = 520


class RiskAgent:
    name = "risk"

    def run(self, ctx: AgentContext, upstream: dict[str, AgentResult]) -> AgentResult:
        prices = md.get_prices(ctx.db, ctx.market, ctx.ticker, ctx.market_code, ctx.period, ctx.as_of,
                               task_id=ctx.task_id, now=ctx.now)
        limitations = []
        stale = [i.message for i in prices.validation.issues]
        for name in ("fundamental", "technical", "news"):
            r = upstream.get(name)
            if r is None or r.status != AgentStatus.success:
                stale.append(f"{name.capitalize()} analysis unavailable")
        if not prices.validation.is_usable:
            return AgentResult(agent=self.name, status=AgentStatus.unavailable,
                               limitations=stale or ["Insufficient price history for risk metrics"])
        closes = [float(r["close"]) for r in prices.rows[-MAX_HISTORY:]]
        b, risks = ClaimBuilder(self.name), []
        vol = b.calc(f"Annualised volatility over the last {len(closes)} sessions", "historical_volatility",
                     {"values": closes}, "volatility")
        mdd = b.calc(f"Maximum drawdown over the last {len(closes)} sessions", "max_drawdown",
                     {"values": closes}, "max_drawdown")

        def up(agent, key):  # claim id of an upstream metric, if present
            r = upstream.get(agent)
            return (r.data.get("claim_ids", {}).get(key) if r and r.status == AgentStatus.success else None)

        def risk(text, *support_ids):
            ids = [i for i in support_ids if i]
            if ids and b.interpret(text, ids):
                risks.append(text)

        if vol is not None and vol > 0.25:
            risk("Volatility is high" if vol > 0.40 else "Volatility is elevated", b.index.get("volatility"))
        if mdd is not None and mdd <= -0.30:
            risk("A drawdown of 30% or more occurred in the period", b.index.get("max_drawdown"))
        fund = upstream.get("fundamental")
        fm = fund.data.get("metrics", {}) if fund and fund.status == AgentStatus.success else {}
        if fm.get("debt_to_equity") is not None and fm["debt_to_equity"] > 1.5:
            risk("Leverage is high (debt to equity above 1.5)", up("fundamental", "debt_to_equity"))
        if fm.get("net_margin") is not None and fm["net_margin"] < 0:
            risk("The company reported a net loss", up("fundamental", "net_margin"))
        if fm.get("revenue_growth") is not None and fm["revenue_growth"] < 0:
            risk("Revenue declined year over year", up("fundamental", "revenue_growth"))
        news = upstream.get("news")
        if news and news.status == AgentStatus.success and news.data.get("signal") == "bearish":
            news_ids = [c.claim_id for c in news.claims if c.type.value == "FACT"][:3]
            risk("Recent news flow is predominantly negative", *news_ids)

        contradictions = detect_contradictions(upstream)
        scenarios = []
        for c in contradictions:
            scenarios.append(f"If the {c.agent_a} view proves right, the {c.agent_b} concern may be priced in; "
                             f"if the {c.agent_b} view proves right, the {c.agent_a} signal may reverse.")
        scenarios.append("If recent volatility persists, short-term price swings could exceed what trend indicators imply.")
        if "volatility" in b.index:
            for s in scenarios:
                b.interpret(s, [b.index["volatility"]])

        for name in ("fundamental", "technical", "news"):
            r = upstream.get(name)
            if r is not None:
                limitations += [f"{name}: {l}" for l in r.limitations[:3]]
        limitations.append("Risk metrics describe past behaviour and do not forecast future losses")
        summary = ctx.llm.summarize(self.name, {"volatility": pct(vol), "max drawdown": pct(mdd),
                                                "risk flags": str(len(risks)), "contradictions": str(len(contradictions))})
        b.interpret(summary, key="summary")
        out = RiskOutput(volatility_annualized=vol, max_drawdown=mdd, risks=risks, scenarios=scenarios,
                         stale_or_missing=stale, contradictions=contradictions, summary=summary)
        return AgentResult(agent=self.name, status=AgentStatus.success,
                           data={**out.model_dump(mode="json"), "claim_ids": b.index}, claims=b.claims,
                           limitations=limitations)
