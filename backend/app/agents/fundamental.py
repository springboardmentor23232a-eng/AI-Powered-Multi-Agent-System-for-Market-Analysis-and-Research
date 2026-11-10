from app.agents.base import AgentContext, ClaimBuilder, num, pct
from app.schemas.agents import AgentResult, AgentStatus, FundamentalOutput, Signal
from app.services import market_data as md
from app.services.market_data import ProviderError

LABELS = {"revenue_growth": "revenue growth", "net_margin": "net margin", "operating_margin": "operating margin",
          "debt_to_equity": "debt to equity", "roe": "ROE", "pe": "P/E", "pb": "P/B"}


def score_fundamentals(m: dict) -> Signal:
    """Rule-based signal from tool-computed metrics."""
    score = 0
    g, nm, nmp, de, roe = (m.get(k) for k in ("revenue_growth", "net_margin", "net_margin_prev", "debt_to_equity", "roe"))
    if g is not None:
        score += 1 if g > 0.05 else -1 if g < 0 else 0
    if nm is not None and nmp is not None:
        score += 1 if nm > nmp else -1 if nm < nmp else 0
    if nm is not None and nm < 0:
        score -= 1
    if de is not None:
        score += 1 if de < 0.5 else -1 if de > 1.5 else 0
    if roe is not None:
        score += 1 if roe > 0.15 else -1 if roe < 0.08 else 0
    return Signal.bullish if score >= 2 else Signal.bearish if score <= -2 else Signal.neutral


class FundamentalAgent:
    name = "fundamental"

    def run(self, ctx: AgentContext) -> AgentResult:
        fin = md.get_financials(ctx.db, ctx.market, ctx.ticker, ctx.market_code, task_id=ctx.task_id, now=ctx.now)
        limitations = [i.message for i in fin.issues]
        annual = sorted(fin.data.get("annual") or [], key=lambda y: -y["year"])
        if not annual:
            return AgentResult(agent=self.name, status=AgentStatus.unavailable,
                               limitations=limitations or ["No financial statements available"])
        cur, prev = annual[0], (annual[1] if len(annual) > 1 else {})
        fy, py = cur["year"], prev.get("year")
        b, m = ClaimBuilder(self.name), {}
        h = fin.source.content_hash

        for field, label in (("revenue", "revenue"), ("net_income", "net income")):
            if cur.get(field) is not None:
                b.fact(f"FY{fy} {label} was {cur[field]:,.0f}", h, md.fact_line(fy, field, cur[field]), key=f"{field}_fact")

        m["revenue_growth"] = b.calc(f"Revenue growth FY{py} to FY{fy}", "growth_rate",
                                     {"current": cur.get("revenue"), "previous": prev.get("revenue")}, "revenue_growth")
        m["net_margin"] = b.calc(f"Net margin FY{fy}", "margin",
                                 {"numerator": cur.get("net_income"), "revenue": cur.get("revenue")}, "net_margin")
        m["net_margin_prev"] = b.calc(f"Net margin FY{py}", "margin",
                                      {"numerator": prev.get("net_income"), "revenue": prev.get("revenue")}, "net_margin_prev")
        m["operating_margin"] = b.calc(f"Operating margin FY{fy}", "margin",
                                       {"numerator": cur.get("operating_income"), "revenue": cur.get("revenue")}, "operating_margin")
        m["debt_to_equity"] = b.calc(f"Debt to equity FY{fy}", "debt_to_equity",
                                     {"total_debt": cur.get("total_debt"), "total_equity": cur.get("total_equity")}, "debt_to_equity")
        m["roe"] = b.calc(f"Return on equity FY{fy}", "roe",
                          {"net_income": cur.get("net_income"), "equity_end": cur.get("total_equity"),
                           "equity_begin": prev.get("total_equity")}, "roe")

        price = None
        try:
            prices = md.get_prices(ctx.db, ctx.market, ctx.ticker, ctx.market_code, ctx.period, ctx.as_of,
                                   task_id=ctx.task_id, now=ctx.now)
            if prices.validation.is_usable and prices.rows:
                last = prices.rows[-1]
                price = last["close"]
                b.fact(f"Latest close was {price:,.2f} on {last['date']}", prices.source.content_hash,
                       md.last_close_line(last["date"], price), key="price_fact")
        except ProviderError:
            pass
        if price is None:
            limitations.append("Price unavailable, so valuation ratios (P/E, P/B) were not computed")
        shares = (fin.data.get("profile") or {}).get("sharesOutstanding")
        eps_v = b.calc(f"EPS FY{fy}", "eps", {"net_income": cur.get("net_income"), "shares": shares}, "eps")
        bvps = b.calc(f"Book value per share FY{fy}", "book_value_per_share",
                      {"total_equity": cur.get("total_equity"), "shares": shares}, "bvps")
        m["pe"] = b.calc("P/E ratio", "pe_ratio", {"price": price, "earnings_per_share": eps_v}, "pe")
        m["pb"] = b.calc("P/B ratio", "pb_ratio", {"price": price, "book_value_ps": bvps}, "pb")

        for k, label in LABELS.items():
            if m.get(k) is None:
                limitations.append(f"{label} could not be computed from the available data")
        if ctx.as_of:
            limitations.append("Financial statements are not point-in-time; replay uses the latest filings available")
        limitations.append("Peer comparison not performed")

        fmt = {k: (num(v) if k in ("debt_to_equity", "pe", "pb") else pct(v)) for k, v in m.items()
               if v is not None and k != "net_margin_prev"}
        facts = {LABELS[k]: v for k, v in fmt.items()}
        signal = score_fundamentals(m)
        summary = ctx.llm.summarize(self.name, facts)
        b.interpret(summary, key="summary")
        out = FundamentalOutput(
            metrics={k: v for k, v in m.items()},
            trend={f: [y[f] for y in reversed(annual) if y.get(f) is not None] for f in ("revenue", "net_income")},
            signal=signal, summary=summary)
        return AgentResult(agent=self.name, status=AgentStatus.success,
                           data={**out.model_dump(mode="json"), "claim_ids": b.index}, claims=b.claims,
                           limitations=limitations)
