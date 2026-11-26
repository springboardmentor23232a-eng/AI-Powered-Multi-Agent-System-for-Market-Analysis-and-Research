"""Financial ratio calculations (Milestone 2). Each ratio returns its value AND how it was computed, so the report can
distinguish calculated metrics from reported facts. A ratio is None (with a reason) when its inputs are missing."""


def _ok(*xs) -> bool:
    return all(x is not None for x in xs)


def safe_div(a, b):
    return a / b if _ok(a, b) and b != 0 else None


def pct_change(new, old):
    if not _ok(new, old) or old == 0:
        return None
    return (new - old) / abs(old)


def cagr(first, last_, years: float):
    if not _ok(first, last_) or first <= 0 or last_ <= 0 or years <= 0:
        return None
    return (last_ / first) ** (1 / years) - 1


def ratio(name: str, value, formula: str, inputs: dict, reason: str | None = None) -> dict:
    return {"name": name, "value": value, "formula": formula, "inputs": inputs,
            "kind": "calculated", "reason_unavailable": None if value is not None else (reason or "Required inputs are missing.")}


def compute_ratios(m: dict[str, list], price: float | None = None, price_is_reliable: bool = False) -> dict[str, dict]:
    """`m` = per-period metric lists (oldest -> newest), keys: revenue, gross_profit, operating_income, net_income,
    total_assets, total_debt, equity, operating_cash_flow, free_cash_flow, eps, shares_outstanding, plus any
    `reported_*` values from a dataset. Uses the LATEST period unless stated."""
    def at(key, i=-1):
        s = m.get(key) or []
        return s[i] if s and -len(s) <= i < len(s) else None

    rev, rev_prev = at("revenue"), at("revenue", -2)
    ni, eq, assets, debt = at("net_income"), at("equity"), at("total_assets"), at("total_debt")
    eq_prev = at("equity", -2)
    eps, shares = at("eps"), at("shares_outstanding")
    out: dict[str, dict] = {}

    out["revenue_growth_yoy"] = ratio("Revenue growth (YoY)", pct_change(rev, rev_prev), "(revenue - previous revenue) / |previous revenue|",
                                      {"revenue": rev, "previous_revenue": rev_prev})
    n_periods = len([v for v in (m.get("revenue") or []) if v is not None])
    first_rev = next((v for v in (m.get("revenue") or []) if v is not None), None)
    out["revenue_cagr"] = ratio("Revenue CAGR (all periods)", cagr(first_rev, rev, n_periods - 1), "(latest / first)^(1/years) - 1",
                                {"first_revenue": first_rev, "latest_revenue": rev, "years": n_periods - 1})
    out["net_income_growth_yoy"] = ratio("Net income growth (YoY)", pct_change(ni, at("net_income", -2)),
                                         "(net income - previous) / |previous|", {"net_income": ni, "previous_net_income": at("net_income", -2)})
    out["gross_margin"] = ratio("Gross margin", safe_div(at("gross_profit"), rev), "gross profit / revenue",
                                {"gross_profit": at("gross_profit"), "revenue": rev})
    out["operating_margin"] = ratio("Operating margin", safe_div(at("operating_income"), rev), "operating income / revenue",
                                    {"operating_income": at("operating_income"), "revenue": rev})
    out["net_margin"] = ratio("Net profit margin", safe_div(ni, rev), "net income / revenue", {"net_income": ni, "revenue": rev})
    avg_eq = (eq + eq_prev) / 2 if _ok(eq, eq_prev) else eq
    out["roe"] = ratio("Return on equity (ROE)", safe_div(ni, avg_eq) if avg_eq and avg_eq > 0 else None,
                       "net income / average shareholders' equity (latest equity if only one period)",
                       {"net_income": ni, "average_equity": avg_eq}, "Equity is missing or not positive.")
    out["roa"] = ratio("Return on assets (ROA)", safe_div(ni, assets), "net income / total assets", {"net_income": ni, "total_assets": assets})
    d_e = safe_div(debt, eq) if eq and eq > 0 else None
    if d_e is None and m.get("reported_debt_to_equity"):
        d_e = at("reported_debt_to_equity")
        out["debt_to_equity"] = ratio("Debt-to-equity", d_e, "as reported by the dataset", {"reported_debt_to_equity": d_e})
        out["debt_to_equity"]["kind"] = "reported"
    else:
        out["debt_to_equity"] = ratio("Debt-to-equity", d_e, "total debt / shareholders' equity", {"total_debt": debt, "equity": eq},
                                      "Debt or positive equity is missing.")
    cr = at("reported_current_ratio")
    out["current_ratio"] = ratio("Current ratio", cr, "as reported by the dataset (current assets / current liabilities)", {"reported": cr},
                                 "Current assets/liabilities are not in the data source.")
    if cr is not None:
        out["current_ratio"]["kind"] = "reported"
    out["free_cash_flow_margin"] = ratio("Free cash flow margin", safe_div(at("free_cash_flow"), rev), "free cash flow / revenue",
                                         {"free_cash_flow": at("free_cash_flow"), "revenue": rev})
    out["cash_conversion"] = ratio("Operating cash flow / net income", safe_div(at("operating_cash_flow"), ni) if ni and ni > 0 else None,
                                   "operating cash flow / net income (net income > 0)", {"operating_cash_flow": at("operating_cash_flow"), "net_income": ni})

    # valuation needs a market price: only computed when the price is in the same currency and not synthetic
    why = None if price_is_reliable else "Price is synthetic demo data or in a different currency than the financials, so valuation is not computed."
    pe = safe_div(price, eps) if price_is_reliable and eps and eps > 0 else None
    out["pe"] = ratio("Price / earnings (P/E)", pe, "latest close / earnings per share", {"price": price, "eps": eps},
                      why or "EPS is missing or not positive.")
    bvps = safe_div(eq, shares)
    pb = safe_div(price, bvps) if price_is_reliable and bvps and bvps > 0 else None
    out["pb"] = ratio("Price / book (P/B)", pb, "latest close / (equity / shares outstanding)",
                      {"price": price, "equity": eq, "shares_outstanding": shares}, why or "Equity or shares outstanding is missing.")
    return out
