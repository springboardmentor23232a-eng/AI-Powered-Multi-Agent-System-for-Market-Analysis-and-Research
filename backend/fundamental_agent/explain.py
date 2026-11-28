"""Plain-language explanation of the numbers (rules, not the KNN)."""


def money(x, currency=None, unit=1.0):
    v = float(x) * unit
    sign = "-" if v < 0 else ""
    v = abs(v)
    for size, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if v >= size:
            text = f"{v / size:,.2f}{suffix}"
            break
    else:
        text = f"{v:,.0f}"
    return f"{sign}{text}" + (f" {currency}" if currency else "")


def _growth_word(g):
    if g >= 15:
        return "strong growth"
    if g >= 5:
        return "solid growth"
    if g >= 0:
        return "modest growth"
    return "a decline"


def _margin_word(m):
    if m >= 20:
        return "very strong"
    if m >= 10:
        return "healthy"
    if m >= 0:
        return "thin"
    return "negative (the company lost money)"


def build_explanation(raw, f, label, neighbours, k, currency=None, unit=1.0):
    m = lambda x: money(x, currency, unit)
    out = {}

    g = f["rev_growth"]
    out["revenue_growth"] = (
        f"Revenue {'grew' if g >= 0 else 'fell'} {abs(g):.1f}% year over year, from "
        f"{m(raw['prev_revenue'])} to {m(raw['revenue'])}. That is {_growth_word(g)}."
    )

    ni, prev = raw["net_income"], raw.get("prev_net_income")
    if prev is None:
        out["earnings"] = f"Net income was {m(ni)}, a net margin of {f['net_margin']:.1f}%."
    elif prev > 0 and ni > 0:
        ch = (ni / prev - 1) * 100
        out["earnings"] = (f"Net income {'rose' if ch >= 0 else 'fell'} {abs(ch):.1f}% to {m(ni)} "
                           f"(previous year {m(prev)}).")
    elif prev > 0 >= ni:
        out["earnings"] = f"Net income swung from a profit of {m(prev)} to a loss of {m(abs(ni))}."
    elif prev <= 0 < ni:
        out["earnings"] = f"The company returned to profit: net income was {m(ni)} after a loss of {m(abs(prev))}."
    else:
        word = "narrowed" if ni > prev else "widened"
        out["earnings"] = f"The loss {word}: net income was {m(ni)} (previous year {m(prev)})."

    out["profitability"] = (
        f"Net margin is {f['net_margin']:.1f}%, which is {_margin_word(f['net_margin'])}. "
        f"Gross margin is {f['gross_margin']:.1f}% and EBITDA margin {f['ebitda_margin']:.1f}%. "
        f"Return on assets is {f['roa']:.1f}%."
    )

    ocf = f["ocf_margin"]
    if ocf < 0:
        cash = f"The business used cash in its operations: operating cash flow is {ocf:.1f}% of revenue."
    elif ni <= 0:
        cash = (f"Operating cash flow is positive ({ocf:.1f}% of revenue) even though the company reported a loss, "
                "so the loss is partly non-cash.")
    elif ocf >= f["net_margin"]:
        cash = f"Operating cash flow is {ocf:.1f}% of revenue, so cash generation supports the reported profit."
    else:
        cash = (f"Operating cash flow is {ocf:.1f}% of revenue, weaker than the {f['net_margin']:.1f}% net margin, "
                "which deserves a closer look.")
    out["cash_flow"] = cash

    cr = f["current_ratio"]
    word = "comfortable" if cr >= 1.5 else ("adequate" if cr >= 1 else
                                            "below 1, so short-term obligations exceed short-term assets")
    out["liquidity"] = f"The current ratio is {cr:.2f}, which is {word}."

    if raw["equity"] <= 0:
        out["leverage"] = ("Shareholders' equity is zero or negative, so debt-to-equity is not meaningful. "
                           "It is treated as very high leverage.")
    else:
        de = f["debt_equity"]
        word = "low" if de < 0.5 else ("moderate" if de <= 1.5 else "high")
        out["leverage"] = f"Debt-to-equity is {de:.2f}, which is {word}."

    votes = sum(1 for n in neighbours if n["label"] == label)
    close = ", ".join(f"{n['Company']} {n['Year']} ({n['label']})" for n in neighbours[:3])
    out["overall"] = (
        f"Overall financial condition: {label}. {votes} of the {k} most similar company-years in the "
        f"training data were {label}. Closest matches: {close}."
    )
    return out
