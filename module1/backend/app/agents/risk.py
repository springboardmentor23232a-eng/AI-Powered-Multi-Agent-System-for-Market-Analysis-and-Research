"""Risk Analysis Agent (Milestone 2).

Historical volatility, maximum drawdown, 1-day historical VaR, financial/sector risk flags, DETECTION OF CONFLICTS between the
other agents (it reports disagreement, it does not hide it), missing/outdated information, simple historical-distribution
scenarios, and an explicit statement of uncertainty.

The risk level is a deterministic score (documented in `level_basis`) so the same data always gives the same result.
"""
from datetime import datetime, timezone

from ..analysis import indicators as ind
from .context import ResearchContext
from .schemas import Conflict, Finding, RiskOutput, Scenario, SourceRef

MIN_BARS = 30
SCENARIO_DAYS = 21
MIN_SCENARIO_WINDOWS = 60
STALE_DAYS = 7


def _ratio(fund, key):
    if fund is None or fund.status != "Completed":
        return None
    return next((r.value for r in fund.ratios if r.key == key), None)


def _financial_risks(fund) -> list[str]:
    out = []
    g, nig, nm = _ratio(fund, "revenue_growth_yoy"), _ratio(fund, "net_income_growth_yoy"), _ratio(fund, "net_margin")
    de, cr, fcf = _ratio(fund, "debt_to_equity"), _ratio(fund, "current_ratio"), _ratio(fund, "free_cash_flow_margin")
    if g is not None and g < 0:
        out.append(f"Revenue declined {abs(g) * 100:.1f}% year over year.")
    if nig is not None and nig < 0:
        out.append(f"Net income fell {abs(nig) * 100:.1f}% year over year.")
    if nm is not None and nm < 0:
        out.append("The company is loss-making (negative net margin).")
    if de is not None and de > 2:
        out.append(f"High leverage: debt-to-equity is {de:.2f}x (above 2x).")
    if cr is not None and cr < 1:
        out.append(f"Liquidity: current ratio is {cr:.2f}x (below 1x).")
    if fcf is not None and fcf < 0:
        out.append("Free cash flow is negative.")
    return out


def _profit_declining(fund) -> bool:
    nig, margin = _ratio(fund, "net_income_growth_yoy"), None
    if fund is not None and fund.status == "Completed":
        m = fund.history.get("series", {}).get("net_margin") or []
        vals = [x for x in m if x is not None]
        margin = (vals[-1] - vals[-2]) if len(vals) >= 2 else None
    return (nig is not None and nig < 0) or (margin is not None and margin < 0)


def _fundamentals_strong(fund, flags) -> bool:
    g, nm = _ratio(fund, "revenue_growth_yoy"), _ratio(fund, "net_margin")
    return not flags and g is not None and g > 0.05 and nm is not None and nm > 0.10


def run(ctx: ResearchContext, fund=None, tech=None, news=None) -> RiskOutput:
    stock, bars = ctx.stock, ctx.bars
    base = dict(ticker=stock.ticker, market=stock.market, generated_at=datetime.now(timezone.utc), currency=ctx.currency,
                sources=[SourceRef(name=ctx.ohlcv.source, url=ctx.ohlcv.source_url, retrieved_at=ctx.ohlcv.retrieved_at,
                                   synthetic=ctx.price_is_synthetic)])
    limitations = [
        "Risk metrics are computed from past prices and may not repeat; markets can behave very differently from their history.",
        "Scenarios are percentiles of historical 21-day returns, not forecasts, and ignore events that never occurred in the sample.",
        "Sector/macro risks (regulation, commodity prices, interest rates, geopolitics) are not quantified from the available data.",
    ]
    if len(bars) < MIN_BARS:
        return RiskOutput(status="Unavailable", summary=f"Only {len(bars)} valid price rows - at least {MIN_BARS} are needed.",
                          limitations=limitations, **base)
    use = ctx.window if len(ctx.window) >= MIN_BARS else bars
    if use is bars and ctx.period != "1Y":
        limitations.append(f"The selected period has fewer than {MIN_BARS} trading days; risk metrics use the last year of data.")
    closes = [b.close for b in use]
    vol = ind.annualised_volatility(closes)
    dd = ind.max_drawdown(closes, [b.date for b in use])
    var = ind.historical_var(closes, 0.95)
    daily = [b / a - 1 for a, b in zip(closes, closes[1:])]
    metrics = {"annualised_volatility_pct": None if vol is None else round(vol * 100, 2),
               "max_drawdown_pct": None if dd is None else round(dd["max_drawdown"] * 100, 2),
               "var_95_1d_pct": None if var is None else round(var * 100, 2),
               "worst_day_pct": round(min(daily) * 100, 2) if daily else None, "best_day_pct": round(max(daily) * 100, 2) if daily else None,
               "down_days_pct": round(sum(d < 0 for d in daily) / len(daily) * 100, 1) if daily else None}

    # ---- scenarios from the historical distribution of 21-day returns
    scenarios: list[Scenario] = []
    rolling = sorted(ind.rolling_returns_pct([b.close for b in bars], SCENARIO_DAYS))
    if len(rolling) >= MIN_SCENARIO_WINDOWS and ctx.last_price:
        for name, q, text in (("Downside (5th percentile)", 0.05, "1 in 20 historical 21-day periods was this bad or worse."),
                              ("Median", 0.50, "The typical historical 21-day return."),
                              ("Upside (95th percentile)", 0.95, "1 in 20 historical 21-day periods was this good or better.")):
            r = ind.percentile(rolling, q)
            scenarios.append(Scenario(name=name, return_pct=round(r, 2), price=round(ctx.last_price * (1 + r / 100), 2), description=text))
    else:
        limitations.append("Not enough price history to build historical scenarios (needs about 80 trading days).")

    flags = _financial_risks(fund)
    sector: list[str] = []
    peers = fund.peers if fund is not None and fund.status == "Completed" else None
    if peers:
        me, med = peers["company"], peers["median"]
        if me.get("net_margin") is not None and med.get("net_margin") is not None and me["net_margin"] < med["net_margin"]:
            sector.append(f"Net margin is below the median of {peers['count']} peers in '{peers['category']}'.")
        if me.get("debt_to_equity") is not None and med.get("debt_to_equity") and me["debt_to_equity"] > 1.5 * med["debt_to_equity"]:
            sector.append("Debt-to-equity is more than 1.5x the peer median.")
    elif fund is not None and fund.status == "Completed":
        sector.append("No peer data, so relative sector risk cannot be assessed.")

    # ---- conflicts between agents (reported, never smoothed over)
    conflicts: list[Conflict] = []
    tbias = tech.bias if tech is not None and tech.status == "Completed" else None
    if tbias == "upward" and _profit_declining(fund):
        conflicts.append(Conflict(between=["technical", "fundamental"],
                                  description="Technical indicators look positive (upward trend) but fundamental analysis shows declining profitability."))
    if tbias == "downward" and _fundamentals_strong(fund, flags):
        conflicts.append(Conflict(between=["technical", "fundamental"],
                                  description="Technical indicators look negative (downward trend) while fundamentals look healthy (growth, solid margin, no risk flags)."))
    ntone = news.tone if news is not None and news.status == "Completed" else None
    if ntone == "Positive" and tbias == "downward":
        conflicts.append(Conflict(between=["news", "technical"], description="News tone is positive but price indicators show a downward trend."))
    if ntone == "Negative" and tbias == "upward":
        conflicts.append(Conflict(between=["news", "technical"], description="News tone is negative but price indicators show an upward trend."))
    if ntone == "Negative" and _fundamentals_strong(fund, flags):
        conflicts.append(Conflict(between=["news", "fundamental"], description="News tone is negative while fundamentals look healthy."))
    if ntone == "Positive" and flags:
        conflicts.append(Conflict(between=["news", "fundamental"], description="News tone is positive but fundamental analysis raises risk flags."))
    if news is not None and news.status == "Completed" and news.conflicts:
        conflicts.append(Conflict(between=["news"], description="; ".join(news.conflicts)))

    # ---- missing or outdated information
    gaps: list[str] = []
    for name, out in (("fundamental", fund), ("technical", tech), ("news", news)):
        if out is None or out.status != "Completed":
            gaps.append(f"The {name} analysis is unavailable, so the risk view is incomplete.")
        elif any(s.synthetic for s in out.sources):
            gaps.append(f"The {name} analysis uses SYNTHETIC demo data.")
    age = (ctx.today - bars[-1].date).days
    if age > STALE_DAYS and not ctx.price_is_synthetic:
        gaps.append(f"The latest price is {age} days old.")
    if fund is not None and fund.status == "Completed" and fund.latest_period and fund.latest_period[:4].isdigit() \
            and ctx.today.year - int(fund.latest_period[:4]) > 1:
        gaps.append(f"Financial statements are outdated (latest period {fund.latest_period}).")
    if fund is not None and fund.status == "Completed" and fund.data_issues:
        gaps.append(f"{len(fund.data_issues)} missing/inconsistent financial data issue(s) were found.")
    bad_quality = [i["message"] for i in ctx.quality.get("issues", []) if i.get("severity") != "info"]
    if bad_quality:
        gaps.append("Price data quality: " + " ".join(bad_quality[:2]))

    # ---- deterministic level
    points, basis = [], []
    if vol is not None:
        v = vol * 100
        p = 0 if v < 20 else 1 if v < 35 else 2
        points.append(p); basis.append(f"Volatility {v:.1f}% -> {['low', 'moderate', 'high'][p]} (<20% / 20-35% / >35%)")
    if dd is not None:
        d = dd["max_drawdown"] * 100
        p = 0 if d > -15 else 1 if d > -30 else 2
        points.append(p); basis.append(f"Max drawdown {d:.1f}% -> {['low', 'moderate', 'high'][p]} (>-15% / -15 to -30% / <-30%)")
    if fund is not None and fund.status == "Completed":
        p = 0 if not flags else 1 if len(flags) <= 2 else 2
        points.append(p); basis.append(f"{len(flags)} financial risk flag(s) -> {['low', 'moderate', 'high'][p]} (0 / 1-2 / 3+)")
    avg = sum(points) / len(points) if points else None
    level = "Insufficient data" if avg is None else "Low" if avg < 0.5 else "Moderate" if avg < 1.25 else "High"

    findings: list[Finding] = []
    if vol is not None:
        findings.append(Finding(text=f"Annualised historical volatility is {vol * 100:.1f}%.", kind="calculated"))
    if dd is not None:
        findings.append(Finding(text=f"Maximum drawdown was {dd['max_drawdown'] * 100:.1f}% (peak {dd.get('peak_date')}, trough {dd.get('trough_date')}; "
                                     f"{'recovered' if dd['recovered'] else 'not yet recovered'}).", kind="calculated", tone="caution"))
    if var is not None:
        findings.append(Finding(text=f"On 5% of days the stock lost at least {var * 100:.2f}% (1-day historical VaR, 95%).", kind="calculated"))
    for t in flags:
        findings.append(Finding(text=t, kind="interpretation", tone="negative"))
    for t in sector:
        findings.append(Finding(text=t, kind="interpretation", tone="caution"))
    for c in conflicts:
        findings.append(Finding(text="Conflict: " + c.description, kind="interpretation", tone="caution"))
    for g in gaps:
        findings.append(Finding(text=g, kind="fact", tone="caution"))

    summary = (f"Risk level {level.lower()}" + (f": volatility {vol * 100:.1f}%" if vol is not None else "")
               + (f", max drawdown {dd['max_drawdown'] * 100:.1f}%" if dd else "")
               + f"; {len(conflicts)} conflicting finding(s), {len(gaps)} data gap(s).")
    return RiskOutput(summary=summary, findings=findings, limitations=limitations, level=level, level_basis=basis, metrics=metrics,
                      drawdown=dd, scenarios=scenarios, financial_risks=flags, sector_risks=sector, conflicts=conflicts,
                      data_gaps=gaps, **base)
