import logging
import math
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
import yfinance as yf

from app.schemas.stock import FinancialStatementsResponse, StockOverviewResponse, StatementData
from app.schemas.fundamental import (
    MetricItem,
    RevenueEarningsSection,
    ProfitabilitySection,
    DebtStabilitySection,
    ValuationSection,
    HistoricalStatementYear,
    HistoricalStatementComparison,
    PeerBenchmarkItem,
    PeerComparisonSection,
    BalanceSheetPeriodAudit,
    AuditFindingItem,
    AuditCategoryScores,
    DataIntegrityAudit,
    OptionalEnhancementsSection,
    FundamentalAnalysisResponse,
)
from app.services.stock_service import (
    PREDEFINED_UNIVERSE,
    CURATED_PEERS,
    get_company_overview,
    _infer_market_from_exchange_and_symbol,
)

logger = logging.getLogger("uvicorn.error")

# Line item alias definitions covering diverse reporting taxonomies (US GAAP, IFRS, Ind-AS)
LINE_ITEM_ALIASES: Dict[str, List[str]] = {
    "revenue": [
        "total revenue", "operating revenue", "revenue", "total operating revenue",
        "sales", "net sales", "revenues"
    ],
    "gross_profit": [
        "gross profit", "gross income"
    ],
    "operating_income": [
        "operating income", "operating profit", "ebit", "operating revenue and other income",
        "profit before interest and tax"
    ],
    "net_income": [
        "net income", "net income common stockholders", "net profit",
        "net income continuous operations", "profit after tax", "net income applicable to common shares"
    ],
    "diluted_eps": [
        "diluted eps", "diluted earnings per share", "eps diluted"
    ],
    "basic_eps": [
        "basic eps", "basic earnings per share", "eps basic"
    ],
    "total_assets": [
        "total assets", "assets"
    ],
    "current_assets": [
        "current assets", "total current assets"
    ],
    "current_liabilities": [
        "current liabilities", "total current liabilities"
    ],
    "total_liabilities": [
        "total liabilities", "total liabilities net minority interest"
    ],
    "stockholders_equity": [
        "stockholders equity", "total stockholders equity", "common stock equity",
        "total equity gross minority interest", "stockholders' equity", "total equity",
        "shareholders equity", "total shareholder equity"
    ],
    "total_debt": [
        "total debt", "long term debt and capital lease obligation", "long term debt"
    ],
    "short_term_debt": [
        "current debt and capital lease obligation", "current debt", "current portion of long term debt",
        "short term debt", "short term borrowings", "commercial paper", "current notes payable"
    ],
    "long_term_debt": [
        "long term debt and capital lease obligation", "long term debt", "non current debt",
        "long term borrowings", "long term debt non current"
    ],
    "cash_and_equivalents": [
        "cash and cash equivalents", "cash financial", "cash cash equivalents and short term investments",
        "cash and short term investments", "cash & cash equivalents"
    ],
    "receivables": [
        "receivables", "accounts receivable", "trade receivables"
    ],
    "inventory": [
        "inventory", "inventories"
    ],
    "operating_cash_flow": [
        "operating cash flow", "cash flow from continuing operating activities",
        "cash generated from operating activities", "net cash from operating activities"
    ],
    "capital_expenditure": [
        "capital expenditure", "capital expenditures", "investments in property plant and equipment",
        "purchase of property plant and equipment", "capex"
    ],
    "interest_expense": [
        "interest expense", "interest expense non operating", "finance costs"
    ],
    "cost_of_revenue": [
        "cost of revenue", "cost of goods sold", "cost of goods and services sold", "cogs", "cost of sales"
    ],
    "operating_expense": [
        "operating expense", "operating expenses", "total operating expenses"
    ],
    "tax_expense": [
        "tax expense", "income tax expense", "provision for income taxes", "tax provision", "income tax"
    ],
    "free_cash_flow": [
        "free cash flow"
    ],
}


def _clean_str(s: str) -> str:
    return "".join(c for c in s.lower() if c.isalnum() or c.isspace()).strip()


def _extract_series_from_statement(
    statement_data: Optional[StatementData],
    alias_key: str
) -> Dict[str, float]:
    """
    Extracts a dictionary of {period_str: float_val} for a given canonical alias_key.
    Prioritizes exact alias matches first, falling back to substring matches.
    Periods are guaranteed sorted newest-first in the returned dict.
    """
    if not statement_data or not statement_data.items:
        return {}

    target_aliases = [_clean_str(k) for k in LINE_ITEM_ALIASES.get(alias_key, [alias_key])]
    values_map: Dict[str, float] = {}

    # Pass 1: Exact matches
    for item in statement_data.items:
        raw_name = getattr(item, "line_item", None) or getattr(item, "metric", None) or getattr(item, "item_name", "")
        name_clean = _clean_str(raw_name)
        if any(name_clean == alias for alias in target_aliases):
            for period, raw_val in item.values.items():
                if raw_val is not None and not (isinstance(raw_val, float) and math.isnan(raw_val)):
                    try:
                        values_map[str(period)] = float(raw_val)
                    except (ValueError, TypeError):
                        continue
            if values_map:
                break

    # Pass 2: Substring matches if exact match didn't yield values
    if not values_map:
        for item in statement_data.items:
            raw_name = getattr(item, "line_item", None) or getattr(item, "metric", None) or getattr(item, "item_name", "")
            name_clean = _clean_str(raw_name)
            if any(alias in name_clean for alias in target_aliases):
                for period, raw_val in item.values.items():
                    if raw_val is not None and not (isinstance(raw_val, float) and math.isnan(raw_val)):
                        try:
                            values_map[str(period)] = float(raw_val)
                        except (ValueError, TypeError):
                            continue
                if values_map:
                    break

    # Sort descending by period string if possible
    sorted_periods = sorted(values_map.keys(), reverse=True)
    return {p: values_map[p] for p in sorted_periods}


def _format_currency(val: Optional[float], currency: str = "USD") -> str:
    if val is None or math.isnan(val):
        return "N/A"
    sym = "₹" if currency in {"INR", "₹"} else "$"
    abs_val = abs(val)
    sign = "-" if val < 0 else ""
    if abs_val >= 1e12:
        return f"{sign}{sym}{abs_val / 1e12:.2f}T"
    if abs_val >= 1e9:
        return f"{sign}{sym}{abs_val / 1e9:.2f}B"
    if abs_val >= 1e6:
        return f"{sign}{sym}{abs_val / 1e6:.2f}M"
    if abs_val >= 1e3:
        return f"{sign}{sym}{abs_val / 1e3:.2f}K"
    return f"{sign}{sym}{abs_val:.2f}"


def _format_percentage(val: Optional[float]) -> str:
    if val is None or math.isnan(val):
        return "N/A"
    return f"{val:.2f}%"


def _format_multiple(val: Optional[float]) -> str:
    if val is None or math.isnan(val):
        return "N/A"
    return f"{val:.2f}x"


def calculate_safe_cagr(
    initial_val: Optional[float],
    final_val: Optional[float],
    num_years: int,
    metric_name: str = "Metric"
) -> Tuple[Optional[float], str, Optional[str]]:
    """
    Safely computes Compound Annual Growth Rate.
    Gracefully handles zero, negative, and missing starting values without math errors.
    Returns: (cagr_val_percent, status_code, explanatory_notes)
    """
    if num_years < 1:
        return (
            None,
            "insufficient_periods",
            f"At least 2 distinct reporting years required for {metric_name} CAGR; {num_years} elapsed years available."
        )

    if initial_val is None or final_val is None:
        return (
            None,
            "missing_data",
            f"Insufficient historical disclosures to calculate {metric_name} CAGR."
        )

    # 1. Zero initial value
    if initial_val == 0:
        return (
            None,
            "undefined_zero_base",
            f"{metric_name} starting value was zero; compound annual growth rate cannot be calculated."
        )

    # 2. Negative initial value transitioning to positive (Turnaround)
    if initial_val < 0 and final_val > 0:
        return (
            None,
            "turnaround_loss_to_profit",
            f"Turnaround: shifted from initial net deficit ({initial_val:,.0f}) to positive earnings ({final_val:,.0f}) over {num_years} years."
        )

    # 3. Positive initial value deteriorating to negative
    if initial_val > 0 and final_val < 0:
        return (
            None,
            "deterioration_profit_to_loss",
            f"Deterioration: shifted from initial positive profit ({initial_val:,.0f}) to net loss ({final_val:,.0f}) over {num_years} years."
        )

    # 4. Negative initial and negative final (Continuous Loss)
    if initial_val < 0 and final_val < 0:
        return (
            None,
            "continuous_loss",
            f"{metric_name} was negative in both base and final reporting periods; standard CAGR is not economically meaningful."
        )

    # 5. Standard valid positive CAGR
    try:
        ratio = final_val / initial_val
        cagr = (math.pow(ratio, 1.0 / num_years) - 1.0) * 100.0
        return (round(cagr, 2), "calculated", f"Compound annual growth over {num_years} consecutive years.")
    except Exception as exc:
        logger.warning(f"CAGR calculation exception for {metric_name}: {exc}")
        return (None, "calculation_error", f"Could not determine {metric_name} CAGR due to numerical limits.")


# ── 1. Revenue & Earnings Analysis Engine ──────────────────────────────────────

def analyze_revenue_and_earnings(
    statements: FinancialStatementsResponse,
    overview: StockOverviewResponse
) -> RevenueEarningsSection:
    currency = statements.currency or overview.currency or "USD"
    annual_income = getattr(statements.income_statement, "annual", None)
    quarterly_income = getattr(statements.income_statement, "quarterly", None)
    annual_cashflow = getattr(statements.cash_flow, "annual", None)

    rev_annual = _extract_series_from_statement(annual_income, "revenue")
    net_annual = _extract_series_from_statement(annual_income, "net_income")
    gross_annual = _extract_series_from_statement(annual_income, "gross_profit")
    op_annual = _extract_series_from_statement(annual_income, "operating_income")
    diluted_eps_annual = _extract_series_from_statement(annual_income, "diluted_eps")
    basic_eps_annual = _extract_series_from_statement(annual_income, "basic_eps")
    ocf_annual = _extract_series_from_statement(annual_cashflow, "operating_cash_flow")
    rev_quarterly = _extract_series_from_statement(quarterly_income, "revenue")

    annual_periods = list(rev_annual.keys())
    t0 = annual_periods[0] if annual_periods else None
    t1 = annual_periods[1] if len(annual_periods) > 1 else None
    t_base = annual_periods[-1] if len(annual_periods) > 1 else None

    # Latest Revenue
    rev_val = rev_annual.get(t0) if t0 else None
    rev_metric = MetricItem(
        name="total_revenue",
        value=rev_val,
        formatted=_format_currency(rev_val, currency),
        period=t0,
        status="calculated" if rev_val is not None else "unavailable",
    )

    # YoY Revenue Growth
    rev_yoy_val = None
    rev_yoy_status = "unavailable"
    if t0 and t1 and rev_annual.get(t1):
        prior = rev_annual[t1]
        if prior != 0:
            rev_yoy_val = round(((rev_val - prior) / abs(prior)) * 100.0, 2)
            rev_yoy_status = "calculated"
    rev_yoy_metric = MetricItem(
        name="revenue_growth_yoy",
        value=rev_yoy_val,
        formatted=_format_percentage(rev_yoy_val),
        period=f"{t0} vs {t1}" if t1 else t0,
        status=rev_yoy_status,
        method="year_over_year",
    )

    # QoQ Revenue Growth
    q_periods = list(rev_quarterly.keys())
    rev_qoq_val = None
    rev_qoq_status = "unavailable"
    if len(q_periods) >= 2:
        q0, q1 = q_periods[0], q_periods[1]
        prior_q = rev_quarterly.get(q1)
        curr_q = rev_quarterly.get(q0)
        if prior_q and prior_q != 0 and curr_q is not None:
            rev_qoq_val = round(((curr_q - prior_q) / abs(prior_q)) * 100.0, 2)
            rev_qoq_status = "calculated"
    rev_qoq_metric = MetricItem(
        name="revenue_growth_qoq",
        value=rev_qoq_val,
        formatted=_format_percentage(rev_qoq_val),
        period=f"{q_periods[0]} vs {q_periods[1]}" if len(q_periods) >= 2 else None,
        status=rev_qoq_status,
        method="quarter_over_quarter",
    )

    # Revenue CAGR
    num_years_rev = len(annual_periods) - 1 if len(annual_periods) > 1 else 0
    cagr_rev, cagr_rev_status, cagr_rev_notes = calculate_safe_cagr(
        initial_val=rev_annual.get(t_base) if t_base else None,
        final_val=rev_val,
        num_years=num_years_rev,
        metric_name="Revenue",
    )
    rev_cagr_metric = MetricItem(
        name="revenue_cagr",
        value=cagr_rev,
        formatted=_format_percentage(cagr_rev),
        period=f"{t_base} to {t0}" if t_base and t0 else None,
        status=cagr_rev_status,
        method="multi_year_cagr",
        notes=cagr_rev_notes,
    )

    # Gross Profit & Operating Income
    gp_val = gross_annual.get(t0) if t0 else None
    gp_metric = MetricItem(
        name="gross_profit",
        value=gp_val,
        formatted=_format_currency(gp_val, currency),
        period=t0,
        status="calculated" if gp_val is not None else "unavailable",
    )

    op_val = op_annual.get(t0) if t0 else None
    op_metric = MetricItem(
        name="operating_income",
        value=op_val,
        formatted=_format_currency(op_val, currency),
        period=t0,
        status="calculated" if op_val is not None else "unavailable",
    )

    # Net Income
    net_val = net_annual.get(t0) if t0 else None
    net_metric = MetricItem(
        name="net_income",
        value=net_val,
        formatted=_format_currency(net_val, currency),
        period=t0,
        status="calculated" if net_val is not None else "unavailable",
    )

    # Net Income YoY Growth
    net_yoy_val = None
    net_yoy_status = "unavailable"
    if t0 and t1 and net_annual.get(t1) is not None:
        prior_net = net_annual[t1]
        if prior_net != 0:
            net_yoy_val = round(((net_val - prior_net) / abs(prior_net)) * 100.0, 2)
            net_yoy_status = "calculated"
    net_yoy_metric = MetricItem(
        name="net_income_growth_yoy",
        value=net_yoy_val,
        formatted=_format_percentage(net_yoy_val),
        period=f"{t0} vs {t1}" if t1 else t0,
        status=net_yoy_status,
        method="year_over_year",
    )

    # Net Income CAGR (Safe)
    cagr_net, cagr_net_status, cagr_net_notes = calculate_safe_cagr(
        initial_val=net_annual.get(t_base) if t_base else None,
        final_val=net_val,
        num_years=num_years_rev,
        metric_name="Net Income",
    )
    net_cagr_metric = MetricItem(
        name="net_income_cagr",
        value=cagr_net,
        formatted=_format_percentage(cagr_net),
        period=f"{t_base} to {t0}" if t_base and t0 else None,
        status=cagr_net_status,
        method="multi_year_cagr",
        notes=cagr_net_notes,
    )

    # Diluted & Basic EPS
    eps_val = diluted_eps_annual.get(t0)
    eps_metric = MetricItem(
        name="diluted_eps",
        value=eps_val,
        formatted=f"{currency} {eps_val:.2f}" if eps_val is not None else "N/A",
        period=t0,
        status="reported" if eps_val is not None else "unavailable",
    )

    basic_eps_val = basic_eps_annual.get(t0)
    basic_eps_metric = MetricItem(
        name="basic_eps",
        value=basic_eps_val,
        formatted=f"{currency} {basic_eps_val:.2f}" if basic_eps_val is not None else "N/A",
        period=t0,
        status="reported" if basic_eps_val is not None else "unavailable",
    )

    # Quality of Earnings (Operating Cash Flow / Net Income)
    quality_val = None
    quality_status = "unavailable"
    quality_notes = None
    ocf_val = ocf_annual.get(t0)
    if ocf_val is not None and net_val is not None:
        if net_val > 0:
            quality_val = round(ocf_val / net_val, 2)
            quality_status = "calculated"
            quality_notes = "Ratio > 1.0 indicates strong cash backing for reported net income." if quality_val >= 1.0 else "Operating cash flow is lower than reported net income."
        elif net_val < 0:
            quality_status = "loss_making"
            quality_notes = "Net income is negative; cash flow conversion ratio is not applicable."
    quality_metric = MetricItem(
        name="earnings_quality_ratio",
        value=quality_val,
        formatted=_format_multiple(quality_val),
        period=t0,
        status=quality_status,
        method="ocf_to_net_income",
        notes=quality_notes,
    )

    # Narrative synthesis
    narrative_parts = []
    if rev_val is not None:
        narrative_parts.append(f"Reported total revenue of {_format_currency(rev_val, currency)} for {t0}.")
    if rev_yoy_val is not None:
        trend_word = "expanded" if rev_yoy_val > 0 else "declined"
        narrative_parts.append(f"Top-line {trend_word} by {abs(rev_yoy_val):.2f}% YoY.")
    if cagr_rev is not None:
        narrative_parts.append(f"{num_years_rev}-year revenue CAGR is {cagr_rev:.2f}%.")
    elif cagr_rev_notes:
        narrative_parts.append(cagr_rev_notes)
    if net_val is not None:
        p_or_l = "net income" if net_val >= 0 else "net loss"
        narrative_parts.append(f"Generated {p_or_l} of {_format_currency(net_val, currency)}.")

    return RevenueEarningsSection(
        revenue=rev_metric,
        revenue_growth_yoy=rev_yoy_metric,
        revenue_growth_qoq=rev_qoq_metric,
        revenue_cagr=rev_cagr_metric,
        gross_profit=gp_metric,
        operating_income=op_metric,
        net_income=net_metric,
        net_income_growth_yoy=net_yoy_metric,
        net_income_cagr=net_cagr_metric,
        diluted_eps=eps_metric,
        basic_eps=basic_eps_metric,
        earnings_quality_ratio=quality_metric,
        summary_narrative=" ".join(narrative_parts) or "Revenue and earnings metrics extracted from reported filings.",
    )


# ── 2. Profitability Analysis Engine ──────────────────────────────────────────

def analyze_profitability(
    statements: FinancialStatementsResponse,
    overview: StockOverviewResponse
) -> ProfitabilitySection:
    annual_income = getattr(statements.income_statement, "annual", None)
    annual_balance = getattr(statements.balance_sheet, "annual", None)

    rev_annual = _extract_series_from_statement(annual_income, "revenue")
    gross_annual = _extract_series_from_statement(annual_income, "gross_profit")
    op_annual = _extract_series_from_statement(annual_income, "operating_income")
    net_annual = _extract_series_from_statement(annual_income, "net_income")
    assets_annual = _extract_series_from_statement(annual_balance, "total_assets")
    equity_annual = _extract_series_from_statement(annual_balance, "stockholders_equity")

    periods = list(rev_annual.keys())
    t0 = periods[0] if periods else None
    t1 = periods[1] if len(periods) > 1 else None

    # Gross Margin
    gm_val = None
    gm_status = "unavailable"
    if t0 and rev_annual.get(t0) and gross_annual.get(t0) is not None:
        r = rev_annual[t0]
        if r > 0:
            gm_val = round((gross_annual[t0] / r) * 100.0, 2)
            gm_status = "calculated"
    gm_metric = MetricItem(
        name="gross_margin",
        value=gm_val,
        formatted=_format_percentage(gm_val),
        period=t0,
        status=gm_status,
        method="gross_profit_over_revenue",
    )

    # Operating Margin
    om_val = None
    om_status = "unavailable"
    if t0 and rev_annual.get(t0) and op_annual.get(t0) is not None:
        r = rev_annual[t0]
        if r > 0:
            om_val = round((op_annual[t0] / r) * 100.0, 2)
            om_status = "calculated"
    om_metric = MetricItem(
        name="operating_margin",
        value=om_val,
        formatted=_format_percentage(om_val),
        period=t0,
        status=om_status,
        method="operating_income_over_revenue",
    )

    # Net Margin
    nm_val = None
    nm_status = "unavailable"
    if t0 and rev_annual.get(t0) and net_annual.get(t0) is not None:
        r = rev_annual[t0]
        if r > 0:
            nm_val = round((net_annual[t0] / r) * 100.0, 2)
            nm_status = "calculated"
    nm_metric = MetricItem(
        name="net_margin",
        value=nm_val,
        formatted=_format_percentage(nm_val),
        period=t0,
        status=nm_status,
        method="net_income_over_revenue",
    )

    # ROA
    roa_val = None
    roa_status = "unavailable"
    if t0 and net_annual.get(t0) is not None and assets_annual.get(t0):
        a = assets_annual[t0]
        if a > 0:
            roa_val = round((net_annual[t0] / a) * 100.0, 2)
            roa_status = "calculated"
    roa_metric = MetricItem(
        name="return_on_assets",
        value=roa_val,
        formatted=_format_percentage(roa_val),
        period=t0,
        status=roa_status,
        method="net_income_over_total_assets",
    )

    # ROE with Dual-Method & Deficit Protection (Mandatory Correction #3)
    roe_val = None
    roe_method = None
    roe_status = "unavailable"
    roe_notes = None

    if t0 and net_annual.get(t0) is not None:
        net_inc = net_annual[t0]
        eq_t0 = equity_annual.get(t0)
        eq_t1 = equity_annual.get(t1) if t1 else None

        # Check if average equity can be used
        if eq_t0 is not None and eq_t1 is not None:
            avg_equity = (eq_t0 + eq_t1) / 2.0
            if avg_equity > 0:
                roe_val = round((net_inc / avg_equity) * 100.0, 2)
                roe_method = "average_equity"
                roe_status = "calculated"
                roe_notes = f"Calculated using 2-period average equity (FY{t0} and FY{t1})."
            else:
                roe_method = "not_computable"
                roe_status = "negative_equity_deficit"
                roe_notes = "Average shareholder equity is negative (accumulated deficit); ROE is economically non-meaningful."
        elif eq_t0 is not None:
            # Fallback to ending equity
            if eq_t0 > 0:
                roe_val = round((net_inc / eq_t0) * 100.0, 2)
                roe_method = "ending_equity"
                roe_status = "calculated"
                roe_notes = f"Calculated using ending equity for {t0} (prior period equity unavailable for averaging)."
            else:
                roe_method = "not_computable"
                roe_status = "negative_equity_deficit"
                roe_notes = "Shareholder equity is negative (accumulated deficit); ROE is economically non-meaningful."
        else:
            roe_status = "missing_data"
            roe_notes = "Shareholder equity is not disclosed in reported balance sheet."

    roe_metric = MetricItem(
        name="return_on_equity",
        value=roe_val,
        formatted=_format_percentage(roe_val),
        period=t0,
        status=roe_status,
        method=roe_method,
        notes=roe_notes,
    )

    # Margin Trend Determination (Expanding vs Contracting)
    margin_trend = "Stable"
    if t0 and t1 and rev_annual.get(t1) and op_annual.get(t1):
        prev_r = rev_annual[t1]
        prev_op = op_annual[t1]
        if prev_r > 0 and om_val is not None:
            prev_om = (prev_op / prev_r) * 100.0
            diff = om_val - prev_om
            if diff > 0.5:
                margin_trend = "Expanding"
            elif diff < -0.5:
                margin_trend = "Contracting"
            else:
                margin_trend = "Stable"
    elif om_val is None:
        margin_trend = "Insufficient Data"

    # Narrative
    narrative_parts = []
    if om_val is not None:
        narrative_parts.append(f"Operating margin stands at {om_val:.2f}% ({margin_trend}).")
    if nm_val is not None:
        narrative_parts.append(f"Net profit margin is {nm_val:.2f}%.")
    if roe_val is not None:
        narrative_parts.append(f"Delivered a Return on Equity of {roe_val:.2f}% using {roe_method.replace('_', ' ')}.")
    elif roe_notes:
        narrative_parts.append(roe_notes)

    return ProfitabilitySection(
        gross_margin=gm_metric,
        operating_margin=om_metric,
        net_margin=nm_metric,
        return_on_assets=roa_metric,
        return_on_equity=roe_metric,
        margin_trend=margin_trend,
        summary_narrative=" ".join(narrative_parts) or "Profitability margins evaluated from income and balance sheet statements.",
    )


# ── 3. Debt & Financial Stability Engine ──────────────────────────────────────

def analyze_financial_stability(
    statements: FinancialStatementsResponse,
    overview: StockOverviewResponse
) -> DebtStabilitySection:
    currency = statements.currency or overview.currency or "USD"
    annual_income = getattr(statements.income_statement, "annual", None)
    annual_balance = getattr(statements.balance_sheet, "annual", None)
    annual_cashflow = getattr(statements.cash_flow, "annual", None)

    assets_annual = _extract_series_from_statement(annual_balance, "total_assets")
    current_assets = _extract_series_from_statement(annual_balance, "current_assets")
    current_liab = _extract_series_from_statement(annual_balance, "current_liabilities")
    total_liab = _extract_series_from_statement(annual_balance, "total_liabilities")
    equity_annual = _extract_series_from_statement(annual_balance, "stockholders_equity")
    debt_annual = _extract_series_from_statement(annual_balance, "total_debt")
    short_term_debt_series = _extract_series_from_statement(annual_balance, "short_term_debt")
    long_term_debt_series = _extract_series_from_statement(annual_balance, "long_term_debt")
    cash_annual = _extract_series_from_statement(annual_balance, "cash_and_equivalents")
    inventory_annual = _extract_series_from_statement(annual_balance, "inventory")
    receivables_annual = _extract_series_from_statement(annual_balance, "receivables")

    ebit_annual = _extract_series_from_statement(annual_income, "operating_income")
    interest_annual = _extract_series_from_statement(annual_income, "interest_expense")

    ocf_annual = _extract_series_from_statement(annual_cashflow, "operating_cash_flow")
    capex_annual = _extract_series_from_statement(annual_cashflow, "capital_expenditure")

    periods = list(assets_annual.keys()) or list(debt_annual.keys()) or list(current_assets.keys()) or list(equity_annual.keys())
    t0 = periods[0] if periods else None

    # Total Debt
    tot_debt = debt_annual.get(t0)
    tot_debt_metric = MetricItem(
        name="total_debt",
        value=tot_debt,
        formatted=_format_currency(tot_debt, currency),
        period=t0,
        status="calculated" if tot_debt is not None else "unavailable",
    )

    # Short-term and Long-term Debt Obligations & Reconciliation
    st_debt_val = short_term_debt_series.get(t0)
    lt_debt_val = long_term_debt_series.get(t0)

    st_notes = None
    lt_notes = None
    if st_debt_val is not None and lt_debt_val is not None:
        component_sum = st_debt_val + lt_debt_val
        if tot_debt is not None:
            discrepancy_amount = round(abs(component_sum - tot_debt), 2)
            if discrepancy_amount <= 1.0 or (tot_debt > 0 and (discrepancy_amount / tot_debt) <= 0.001):
                if tot_debt > 0:
                    st_pct = (st_debt_val / tot_debt) * 100.0
                    lt_pct = (lt_debt_val / tot_debt) * 100.0
                    st_notes = f"Short-term obligations account for {st_pct:.1f}% of total debt ({_format_currency(st_debt_val, currency)}). Reconciles with reported total debt."
                    lt_notes = f"Long-term obligations account for {lt_pct:.1f}% of total debt ({_format_currency(lt_debt_val, currency)}). Reconciles with reported total debt."
                else:
                    st_notes = "Zero total debt reported."
                    lt_notes = "Zero total debt reported."
            else:
                st_notes = f"Reported short-term debt: {_format_currency(st_debt_val, currency)}. Component sum ({_format_currency(component_sum, currency)}) differs from reported total debt ({_format_currency(tot_debt, currency)}) by {_format_currency(discrepancy_amount, currency)}. May reflect other obligations or reporting differences."
                lt_notes = f"Reported long-term debt: {_format_currency(lt_debt_val, currency)}. Component sum ({_format_currency(component_sum, currency)}) differs from reported total debt ({_format_currency(tot_debt, currency)}) by {_format_currency(discrepancy_amount, currency)}. May reflect other obligations or reporting differences."
        else:
            st_notes = f"Reported short-term debt: {_format_currency(st_debt_val, currency)}."
            lt_notes = f"Reported long-term debt: {_format_currency(lt_debt_val, currency)}."
    elif st_debt_val is not None:
        if tot_debt is not None and tot_debt > 0:
            st_pct = (st_debt_val / tot_debt) * 100.0
            st_notes = f"Reported short-term debt: {_format_currency(st_debt_val, currency)} ({st_pct:.1f}% of total debt). Long-term portion not separately itemized."
        else:
            st_notes = f"Reported short-term debt: {_format_currency(st_debt_val, currency)}. Long-term portion not separately itemized."
        lt_notes = "Long-term debt obligations not separately itemized in financial statement."
    elif lt_debt_val is not None:
        if tot_debt is not None and tot_debt > 0:
            lt_pct = (lt_debt_val / tot_debt) * 100.0
            lt_notes = f"Reported long-term debt: {_format_currency(lt_debt_val, currency)} ({lt_pct:.1f}% of total debt). Short-term portion not separately itemized."
        else:
            lt_notes = f"Reported long-term debt: {_format_currency(lt_debt_val, currency)}. Short-term portion not separately itemized."
        st_notes = "Short-term debt obligations not separately itemized in financial statement."
    else:
        st_notes = "Short-term debt obligations not separately itemized in financial statement."
        lt_notes = "Long-term debt obligations not separately itemized in financial statement."

    st_debt_metric = MetricItem(
        name="short_term_debt",
        value=st_debt_val,
        formatted=_format_currency(st_debt_val, currency),
        period=t0,
        status="reported" if st_debt_val is not None else "unavailable",
        method="balance_sheet_current_debt",
        notes=st_notes,
    )

    lt_debt_metric = MetricItem(
        name="long_term_debt",
        value=lt_debt_val,
        formatted=_format_currency(lt_debt_val, currency),
        period=t0,
        status="reported" if lt_debt_val is not None else "unavailable",
        method="balance_sheet_long_term_debt",
        notes=lt_notes,
    )

    # Net Debt
    cash_val = cash_annual.get(t0, 0.0)
    net_debt_val = None
    net_debt_status = "unavailable"
    net_debt_notes = None
    if tot_debt is not None:
        net_debt_val = tot_debt - cash_val
        net_debt_status = "calculated"
        net_debt_notes = "Net cash positive (cash exceeds total debt)." if net_debt_val < 0 else "Net debt is positive."
    net_debt_metric = MetricItem(
        name="net_debt",
        value=net_debt_val,
        formatted=_format_currency(net_debt_val, currency),
        period=t0,
        status=net_debt_status,
        method="total_debt_minus_cash",
        notes=net_debt_notes,
    )

    # Debt-to-Equity (D/E)
    de_val = None
    de_status = "unavailable"
    de_notes = None
    eq_val = equity_annual.get(t0)
    if tot_debt is not None and eq_val is not None:
        if eq_val > 0:
            de_val = round(tot_debt / eq_val, 2)
            de_status = "calculated"
        elif eq_val < 0:
            de_status = "negative_equity"
            de_notes = "Stockholders equity is negative; standard Debt-to-Equity ratio is not meaningful."
        else:
            de_status = "zero_denominator"
    de_metric = MetricItem(
        name="debt_to_equity",
        value=de_val,
        formatted=_format_multiple(de_val),
        period=t0,
        status=de_status,
        method="total_debt_over_equity",
        notes=de_notes,
    )

    # Debt-to-Assets
    da_val = None
    da_status = "unavailable"
    assets_val = assets_annual.get(t0)
    if tot_debt is not None and assets_val and assets_val > 0:
        da_val = round(tot_debt / assets_val, 2)
        da_status = "calculated"
    da_metric = MetricItem(
        name="debt_to_assets",
        value=da_val,
        formatted=_format_multiple(da_val),
        period=t0,
        status=da_status,
        method="total_debt_over_assets",
    )

    # Equity Ratio: Stockholders' Equity / Total Assets (as a percentage)
    er_val = None
    er_status = "unavailable"
    er_notes = None
    if eq_val is not None and assets_val is not None:
        if assets_val > 0:
            er_val = round((eq_val / assets_val) * 100.0, 2)
            if eq_val < 0:
                er_status = "negative_equity"
                er_notes = f"Negative stockholders' equity ({_format_currency(eq_val, currency)}) results in negative equity ratio of {er_val:.2f}%; indicates balance sheet deficit."
            else:
                er_status = "calculated"
                er_notes = f"Shareholders' equity finances {er_val:.2f}% of total assets."
        elif assets_val == 0:
            er_status = "zero_denominator"
            er_notes = "Reported total assets is zero; equity ratio is not computable."
        else:
            er_status = "invalid_data"
            er_notes = "Reported total assets is negative; equity ratio is invalid."
    elif assets_val is None or eq_val is None:
        er_status = "unavailable"
        er_notes = "Stockholders' equity or total assets data unavailable."

    er_metric = MetricItem(
        name="equity_ratio",
        value=er_val,
        formatted=_format_percentage(er_val),
        period=t0,
        status=er_status,
        method="stockholders_equity_over_total_assets",
        notes=er_notes,
    )

    # Balance Sheet Context Metrics
    cl_val = current_liab.get(t0)
    tot_liab_val = total_liab.get(t0)

    curr_liab_metric = MetricItem(
        name="current_liabilities",
        value=cl_val,
        formatted=_format_currency(cl_val, currency),
        period=t0,
        status="reported" if cl_val is not None else "unavailable",
        notes="Total obligations due within one operating cycle / one year.",
    )

    tot_liab_metric = MetricItem(
        name="total_liabilities",
        value=tot_liab_val,
        formatted=_format_currency(tot_liab_val, currency),
        period=t0,
        status="reported" if tot_liab_val is not None else "unavailable",
        notes="Total claims by creditors against company assets.",
    )

    tot_assets_metric = MetricItem(
        name="total_assets",
        value=assets_val,
        formatted=_format_currency(assets_val, currency),
        period=t0,
        status="reported" if assets_val is not None else "unavailable",
        notes="Total economic resources owned and controlled by the company.",
    )

    stockholders_equity_metric = MetricItem(
        name="stockholders_equity",
        value=eq_val,
        formatted=_format_currency(eq_val, currency),
        period=t0,
        status="reported" if eq_val is not None else "unavailable",
        notes="Net book value attributable to shareholders.",
    )

    # Current Ratio
    cr_val = None
    cr_status = "unavailable"
    ca_val = current_assets.get(t0)
    if ca_val is not None and cl_val is not None:
        if cl_val > 0:
            cr_val = round(ca_val / cl_val, 2)
            cr_status = "calculated"
        else:
            cr_status = "zero_denominator"
    cr_metric = MetricItem(
        name="current_ratio",
        value=cr_val,
        formatted=_format_multiple(cr_val),
        period=t0,
        status=cr_status,
        method="current_assets_over_current_liabilities",
    )

    # Quick Ratio: (Cash + Receivables) / Current Liabilities OR (Current Assets - Inventory) / CL
    qr_val = None
    qr_status = "unavailable"
    if ca_val is not None and cl_val and cl_val > 0:
        inv_val = inventory_annual.get(t0, 0.0)
        qr_val = round((ca_val - inv_val) / cl_val, 2)
        qr_status = "calculated"
    elif cash_val is not None and cl_val and cl_val > 0:
        rec_val = receivables_annual.get(t0, 0.0)
        qr_val = round((cash_val + rec_val) / cl_val, 2)
        qr_status = "calculated"
    qr_metric = MetricItem(
        name="quick_ratio",
        value=qr_val,
        formatted=_format_multiple(qr_val),
        period=t0,
        status=qr_status,
        method="quick_assets_over_current_liabilities",
    )

    # Interest Coverage: EBIT / Interest Expense
    ic_val = None
    ic_status = "unavailable"
    ic_notes = None
    ebit_val = ebit_annual.get(t0)
    int_exp = interest_annual.get(t0)
    if ebit_val is not None and int_exp is not None:
        int_exp_abs = abs(int_exp)
        if int_exp_abs > 0:
            ic_val = round(ebit_val / int_exp_abs, 2)
            ic_status = "calculated"
            ic_notes = f"EBIT covers interest expense by {ic_val:.1f}x."
        else:
            ic_status = "zero_denominator"
            ic_notes = "Zero interest expense reported (negligible debt service)."
    elif tot_debt == 0 or tot_debt is None:
        ic_status = "not_applicable"
        ic_notes = "Negligible or zero total debt; interest coverage is not a constraint."
    ic_metric = MetricItem(
        name="interest_coverage",
        value=ic_val,
        formatted=_format_multiple(ic_val),
        period=t0,
        status=ic_status,
        method="ebit_over_interest_expense",
        notes=ic_notes,
    )

    # Free Cash Flow: Operating Cash Flow - CapEx
    fcf_val = None
    fcf_status = "unavailable"
    fcf_notes = None
    ocf_val = ocf_annual.get(t0)
    capex_val = capex_annual.get(t0)
    if ocf_val is not None:
        capex_clean = abs(capex_val) if capex_val is not None else 0.0
        fcf_val = round(ocf_val - capex_clean, 2)
        fcf_status = "calculated"
        fcf_notes = "Derived from Operating Cash Flow less Capital Expenditures." if capex_val is not None else "CapEx not reported; approximate FCF based on Operating Cash Flow."
    fcf_metric = MetricItem(
        name="free_cash_flow",
        value=fcf_val,
        formatted=_format_currency(fcf_val, currency),
        period=t0,
        status=fcf_status,
        method="ocf_minus_capex",
        notes=fcf_notes,
    )

    # Stability Rating synthesis
    stability_rating = "Moderate"
    if cr_val is not None and de_val is not None:
        if de_val < 0.5 and cr_val >= 1.5 and (net_debt_val is not None and net_debt_val <= 0):
            stability_rating = "Strong"
        elif de_val > 2.0 or (cr_val < 1.0):
            stability_rating = "Elevated Risk"
        elif de_val > 3.0 and cr_val < 0.8:
            stability_rating = "High Risk"
        else:
            stability_rating = "Moderate"
    elif cr_val is None and de_val is None:
        stability_rating = "Insufficient Data"

    # Narrative
    narrative_parts = []
    if cr_val is not None:
        narrative_parts.append(f"Current ratio of {cr_val:.2f}x reflects {'adequate' if cr_val >= 1.0 else 'tight'} short-term liquidity.")
    if de_val is not None:
        narrative_parts.append(f"Debt-to-equity is {de_val:.2f}x.")
    elif de_notes:
        narrative_parts.append(de_notes)
    if er_val is not None:
        if eq_val is not None and eq_val < 0:
            narrative_parts.append(f"Equity ratio is {er_val:.2f}% (negative equity indicates accumulated deficit).")
        else:
            narrative_parts.append(f"Equity ratio is {er_val:.2f}%, indicating equity finances {er_val:.1f}% of total assets.")
    if tot_debt is not None and tot_debt > 0:
        if st_debt_val is not None and lt_debt_val is not None:
            st_p = (st_debt_val / tot_debt) * 100.0
            lt_p = (lt_debt_val / tot_debt) * 100.0
            narrative_parts.append(f"Debt composition consists of {lt_p:.1f}% long-term debt and {st_p:.1f}% short-term obligations.")
        elif lt_debt_val is not None:
            lt_p = (lt_debt_val / tot_debt) * 100.0
            narrative_parts.append(f"Long-term debt represents {lt_p:.1f}% of total debt obligations.")
        elif st_debt_val is not None:
            st_p = (st_debt_val / tot_debt) * 100.0
            narrative_parts.append(f"Short-term debt represents {st_p:.1f}% of total debt obligations.")
    if net_debt_val is not None and net_debt_val < 0:
        narrative_parts.append(f"Maintains a net cash reserve of {_format_currency(abs(net_debt_val), currency)}.")
    if fcf_val is not None:
        narrative_parts.append(f"Generated {_format_currency(fcf_val, currency)} in Free Cash Flow.")

    return DebtStabilitySection(
        total_debt=tot_debt_metric,
        net_debt=net_debt_metric,
        debt_to_equity=de_metric,
        debt_to_assets=da_metric,
        equity_ratio=er_metric,
        current_ratio=cr_metric,
        quick_ratio=qr_metric,
        interest_coverage=ic_metric,
        free_cash_flow=fcf_metric,
        short_term_debt=st_debt_metric,
        long_term_debt=lt_debt_metric,
        current_liabilities=curr_liab_metric,
        total_liabilities=tot_liab_metric,
        total_assets=tot_assets_metric,
        stockholders_equity=stockholders_equity_metric,
        stability_rating=stability_rating,
        summary_narrative=" ".join(narrative_parts) or "Financial stability and liquidity assessed from balance sheet and cash flows.",
    )


# ── 4. Valuation Ratios Engine (P/E, P/B, ROE) ─────────────────────────────────

def calculate_valuation_ratios(
    overview: StockOverviewResponse,
    statements: FinancialStatementsResponse,
    profitability: ProfitabilitySection
) -> ValuationSection:
    price = overview.current_price
    currency = statements.currency or overview.currency or "USD"
    trailing_pe_val = None
    trailing_pe_status = "unavailable"
    trailing_pe_notes = None
    trailing_pe_method = None
    trailing_pe_period = None

    # 1. Trailing P/E
    # Priority A: Provider-reported trailing P/E
    if getattr(overview, "trailing_pe", None) is not None and overview.trailing_pe > 0:
        trailing_pe_val = round(overview.trailing_pe, 2)
        trailing_pe_status = "reported"
        trailing_pe_period = "TTM"
        trailing_pe_method = "provider_reported_ttm"
        trailing_pe_notes = "Reported trailing twelve months (TTM) Price-to-Earnings ratio."
    elif overview.pe_ratio is not None and overview.pe_ratio > 0 and getattr(overview, "forward_pe", None) != overview.pe_ratio:
        # Fallback to existing overview.pe_ratio when distinct from forward_pe
        trailing_pe_val = round(overview.pe_ratio, 2)
        trailing_pe_status = "reported"
        trailing_pe_period = "TTM"
        trailing_pe_method = "provider_reported_ttm"
        trailing_pe_notes = "Reported trailing twelve months (TTM) Price-to-Earnings ratio."
    # Priority B: Calculate from current price and compatible EPS
    elif price and price > 0:
        eps_val = None
        eps_source = None
        # Check if provider trailing EPS is available
        if getattr(overview, "trailing_eps", None) is not None:
            eps_val = overview.trailing_eps
            eps_source = "TTM EPS"
            trailing_pe_period = "TTM"
        else:
            # Fallback to annual statement diluted EPS
            annual_income = getattr(statements.income_statement, "annual", None)
            eps_series = _extract_series_from_statement(annual_income, "diluted_eps")
            if eps_series:
                t0_eps = list(eps_series.keys())[0]
                eps_val = eps_series[t0_eps]
                eps_source = f"FY{t0_eps} Statement EPS"
                trailing_pe_period = f"FY{t0_eps}"

        if eps_val is not None:
            if eps_val > 0:
                trailing_pe_val = round(price / eps_val, 2)
                trailing_pe_status = "calculated"
                trailing_pe_method = "price_over_eps"
                trailing_pe_notes = f"Calculated as Current Market Price ({_format_currency(price, currency)}) over {eps_source} ({_format_currency(eps_val, currency)})."
            elif eps_val <= 0:
                trailing_pe_status = "loss_making"
                trailing_pe_method = "price_over_eps"
                trailing_pe_notes = f"Company is loss-making ({eps_source}: {_format_currency(eps_val, currency)}); P/E multiple is not applicable."
    else:
        trailing_pe_status = "unavailable"

    trailing_pe_metric = MetricItem(
        name="trailing_pe",
        value=trailing_pe_val,
        formatted=_format_multiple(trailing_pe_val),
        period=trailing_pe_period,
        status=trailing_pe_status,
        method=trailing_pe_method or "price_over_eps",
        notes=trailing_pe_notes,
    )

    # 2. Forward P/E
    forward_pe_val = None
    forward_pe_status = "unavailable"
    forward_pe_notes = None
    forward_pe_method = None

    if getattr(overview, "forward_pe", None) is not None:
        if overview.forward_pe > 0:
            forward_pe_val = round(overview.forward_pe, 2)
            forward_pe_status = "reported"
            forward_pe_method = "provider_forward_estimate"
            forward_eps_str = f" ({_format_currency(overview.forward_eps, currency)} NTM EPS)" if getattr(overview, "forward_eps", None) else ""
            forward_pe_notes = f"Forward P/E based on consensus next-twelve-months (NTM) earnings estimates{forward_eps_str}."
        elif overview.forward_pe <= 0:
            forward_pe_status = "loss_making"
            forward_pe_method = "provider_forward_estimate"
            forward_pe_notes = "Company forward earnings estimate is negative; Forward P/E is not applicable."
    else:
        forward_pe_notes = "Forward earnings estimates are not disclosed by data provider."

    forward_pe_metric = MetricItem(
        name="forward_pe",
        value=forward_pe_val,
        formatted=_format_multiple(forward_pe_val),
        period="Forward (NTM)" if forward_pe_status == "reported" else None,
        status=forward_pe_status,
        method=forward_pe_method,
        notes=forward_pe_notes,
    )

    # 3. Price-to-Book (P/B) with Currency Parity Protection
    pb_val = None
    pb_status = "unavailable"
    pb_notes = None
    pb_method = None

    # Priority 1: Provider-reported priceToBook
    if getattr(overview, "price_to_book", None) is not None:
        if overview.price_to_book > 0:
            pb_val = round(overview.price_to_book, 2)
            pb_status = "reported"
            pb_method = "provider_reported_pb"
            pb_notes = f"Reported Price-to-Book ratio ({pb_val:.2f}x) from market data provider."
        elif overview.price_to_book <= 0:
            pb_status = "negative_equity"
            pb_method = "provider_reported_pb"
            pb_notes = "Reported Price-to-Book indicates negative book value; multiple is not meaningful."

    # Priority 2: Current Market Price / Book Value Per Share (same trading currency)
    elif price and price > 0 and getattr(overview, "book_value", None) is not None:
        if overview.book_value > 0:
            pb_val = round(price / overview.book_value, 2)
            pb_status = "calculated"
            pb_method = "price_over_bvps"
            pb_notes = f"Calculated as Current Market Price ({_format_currency(price, currency)}) over Book Value Per Share ({_format_currency(overview.book_value, currency)})."
        elif overview.book_value < 0:
            pb_status = "negative_equity"
            pb_method = "price_over_bvps"
            pb_notes = "Book value per share is negative (accumulated deficit); Price-to-Book multiple is not meaningful."
        else:
            pb_status = "zero_denominator"
            pb_method = "price_over_bvps"
            pb_notes = "Book value per share is zero; Price-to-Book multiple is not computable."

    # Priority 3: Market Capitalization / Balance Sheet Stockholders' Equity (with Currency Parity Check)
    else:
        annual_balance = getattr(statements.balance_sheet, "annual", None)
        equity_series = _extract_series_from_statement(annual_balance, "stockholders_equity")
        if equity_series and price and price > 0 and overview.market_cap:
            t0 = list(equity_series.keys())[0]
            eq_val = equity_series[t0]
            stmt_curr = getattr(statements, "currency", None)
            ov_curr = getattr(overview, "currency", None)

            # Currency parity guard: Do not divide if currencies conflict
            if stmt_curr and ov_curr and stmt_curr.strip().upper() != ov_curr.strip().upper():
                pb_status = "unavailable"
                pb_notes = f"Price-to-Book calculation suppressed due to currency mismatch: Market Cap is in {ov_curr} while balance sheet equity is in {stmt_curr}."
            elif eq_val > 0:
                pb_val = round(overview.market_cap / eq_val, 2)
                pb_status = "calculated"
                pb_method = "market_cap_over_book_value"
                pb_notes = f"Calculated as Market Capitalization over Stockholders Equity for {t0}."
            elif eq_val <= 0:
                pb_status = "negative_equity"
                pb_method = "market_cap_over_book_value"
                pb_notes = "Stockholders equity is negative (accumulated deficit); Price-to-Book multiple is not meaningful."
        else:
            pb_status = "unavailable"
            pb_notes = "Price-to-Book data unavailable."

    pb_metric = MetricItem(
        name="price_to_book",
        value=pb_val,
        formatted=_format_multiple(pb_val),
        status=pb_status,
        method=pb_method,
        notes=pb_notes,
    )

    # Narrative
    narrative_parts = []
    if trailing_pe_val is not None:
        narrative_parts.append(f"Trading at a trailing Price-to-Earnings multiple of {trailing_pe_val:.2f}x.")
    elif trailing_pe_notes:
        narrative_parts.append(trailing_pe_notes)
    if forward_pe_val is not None:
        narrative_parts.append(f"Forward P/E is {forward_pe_val:.2f}x based on consensus estimates.")
    if pb_val is not None:
        narrative_parts.append(f"Price-to-Book ratio is {pb_val:.2f}x.")
    elif pb_notes:
        narrative_parts.append(pb_notes)

    roe_val = profitability.return_on_equity.value
    if roe_val is not None:
        narrative_parts.append(f"Return on Equity is {profitability.return_on_equity.formatted}.")

    return ValuationSection(
        trailing_pe=trailing_pe_metric,
        forward_pe=forward_pe_metric,
        price_to_book=pb_metric,
        return_on_equity=profitability.return_on_equity,
        summary_narrative=" ".join(narrative_parts) or "Valuation ratios derived from market price and reported accounting equity.",
    )


# ── 5. Historical Financial Performance Engine ────────────────────────────────

def build_historical_comparison(
    statements: FinancialStatementsResponse,
    overview: Optional[StockOverviewResponse] = None
) -> HistoricalStatementComparison:
    annual_income = getattr(statements.income_statement, "annual", None)
    annual_balance = getattr(statements.balance_sheet, "annual", None)
    annual_cashflow = getattr(statements.cash_flow, "annual", None)

    # Resolve reporting currency for financial statement disclosures
    stmt_curr = (
        getattr(statements, "financial_currency", None)
        or getattr(overview, "financial_currency", None)
        or getattr(statements, "currency", None)
        or getattr(overview, "currency", None)
        or "USD"
    )

    rev_s = _extract_series_from_statement(annual_income, "revenue")
    gp_s = _extract_series_from_statement(annual_income, "gross_profit")
    op_s = _extract_series_from_statement(annual_income, "operating_income")
    net_s = _extract_series_from_statement(annual_income, "net_income")
    eps_s = _extract_series_from_statement(annual_income, "diluted_eps")
    if not eps_s:
        eps_s = _extract_series_from_statement(annual_income, "basic_eps")

    assets_s = _extract_series_from_statement(annual_balance, "total_assets")
    liab_s = _extract_series_from_statement(annual_balance, "total_liabilities")
    debt_s = _extract_series_from_statement(annual_balance, "total_debt")
    eq_s = _extract_series_from_statement(annual_balance, "stockholders_equity")

    ocf_s = _extract_series_from_statement(annual_cashflow, "operating_cash_flow")
    capex_s = _extract_series_from_statement(annual_cashflow, "capital_expenditure")

    # Gather union of all periods, sorted descending (newest-first)
    all_periods = sorted(
        list(set(rev_s.keys()) | set(net_s.keys()) | set(assets_s.keys()) | set(liab_s.keys()) | set(eq_s.keys())),
        reverse=True
    )[:4]  # Maximum 4 annual periods

    all_sorted_eq_periods = sorted(list(eq_s.keys()), reverse=True)

    years_list: List[HistoricalStatementYear] = []
    for idx, p in enumerate(all_periods):
        prior_p = all_periods[idx + 1] if idx + 1 < len(all_periods) else None

        rev_v = rev_s.get(p)
        gp_v = gp_s.get(p)
        op_v = op_s.get(p)
        net_v = net_s.get(p)
        eps_v = eps_s.get(p)
        assets_v = assets_s.get(p)
        liab_v = liab_s.get(p)
        debt_v = debt_s.get(p)
        eq_curr = eq_s.get(p)

        ocf_v = ocf_s.get(p)
        capex_v = capex_s.get(p)
        capex_clean = abs(capex_v) if capex_v is not None else None
        fcf_v = (ocf_v - capex_clean) if ocf_v is not None and capex_clean is not None else ocf_v

        # Historical Margins
        gm_pct = round((gp_v / rev_v) * 100.0, 2) if rev_v and gp_v is not None and rev_v > 0 else None
        om_pct = round((op_v / rev_v) * 100.0, 2) if rev_v and op_v is not None and rev_v > 0 else None
        nm_pct = round((net_v / rev_v) * 100.0, 2) if rev_v and net_v is not None and rev_v > 0 else None

        # Return on Assets (ROA)
        roa_pct = round((net_v / assets_v) * 100.0, 2) if assets_v and net_v is not None and assets_v > 0 else None

        # Historical ROE calculation (Dual-method: 2-period average equity preferred, fallback to ending equity)
        hist_roe = None
        if net_v is not None and eq_curr is not None:
            try:
                curr_idx = all_sorted_eq_periods.index(p)
                prior_eq_p = all_sorted_eq_periods[curr_idx + 1] if curr_idx + 1 < len(all_sorted_eq_periods) else None
            except ValueError:
                prior_eq_p = None

            eq_prior = eq_s.get(prior_eq_p) if prior_eq_p else None

            if eq_prior is not None:
                avg_eq = (eq_curr + eq_prior) / 2.0
                if avg_eq > 0:
                    hist_roe = round((net_v / avg_eq) * 100.0, 2)
            elif eq_curr > 0:
                hist_roe = round((net_v / eq_curr) * 100.0, 2)

        # Historical YoY Growth across chronological consecutive periods
        rev_growth = None
        if prior_p and rev_v is not None:
            rev_prior = rev_s.get(prior_p)
            if rev_prior is not None and rev_prior > 0:
                rev_growth = round(((rev_v - rev_prior) / rev_prior) * 100.0, 2)

        net_growth = None
        if prior_p and net_v is not None:
            net_prior = net_s.get(prior_p)
            if net_prior is not None and net_prior > 0:
                net_growth = round(((net_v - net_prior) / net_prior) * 100.0, 2)

        years_list.append(
            HistoricalStatementYear(
                period=p,
                total_revenue=rev_v,
                revenue=rev_v,
                gross_profit=gp_v,
                operating_income=op_v,
                net_income=net_v,
                operating_cash_flow=ocf_v,
                capital_expenditures=capex_v,
                free_cash_flow=fcf_v,
                total_assets=assets_v,
                total_liabilities=liab_v,
                total_debt=debt_v,
                stockholders_equity=eq_curr,
                gross_margin_pct=gm_pct,
                operating_margin_pct=om_pct,
                net_margin_pct=nm_pct,
                roa_pct=roa_pct,
                roe_pct=hist_roe,
                diluted_eps=eps_v,
                revenue_growth_yoy=rev_growth,
                net_income_growth_yoy=net_growth,
            )
        )

    # Multi-year factual trend narrative synthesis
    if not years_list:
        narrative = "Historical statements not available."
    elif len(years_list) == 1:
        narrative = f"Historical multi-year financial performance is currently limited to a single reported fiscal period ({all_periods[0]}). Multi-year trends cannot be established."
    else:
        chrono_years = list(reversed(years_list))
        narrative_parts = []

        # Revenue direction
        rev_tuples = [(y.period, y.total_revenue) for y in chrono_years if y.total_revenue is not None]
        if len(rev_tuples) >= 2:
            rev_diffs = [rev_tuples[k][1] - rev_tuples[k - 1][1] for k in range(1, len(rev_tuples))]
            if all(d > 0 for d in rev_diffs):
                narrative_parts.append("revenue expanded consistently")
            elif all(d < 0 for d in rev_diffs):
                narrative_parts.append("revenue contracted steadily")
            elif rev_tuples[-1][1] > rev_tuples[0][1]:
                narrative_parts.append("revenue grew overall despite period fluctuations")
            else:
                narrative_parts.append("revenue faced downward pressure over the comparison window")

        # Net income direction
        net_tuples = [(y.period, y.net_income) for y in chrono_years if y.net_income is not None]
        if len(net_tuples) >= 2:
            net_diffs = [net_tuples[k][1] - net_tuples[k - 1][1] for k in range(1, len(net_tuples))]
            if all(d > 0 for d in net_diffs):
                narrative_parts.append("net income grew consistently")
            elif all(d < 0 for d in net_diffs):
                narrative_parts.append("net income experienced a multi-year decline")
            elif net_tuples[-1][1] > net_tuples[0][1]:
                narrative_parts.append("net income showed overall improvement")
            else:
                narrative_parts.append("net income exhibited variable performance across fiscal years")

        # Operating margin trend
        om_vals = [y.operating_margin_pct for y in chrono_years if y.operating_margin_pct is not None]
        if len(om_vals) >= 2:
            om_delta = om_vals[-1] - om_vals[0]
            if om_delta > 1.0:
                narrative_parts.append(f"operating margin expanded by {om_delta:.1f}% (from {om_vals[0]:.1f}% to {om_vals[-1]:.1f}%)")
            elif om_delta < -1.0:
                narrative_parts.append(f"operating margin compressed by {abs(om_delta):.1f}% (from {om_vals[0]:.1f}% to {om_vals[-1]:.1f}%)")
            else:
                narrative_parts.append(f"operating margin remained relatively stable at {om_vals[-1]:.1f}%")

        # Debt trajectory
        debt_vals = [y.total_debt for y in chrono_years if y.total_debt is not None]
        if len(debt_vals) >= 2:
            if debt_vals[-1] == 0 and debt_vals[0] == 0:
                narrative_parts.append("the company maintained zero debt obligations")
            elif debt_vals[0] and debt_vals[0] > 0:
                debt_delta_pct = ((debt_vals[-1] - debt_vals[0]) / debt_vals[0]) * 100.0
                if debt_delta_pct > 15.0:
                    narrative_parts.append("total debt obligations increased")
                elif debt_delta_pct < -15.0:
                    narrative_parts.append("total debt obligations were reduced")
                else:
                    narrative_parts.append("total debt remained relatively stable")

        if narrative_parts:
            body = "; ".join(narrative_parts)
            narrative = f"Across {len(years_list)} reported annual periods ({all_periods[-1]} to {all_periods[0]}), {body}."
        else:
            narrative = f"Historical multi-year financial performance compared across {len(years_list)} reported annual periods ({', '.join(all_periods)})."

    return HistoricalStatementComparison(
        periods=all_periods,
        years=years_list,
        statement_currency=stmt_curr,
        summary_narrative=narrative,
    )


# ── 6. Real-Data Peer Comparison Engine (Task 6) ──────────────────────────────

def benchmark_peers(
    target_ticker: str,
    target_market: str,
    target_sector: Optional[str],
    target_valuation: ValuationSection,
    target_profitability: ProfitabilitySection,
    target_stability: DebtStabilitySection,
    target_rev_yoy: Optional[float],
    target_overview: Optional[StockOverviewResponse] = None,
) -> PeerComparisonSection:
    clean_target = target_ticker.strip().upper()
    # Normalize market code (handles NSI -> NSE, NMS -> NASDAQ, etc.)
    target_mkt = _infer_market_from_exchange_and_symbol(clean_target, target_market)[1]

    # 1. Discover peer candidates using priority hierarchy:
    # Priority A: Curated peer mapping
    # Priority B: Same market + same sector from predefined universe
    # Priority C: Same market fallback from predefined universe
    candidate_symbols: List[str] = []
    seen_symbols = {clean_target}

    # A. Curated list
    if clean_target in CURATED_PEERS:
        for sym in CURATED_PEERS[clean_target]:
            s_up = sym.strip().upper()
            if s_up not in seen_symbols:
                candidate_symbols.append(s_up)
                seen_symbols.add(s_up)

    # B. Same market + same sector
    if len(candidate_symbols) < 4 and target_sector:
        target_sec_clean = target_sector.strip().lower()
        for item in PREDEFINED_UNIVERSE:
            p_sym = item["ticker"].upper()
            if p_sym not in seen_symbols and item.get("market") == target_mkt:
                item_sec = (item.get("sector") or "").strip().lower()
                if item_sec == target_sec_clean:
                    candidate_symbols.append(p_sym)
                    seen_symbols.add(p_sym)

    # C. Same market fallback
    if len(candidate_symbols) < 3:
        for item in PREDEFINED_UNIVERSE:
            p_sym = item["ticker"].upper()
            if p_sym not in seen_symbols and item.get("market") == target_mkt:
                candidate_symbols.append(p_sym)
                seen_symbols.add(p_sym)

    selected_symbols = candidate_symbols[:4]

    # Map candidate symbols to universe metadata if present
    universe_map = {item["ticker"].upper(): item for item in PREDEFINED_UNIVERSE}

    # 2. Extract Peer Metrics (Guaranteed exception containment)
    non_target_peers: List[PeerBenchmarkItem] = []

    for sym in selected_symbols:
        meta = universe_map.get(sym, {})
        name = meta.get("company_name", sym)
        mkt = meta.get("market", target_mkt)
        sector = meta.get("sector", target_sector)

        try:
            peer_ov = get_company_overview(sym)
            comp_name = peer_ov.company_name or name
            m_cap = peer_ov.market_cap
            pe = round(peer_ov.trailing_pe, 2) if peer_ov.trailing_pe and peer_ov.trailing_pe > 0 else (round(peer_ov.pe_ratio, 2) if peer_ov.pe_ratio and peer_ov.pe_ratio > 0 else None)
            fpe = round(peer_ov.forward_pe, 2) if peer_ov.forward_pe and peer_ov.forward_pe > 0 else None
            pb = round(peer_ov.price_to_book, 2) if peer_ov.price_to_book and peer_ov.price_to_book > 0 else None
            ind = peer_ov.industry or peer_ov.sector or sector

            # Lightweight extraction of peer financial ratios from yf.Ticker
            t_info = {}
            try:
                t = yf.Ticker(sym)
                t_info = getattr(t, "info", None) or {}
            except Exception:
                pass

            if fpe is None and t_info.get("forwardPE") and float(t_info["forwardPE"]) > 0:
                fpe = round(float(t_info["forwardPE"]), 2)
            if pb is None and t_info.get("priceToBook") and float(t_info["priceToBook"]) > 0:
                pb = round(float(t_info["priceToBook"]), 2)
            if not ind and t_info.get("industry"):
                ind = t_info["industry"]

            roe = round(float(t_info["returnOnEquity"]) * 100.0, 2) if t_info.get("returnOnEquity") is not None else None
            roa = round(float(t_info["returnOnAssets"]) * 100.0, 2) if t_info.get("returnOnAssets") is not None else None
            op_margin = round(float(t_info["operatingMargins"]) * 100.0, 2) if t_info.get("operatingMargins") is not None else None
            net_margin = round(float(t_info["profitMargins"]) * 100.0, 2) if t_info.get("profitMargins") is not None else None
            gross_margin = round(float(t_info["grossMargins"]) * 100.0, 2) if t_info.get("grossMargins") is not None else None

            de = None
            if t_info.get("debtToEquity") is not None:
                de_val = float(t_info["debtToEquity"])
                # yfinance returns debtToEquity in percent (e.g. 84.28% = 0.84x); standardize to ratio x
                de = round(de_val / 100.0, 2) if de_val > 5.0 else round(de_val, 2)

            rev_growth = round(float(t_info["revenueGrowth"]) * 100.0, 2) if t_info.get("revenueGrowth") is not None else None

            has_any_data = any(v is not None for v in [pe, fpe, pb, roe, roa, op_margin, net_margin, de, rev_growth, m_cap])
            has_full_data = all(v is not None for v in [pe, pb, roe, op_margin, net_margin])

            non_target_peers.append(
                PeerBenchmarkItem(
                    ticker=sym,
                    company_name=comp_name,
                    market=mkt,
                    industry=ind,
                    market_cap=m_cap,
                    pe_ratio=pe,
                    forward_pe=fpe,
                    pb_ratio=pb,
                    roe=roe,
                    roa=roa,
                    operating_margin=op_margin,
                    net_margin=net_margin,
                    gross_margin=gross_margin,
                    debt_to_equity=de,
                    revenue_growth_yoy=rev_growth,
                    is_target=False,
                    data_status="available" if has_full_data else ("partial" if has_any_data else "unavailable"),
                )
            )
        except Exception as exc:
            logger.warning(f"Peer benchmark retrieval failed for {sym}: {exc}")
            non_target_peers.append(
                PeerBenchmarkItem(
                    ticker=sym,
                    company_name=name,
                    market=mkt,
                    industry=sector,
                    is_target=False,
                    data_status="unavailable",
                )
            )

    # 3. Target Company Row Construction (always first item)
    target_comp_name = getattr(target_overview, "company_name", None) or clean_target
    target_industry = getattr(target_overview, "industry", None) or getattr(target_overview, "sector", None) or target_sector
    target_mcap = getattr(target_overview, "market_cap", None)

    target_pe = target_valuation.trailing_pe.value if target_valuation and target_valuation.trailing_pe and target_valuation.trailing_pe.status in ("reported", "calculated") else None
    target_fpe = target_valuation.forward_pe.value if target_valuation and target_valuation.forward_pe and target_valuation.forward_pe.status in ("reported", "calculated") else None
    target_pb = target_valuation.price_to_book.value if target_valuation and target_valuation.price_to_book and target_valuation.price_to_book.status in ("reported", "calculated") else None
    target_roe = target_profitability.return_on_equity.value if target_profitability and target_profitability.return_on_equity and target_profitability.return_on_equity.status in ("reported", "calculated") else None
    target_roa = target_profitability.return_on_assets.value if target_profitability and target_profitability.return_on_assets and target_profitability.return_on_assets.status in ("reported", "calculated") else None
    target_om = target_profitability.operating_margin.value if target_profitability and target_profitability.operating_margin and target_profitability.operating_margin.status in ("reported", "calculated") else None
    target_nm = target_profitability.net_margin.value if target_profitability and target_profitability.net_margin and target_profitability.net_margin.status in ("reported", "calculated") else None
    target_gm = target_profitability.gross_margin.value if target_profitability and target_profitability.gross_margin and target_profitability.gross_margin.status in ("reported", "calculated") else None
    target_de = target_stability.debt_to_equity.value if target_stability and target_stability.debt_to_equity and target_stability.debt_to_equity.status in ("reported", "calculated") else None
    target_growth = target_rev_yoy

    target_item = PeerBenchmarkItem(
        ticker=clean_target,
        company_name=target_comp_name,
        market=target_mkt,
        industry=target_industry,
        market_cap=target_mcap,
        pe_ratio=target_pe,
        forward_pe=target_fpe,
        pb_ratio=target_pb,
        roe=target_roe,
        roa=target_roa,
        operating_margin=target_om,
        net_margin=target_nm,
        gross_margin=target_gm,
        debt_to_equity=target_de,
        revenue_growth_yoy=target_growth,
        is_target=True,
        data_status="available",
    )

    # 4. Calculate True Medians strictly across non-target peers
    def _median(vals: List[float]) -> Optional[float]:
        clean_vals = [v for v in vals if v is not None and not (isinstance(v, float) and (math.isnan(v) or math.isinf(v)))]
        if not clean_vals:
            return None
        s = sorted(clean_vals)
        n = len(s)
        mid = n // 2
        return round((s[mid] if n % 2 != 0 else (s[mid - 1] + s[mid]) / 2.0), 2)

    # Multiples medians exclude negative/loss-making values
    median_pe = _median([p.pe_ratio for p in non_target_peers if p.pe_ratio is not None and p.pe_ratio > 0])
    median_fpe = _median([p.forward_pe for p in non_target_peers if p.forward_pe is not None and p.forward_pe > 0])
    median_pb = _median([p.pb_ratio for p in non_target_peers if p.pb_ratio is not None and p.pb_ratio > 0])

    # Financial returns, margins and leverage medians
    median_roe = _median([p.roe for p in non_target_peers if p.roe is not None])
    median_roa = _median([p.roa for p in non_target_peers if p.roa is not None])
    median_om = _median([p.operating_margin for p in non_target_peers if p.operating_margin is not None])
    median_nm = _median([p.net_margin for p in non_target_peers if p.net_margin is not None])
    median_gm = _median([p.gross_margin for p in non_target_peers if p.gross_margin is not None])
    median_de = _median([p.debt_to_equity for p in non_target_peers if p.debt_to_equity is not None])
    median_growth = _median([p.revenue_growth_yoy for p in non_target_peers if p.revenue_growth_yoy is not None])

    # 5. Evaluate Multi-Dimensional Relative Positioning
    # A. Relative Valuation Position
    rel_val = "In Line"
    if target_valuation and target_valuation.trailing_pe and target_valuation.trailing_pe.status == "loss_making":
        rel_val = "Not Applicable (Loss-Making)"
    elif target_pe is not None and median_pe is not None:
        if target_pe < median_pe * 0.90:
            rel_val = "Below Peer Median (Discount)"
        elif target_pe > median_pe * 1.10:
            rel_val = "Above Peer Median (Premium)"
        else:
            rel_val = "In Line"
    elif target_pb is not None and median_pb is not None:
        if target_pb < median_pb * 0.90:
            rel_val = "Below Peer Median (Discount)"
        elif target_pb > median_pb * 1.10:
            rel_val = "Above Peer Median (Premium)"
        else:
            rel_val = "In Line"
    elif median_pe is None and median_pb is None:
        rel_val = "Not Computable"

    # B. Relative Profitability Position
    rel_prof = "In Line"
    if target_roe is not None and median_roe is not None:
        if target_roe > median_roe * 1.05:
            rel_prof = "Above Peer Median (Outperforming)"
        elif target_roe < median_roe * 0.95:
            rel_prof = "Below Peer Median (Underperforming)"
        else:
            rel_prof = "In Line"
    elif target_nm is not None and median_nm is not None:
        if target_nm > median_nm * 1.05:
            rel_prof = "Above Peer Median (Outperforming)"
        elif target_nm < median_nm * 0.95:
            rel_prof = "Below Peer Median (Underperforming)"
        else:
            rel_prof = "In Line"
    elif median_roe is None and median_nm is None:
        rel_prof = "Not Computable"

    # C. Relative Leverage Position
    rel_lev = "In Line"
    if target_de is not None and median_de is not None:
        if target_de < median_de * 0.85:
            rel_lev = "Conservative"
        elif target_de > median_de * 1.15:
            rel_lev = "Elevated"
        else:
            rel_lev = "In Line"
    elif target_de is not None and target_de <= 0.20:
        rel_lev = "Conservative"
    elif median_de is None:
        rel_lev = "Not Computable"

    # D. Relative Financial Strength Position
    rel_strength = "In Line"
    if rel_lev == "Conservative" and ("Above" in rel_prof or rel_prof == "In Line"):
        rel_strength = "Strong"
    elif rel_lev == "Elevated" and "Below" in rel_prof:
        rel_strength = "Vulnerable"
    elif rel_lev == "Conservative":
        rel_strength = "Strong"
    elif rel_lev == "Elevated":
        rel_strength = "Vulnerable"
    else:
        rel_strength = "In Line"

    # 6. Overall Section Data Status
    valid_peer_count = sum(1 for p in non_target_peers if p.data_status in ("available", "partial"))
    if not non_target_peers:
        section_status = "unavailable"
    elif valid_peer_count == len(non_target_peers):
        section_status = "available"
    elif valid_peer_count > 0:
        section_status = "partial"
    else:
        section_status = "unavailable"

    # 7. Comprehensive Multi-Metric Factual Summary Narrative
    if not non_target_peers:
        narrative = f"No comparable peer equities were identified in the {target_mkt} market for benchmarking."
    else:
        peer_tickers_str = ", ".join(p.ticker for p in non_target_peers)
        narrative_parts = [
            f"Benchmarked against {len(non_target_peers)} comparable {target_mkt} peer equities ({peer_tickers_str})."
        ]

        # Valuation sentence
        if rel_val == "Not Applicable (Loss-Making)":
            narrative_parts.append("Valuation multiple is not applicable due to reported net losses.")
        elif target_pe is not None and median_pe is not None:
            if "Discount" in rel_val:
                narrative_parts.append(f"Trades at a valuation discount with Trailing P/E of {target_pe:.2f}x compared to peer median of {median_pe:.2f}x.")
            elif "Premium" in rel_val:
                narrative_parts.append(f"Commands a valuation premium with Trailing P/E of {target_pe:.2f}x versus peer median of {median_pe:.2f}x.")
            else:
                narrative_parts.append(f"Valuation is in line with peers at a Trailing P/E of {target_pe:.2f}x (peer median: {median_pe:.2f}x).")
        elif target_pb is not None and median_pb is not None:
            narrative_parts.append(f"Price-to-Book multiple is {target_pb:.2f}x versus peer median of {median_pb:.2f}x ({rel_val}).")

        # Profitability sentence
        if target_roe is not None and median_roe is not None:
            if "Above" in rel_prof:
                narrative_parts.append(f"Capital efficiency outperforms the peer group with an ROE of {target_roe:.2f}% versus peer median of {median_roe:.2f}%.")
            elif "Below" in rel_prof:
                narrative_parts.append(f"Capital efficiency trails peers with an ROE of {target_roe:.2f}% versus peer median of {median_roe:.2f}%.")
            else:
                narrative_parts.append(f"Return on Equity of {target_roe:.2f}% is comparable to peer median of {median_roe:.2f}%.")

        # Leverage sentence
        if target_de is not None and median_de is not None:
            if rel_lev == "Conservative":
                narrative_parts.append(f"Capital structure reflects conservative leverage with Debt-to-Equity of {target_de:.2f}x versus peer median of {median_de:.2f}x.")
            elif rel_lev == "Elevated":
                narrative_parts.append(f"Leverage is elevated relative to peers with Debt-to-Equity of {target_de:.2f}x versus peer median of {median_de:.2f}x.")
            else:
                narrative_parts.append(f"Debt-to-Equity ratio of {target_de:.2f}x is in line with peer median of {median_de:.2f}x.")
        elif target_de is not None and target_de <= 0.20:
            narrative_parts.append(f"Maintains a low-debt capital structure with Debt-to-Equity of {target_de:.2f}x.")

        narrative = " ".join(narrative_parts)

    # All peers: target item at index 0, followed by non-target peers
    all_peer_items = [target_item] + non_target_peers

    return PeerComparisonSection(
        target_ticker=clean_target,
        peers=all_peer_items,
        peer_median_pe=median_pe,
        peer_median_forward_pe=median_fpe,
        peer_median_pb=median_pb,
        peer_median_roe=median_roe,
        peer_median_roa=median_roa,
        peer_median_operating_margin=median_om,
        peer_median_net_margin=median_nm,
        peer_median_gross_margin=median_gm,
        peer_median_debt_to_equity=median_de,
        peer_median_revenue_growth=median_growth,
        relative_valuation_position=rel_val,
        relative_profitability_position=rel_prof,
        relative_leverage_position=rel_lev,
        relative_financial_strength_position=rel_strength,
        data_status=section_status,
        summary_narrative=narrative,
    )


# ── 7. Data Integrity & Inconsistency Audit Engine ────────────────────────────

def audit_data_integrity(
    statements: FinancialStatementsResponse,
    overview: StockOverviewResponse
) -> DataIntegrityAudit:
    annual_income = getattr(statements.income_statement, "annual", None)
    annual_balance = getattr(statements.balance_sheet, "annual", None)
    annual_cashflow = getattr(statements.cash_flow, "annual", None)

    missing_items: List[str] = []
    inconsistent_items: List[str] = []
    warnings: List[str] = []
    suspicious_values_detected: List[str] = []
    structured_findings: List[AuditFindingItem] = []

    # 1. Statement existence & Period Extraction
    income_periods: List[str] = []
    if annual_income and annual_income.items:
        for it in annual_income.items:
            for p in it.values.keys():
                if p not in income_periods:
                    income_periods.append(p)
    else:
        missing_items.append("Income Statement (Annual)")

    balance_periods: List[str] = []
    if annual_balance and annual_balance.items:
        for it in annual_balance.items:
            for p in it.values.keys():
                if p not in balance_periods:
                    balance_periods.append(p)
    else:
        missing_items.append("Balance Sheet (Annual)")

    cashflow_periods: List[str] = []
    if annual_cashflow and annual_cashflow.items:
        for it in annual_cashflow.items:
            for p in it.values.keys():
                if p not in cashflow_periods:
                    cashflow_periods.append(p)
    else:
        missing_items.append("Cash Flow Statement (Annual)")

    all_periods_set = set(income_periods) | set(balance_periods) | set(cashflow_periods)
    periods_audited = sorted(list(all_periods_set), reverse=True)

    # 2. Period Alignment & Duplicate Check
    stmt_count = sum(1 for s in [annual_income, annual_balance, annual_cashflow] if s and s.items)
    period_alignment_status = "aligned"
    period_alignment_notes = ""

    if stmt_count == 3:
        inc_set = set(income_periods)
        bal_set = set(balance_periods)
        cf_set = set(cashflow_periods)
        if inc_set == bal_set == cf_set and inc_set:
            period_alignment_status = "aligned"
            period_alignment_notes = f"All 3 statements report synchronized annual fiscal periods: {', '.join(periods_audited)}."
        elif inc_set & bal_set & cf_set:
            period_alignment_status = "partial"
            common = sorted(list(inc_set & bal_set & cf_set), reverse=True)
            period_alignment_notes = f"Partial period synchronization across statements. Common periods: {', '.join(common)}. Total distinct periods: {len(periods_audited)}."
        else:
            period_alignment_status = "misaligned"
            period_alignment_notes = "Reporting periods across financial statements do not overlap."
            warnings.append(period_alignment_notes)
            structured_findings.append(AuditFindingItem(
                category="alignment",
                title="Statement Period Misalignment",
                statement="Cross-Statement",
                severity="medium",
                explanation=period_alignment_notes
            ))
    elif stmt_count > 0:
        period_alignment_status = "partial"
        period_alignment_notes = f"Audit completed over {len(periods_audited)} periods with {stmt_count} of 3 statements available."
    else:
        period_alignment_status = "misaligned"
        period_alignment_notes = "No financial statements available for period alignment audit."

    # 3. Extraction of Key Series
    rev_s = _extract_series_from_statement(annual_income, "revenue")
    net_s = _extract_series_from_statement(annual_income, "net_income")
    opinc_s = _extract_series_from_statement(annual_income, "operating_income")
    gp_s = _extract_series_from_statement(annual_income, "gross_profit")
    eps_s = _extract_series_from_statement(annual_income, "diluted_eps")
    tax_s = _extract_series_from_statement(annual_income, "tax_expense")
    int_exp_s = _extract_series_from_statement(annual_income, "interest_expense")
    cogs_s = _extract_series_from_statement(annual_income, "cost_of_revenue")
    opex_s = _extract_series_from_statement(annual_income, "operating_expense")

    assets_s = _extract_series_from_statement(annual_balance, "total_assets")
    liab_s = _extract_series_from_statement(annual_balance, "total_liabilities")
    equity_s = _extract_series_from_statement(annual_balance, "stockholders_equity")
    cur_assets_s = _extract_series_from_statement(annual_balance, "current_assets")
    cur_liab_s = _extract_series_from_statement(annual_balance, "current_liabilities")
    cash_s = _extract_series_from_statement(annual_balance, "cash_and_equivalents")
    tot_debt_s = _extract_series_from_statement(annual_balance, "total_debt")
    st_debt_s = _extract_series_from_statement(annual_balance, "short_term_debt")
    lt_debt_s = _extract_series_from_statement(annual_balance, "long_term_debt")

    ocf_s = _extract_series_from_statement(annual_cashflow, "operating_cash_flow")
    capex_s = _extract_series_from_statement(annual_cashflow, "capital_expenditure")
    fcf_s = _extract_series_from_statement(annual_cashflow, "free_cash_flow")
    cf_net_s = _extract_series_from_statement(annual_cashflow, "net_income")

    # 4. 16 Line Item Completeness Checks
    critical_checks = [
        ("Total Revenue", rev_s, "Income Statement", "high"),
        ("Net Income", net_s, "Income Statement", "high"),
        ("Operating Income", opinc_s, "Income Statement", "high"),
        ("Gross Profit", gp_s, "Income Statement", "medium"),
        ("Diluted EPS", eps_s, "Income Statement", "medium"),
        ("Tax Expense", tax_s, "Income Statement", "low"),
        ("Interest Expense", int_exp_s, "Income Statement", "low"),
        ("Total Assets", assets_s, "Balance Sheet", "high"),
        ("Total Liabilities", liab_s, "Balance Sheet", "high"),
        ("Stockholders' Equity", equity_s, "Balance Sheet", "high"),
        ("Current Assets", cur_assets_s, "Balance Sheet", "medium"),
        ("Current Liabilities", cur_liab_s, "Balance Sheet", "medium"),
        ("Cash and Cash Equivalents", cash_s, "Balance Sheet", "medium"),
        ("Total Debt", tot_debt_s, "Balance Sheet", "medium"),
        ("Operating Cash Flow", ocf_s, "Cash Flow Statement", "high"),
        ("Capital Expenditures", capex_s, "Cash Flow Statement", "medium"),
    ]

    for item_name, series_data, stmt_name, severity in critical_checks:
        if not series_data:
            missing_items.append(f"{item_name} ({stmt_name})")
            structured_findings.append(AuditFindingItem(
                category="completeness",
                title=f"Missing Line Item: {item_name}",
                statement=stmt_name,
                severity=severity,
                explanation=f"{item_name} line item is absent or unpopulated in {stmt_name}."
            ))

    # 5. Multi-Period Accounting Equation Verification: Assets ≈ Liabilities + Equity
    multi_period_balance_audits: List[BalanceSheetPeriodAudit] = []
    bs_periods = sorted(list(set(assets_s.keys()) | set(liab_s.keys()) | set(equity_s.keys())), reverse=True)
    all_equations_hold = True
    any_equation_evaluated = False
    latest_bs_disc: Optional[float] = None
    latest_bs_holds: Optional[bool] = None

    for p in bs_periods:
        a = assets_s.get(p)
        l = liab_s.get(p)
        e = equity_s.get(p)

        if a is not None and l is not None and e is not None and a > 0:
            any_equation_evaluated = True
            sum_le = l + e
            diff = abs(a - sum_le)
            disc_pct = round((diff / a) * 100.0, 2)
            holds = disc_pct <= 2.0
            status = "balanced" if holds else "discrepancy"

            if not holds:
                all_equations_hold = False
                inconsistent_items.append(
                    f"Balance sheet mismatch in {p}: Assets ({a:,.0f}) != Liabilities + Equity ({sum_le:,.0f}), discrepancy {disc_pct}%."
                )
                warnings.append(
                    f"Accounting equation discrepancy of {disc_pct}% detected in period {p}."
                )
                structured_findings.append(AuditFindingItem(
                    category="consistency",
                    title=f"Balance Sheet Discrepancy ({p})",
                    statement="Balance Sheet",
                    period=p,
                    severity="high",
                    explanation=f"Accounting equation Assets != Liabilities + Equity in fiscal year {p}. Assets={a:,.0f}, Liabilities+Equity={sum_le:,.0f}, variance={diff:,.0f} ({disc_pct}%).",
                    values={"assets": a, "liabilities": l, "equity": e, "discrepancy_pct": disc_pct}
                ))

            if latest_bs_disc is None:
                latest_bs_disc = disc_pct
                latest_bs_holds = holds

            multi_period_balance_audits.append(BalanceSheetPeriodAudit(
                period=p,
                total_assets=a,
                total_liabilities=l,
                stockholders_equity=e,
                discrepancy_amount=round(diff, 2),
                discrepancy_pct=disc_pct,
                equation_holds=holds,
                status=status
            ))
        elif a is not None:
            multi_period_balance_audits.append(BalanceSheetPeriodAudit(
                period=p,
                total_assets=a,
                total_liabilities=l,
                stockholders_equity=e,
                discrepancy_amount=None,
                discrepancy_pct=None,
                equation_holds=None,
                status="insufficient_data"
            ))

    top_bs_holds = all_equations_hold if any_equation_evaluated else None
    top_bs_disc = latest_bs_disc

    # 6. Cross-Statement & Breakdown Reconciliations
    # (a) Total Debt vs Short-term + Long-term debt
    if tot_debt_s and st_debt_s and lt_debt_s:
        for p in set(tot_debt_s.keys()) & set(st_debt_s.keys()) & set(lt_debt_s.keys()):
            td = tot_debt_s[p]
            st = st_debt_s[p]
            lt = lt_debt_s[p]
            if td > 0:
                calc_tot = st + lt
                diff_debt = abs(td - calc_tot)
                debt_disc_pct = round((diff_debt / td) * 100.0, 2)
                if debt_disc_pct > 2.0:
                    inconsistent_items.append(
                        f"Debt breakdown variance in {p}: Total Debt ({td:,.0f}) != Short-term ({st:,.0f}) + Long-term ({lt:,.0f}), discrepancy {debt_disc_pct}%."
                    )
                    structured_findings.append(AuditFindingItem(
                        category="consistency",
                        title=f"Debt Breakdown Mismatch ({p})",
                        statement="Balance Sheet",
                        period=p,
                        severity="medium",
                        explanation=f"Short-Term Debt ({st:,.0f}) + Long-Term Debt ({lt:,.0f}) differs from reported Total Debt ({td:,.0f}) by {debt_disc_pct}%.",
                        values={"total_debt": td, "short_term_debt": st, "long_term_debt": lt, "discrepancy_pct": debt_disc_pct}
                    ))

    # (b) Gross Profit vs Revenue - COGS
    if rev_s and gp_s and cogs_s:
        for p in set(rev_s.keys()) & set(gp_s.keys()) & set(cogs_s.keys()):
            r = rev_s[p]
            gp = gp_s[p]
            cg = cogs_s[p]
            if r > 0:
                expected_gp = r - cg
                diff_gp = abs(expected_gp - gp)
                gp_disc_pct = round((diff_gp / r) * 100.0, 2)
                if gp_disc_pct > 2.0:
                    inconsistent_items.append(
                        f"Gross profit variance in {p}: Reported ({gp:,.0f}) != Revenue - COGS ({expected_gp:,.0f}), discrepancy {gp_disc_pct}%."
                    )
                    structured_findings.append(AuditFindingItem(
                        category="consistency",
                        title=f"Gross Profit Calculation Discrepancy ({p})",
                        statement="Income Statement",
                        period=p,
                        severity="medium",
                        explanation=f"Reported Gross Profit ({gp:,.0f}) deviates from Revenue ({r:,.0f}) minus COGS ({cg:,.0f}) by {gp_disc_pct}% of revenue.",
                        values={"reported_gross_profit": gp, "calculated_gross_profit": expected_gp, "discrepancy_pct": gp_disc_pct}
                    ))

    # (c) Free Cash Flow vs OCF - Capex
    if fcf_s and ocf_s and capex_s:
        for p in set(fcf_s.keys()) & set(ocf_s.keys()) & set(capex_s.keys()):
            rep_fcf = fcf_s[p]
            ocf = ocf_s[p]
            cap = capex_s[p]
            calc_fcf = ocf - abs(cap)
            if abs(rep_fcf) > 0:
                fcf_disc = round(abs(rep_fcf - calc_fcf) / abs(rep_fcf) * 100.0, 2)
                if fcf_disc > 5.0:
                    inconsistent_items.append(
                        f"FCF variance in {p}: Reported ({rep_fcf:,.0f}) != OCF - Capex ({calc_fcf:,.0f}), discrepancy {fcf_disc}%."
                    )
                    structured_findings.append(AuditFindingItem(
                        category="consistency",
                        title=f"Free Cash Flow Discrepancy ({p})",
                        statement="Cash Flow Statement",
                        period=p,
                        severity="low",
                        explanation=f"Reported FCF ({rep_fcf:,.0f}) differs from Operating Cash Flow ({ocf:,.0f}) - Capex ({abs(cap):,.0f}) by {fcf_disc}%.",
                        values={"reported_fcf": rep_fcf, "calculated_fcf": calc_fcf, "discrepancy_pct": fcf_disc}
                    ))

    # (d) Net Income (IS vs CFS)
    if net_s and cf_net_s:
        for p in set(net_s.keys()) & set(cf_net_s.keys()):
            ni_is = net_s[p]
            ni_cf = cf_net_s[p]
            if abs(ni_is) > 0:
                ni_disc = round(abs(ni_is - ni_cf) / abs(ni_is) * 100.0, 2)
                if ni_disc > 2.0:
                    inconsistent_items.append(
                        f"Net income statement variance in {p}: Income Statement ({ni_is:,.0f}) != Cash Flow Statement ({ni_cf:,.0f}), discrepancy {ni_disc}%."
                    )
                    structured_findings.append(AuditFindingItem(
                        category="consistency",
                        title=f"Net Income Cross-Statement Variance ({p})",
                        statement="Cross-Statement",
                        period=p,
                        severity="medium",
                        explanation=f"Net income reported in Income Statement ({ni_is:,.0f}) differs from Cash Flow Statement ({ni_cf:,.0f}) by {ni_disc}%.",
                        values={"is_net_income": ni_is, "cf_net_income": ni_cf, "discrepancy_pct": ni_disc}
                    ))

    # 7. Suspicious Values & Sanity Checks
    # Non-positive assets
    for p, a_val in assets_s.items():
        if a_val <= 0:
            msg = f"Non-positive Total Assets ({a_val:,.0f}) reported in period {p}."
            suspicious_values_detected.append(msg)
            warnings.append(msg)
            structured_findings.append(AuditFindingItem(
                category="plausibility",
                title=f"Non-Positive Total Assets ({p})",
                statement="Balance Sheet",
                period=p,
                severity="high",
                explanation="Total assets cannot be zero or negative under standard accounting frameworks.",
                values={"total_assets": a_val}
            ))

    # Negative cash balance
    for p, c_val in cash_s.items():
        if c_val < 0:
            msg = f"Negative Cash and Cash Equivalents ({c_val:,.0f}) reported in period {p}."
            suspicious_values_detected.append(msg)
            warnings.append(msg)
            structured_findings.append(AuditFindingItem(
                category="plausibility",
                title=f"Negative Cash Balance ({p})",
                statement="Balance Sheet",
                period=p,
                severity="high",
                explanation="Cash and cash equivalents reported as negative, indicating possible overdraft or reporting irregularity.",
                values={"cash_and_equivalents": c_val}
            ))

    # Negative revenue
    for p, r_val in rev_s.items():
        if r_val < 0:
            msg = f"Negative Revenue ({r_val:,.0f}) reported in period {p}."
            suspicious_values_detected.append(msg)
            warnings.append(msg)
            structured_findings.append(AuditFindingItem(
                category="plausibility",
                title=f"Negative Revenue ({p})",
                statement="Income Statement",
                period=p,
                severity="high",
                explanation="Reported operating revenue is negative, indicating abnormal accounting adjustments or data error.",
                values={"revenue": r_val}
            ))

    # Margin sanity bounds
    for p, r_val in rev_s.items():
        if r_val > 0:
            if p in gp_s:
                gm = (gp_s[p] / r_val) * 100.0
                if gm > 100.0 or gm < -100.0:
                    msg = f"Extreme Gross Margin ({gm:.1f}%) in period {p} falls outside [-100%, +100%]."
                    suspicious_values_detected.append(msg)
                    warnings.append(msg)
                    structured_findings.append(AuditFindingItem(
                        category="plausibility",
                        title=f"Extreme Gross Margin ({p})",
                        statement="Income Statement",
                        period=p,
                        severity="medium",
                        explanation=msg,
                        values={"gross_margin": round(gm, 2)}
                    ))
            if p in opinc_s:
                opm = (opinc_s[p] / r_val) * 100.0
                if opm > 100.0 or opm < -100.0:
                    msg = f"Extreme Operating Margin ({opm:.1f}%) in period {p} falls outside [-100%, +100%]."
                    suspicious_values_detected.append(msg)
                    warnings.append(msg)
                    structured_findings.append(AuditFindingItem(
                        category="plausibility",
                        title=f"Extreme Operating Margin ({p})",
                        statement="Income Statement",
                        period=p,
                        severity="medium",
                        explanation=msg,
                        values={"operating_margin": round(opm, 2)}
                    ))

    # Negative equity audit warning
    for p, e_val in equity_s.items():
        if e_val < 0:
            msg = f"Stockholders' equity for {p} is negative ({e_val:,.0f}, accumulated deficit). Ratios dependent on equity are flagged accordingly."
            warnings.append(msg)
            structured_findings.append(AuditFindingItem(
                category="plausibility",
                title=f"Negative Stockholders Equity ({p})",
                statement="Balance Sheet",
                period=p,
                severity="medium",
                explanation=msg,
                values={"stockholders_equity": e_val}
            ))
            break

    # 8. Currency Mismatch Audit
    trading_curr = (
        getattr(overview, "currency", None)
        or getattr(statements, "currency", None)
        or "USD"
    ).upper()
    rep_curr = (
        getattr(statements, "financial_currency", None)
        or getattr(overview, "financial_currency", None)
        or getattr(statements, "currency", None)
        or trading_curr
    ).upper()
    curr_mismatch = (trading_curr != rep_curr)
    curr_notes = None

    if curr_mismatch:
        curr_notes = (
            f"Trading currency ({trading_curr}) differs from financial statement reporting currency ({rep_curr}). "
            "Market-derived valuation multiples (e.g., P/B) require unified currency conversions or ADR share ratio adjustments."
        )
        warnings.append(curr_notes)
        structured_findings.append(AuditFindingItem(
            category="currency",
            title="Currency Reporting Variance",
            statement="Cross-Statement",
            severity="info",
            explanation=curr_notes,
            values={"trading_currency": trading_curr, "reporting_currency": rep_curr}
        ))

    # 9. Weighted Scoring Model (4 Categories)
    # (a) Completeness: 40%
    comp_score = 100.0
    if not annual_income or not annual_income.items:
        comp_score -= 30.0
    if not annual_balance or not annual_balance.items:
        comp_score -= 35.0
    if not annual_cashflow or not annual_cashflow.items:
        comp_score -= 25.0
    for _, series_data, _, sev in critical_checks:
        if not series_data:
            if sev == "high":
                comp_score -= 4.0
            elif sev == "medium":
                comp_score -= 2.0
            else:
                comp_score -= 1.0
    comp_score = max(0.0, min(100.0, round(comp_score, 1)))

    # (b) Consistency: 30%
    cons_score = 100.0
    if top_bs_holds is False:
        cons_score -= 35.0
    elif top_bs_disc and top_bs_disc > 2.0:
        cons_score -= 25.0
    elif top_bs_disc and top_bs_disc > 1.0:
        cons_score -= 10.0
    cons_score -= min(40.0, len(inconsistent_items) * 10.0)
    cons_score = max(0.0, min(100.0, round(cons_score, 1)))

    # (c) Plausibility: 20%
    plaus_score = 100.0
    for s_msg in suspicious_values_detected:
        if "Total Assets" in s_msg:
            plaus_score -= 50.0
        elif "Cash" in s_msg:
            plaus_score -= 30.0
        elif "Revenue" in s_msg:
            plaus_score -= 30.0
        elif "Margin" in s_msg:
            plaus_score -= 15.0
    if any(e_val < 0 for e_val in equity_s.values()):
        plaus_score -= 10.0
    plaus_score = max(0.0, min(100.0, round(plaus_score, 1)))

    # (d) Period Alignment: 10%
    if period_alignment_status == "aligned":
        align_score = 100.0
    elif period_alignment_status == "partial":
        align_score = 75.0
    else:
        align_score = 35.0

    category_scores = AuditCategoryScores(
        completeness=comp_score,
        consistency=cons_score,
        plausibility=plaus_score,
        period_alignment=align_score,
    )

    weighted_score = round(
        (comp_score * 0.40) +
        (cons_score * 0.30) +
        (plaus_score * 0.20) +
        (align_score * 0.10),
        1
    )
    weighted_score = max(0.0, min(100.0, weighted_score))

    # Data Quality Tier
    if weighted_score >= 90.0:
        tier = "High Quality"
    elif weighted_score >= 75.0:
        tier = "Acceptable"
    elif weighted_score >= 50.0:
        tier = "Caveats"
    else:
        tier = "Low Quality"

    # Overall Status
    critical_plausibility_fail = any("Total Assets" in s for s in suspicious_values_detected)
    if weighted_score >= 75.0 and (top_bs_holds is True or top_bs_holds is None) and not critical_plausibility_fail and len(inconsistent_items) == 0:
        overall_status = "pass"
    elif weighted_score < 50.0 or top_bs_holds is False or critical_plausibility_fail:
        overall_status = "fail"
    else:
        overall_status = "caveats"

    is_consistent = (
        len(inconsistent_items) == 0
        and len(suspicious_values_detected) == 0
        and (top_bs_holds is True or top_bs_holds is None)
    )

    # 10. Factual Summary Narrative
    narrative_parts = [
        f"Data integrity audit completed with overall rating: {overall_status.upper()} (Data Quality Score: {weighted_score}/100, Tier: {tier})."
    ]
    if periods_audited:
        narrative_parts.append(
            f"Evaluated {len(periods_audited)} annual reporting periods ({', '.join(periods_audited[:4])}) across {stmt_count} of 3 statements."
        )
    if top_bs_holds is True:
        narrative_parts.append(
            f"The fundamental accounting equation (Assets = Liabilities + Equity) holds across all {len(multi_period_balance_audits)} evaluated balance sheet periods (latest variance {top_bs_disc or 0.0}%)."
        )
    elif top_bs_holds is False:
        narrative_parts.append(
            f"Accounting equation discrepancy of {top_bs_disc}% detected in balance sheet data; adjustments or non-controlling interests may be present."
        )
    else:
        narrative_parts.append("Accounting equation could not be fully verified due to incomplete balance sheet line items.")

    if missing_items:
        narrative_parts.append(f"{len(missing_items)} line items or statements missing or unpopulated.")
    else:
        narrative_parts.append("All 16 audited financial line items are populated across statements.")

    if curr_mismatch:
        narrative_parts.append(f"Currency variance identified: trading in {trading_curr} vs reporting in {rep_curr}.")

    if suspicious_values_detected:
        narrative_parts.append(f"{len(suspicious_values_detected)} sanity/plausibility alerts flagged.")

    summary_narrative = " ".join(narrative_parts)

    return DataIntegrityAudit(
        is_consistent=is_consistent,
        balance_sheet_equation_holds=top_bs_holds,
        balance_sheet_discrepancy_pct=top_bs_disc,
        missing_line_items=missing_items,
        inconsistent_items=inconsistent_items,
        audit_warnings=warnings,
        data_quality_score=weighted_score,
        data_quality_tier=tier,
        category_scores=category_scores,
        currency_mismatch_detected=curr_mismatch,
        trading_currency=trading_curr,
        reporting_currency=rep_curr,
        currency_notes=curr_notes,
        period_alignment_status=period_alignment_status,
        period_alignment_notes=period_alignment_notes,
        periods_audited=periods_audited,
        suspicious_values_detected=suspicious_values_detected,
        multi_period_balance_audits=multi_period_balance_audits,
        structured_findings=structured_findings,
        overall_status=overall_status,
        summary_narrative=summary_narrative,
    )


# ── 8. Optional Enhancements Section (Clearly Segregated) ─────────────────────

def calculate_optional_enhancements(
    overview: StockOverviewResponse,
    statements: FinancialStatementsResponse
) -> OptionalEnhancementsSection:
    price = overview.current_price
    mcap = overview.market_cap

    annual_income = getattr(statements.income_statement, "annual", None)
    annual_balance = getattr(statements.balance_sheet, "annual", None)

    rev_s = _extract_series_from_statement(annual_income, "revenue")
    t0 = list(rev_s.keys())[0] if rev_s else None

    # Price to Sales (P/S)
    ps_metric = None
    if mcap and t0 and rev_s.get(t0) and rev_s[t0] > 0:
        ps_val = round(mcap / rev_s[t0], 2)
        ps_metric = MetricItem(
            name="price_to_sales",
            value=ps_val,
            formatted=_format_multiple(ps_val),
            period=t0,
            status="calculated",
            method="market_cap_over_revenue",
        )

    # Dividend Yield
    div_metric = None
    if overview.dividend_yield is not None:
        div_metric = MetricItem(
            name="dividend_yield",
            value=round(overview.dividend_yield * 100.0, 2),
            formatted=f"{overview.dividend_yield * 100.0:.2f}%",
            status="reported",
        )

    return OptionalEnhancementsSection(
        price_to_sales=ps_metric,
        dividend_yield=div_metric,
    )


# ── Master Orchestrator: run_fundamental_analysis ─────────────────────────────

def run_fundamental_analysis(
    ticker: str,
    statements: Optional[FinancialStatementsResponse] = None,
    overview: Optional[StockOverviewResponse] = None,
    financials: Optional[FinancialStatementsResponse] = None,
) -> FundamentalAnalysisResponse:
    """
    Executes the comprehensive Fundamental Analysis Agent workflow.
    Guarantees zero raw unhandled exceptions: all errors are logged and safe fallbacks returned.
    Accepts either `statements` or `financials` keyword arguments.
    """
    if statements is None and financials is not None:
        statements = financials

    clean_ticker = ticker.strip().upper()
    raw_exchange = getattr(overview, "exchange", None) or getattr(overview, "market", None)
    _, standard_market = _infer_market_from_exchange_and_symbol(clean_ticker, raw_exchange)
    market = standard_market or getattr(overview, "market", None) or "NSE"
    company_name = getattr(overview, "company_name", None) or clean_ticker
    currency = getattr(statements, "currency", None) or getattr(overview, "currency", None) or "USD"
    now_str = datetime.now(timezone.utc).isoformat()

    try:
        if statements is None:
            raise ValueError(f"No financial statements available for {clean_ticker}")

        rev_section = analyze_revenue_and_earnings(statements, overview)
        prof_section = analyze_profitability(statements, overview)
        stab_section = analyze_financial_stability(statements, overview)
        val_section = calculate_valuation_ratios(overview, statements, prof_section)
        hist_section = build_historical_comparison(statements, overview)
        peer_section = benchmark_peers(
            target_ticker=clean_ticker,
            target_market=market,
            target_sector=getattr(overview, "sector", None),
            target_valuation=val_section,
            target_profitability=prof_section,
            target_stability=stab_section,
            target_rev_yoy=rev_section.revenue_growth_yoy.value,
            target_overview=overview,
        )
        audit_section = audit_data_integrity(statements, overview)
        opt_section = calculate_optional_enhancements(overview, statements)

        # Executive summary synthesis
        exec_summary = (
            f"Fundamental analysis for {company_name} ({clean_ticker}) on {market}. "
            f"{rev_section.summary_narrative} {prof_section.summary_narrative} "
            f"{stab_section.summary_narrative} {val_section.summary_narrative}"
        )

        return FundamentalAnalysisResponse(
            status="success",
            ticker=clean_ticker,
            company_name=company_name,
            market=market,
            currency=currency,
            statement_currency=hist_section.statement_currency,
            retrieval_timestamp=now_str,
            data_source="yfinance",
            revenue_and_earnings=rev_section,
            profitability=prof_section,
            debt_and_stability=stab_section,
            valuation_ratios=val_section,
            historical_comparison=hist_section,
            peer_comparison=peer_section,
            data_integrity_audit=audit_section,
            optional_enhancements=opt_section,
            executive_summary=exec_summary,
        )

    except Exception as exc:
        # Final Safeguard 2: Log technical error, return safe user-facing response
        logger.error(f"FundamentalAnalysisAgent unexpected error for {clean_ticker}: {exc}", exc_info=True)
        fallback_metric = MetricItem(name="unavailable", formatted="N/A", status="unavailable", notes="Data could not be processed.")
        return FundamentalAnalysisResponse(
            status="partial",
            ticker=clean_ticker,
            company_name=company_name,
            market=market,
            currency=currency,
            statement_currency=None,
            retrieval_timestamp=now_str,
            data_source="yfinance",
            revenue_and_earnings=RevenueEarningsSection(
                revenue=fallback_metric, revenue_growth_yoy=fallback_metric, revenue_growth_qoq=fallback_metric,
                revenue_cagr=fallback_metric, gross_profit=fallback_metric, operating_income=fallback_metric,
                net_income=fallback_metric, net_income_growth_yoy=fallback_metric, net_income_cagr=fallback_metric,
                diluted_eps=fallback_metric, basic_eps=fallback_metric, earnings_quality_ratio=fallback_metric,
                summary_narrative="Partial fundamental analysis data available."
            ),
            profitability=ProfitabilitySection(
                gross_margin=fallback_metric, operating_margin=fallback_metric, net_margin=fallback_metric,
                return_on_assets=fallback_metric, return_on_equity=fallback_metric, margin_trend="Insufficient Data",
                summary_narrative="Profitability metrics could not be fully derived."
            ),
            debt_and_stability=DebtStabilitySection(
                total_debt=fallback_metric, net_debt=fallback_metric, debt_to_equity=fallback_metric,
                debt_to_assets=fallback_metric, current_ratio=fallback_metric, quick_ratio=fallback_metric,
                interest_coverage=fallback_metric, free_cash_flow=fallback_metric, stability_rating="Insufficient Data",
                summary_narrative="Solvency metrics could not be fully derived."
            ),
            valuation_ratios=ValuationSection(
                trailing_pe=fallback_metric, forward_pe=fallback_metric, price_to_book=fallback_metric,
                return_on_equity=fallback_metric, summary_narrative="Valuation multiples unavailable."
            ),
            historical_comparison=HistoricalStatementComparison(periods=[], years=[], summary_narrative="Historical statements unavailable."),
            peer_comparison=PeerComparisonSection(target_ticker=clean_ticker, peers=[], summary_narrative="Peer benchmark unavailable."),
            data_integrity_audit=DataIntegrityAudit(is_consistent=False, audit_warnings=["Financial statement processing encountered limited disclosures."]),
            executive_summary=f"Fundamental analysis completed with limited disclosures for {clean_ticker}.",
        )
