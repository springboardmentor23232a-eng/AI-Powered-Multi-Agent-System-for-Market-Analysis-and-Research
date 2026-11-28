"""Turns the Yahoo statements the app already collects into the agent's inputs."""
from .errors import Reason

# agent field -> (which statement, Yahoo row names to try in order)
FIELD_MAP = {
    "revenue": ("income_statement", ["Total Revenue", "Operating Revenue"]),
    "gross_profit": ("income_statement", ["Gross Profit"]),
    "net_income": ("income_statement", ["Net Income", "Net Income Common Stockholders"]),
    "ebitda": ("income_statement", ["EBITDA", "Normalized EBITDA"]),
    "operating_cash_flow": ("cash_flow", ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"]),
    "current_assets": ("balance_sheet", ["Current Assets", "Total Current Assets"]),
    "current_liabilities": ("balance_sheet", ["Current Liabilities", "Total Current Liabilities"]),
    "total_debt": ("balance_sheet", ["Total Debt"]),
    "equity": ("balance_sheet", ["Stockholders Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"]),
    "total_assets": ("balance_sheet", ["Total Assets"]),
}
STATEMENT_NAME = {"income_statement": "income statement", "balance_sheet": "balance sheet", "cash_flow": "cash flow statement"}
BANK_HINT = " This is typical for banks and insurers, whose statements are structured differently and were not part of the model's training."
BANK_FIELDS = {"gross_profit", "current_assets", "current_liabilities"}


def _row(statement, names):
    for name in names:
        for row in statement["rows"]:
            if row["item"] == name:
                return name, row["values"]
    return None, None


def raw_from_yahoo(fin: dict):
    """Returns (raw_inputs, reasons). If reasons is not empty, raw_inputs is None."""
    reasons = []
    for key, label in STATEMENT_NAME.items():
        st = fin.get(key)
        if not st or not st.get("available"):
            reasons.append(Reason("statement_unavailable", key,
                                  f"Yahoo Finance returned no annual {label} for this company, so it cannot be analysed."))
    if reasons:
        return None, reasons

    # the three statements must describe the same financial year
    latest = {k: fin[k]["periods"][0] for k in STATEMENT_NAME if fin[k]["periods"]}
    if len(set(latest.values())) > 1:
        reasons.append(Reason("period_mismatch", None,
                              "The statements are for different financial years: "
                              + ", ".join(f"{STATEMENT_NAME[k]} {v}" for k, v in latest.items()) + "."))
        return None, reasons

    raw = {}
    for field, (stmt, names) in FIELD_MAP.items():
        _, values = _row(fin[stmt], names)
        if not values or values[0] is None:
            hint = BANK_HINT if field in BANK_FIELDS else ""
            reasons.append(Reason("not_reported", field,
                                  f"Yahoo Finance does not report '{names[0]}' for this company's latest year.{hint}"))
        else:
            raw[field] = values[0]
        if field == "revenue" and values:
            if len(values) > 1 and values[1] is not None:
                raw["prev_revenue"] = values[1]
            else:
                reasons.append(Reason("not_reported", "prev_revenue",
                                      "Previous-year revenue is not available, so revenue growth cannot be computed."))
        if field == "net_income" and values and len(values) > 1 and values[1] is not None:
            raw["prev_net_income"] = values[1]  # optional, only used in the explanation
    return (None, reasons) if reasons else (raw, [])
