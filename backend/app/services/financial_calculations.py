from typing import Any, Dict, List, Optional, Sequence


def _safe_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        f = float(val)
        if f != f:  # NaN check
            return None
        return f
    except (TypeError, ValueError):
        return None


def _round_opt(val: Optional[float], digits: int = 2) -> Optional[float]:
    if val is None:
        return None
    return round(val, digits)


def extract_statement_series(
    statement: Dict[str, Any],
    candidate_keys: Sequence[str],
) -> List[Optional[float]]:
    """Return the first matching metric row aligned with statement['periods']."""
    rows = (statement or {}).get("rows") or {}
    periods = (statement or {}).get("periods") or []
    for key in candidate_keys:
        if key in rows:
            vals = rows[key]
            if any(v is not None for v in vals):
                return [_safe_float(v) for v in vals]
    # Case-insensitive fallback
    lower_map = {k.lower(): v for k, v in rows.items()}
    for key in candidate_keys:
        if key.lower() in lower_map:
            vals = lower_map[key.lower()]
            if any(v is not None for v in vals):
                return [_safe_float(v) for v in vals]
    return [None] * len(periods)


def get_period_value(series: Sequence[Optional[float]], index: int = 0) -> Optional[float]:
    if index < len(series):
        return _safe_float(series[index])
    return None


def compute_growth_pct(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    if current is None or previous is None or previous == 0:
        return None
    return round(((current - previous) / abs(previous)) * 100.0, 2)


def compute_cagr_pct(
    latest: Optional[float],
    earliest: Optional[float],
    years: int,
) -> Optional[float]:
    if latest is None or earliest is None or years <= 0:
        return None
    if latest <= 0 or earliest <= 0:
        return None
    return round((((latest / earliest) ** (1.0 / years)) - 1.0) * 100.0, 2)


def compute_margin_pct(numerator: Optional[float], revenue: Optional[float]) -> Optional[float]:
    if numerator is None or revenue is None or revenue <= 0:
        return None
    return round((numerator / revenue) * 100.0, 2)


def compute_pe_ratio(
    current_price: Optional[float],
    diluted_eps: Optional[float],
    market_cap: Optional[float] = None,
    net_income: Optional[float] = None,
    provider_pe: Optional[float] = None,
) -> Dict[str, Any]:
    """Compute Price-to-Earnings ratio with transparent provenance and edge-case handling."""
    price = _safe_float(current_price)
    eps = _safe_float(diluted_eps)
    mcap = _safe_float(market_cap)
    ni = _safe_float(net_income)
    fallback = _safe_float(provider_pe)

    if price is not None and price > 0 and eps is not None:
        if eps > 0:
            return {
                "value": round(price / eps, 2),
                "formula": "Current Price / Diluted EPS",
                "inputs_used": {"current_price": round(price, 2), "diluted_eps": round(eps, 4)},
                "status": "COMPUTED",
                "note": "Computed directly from market price and latest diluted EPS.",
            }
        return {
            "value": None,
            "formula": "Current Price / Diluted EPS",
            "inputs_used": {"current_price": round(price, 2), "diluted_eps": round(eps, 4)},
            "status": "UNAVAILABLE",
            "note": "P/E ratio is not meaningful because Diluted EPS is zero or negative.",
        }

    if mcap is not None and mcap > 0 and ni is not None and ni > 0:
        return {
            "value": round(mcap / ni, 2),
            "formula": "Market Capitalization / Net Income",
            "inputs_used": {"market_cap": mcap, "net_income": ni},
            "status": "COMPUTED",
            "note": "Computed from Market Cap and Net Income.",
        }

    if fallback is not None and fallback > 0:
        return {
            "value": round(fallback, 2),
            "formula": "Provider Trailing P/E",
            "inputs_used": {"provider_trailing_pe": round(fallback, 2)},
            "status": "PROVIDER_FALLBACK",
            "note": "Using provider-reported trailing P/E because EPS inputs were incomplete.",
        }

    return {
        "value": None,
        "formula": "Current Price / Diluted EPS",
        "inputs_used": {},
        "status": "UNAVAILABLE",
        "note": "Insufficient earnings or price data to compute P/E ratio.",
    }


def compute_pb_ratio(
    market_cap: Optional[float],
    stockholders_equity: Optional[float],
    current_price: Optional[float] = None,
    book_value_per_share: Optional[float] = None,
    provider_pb: Optional[float] = None,
) -> Dict[str, Any]:
    """Compute Price-to-Book ratio with negative-equity protection."""
    mcap = _safe_float(market_cap)
    equity = _safe_float(stockholders_equity)
    price = _safe_float(current_price)
    bvps = _safe_float(book_value_per_share)
    fallback = _safe_float(provider_pb)

    if mcap is not None and mcap > 0 and equity is not None:
        if equity > 0:
            return {
                "value": round(mcap / equity, 2),
                "formula": "Market Capitalization / Stockholders Equity",
                "inputs_used": {"market_cap": mcap, "stockholders_equity": equity},
                "status": "COMPUTED",
                "note": "Computed from Market Cap and latest Total Stockholders' Equity.",
            }
        return {
            "value": None,
            "formula": "Market Capitalization / Stockholders Equity",
            "inputs_used": {"market_cap": mcap, "stockholders_equity": equity},
            "status": "UNAVAILABLE",
            "note": "P/B ratio is not meaningful due to zero or negative stockholders' equity.",
        }

    if price is not None and price > 0 and bvps is not None and bvps > 0:
        return {
            "value": round(price / bvps, 2),
            "formula": "Current Price / Book Value Per Share",
            "inputs_used": {"current_price": round(price, 2), "book_value_per_share": round(bvps, 2)},
            "status": "COMPUTED",
            "note": "Computed from Current Price and Book Value Per Share.",
        }

    if fallback is not None and fallback > 0:
        return {
            "value": round(fallback, 2),
            "formula": "Provider Price/Book",
            "inputs_used": {"provider_pb": round(fallback, 2)},
            "status": "PROVIDER_FALLBACK",
            "note": "Using provider-reported Price/Book ratio.",
        }

    return {
        "value": None,
        "formula": "Market Capitalization / Stockholders Equity",
        "inputs_used": {},
        "status": "UNAVAILABLE",
        "note": "Insufficient balance sheet equity data to compute P/B ratio.",
    }


def compute_roe_pct(
    net_income: Optional[float],
    stockholders_equity: Optional[float],
    provider_roe: Optional[float] = None,
) -> Dict[str, Any]:
    """Compute Return on Equity (%) = (Net Income / Stockholders Equity) * 100."""
    ni = _safe_float(net_income)
    equity = _safe_float(stockholders_equity)
    fallback = _safe_float(provider_roe)

    if ni is not None and equity is not None:
        if equity > 0:
            return {
                "value": round((ni / equity) * 100.0, 2),
                "formula": "(Net Income / Stockholders Equity) * 100",
                "inputs_used": {"net_income": ni, "stockholders_equity": equity},
                "status": "COMPUTED",
                "note": "Computed directly from Net Income and Stockholders' Equity.",
            }
        return {
            "value": None,
            "formula": "(Net Income / Stockholders Equity) * 100",
            "inputs_used": {"net_income": ni, "stockholders_equity": equity},
            "status": "UNAVAILABLE",
            "note": "ROE is not meaningful due to zero or negative stockholders' equity.",
        }

    if fallback is not None:
        return {
            "value": round(fallback * 100.0, 2),
            "formula": "Provider Return on Equity",
            "inputs_used": {"provider_roe": fallback},
            "status": "PROVIDER_FALLBACK",
            "note": "Using provider-reported ROE.",
        }

    return {
        "value": None,
        "formula": "(Net Income / Stockholders Equity) * 100",
        "inputs_used": {},
        "status": "UNAVAILABLE",
        "note": "Insufficient income or equity data to compute ROE.",
    }


def compute_roa_pct(net_income: Optional[float], total_assets: Optional[float]) -> Optional[float]:
    ni = _safe_float(net_income)
    assets = _safe_float(total_assets)
    if ni is None or assets is None or assets <= 0:
        return None
    return round((ni / assets) * 100.0, 2)


def compute_stability_metrics(
    total_debt: Optional[float],
    cash_and_equivalents: Optional[float],
    stockholders_equity: Optional[float],
    current_assets: Optional[float],
    current_liabilities: Optional[float],
    inventory: Optional[float],
    operating_income: Optional[float],
    interest_expense: Optional[float],
    operating_cash_flow: Optional[float],
    capex: Optional[float],
    free_cash_flow_direct: Optional[float] = None,
) -> Dict[str, Any]:
    """Compute debt, liquidity, interest coverage, and cash flow stability metrics."""
    debt = _safe_float(total_debt)
    cash = _safe_float(cash_and_equivalents)
    equity = _safe_float(stockholders_equity)
    ca = _safe_float(current_assets)
    cl = _safe_float(current_liabilities)
    inv = _safe_float(inventory)
    ebit = _safe_float(operating_income)
    interest = _safe_float(interest_expense)
    ocf = _safe_float(operating_cash_flow)
    capex_val = _safe_float(capex)
    fcf_direct = _safe_float(free_cash_flow_direct)

    net_debt = round(debt - cash, 2) if (debt is not None and cash is not None) else None
    debt_to_equity = round(debt / equity, 2) if (debt is not None and equity is not None and equity > 0) else None
    current_ratio = round(ca / cl, 2) if (ca is not None and cl is not None and cl > 0) else None
    quick_ratio = (
        round((ca - (inv or 0.0)) / cl, 2)
        if (ca is not None and cl is not None and cl > 0)
        else None
    )
    interest_coverage = (
        round(ebit / abs(interest), 2)
        if (ebit is not None and interest is not None and abs(interest) > 0)
        else None
    )

    if ocf is not None and capex_val is not None:
        free_cash_flow = round(ocf - abs(capex_val), 2)
    else:
        free_cash_flow = _round_opt(fcf_direct, 2)

    return {
        "total_debt": _round_opt(debt, 2),
        "cash_and_equivalents": _round_opt(cash, 2),
        "net_debt": net_debt,
        "stockholders_equity": _round_opt(equity, 2),
        "debt_to_equity": debt_to_equity,
        "current_ratio": current_ratio,
        "quick_ratio": quick_ratio,
        "interest_coverage": interest_coverage,
        "operating_cash_flow": _round_opt(ocf, 2),
        "capital_expenditure": _round_opt(abs(capex_val), 2) if capex_val is not None else None,
        "free_cash_flow": free_cash_flow,
    }

