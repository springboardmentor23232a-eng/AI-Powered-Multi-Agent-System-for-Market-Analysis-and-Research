"""Fundamental Analysis Agent (Milestone 2).

Revenue/earnings, profitability, debt & stability, valuation ratios (when the inputs exist), historical comparison,
peer comparison (when the reference dataset has comparable companies) and identification of missing/inconsistent data.

Data source priority:  1) real provider financials (Yahoo)   2) the reference CSV dataset (Kaggle)   3) demo SYNTHETIC data
(only if nothing real exists - and then every output says so). Nothing is ever estimated to fill a gap.
"""
import statistics
from datetime import datetime, timezone

from ..analysis.ratios import compute_ratios, safe_div
from ..financial_dataset import (DATASET_NAME, DATASET_URL, get_dataset, match_company, peers as ds_peers, series_for)
from ..market_data import Fetched, MarketDataError, fetch_financials
from .context import ResearchContext
from .schemas import Finding, FundamentalOutput, RatioItem, SourceRef

PERCENT_KEYS = {"revenue_growth_yoy", "revenue_cagr", "net_income_growth_yoy", "gross_margin", "operating_margin",
                "net_margin", "roe", "roa", "free_cash_flow_margin"}
USD_MARKETS = {"NASDAQ", "NYSE"}
MAX_PRICE_AGE_YEARS = 1     # valuation ratios need financials no older than this (years before today)


def _fmt_pct(x):
    return f"{x * 100:.1f}%"


def _provider_metrics(fin: dict) -> tuple[list[str], dict]:
    def g(stmt, key):
        return list(fin.get(stmt, {}).get(key) or [])
    m = {"revenue": g("income_statement", "total_revenue"), "gross_profit": g("income_statement", "gross_profit"),
         "operating_income": g("income_statement", "operating_income"), "net_income": g("income_statement", "net_income"),
         "total_assets": g("balance_sheet", "total_assets"), "total_debt": g("balance_sheet", "total_debt"),
         "equity": g("balance_sheet", "stockholders_equity"), "operating_cash_flow": g("cash_flow", "operating_cash_flow"),
         "free_cash_flow": g("cash_flow", "free_cash_flow"), "eps": g("per_share", "eps"),
         "shares_outstanding": g("per_share", "shares_outstanding")}
    return list(fin.get("periods") or []), m


def _data_issues(periods: list[str], m: dict) -> list[str]:
    out: list[str] = []
    labels = {"revenue": "Revenue", "net_income": "Net income", "equity": "Shareholders' equity", "gross_profit": "Gross profit",
              "total_debt": "Total debt", "total_assets": "Total assets", "operating_cash_flow": "Operating cash flow", "eps": "EPS"}
    for key, label in labels.items():
        vals = m.get(key) or []
        if not any(v is not None for v in vals):
            continue                      # whole metric absent from this source: reported as a limitation, not an "issue"
        gaps = [periods[i] for i, v in enumerate(vals) if v is None and i < len(periods)]
        if gaps:
            out.append(f"{label} is missing for {', '.join(gaps[:6])}.")
    for i, p in enumerate(periods):
        rev, ni = (m.get("revenue") or [None] * len(periods))[i], (m.get("net_income") or [None] * len(periods))[i]
        gp = (m.get("gross_profit") or [None] * len(periods))[i]
        eq = (m.get("equity") or [None] * len(periods))[i]
        if rev is not None and rev <= 0:
            out.append(f"Revenue is zero or negative in {p} - growth and margins are not meaningful.")
        if rev and ni is not None and ni > rev > 0:
            out.append(f"Net income exceeds revenue in {p}, which is inconsistent (check for a one-off gain or a data error).")
        if rev and gp is not None and gp > rev > 0:
            out.append(f"Gross profit exceeds revenue in {p}, which is inconsistent.")
        if eq is not None and eq <= 0:
            out.append(f"Shareholders' equity is zero or negative in {p} - ROE and debt-to-equity are not meaningful.")
    if all(p.isdigit() for p in periods) and len(periods) > 1:
        ys = [int(p) for p in periods]
        skipped = [str(y) for a, b in zip(ys, ys[1:]) for y in range(a + 1, b)]
        if skipped:
            out.append(f"No data for {', '.join(skipped[:6])} (non-consecutive years); growth rates span the gap.")
    return out


def _peer_block(ds, company: str, category: str, year: int) -> dict | None:
    def stats(r):
        rev, ni, eq = r.get("revenue"), r.get("net_income"), r.get("equity")
        return {"net_margin": safe_div(ni, rev) if rev and rev > 0 else None,
                "roe": safe_div(ni, eq) if eq and eq > 0 and ni is not None else None,
                "debt_to_equity": r.get("reported_debt_to_equity")}
    rows = ds_peers(ds, company, category, year)
    me = next((r for r in ds.rows if r["company"] == company and r["year"] == year), None)
    if not rows or me is None:
        return None
    members = [{"company": r["company"], **stats(r)} for r in rows]
    median = {k: (statistics.median(v) if (v := [x[k] for x in members if x[k] is not None]) else None)
              for k in ("net_margin", "roe", "debt_to_equity")}
    return {"category": category, "year": year, "count": len(rows), "company": stats(me), "median": median,
            "members": sorted(members, key=lambda x: x["company"])[:10]}


def run(ctx: ResearchContext) -> FundamentalOutput:
    stock, now = ctx.stock, datetime.now(timezone.utc)
    base = dict(ticker=stock.ticker, market=stock.market, generated_at=now)
    limitations: list[str] = []
    sources: list[SourceRef] = []

    # ---- gather candidate sources
    fin: Fetched | None = None
    try:
        fin = fetch_financials(stock)
        ctx.record("financials", fin, len((fin.data.get("periods") or [])), {"missing_metrics": fin.data.get("missing_metrics", [])})
    except MarketDataError as exc:
        limitations.append(str(exc))
    ds, ds_company, ds_series = None, None, None
    try:
        ds = get_dataset()
    except ValueError as exc:
        limitations.append(f"Reference dataset could not be read: {exc}")
    if ds:
        ds_company = match_company(ds, stock.ticker, stock.name)
        if ds_company:
            ds_series = series_for(ds, ds_company)
            ctx.record("financials", Fetched(None, f"{DATASET_NAME} - local CSV", DATASET_URL, False, ds.loaded_at),
                       len(ds_series["periods"]), {"dataset_rows": ds.report})

    # ---- choose the basis
    if fin is not None and not fin.synthetic:
        basis, periods, m = fin.source, *_provider_metrics(fin.data)
        sources.append(SourceRef(name=fin.source, url=fin.source_url, retrieved_at=fin.retrieved_at))
        currency, synthetic = fin.data.get("currency"), False
    elif ds_series:
        basis, periods, m = f"{DATASET_NAME} (company '{ds_company}')", ds_series["periods"], ds_series["metrics"]
        sources.append(SourceRef(name=DATASET_NAME, url=DATASET_URL, retrieved_at=ds.loaded_at))
        currency, synthetic = ("USD" if stock.market in USD_MARKETS else None), False
        if currency is None:
            limitations.append("The dataset's currency is not stated; amounts are shown without a currency.")
        else:
            limitations.append("The dataset's currency is assumed to be USD.")
    elif fin is not None:
        basis, (periods, m) = fin.source, _provider_metrics(fin.data)
        sources.append(SourceRef(name=fin.source, retrieved_at=fin.retrieved_at, synthetic=True))
        currency, synthetic = fin.data.get("currency"), True
        limitations.append("These financials are SYNTHETIC demo data. Set MARKET_DATA_PROVIDER=yahoo or add the Kaggle CSV "
                           "(backend/data/financial_statements.csv) for real figures.")
    else:
        why = "; ".join(limitations) or "no financial data source is available"
        return FundamentalOutput(status="Unavailable", summary=f"Fundamental analysis is unavailable: {why}",
                                 limitations=limitations + ["No financial statements could be retrieved; nothing was estimated."], **base)

    if ds_series is None and ds is not None:
        limitations.append(f"'{stock.name}' was not found in the reference dataset, so there is no peer comparison.")
    if ds is None and fin is not None and not fin.synthetic:
        limitations.append("No reference dataset loaded; peer comparison is unavailable.")

    # ---- valuation inputs must be current, real and in one currency
    latest = periods[-1] if periods else None
    age_ok = True
    if latest and latest[:4].isdigit():
        age_ok = ctx.today.year - int(latest[:4]) <= MAX_PRICE_AGE_YEARS + 0
    price_ok = (not ctx.price_is_synthetic) and (not synthetic) and age_ok and (currency == ctx.currency)
    ratios_raw = compute_ratios(m, price=ctx.last_price, price_is_reliable=price_ok)
    if not price_ok:
        reason = ("the price history is synthetic demo data" if ctx.price_is_synthetic else
                  "the financials are synthetic demo data" if synthetic else
                  f"the latest financial period ({latest}) is more than {MAX_PRICE_AGE_YEARS} year(s) old, so dividing a current price by it would mislead"
                  if not age_ok else "the price and the financials are not in the same currency")
        for k in ("pe", "pb"):
            ratios_raw[k]["reason_unavailable"] = f"Not computed: {reason}."
    ratios = [RatioItem(key=k, name=r["name"], value=r["value"], unit="%" if k in PERCENT_KEYS else "x", formula=r["formula"],
                        kind=r["kind"], inputs=r["inputs"], reason_unavailable=r["reason_unavailable"])
              for k, r in ratios_raw.items()]
    val = {r.key: r.value for r in ratios}

    # ---- history table
    rev, ni = m.get("revenue") or [], m.get("net_income") or []
    margin = [safe_div(n, r) if r and r > 0 else None for n, r in zip(ni, rev)]
    series = {"revenue": rev, "net_income": ni, "net_margin": margin, "equity": m.get("equity") or [],
              "operating_cash_flow": m.get("operating_cash_flow") or [], "eps": m.get("eps") or []}
    history = {"periods": periods, "series": {k: v for k, v in series.items() if any(x is not None for x in v)}}

    issues = _data_issues(periods, m)
    unavailable = [r.name for r in ratios if r.value is None]
    if unavailable:
        limitations.append("Not available from this source: " + ", ".join(unavailable) + ".")

    # ---- peers
    peers_block = None
    if ds_series and ds_series["category"]:
        years = [int(p) for p in periods if p.isdigit()]
        if years:
            peers_block = _peer_block(ds, ds_company, ds_series["category"], max(years))
        if peers_block is None:
            limitations.append("No comparable companies in the same category were found for the latest year.")

    # ---- findings (facts, then rule-based interpretations)
    F: list[Finding] = []
    unit = f" {currency}" if currency else ""
    if latest and rev and rev[-1] is not None:
        F.append(Finding(text=f"Latest revenue ({latest}): {rev[-1]:,.0f}{unit}; net income: "
                              f"{('n/a' if not ni or ni[-1] is None else format(ni[-1], ',.0f'))}{unit}. Source: {basis}.", kind="fact"))
    g = val.get("revenue_growth_yoy")
    if g is not None:
        tone, word = ("positive", "grew strongly") if g > 0.10 else ("positive", "grew modestly") if g > 0 else ("negative", "declined")
        F.append(Finding(text=f"Revenue {word} {_fmt_pct(g)} year over year.", kind="interpretation", tone=tone))
    if val.get("revenue_cagr") is not None:
        F.append(Finding(text=f"Revenue compound annual growth over the available history: {_fmt_pct(val['revenue_cagr'])}.", kind="calculated"))
    nm = val.get("net_margin")
    if nm is not None:
        band = ("high (above 15%)", "positive") if nm > 0.15 else ("moderate (5-15%)", "neutral") if nm >= 0.05 else \
               ("thin (0-5%)", "caution") if nm >= 0 else ("negative - the company lost money", "negative")
        trend = ""
        prev = next((x for x in reversed(margin[:-1]) if x is not None), None) if len(margin) > 1 else None
        if prev is not None:
            trend = f"; it {'improved' if nm > prev else 'fell' if nm < prev else 'was unchanged'} from {_fmt_pct(prev)} the period before"
        F.append(Finding(text=f"Net profit margin is {_fmt_pct(nm)}, {band[0]}{trend}.", kind="interpretation", tone=band[1]))
    if val.get("roe") is not None:
        F.append(Finding(text=f"Return on equity is {_fmt_pct(val['roe'])}.", kind="calculated"))
    de = val.get("debt_to_equity")
    if de is not None:
        band = ("low", "positive") if de < 1 else ("moderate", "neutral") if de <= 2 else ("high", "caution")
        F.append(Finding(text=f"Debt-to-equity is {de:.2f}x, a {band[0]} leverage level.", kind="interpretation", tone=band[1]))
    cr = val.get("current_ratio")
    if cr is not None:
        F.append(Finding(text=f"Current ratio is {cr:.2f}x" + (" - below 1, short-term liabilities exceed short-term assets." if cr < 1 else "."),
                         kind="interpretation", tone="caution" if cr < 1 else "neutral"))
    if val.get("free_cash_flow_margin") is not None:
        fm = val["free_cash_flow_margin"]
        F.append(Finding(text=f"Free cash flow is {_fmt_pct(fm)} of revenue" + (" (negative: the business consumed cash)." if fm < 0 else "."),
                         kind="interpretation", tone="negative" if fm < 0 else "neutral"))
    if val.get("pe") is not None:
        F.append(Finding(text=f"P/E ratio is {val['pe']:.1f}: the price is {val['pe']:.1f} times the latest annual earnings per share.", kind="calculated"))
    if peers_block and peers_block["median"].get("net_margin") is not None and peers_block["company"].get("net_margin") is not None:
        mine, med = peers_block["company"]["net_margin"], peers_block["median"]["net_margin"]
        F.append(Finding(text=f"Net margin {_fmt_pct(mine)} vs a peer median of {_fmt_pct(med)} ({peers_block['count']} '{peers_block['category']}' "
                              f"companies, {peers_block['year']}): {'above' if mine > med else 'below'} the peer median.",
                         kind="interpretation", tone="positive" if mine > med else "caution"))
    for issue in issues[:4]:
        F.append(Finding(text=issue, kind="fact", tone="caution"))

    parts = []
    if g is not None:
        parts.append(f"revenue {'up' if g > 0 else 'down'} {_fmt_pct(abs(g))}")
    if nm is not None:
        parts.append(f"net margin {_fmt_pct(nm)}")
    if de is not None:
        parts.append(f"debt-to-equity {de:.2f}x")
    summary = (f"{stock.name} ({latest}): " + ", ".join(parts) + ".") if parts else \
        f"Only limited financial data is available for {stock.name}."
    if synthetic:
        summary += " [SYNTHETIC demo data]"

    return FundamentalOutput(summary=summary, findings=F, limitations=limitations, sources=sources, basis=basis,
                             currency=currency, latest_period=latest, ratios=ratios, history=history, peers=peers_block,
                             data_issues=issues, **base)
