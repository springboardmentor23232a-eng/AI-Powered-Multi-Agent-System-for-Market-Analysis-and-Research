"""Fundamental Analysis Agent.

Takes annual financial statements (from market_data.get_statements), calculates ratios
itself, explains them in plain language, compares with peers and reports every data
problem it finds. No LLM is used: all numbers come from validated Python functions and
the text is rule-based, so the output is repeatable. The returned dict is structured JSON
that a later LangGraph node / LLM report agent can consume (Agent Results -> output_json).

Not investment advice. Thresholds below are rules of thumb and differ by industry.
"""
from __future__ import annotations

import math
import re
import statistics
from datetime import datetime, timezone
from typing import Optional

from ..services import market_data as md

# ---------- thresholds (rules of thumb, shown to the user in `limitations`) ----------
REV_GROWTH_STRONG = 0.10
NET_MARGIN_HEALTHY, NET_MARGIN_THIN = 0.15, 0.05
DEBT_EQUITY_LOW, DEBT_EQUITY_HIGH = 0.5, 1.5
CURRENT_RATIO_STRONG, CURRENT_RATIO_WEAK = 1.5, 1.0
COVERAGE_COMFORTABLE, COVERAGE_WEAK = 5.0, 1.5
MAX_PEERS = 4
HISTORY_YEARS = 5
STALE_DAYS = 457          # ~15 months
PE_TOL, PB_TOL, ROE_TOL = 0.25, 0.25, 0.35   # provider vs calculated, relative difference

# our key -> (statement, [row names the provider may use, best first])
ITEMS = {
    "revenue": ("income_statement", ["Total Revenue", "Operating Revenue", "Revenue"]),
    "gross_profit": ("income_statement", ["Gross Profit"]),
    "operating_income": ("income_statement", ["Operating Income", "EBIT"]),
    "net_income": ("income_statement", ["Net Income", "Net Income Common Stockholders"]),
    "eps": ("income_statement", ["Diluted EPS", "Basic EPS"]),
    "interest_expense": ("income_statement", ["Interest Expense", "Interest Expense Non Operating"]),
    "total_assets": ("balance_sheet", ["Total Assets"]),
    "total_liabilities": ("balance_sheet", ["Total Liabilities Net Minority Interest"]),
    "total_equity_gross": ("balance_sheet", ["Total Equity Gross Minority Interest"]),
    "equity": ("balance_sheet", ["Stockholders Equity", "Common Stock Equity"]),
    "total_debt": ("balance_sheet", ["Total Debt"]),
    "cash": ("balance_sheet", ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"]),
    "current_assets": ("balance_sheet", ["Current Assets"]),
    "current_liabilities": ("balance_sheet", ["Current Liabilities"]),
    "shares": ("balance_sheet", ["Ordinary Shares Number", "Share Issued"]),
    "operating_cash_flow": ("cash_flow", ["Operating Cash Flow"]),
    "capex": ("cash_flow", ["Capital Expenditure"]),
    "free_cash_flow": ("cash_flow", ["Free Cash Flow"]),
}
LABELS = {
    "revenue": "Revenue", "gross_profit": "Gross profit", "operating_income": "Operating income",
    "net_income": "Net income", "eps": "EPS", "equity": "Shareholders' equity",
    "total_debt": "Total debt", "current_assets": "Current assets",
    "current_liabilities": "Current liabilities", "free_cash_flow": "Free cash flow",
}
CORE_ITEMS = ["revenue", "net_income", "equity"]
# these do not apply to banks / insurers, so a gap there is not a data problem
FINANCIAL_NA = {"gross_profit", "operating_income", "current_assets", "current_liabilities"}


# ---------- small safe-math helpers ----------
def _fin(x):
    return x if x is not None and math.isfinite(x) else None


def _div(a, b):
    if a is None or b is None or b == 0:
        return None
    return _fin(a / b)


def _growth(new, old):
    """Growth off a zero or negative base is not meaningful, so it returns None."""
    if new is None or old is None or old <= 0:
        return None
    return _fin((new - old) / old)


def _cagr(new, old, periods):
    if new is None or old is None or new <= 0 or old <= 0 or periods < 1:
        return None
    return _fin((new / old) ** (1 / periods) - 1)


def _r(x, d=4):
    return None if x is None else round(x, d)


def _days(newer: str, older: str) -> int:
    return (datetime.strptime(newer, "%Y-%m-%d") - datetime.strptime(older, "%Y-%m-%d")).days


def _pct(x, d=1):
    return "n/a" if x is None else f"{x * 100:.{d}f}%"


def _mult(x, d=1):
    return "n/a" if x is None else f"{x:.{d}f}x"


def _money(v, cur):
    if v is None:
        return "n/a"
    a, sign = abs(v), "-" if v < 0 else ""
    for lim, suf in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if a >= lim:
            return f"{sign}{cur or ''} {a / lim:.2f}{suf}".replace("  ", " ").strip()
    return f"{sign}{cur or ''} {a:.2f}".strip()


# ---------- 1. statements -> one record per fiscal year ----------
def _norm(name) -> str:
    """'Total Revenue' and 'TotalRevenue' must match: newer yfinance versions drop the spaces."""
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def _lookup(table: Optional[dict], aliases: list[str], date: str):
    if not table or date not in table.get("columns", []):
        return None
    i = table["columns"].index(date)
    by_item = {_norm(r["item"]): r["values"] for r in table.get("rows", [])}
    for name in aliases:
        vals = by_item.get(_norm(name))
        if vals is not None and i < len(vals) and vals[i] is not None:
            return _fin(float(vals[i]))
    return None


def extract_years(statements: dict, limit: int = HISTORY_YEARS) -> list[dict]:
    """Newest first. Columns that hold no usable data at all are dropped."""
    dates = set()
    for tb in statements.values():
        dates.update(tb.get("columns", []))
    years = []
    for d in sorted(dates, reverse=True):
        rec = {"date": d, "year": d[:4], "label": f"FY{d[:4]}"}
        for key, (stmt, aliases) in ITEMS.items():
            rec[key] = _lookup(statements.get(stmt), aliases, d)
        if rec["revenue"] is None and rec["total_assets"] is None and rec["net_income"] is None:
            continue
        years.append(rec)
    return years[:limit]


# ---------- 2. ratios ----------
def add_ratios(years: list[dict]) -> None:
    """Adds ratios and year-on-year growth to each record, in place."""
    for i, y in enumerate(years):
        eq_ok = y["equity"] is not None and y["equity"] > 0
        y["fcf_reported"] = y["free_cash_flow"]
        if y["free_cash_flow"] is None and y["operating_cash_flow"] is not None and y["capex"] is not None:
            y["free_cash_flow"] = y["operating_cash_flow"] - abs(y["capex"])
        ie = y["interest_expense"]
        y.update({
            "gross_margin": _div(y["gross_profit"], y["revenue"]),
            "operating_margin": _div(y["operating_income"], y["revenue"]),
            "net_margin": _div(y["net_income"], y["revenue"]),
            "roe": _div(y["net_income"], y["equity"]) if eq_ok else None,
            "roa": _div(y["net_income"], y["total_assets"]),
            "debt_to_equity": _div(y["total_debt"], y["equity"]) if eq_ok else None,
            "current_ratio": _div(y["current_assets"], y["current_liabilities"]),
            "interest_coverage": _div(y["operating_income"], abs(ie)) if ie else None,
            "net_debt": None if y["total_debt"] is None or y["cash"] is None else y["total_debt"] - y["cash"],
            "fcf_margin": _div(y["free_cash_flow"], y["revenue"]),
        })
        older = years[i + 1] if i + 1 < len(years) else None
        consecutive = older is not None and 330 <= _days(y["date"], older["date"]) <= 400
        for k in ("revenue", "net_income", "eps"):
            y[f"{k}_growth"] = _growth(y[k], older[k]) if consecutive else None


def compute_trend(years: list[dict]) -> dict:
    new, old = years[0], years[-1]
    n = len(years) - 1
    contiguous = all(330 <= _days(a["date"], b["date"]) <= 400 for a, b in zip(years, years[1:]))
    out = {"periods": n, "from": old["label"], "to": new["label"], "contiguous": contiguous,
           "revenue_cagr": None, "net_income_cagr": None, "net_margin_change_pp": None,
           "revenue_up_years": None}
    if n >= 1 and contiguous:
        out["revenue_cagr"] = _r(_cagr(new["revenue"], old["revenue"], n))
        out["net_income_cagr"] = _r(_cagr(new["net_income"], old["net_income"], n))
        gs = [y["revenue_growth"] for y in years[:-1] if y["revenue_growth"] is not None]
        out["revenue_up_years"] = {"up": sum(g > 0 for g in gs), "of": len(gs)}
    if n >= 1 and new["net_margin"] is not None and old["net_margin"] is not None:
        out["net_margin_change_pp"] = _r((new["net_margin"] - old["net_margin"]) * 100, 2)
    return out


def compute_valuation(latest: dict, price: Optional[float], profile: dict) -> dict:
    eps, eq = latest["eps"], latest["equity"]
    pe = _fin(price / eps) if price and eps and eps > 0 else None
    mcap = profile.get("market_cap") or (price * latest["shares"] if price and latest["shares"] else None)
    pb = _fin(mcap / eq) if mcap and eq and eq > 0 else None
    return {"pe": _r(pe, 2), "pb": _r(pb, 2), "roe": _r(latest["roe"]),
            "market_cap": mcap, "eps_used": eps,
            "provider": {"pe": profile.get("trailing_pe"), "pb": profile.get("price_to_book"),
                         "roe": profile.get("return_on_equity")}}


# ---------- 3. data quality ----------
def check_quality(years, valuation, profile, price, today=None) -> dict:
    issues = []

    def add(sev, code, msg, year=None):
        issues.append({"severity": sev, "code": code, "message": msg, "year": year})

    financial = "financial" in (profile.get("sector") or "").lower()
    today = today or datetime.now(timezone.utc).date()
    latest = years[0]

    # missing information
    for key, label in LABELS.items():
        if financial and key in FINANCIAL_NA:
            continue
        have = [y["label"] for y in years if y[key] is not None]
        if not have:
            add("error" if key in CORE_ITEMS else "warning", "missing_item",
                f"{label} is not available for any year.")
        elif len(have) < len(years):
            miss = [y["label"] for y in years if y[key] is None]
            add("info", "partial_item", f"{label} is missing for {', '.join(miss)}.")

    if len(years) < 3:
        add("warning", "short_history",
            f"Only {len(years)} annual period(s) available, so trends are limited.")
    if (today - datetime.strptime(latest["date"], "%Y-%m-%d").date()).days > STALE_DAYS:
        add("warning", "stale_statements",
            f"Latest annual statements are for the year ended {latest['date']} (over 15 months old).")
    for a, b in zip(years, years[1:]):
        if not 330 <= _days(a["date"], b["date"]) <= 400:
            add("info", "period_gap",
                f"{b['label']} to {a['label']} is not a one-year gap; growth for {a['label']} was not calculated.", a["label"])

    # inconsistent numbers, checked year by year
    for y in years:
        lab = y["label"]
        if y["revenue"] is not None and y["revenue"] < 0:
            add("error", "negative_revenue", f"Revenue is negative in {lab}.", lab)
        if y["gross_profit"] is not None and y["revenue"] is not None and y["gross_profit"] > y["revenue"]:
            add("error", "gross_profit_above_revenue", f"Gross profit is higher than revenue in {lab}.", lab)
        if y["revenue"] and y["revenue"] > 0 and y["net_income"] is not None and y["net_income"] > y["revenue"]:
            add("warning", "net_income_above_revenue",
                f"Net income is higher than revenue in {lab} (one-off gain or data error).", lab)
        if y["total_assets"] is not None and y["total_assets"] <= 0:
            add("error", "non_positive_assets", f"Total assets are zero or negative in {lab}.", lab)
        if y["total_debt"] is not None and y["total_debt"] < 0:
            add("error", "negative_debt", f"Total debt is negative in {lab}.", lab)
        if None not in (y["total_assets"], y["total_liabilities"], y["total_equity_gross"]) and y["total_assets"] > 0:
            gap = abs(y["total_assets"] - y["total_liabilities"] - y["total_equity_gross"])
            if gap > 0.01 * y["total_assets"]:
                add("warning", "balance_sheet_mismatch",
                    f"Assets do not equal liabilities plus equity in {lab} (off by {_pct(gap / y['total_assets'])}).", lab)
        if None not in (y["fcf_reported"], y["operating_cash_flow"], y["capex"]):
            expected = y["operating_cash_flow"] - abs(y["capex"])
            if abs(y["fcf_reported"] - expected) > 0.02 * max(abs(y["operating_cash_flow"]), 1):
                add("warning", "fcf_mismatch",
                    f"Reported free cash flow differs from operating cash flow minus capex in {lab}.", lab)

    if latest["equity"] is not None and latest["equity"] <= 0:
        add("warning", "negative_equity",
            "Shareholders' equity is zero or negative, so ROE, P/B and debt-to-equity are not meaningful.")
    if latest["eps"] is not None and latest["eps"] <= 0:
        add("info", "loss_making", "EPS is zero or negative, so P/E is not meaningful.")
    if price is None:
        add("warning", "no_price", "Latest price is unavailable, so P/E and P/B could not be calculated.")

    # our numbers vs the provider's own ratios
    prov = valuation["provider"]
    for name, mine, theirs, tol, why in (
        ("P/E", valuation["pe"], prov["pe"], PE_TOL, "the provider uses trailing-twelve-month earnings, we use the latest annual EPS"),
        ("P/B", valuation["pb"], prov["pb"], PB_TOL, "the provider uses the most recent quarter's book value"),
        ("ROE", valuation["roe"], prov["roe"], ROE_TOL, "the provider uses trailing-twelve-month earnings"),
    ):
        if mine is None or theirs in (None, 0):
            continue
        diff = abs(mine - theirs) / abs(theirs)
        if diff > tol:
            fmt = (lambda v: _pct(v)) if name == "ROE" else (lambda v: f"{v:.2f}")
            add("warning", "provider_mismatch",
                f"{name}: calculated {fmt(mine)} vs provider {fmt(theirs)} ({diff * 100:.0f}% apart). Common cause: {why}.")

    errs = sum(i["severity"] == "error" for i in issues)
    warns = sum(i["severity"] == "warning" for i in issues)
    core_ok = all(latest[k] is not None for k in CORE_ITEMS)
    return {"issues": issues, "is_reliable": errs == 0 and core_ok,
            "confidence": "low" if errs or not core_ok else "medium" if warns else "high",
            "counts": {"error": errs, "warning": warns, "info": len(issues) - errs - warns}}


# ---------- 4. written assessment ----------
def _sec(rating, headline, points):
    return {"rating": rating, "headline": headline, "points": points}


def _sec_revenue(ys, trend, cur):
    y = ys[0]
    if y["revenue"] is None:
        return _sec("unknown", "Revenue data is not available.", [])
    g, ng = y["revenue_growth"], y["net_income_growth"]
    pts = [f"Revenue in {y['label']} was {_money(y['revenue'], cur)}"
           + (f", {'up' if g >= 0 else 'down'} {_pct(abs(g))} on the previous year." if g is not None else ".")]
    if trend["revenue_cagr"] is not None:
        pts.append(f"Over {trend['periods']} years ({trend['from']} to {trend['to']}) revenue grew {_pct(trend['revenue_cagr'])} a year (CAGR).")
    if trend["revenue_up_years"]:
        u = trend["revenue_up_years"]
        pts.append(f"Revenue rose in {u['up']} of the last {u['of']} years.")
    if y["net_income"] is not None:
        pts.append(f"Net income was {_money(y['net_income'], cur)}"
                   + (f", {'up' if ng >= 0 else 'down'} {_pct(abs(ng))}." if ng is not None else "."))
    if trend["net_income_cagr"] is not None:
        pts.append(f"Net income CAGR over the same period: {_pct(trend['net_income_cagr'])}.")
    if g is None and ng is None:
        rating = "unknown"
    elif (g is not None and g < 0) or (ng is not None and ng < -0.2):
        rating = "negative"
    elif g is not None and g >= REV_GROWTH_STRONG and (ng is None or ng > 0):
        rating = "positive"
    else:
        rating = "neutral"
    head = (f"Revenue {'grew' if g >= 0 else 'fell'} {_pct(abs(g))} in {y['label']}." if g is not None
            else f"Revenue was {_money(y['revenue'], cur)} in {y['label']}; growth could not be calculated.")
    return _sec(rating, head, pts)


def _sec_profit(ys, trend):
    y = ys[0]
    nm = y["net_margin"]
    if nm is None:
        return _sec("unknown", "Profitability could not be calculated (revenue or net income missing).", [])
    pts = [f"Net margin was {_pct(nm)}: the company kept {nm * 100:.1f} of every 100 of revenue as profit."]
    if y["gross_margin"] is not None:
        pts.append(f"Gross margin {_pct(y['gross_margin'])}.")
    if y["operating_margin"] is not None:
        pts.append(f"Operating margin {_pct(y['operating_margin'])}.")
    if y["roe"] is not None:
        pts.append(f"Return on equity {_pct(y['roe'])} (net income / year-end equity).")
    if y["roa"] is not None:
        pts.append(f"Return on assets {_pct(y['roa'])}.")
    ch = trend["net_margin_change_pp"]
    if ch is not None and trend["periods"] >= 1:
        pts.append(f"Net margin {'improved' if ch >= 0 else 'fell'} by {abs(ch):.1f} percentage points from {trend['from']} to {trend['to']}.")
    rating = "negative" if nm < NET_MARGIN_THIN else "positive" if nm >= NET_MARGIN_HEALTHY else "neutral"
    word = "loss-making" if nm < 0 else "thin" if nm < NET_MARGIN_THIN else "healthy" if nm >= NET_MARGIN_HEALTHY else "moderate"
    return _sec(rating, f"Profitability is {word}, with a {_pct(nm)} net margin in {y['label']}.", pts)


def _sec_stability(ys, cur, financial):
    y = ys[0]
    if financial:
        pts = ["Debt-to-equity and current ratio are not meaningful for banks and other financial companies, so they are not rated here."]
        if y["roe"] is not None:
            pts.append(f"Return on equity was {_pct(y['roe'])}.")
        return _sec("unknown", "Balance-sheet strength needs bank-specific measures (capital adequacy, bad loans) that this data does not include.", pts)
    de, cr, ic, fcf = y["debt_to_equity"], y["current_ratio"], y["interest_coverage"], y["free_cash_flow"]
    pts, score, signals = [], 0, 0
    if de is not None:
        signals += 1
        level = "low" if de <= DEBT_EQUITY_LOW else "high" if de > DEBT_EQUITY_HIGH else "moderate"
        score += 1 if level == "low" else -1 if level == "high" else 0
        pts.append(f"Debt-to-equity is {_mult(de, 2)} ({level}); total debt {_money(y['total_debt'], cur)}.")
    elif y["total_debt"] is not None:
        pts.append(f"Total debt is {_money(y['total_debt'], cur)}; debt-to-equity could not be calculated.")
    if y["net_debt"] is not None:
        pts.append("The company holds more cash than debt (net cash " + _money(-y["net_debt"], cur) + ")." if y["net_debt"] < 0
                   else f"Net debt (debt minus cash) is {_money(y['net_debt'], cur)}.")
    if cr is not None:
        signals += 1
        score += 1 if cr >= CURRENT_RATIO_STRONG else -1 if cr < CURRENT_RATIO_WEAK else 0
        pts.append(f"Current ratio is {_mult(cr, 2)}: "
                   + ("short-term assets cover short-term bills comfortably." if cr >= CURRENT_RATIO_STRONG
                      else "short-term assets do not fully cover short-term bills." if cr < CURRENT_RATIO_WEAK
                      else "short-term bills are covered, with limited cushion."))
    if ic is not None:
        signals += 1
        score += 1 if ic >= COVERAGE_COMFORTABLE else -1 if ic < COVERAGE_WEAK else 0
        pts.append(f"Interest coverage is {_mult(ic)} (operating income / interest expense).")
    if fcf is not None:
        signals += 1
        score += 1 if fcf > 0 else -1
        pts.append(f"Free cash flow was {_money(fcf, cur)}" + (f" ({_pct(y['fcf_margin'])} of revenue)." if y["fcf_margin"] is not None else "."))
    if not signals:
        return _sec("unknown", "Not enough balance-sheet data to judge financial stability.", pts)
    rating = "positive" if score >= 2 else "negative" if score <= -1 else "neutral"
    word = {"positive": "looks strong", "neutral": "looks adequate", "negative": "shows some strain"}[rating]
    return _sec(rating, f"Financial stability {word} in {y['label']}.", pts)


def _sec_valuation(val, price, cur):
    pts = []
    if val["pe"] is not None:
        pts.append(f"P/E is {val['pe']:.1f}: investors pay about {val['pe']:.0f} for each 1 of annual earnings (latest annual EPS).")
    if val["pb"] is not None:
        pts.append(f"P/B is {val['pb']:.2f}: the market values the company at {val['pb']:.2f} times its book value.")
    if val["roe"] is not None:
        pts.append(f"ROE is {_pct(val['roe'])}.")
    if not pts:
        return _sec("unknown", "Valuation ratios could not be calculated with the available data.", [])
    pts.append("A ratio is only meaningful against peers or the company's own history. No buy or sell view is given.")
    parts = [f"P/E {val['pe']:.1f}" if val["pe"] is not None else None, f"P/B {val['pb']:.2f}" if val["pb"] is not None else None]
    return _sec("neutral", "Valuation: " + ", ".join(p for p in parts if p) + ".", pts)


# ---------- 5. peers ----------
RATIO_KEYS = ["gross_margin", "operating_margin", "net_margin", "roe", "roa", "debt_to_equity",
              "current_ratio", "interest_coverage", "net_debt", "fcf_margin",
              "revenue_growth", "net_income_growth", "eps_growth"]
PEER_METRICS = [("revenue_growth", "Revenue growth", "pct"), ("net_margin", "Net margin", "pct"),
                ("roe", "ROE", "pct"), ("debt_to_equity", "Debt to equity", "x"),
                ("pe", "P/E", "x"), ("pb", "P/B", "x")]


def snapshot(report: dict) -> dict:
    y = report["history"][0]
    return {"ticker": report["ticker"], "company_name": report["company_name"], "fiscal_year": y["label"],
            "revenue_growth": y["revenue_growth"], "net_margin": y["net_margin"], "roe": y["roe"],
            "debt_to_equity": y["debt_to_equity"], "pe": report["valuation"]["pe"], "pb": report["valuation"]["pb"]}


def compare_peers(subject: dict, peers: list[dict], unavailable: list[dict]) -> dict:
    if not peers:
        reason = ("No peer tickers were given. Add peers to compare." if not unavailable
                  else "None of the peers had usable data.")
        return {"available": False, "reason": reason, "unavailable": unavailable}
    metrics = []
    for key, label, kind in PEER_METRICS:
        vals = [p[key] for p in peers if p[key] is not None]
        med = statistics.median(vals) if vals else None
        mine = subject[key]
        pos = None
        if mine is not None and med is not None:
            pos = "in line" if abs(mine - med) <= 0.05 * max(abs(med), 1e-9) else "above" if mine > med else "below"
        metrics.append({"key": key, "label": label, "kind": kind, "subject": _r(mine),
                        "peer_median": _r(med), "position": pos, "peers_with_data": len(vals)})
    return {"available": True, "companies": [subject] + peers, "metrics": metrics, "unavailable": unavailable,
            "note": "Peers may have different fiscal year ends and business mixes. Above or below the median is not a good-or-bad verdict."}


# ---------- 6. build the report (pure, no network) ----------
def build_report(ticker, market, statements, profile, price, price_date=None, today=None) -> dict:
    years = extract_years(statements)
    if not years:
        raise md.DataUnavailable(f"No usable annual financial statements for '{ticker}'.")
    add_ratios(years)
    trend = compute_trend(years)
    cur = profile.get("currency")
    financial = "financial" in (profile.get("sector") or "").lower()
    val = compute_valuation(years[0], price, profile)
    val.update({"price": price, "price_date": price_date})
    quality = check_quality(years, val, profile, price, today)

    sections = {
        "revenue_earnings": _sec_revenue(years, trend, cur),
        "profitability": _sec_profit(years, trend),
        "financial_stability": _sec_stability(years, cur, financial),
        "valuation": _sec_valuation(val, price, cur),
    }
    name = profile.get("company_name") or ticker
    overall = " ".join([f"{name}, {years[0]['label']} (year ended {years[0]['date']}):"]
                       + [s["headline"] for s in sections.values()])
    if quality["confidence"] != "high":
        overall += f" Data confidence is {quality['confidence']}; see the data quality notes."

    history = []
    for y in years:
        row = {"date": y["date"], "label": y["label"]}
        row.update({k: y[k] for k in ITEMS})
        row.update({k: _r(y[k], 4) for k in RATIO_KEYS})
        history.append(row)
    return {
        "agent": "fundamental", "ticker": ticker, "market": market,
        "company_name": profile.get("company_name"), "sector": profile.get("sector"), "currency": cur,
        "fiscal_year": years[0]["label"], "generated_at": datetime.now(timezone.utc).isoformat(),
        "assessment": {"overall": overall, "sections": sections},
        "valuation": val, "trend": trend, "history": history,
        "peers": {"available": False, "reason": "No peer tickers were given. Add peers to compare.", "unavailable": []},
        "data_quality": quality,
        "limitations": [
            "Annual statements only; the newest quarter is not included.",
            "ROE and P/B use year-end figures, not averages.",
            "Thresholds (margins, debt, liquidity) are general rules of thumb and vary by industry.",
            "Statement currency can differ from the trading currency for some foreign-listed companies.",
            "This is an analysis aid, not investment advice.",
        ],
        "meta": {"provider": md.PROVIDER, "retrieved_at": datetime.now(timezone.utc).isoformat(),
                 "content_hash": md.sha256_of(history)},
    }


# ---------- 7. entry point (uses the market data service) ----------
def _load(ticker: str):
    st = md.get_statements(ticker, "annual")
    try:
        profile = md.get_profile(ticker)["profile"]
    except md.MarketDataError:
        profile = {}
    price = price_date = None
    try:
        h = md.get_history(ticker, "1y")
        price, price_date = float(h.df["Close"].iloc[-1]), h.df.index[-1].strftime("%Y-%m-%d")
    except md.MarketDataError:
        pass
    return st, profile, price, price_date


def _report_for(ticker, market):
    st, profile, price, price_date = _load(ticker)
    rep = build_report(ticker, market, st["statements"], profile, price, price_date)
    rep["meta"]["source_url"] = st["meta"]["source_url"]
    return rep


def analyze(ticker: str, market: str, peers: Optional[list[str]] = None) -> dict:
    """Raises market_data.DataUnavailable / ProviderError for the main ticker. A peer that fails is
    listed under peers.unavailable and never breaks the report."""
    report = _report_for(ticker, market)
    snaps, unavailable = [], []
    for p in [p for p in dict.fromkeys(peers or []) if p != ticker][:MAX_PEERS]:
        try:
            snaps.append(snapshot(_report_for(p, market)))
        except md.MarketDataError as e:
            unavailable.append({"ticker": p, "reason": str(e)})
    if peers:
        report["peers"] = compare_peers(snapshot(report), snaps, unavailable)
    return report
