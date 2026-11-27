import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.schemas.stock import (
    FinancialStatementsResponse,
    StockOverviewResponse,
    FinancialSection,
    StatementData,
    FinancialStatementItem,
)
from app.schemas.fundamental import (
    HistoricalStatementYear,
    PeerBenchmarkItem,
    PeerComparisonSection,
    BalanceSheetPeriodAudit,
    AuditFindingItem,
    AuditCategoryScores,
    DataIntegrityAudit,
)
from app.services.stock_service import (
    CURATED_PEERS,
    _infer_market_from_exchange_and_symbol,
)
from app.services.fundamental_service import (
    calculate_safe_cagr,
    analyze_revenue_and_earnings,
    analyze_profitability,
    analyze_financial_stability,
    calculate_valuation_ratios,
    build_historical_comparison,
    benchmark_peers,
    audit_data_integrity,
    run_fundamental_analysis,
)


def _make_sample_statement_data(periods, items_dict, statement_type="income_statement"):
    line_items = []
    for name, vals in items_dict.items():
        val_map = {p: v for p, v in zip(periods, vals)}
        line_items.append(FinancialStatementItem(line_item=name, metric=name, values=val_map))
    return StatementData(
        statement_type=statement_type,
        periods=periods,
        line_items=line_items,
        items=line_items,
        available=True,
        raw_available=True,
    )


def _build_mock_statements():
    periods = ["2023-12-31", "2022-12-31", "2021-12-31"]

    income_items = {
        "Total Revenue": [1000000.0, 800000.0, 600000.0],
        "Gross Profit": [400000.0, 320000.0, 240000.0],
        "Operating Income": [250000.0, 160000.0, 120000.0],
        "Net Income": [200000.0, 150000.0, 100000.0],
        "Diluted EPS": [20.0, 15.0, 10.0],
        "Basic EPS": [20.0, 15.0, 10.0],
        "Interest Expense": [10000.0, 10000.0, 10000.0],
    }

    balance_items = {
        "Total Assets": [2000000.0, 1800000.0, 1500000.0],
        "Current Assets": [800000.0, 700000.0, 600000.0],
        "Current Liabilities": [400000.0, 350000.0, 300000.0],
        "Total Liabilities": [1000000.0, 900000.0, 800000.0],
        "Stockholders Equity": [1000000.0, 900000.0, 700000.0],
        "Total Debt": [300000.0, 250000.0, 200000.0],
        "Current Debt And Capital Lease Obligation": [100000.0, 80000.0, 60000.0],
        "Long Term Debt And Capital Lease Obligation": [200000.0, 170000.0, 140000.0],
        "Cash And Cash Equivalents": [500000.0, 400000.0, 300000.0],
        "Inventory": [100000.0, 90000.0, 80000.0],
    }

    cashflow_items = {
        "Operating Cash Flow": [240000.0, 180000.0, 120000.0],
        "Capital Expenditure": [-40000.0, -30000.0, -20000.0],
    }

    annual_income = _make_sample_statement_data(periods, income_items, "income_statement_annual")
    annual_balance = _make_sample_statement_data(periods, balance_items, "balance_sheet_annual")
    annual_cashflow = _make_sample_statement_data(periods, cashflow_items, "cash_flow_annual")

    empty_quarterly = StatementData(statement_type="quarterly", periods=[], line_items=[], items=[], available=False)

    return FinancialStatementsResponse(
        ticker="TEST.NS",
        company_name="Test Company Limited",
        currency="INR",
        data_source="yfinance",
        retrieved_at="2026-11-18T12:00:00Z",
        income_statement=FinancialSection(annual=annual_income, quarterly=empty_quarterly),
        balance_sheet=FinancialSection(annual=annual_balance, quarterly=empty_quarterly),
        cash_flow_statement=FinancialSection(annual=annual_cashflow, quarterly=empty_quarterly),
        cash_flow=FinancialSection(annual=annual_cashflow, quarterly=empty_quarterly),
    )


def _build_mock_overview():
    return StockOverviewResponse(
        ticker="TEST.NS",
        company_name="Test Company Limited",
        market="NSE",
        exchange="NSE",
        currency="INR",
        current_price=500.0,
        pe_ratio=25.0,
        trailing_pe=25.0,
        forward_pe=20.0,
        price_to_book=5.0,
        book_value=100.0,
        forward_eps=25.0,
        trailing_eps=20.0,
        market_cap=5000000.0,
        sector="Information Technology",
        dividend_yield=0.02,
        retrieved_at="2026-11-18T12:00:00Z",
    )


# ── 1. Safe CAGR Calculation Tests (Mandatory Correction #5) ───────────────────

def test_safe_cagr_calculation_positive_base():
    # 600k in 2021 to 1M in 2023 over 2 years
    cagr, status, notes = calculate_safe_cagr(600000.0, 1000000.0, 2, "Revenue")
    assert status == "calculated"
    assert cagr is not None
    assert round(cagr, 1) == 29.1
    assert "2 consecutive years" in notes


def test_safe_cagr_calculation_zero_base():
    cagr, status, notes = calculate_safe_cagr(0.0, 500000.0, 3, "Revenue")
    assert status == "undefined_zero_base"
    assert cagr is None
    assert "zero" in notes.lower()


def test_safe_cagr_calculation_negative_base_turnaround():
    # Loss of -100k turning into profit of +200k
    cagr, status, notes = calculate_safe_cagr(-100000.0, 200000.0, 2, "Net Income")
    assert status == "turnaround_loss_to_profit"
    assert cagr is None
    assert "turnaround" in notes.lower()
    assert "-100,000" in notes


def test_safe_cagr_calculation_deterioration_profit_to_loss():
    # Profit of +100k deteriorating into loss of -50k
    cagr, status, notes = calculate_safe_cagr(100000.0, -50000.0, 2, "Net Income")
    assert status == "deterioration_profit_to_loss"
    assert cagr is None
    assert "deterioration" in notes.lower()


def test_safe_cagr_calculation_continuous_loss():
    cagr, status, notes = calculate_safe_cagr(-50000.0, -20000.0, 2, "Net Income")
    assert status == "continuous_loss"
    assert cagr is None


def test_safe_cagr_calculation_insufficient_periods():
    cagr, status, notes = calculate_safe_cagr(100.0, 200.0, 0, "Revenue")
    assert status == "insufficient_periods"
    assert cagr is None


# ── 2. Revenue & Earnings Analysis Tests ────────────────────────────────────────

def test_revenue_and_earnings_analysis():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    rev_sec = analyze_revenue_and_earnings(stmts, ov)

    assert rev_sec.revenue.value == 1000000.0
    assert "1.00M" in rev_sec.revenue.formatted or "1000000" in rev_sec.revenue.formatted
    # YoY growth: (1M - 800k)/800k = 25%
    assert rev_sec.revenue_growth_yoy.value == 25.0
    assert rev_sec.revenue_growth_yoy.formatted == "25.00%"
    assert rev_sec.gross_profit.value == 400000.0
    assert rev_sec.operating_income.value == 250000.0
    assert rev_sec.net_income.value == 200000.0
    # Net income YoY: (200k - 150k)/150k = 33.33%
    assert rev_sec.net_income_growth_yoy.value == 33.33
    assert rev_sec.diluted_eps.value == 20.0
    # Earnings quality: Operating Cash Flow (240k) / Net Income (200k) = 1.2x
    assert rev_sec.earnings_quality_ratio.value == 1.2
    assert rev_sec.earnings_quality_ratio.status == "calculated"
    assert len(rev_sec.summary_narrative) > 0


# ── 3. Profitability & Dual-Method ROE Tests (Mandatory Correction #3) ─────────

def test_profitability_margins_and_average_equity_roe():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    prof_sec = analyze_profitability(stmts, ov)

    # Gross Margin: 400k / 1M = 40%
    assert prof_sec.gross_margin.value == 40.0
    # Operating Margin: 250k / 1M = 25%
    assert prof_sec.operating_margin.value == 25.0
    # Net Margin: 200k / 1M = 20%
    assert prof_sec.net_margin.value == 20.0
    # ROA: 200k / 2M = 10%
    assert prof_sec.return_on_assets.value == 10.0

    # ROE using 2-period average equity:
    # Net Income = 200k
    # Equity t0 = 1,000,000; Equity t1 = 900,000; Average Equity = 950,000
    # ROE = (200,000 / 950,000) * 100 = 21.05%
    assert prof_sec.return_on_equity.value == 21.05
    assert prof_sec.return_on_equity.method == "average_equity"
    assert prof_sec.return_on_equity.status == "calculated"
    assert "average equity" in prof_sec.return_on_equity.notes.lower()
    assert prof_sec.margin_trend == "Expanding"


def test_roe_fallback_to_ending_equity():
    # Only 1 period available in balance sheet
    single_period = ["2023-12-31"]
    income_items = {"Total Revenue": [1000000.0], "Net Income": [200000.0]}
    balance_items = {"Total Assets": [2000000.0], "Stockholders Equity": [1000000.0]}

    income_data = _make_sample_statement_data(single_period, income_items)
    balance_data = _make_sample_statement_data(single_period, balance_items)
    empty = StatementData(statement_type="empty", periods=[], line_items=[], items=[], available=False)

    stmts = FinancialStatementsResponse(
        ticker="TEST.NS",
        company_name="Test Company",
        currency="INR",
        data_source="yfinance",
        retrieved_at="2026-11-18T12:00:00Z",
        income_statement=FinancialSection(annual=income_data, quarterly=empty),
        balance_sheet=FinancialSection(annual=balance_data, quarterly=empty),
        cash_flow_statement=FinancialSection(annual=empty, quarterly=empty),
        cash_flow=FinancialSection(annual=empty, quarterly=empty),
    )
    ov = _build_mock_overview()
    prof_sec = analyze_profitability(stmts, ov)

    # 200k / 1M = 20%
    assert prof_sec.return_on_equity.value == 20.0
    assert prof_sec.return_on_equity.method == "ending_equity"
    assert "ending equity" in prof_sec.return_on_equity.notes.lower()


def test_roe_negative_equity_handled_safely():
    # Deficit / negative equity
    single_period = ["2023-12-31"]
    income_items = {"Total Revenue": [1000000.0], "Net Income": [100000.0]}
    balance_items = {"Total Assets": [500000.0], "Stockholders Equity": [-200000.0]}

    income_data = _make_sample_statement_data(single_period, income_items)
    balance_data = _make_sample_statement_data(single_period, balance_items)
    empty = StatementData(statement_type="empty", periods=[], line_items=[], items=[], available=False)

    stmts = FinancialStatementsResponse(
        ticker="TEST.NS",
        company_name="Deficit Corp",
        currency="INR",
        data_source="yfinance",
        retrieved_at="2026-11-18T12:00:00Z",
        income_statement=FinancialSection(annual=income_data, quarterly=empty),
        balance_sheet=FinancialSection(annual=balance_data, quarterly=empty),
        cash_flow_statement=FinancialSection(annual=empty, quarterly=empty),
        cash_flow=FinancialSection(annual=empty, quarterly=empty),
    )
    ov = _build_mock_overview()
    prof_sec = analyze_profitability(stmts, ov)

    assert prof_sec.return_on_equity.value is None
    assert prof_sec.return_on_equity.status == "negative_equity_deficit"
    assert prof_sec.return_on_equity.method == "not_computable"
    assert "negative" in prof_sec.return_on_equity.notes.lower()


# ── 4. Debt & Financial Stability Tests ────────────────────────────────────────

def test_debt_and_financial_stability():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    stab_sec = analyze_financial_stability(stmts, ov)

    # Total Debt = 300k, Cash = 500k -> Net Debt = -200k (Net cash positive)
    assert stab_sec.total_debt.value == 300000.0
    assert stab_sec.net_debt.value == -200000.0
    assert "net cash" in stab_sec.net_debt.notes.lower()

    # D/E: 300k / 1M = 0.3x
    assert stab_sec.debt_to_equity.value == 0.3
    # Debt to Assets: 300k / 2M = 0.15x
    assert stab_sec.debt_to_assets.value == 0.15

    # Equity Ratio: Stockholders' Equity (1M) / Total Assets (2M) = 50.0%
    assert stab_sec.equity_ratio.value == 50.0
    assert stab_sec.equity_ratio.formatted == "50.00%"
    assert stab_sec.equity_ratio.status == "calculated"

    # Short-Term and Long-Term Debt Obligations
    assert stab_sec.short_term_debt.value == 100000.0
    assert stab_sec.long_term_debt.value == 200000.0
    assert "reconciles" in stab_sec.short_term_debt.notes.lower()
    assert "reconciles" in stab_sec.long_term_debt.notes.lower()

    # Balance Sheet Context Metrics
    assert stab_sec.total_assets.value == 2000000.0
    assert stab_sec.stockholders_equity.value == 1000000.0
    assert stab_sec.current_liabilities.value == 400000.0
    assert stab_sec.total_liabilities.value == 1000000.0

    # Current Ratio: Current Assets (800k) / Current Liabilities (400k) = 2.0x
    assert stab_sec.current_ratio.value == 2.0
    # Quick Ratio: (800k - 100k inventory) / 400k = 1.75x
    assert stab_sec.quick_ratio.value == 1.75

    # Interest Coverage: EBIT (250k) / Interest (10k) = 25.0x
    assert stab_sec.interest_coverage.value == 25.0

    # Free Cash Flow: Operating Cash Flow (240k) - CapEx (40k) = 200,000.0
    assert stab_sec.free_cash_flow.value == 200000.0
    assert stab_sec.stability_rating == "Strong"
    assert "equity ratio is 50.00%" in stab_sec.summary_narrative.lower()


def test_equity_ratio_calculation():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    stab = analyze_financial_stability(stmts, ov)

    # 1,000,000 equity / 2,000,000 assets = 50.0%
    assert stab.equity_ratio.value == 50.0
    assert stab.equity_ratio.formatted == "50.00%"
    assert stab.equity_ratio.status == "calculated"
    assert "50.00%" in stab.equity_ratio.notes


def test_short_and_long_term_debt_extraction():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    stab = analyze_financial_stability(stmts, ov)

    assert stab.short_term_debt.value == 100000.0
    assert stab.short_term_debt.status == "reported"
    assert stab.long_term_debt.value == 200000.0
    assert stab.long_term_debt.status == "reported"


def test_debt_composition_percentage_calculation():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    stab = analyze_financial_stability(stmts, ov)

    # 100k / 300k = 33.3%, 200k / 300k = 66.7%
    assert "33.3%" in stab.short_term_debt.notes
    assert "66.7%" in stab.long_term_debt.notes
    assert "reconciles with reported total debt" in stab.short_term_debt.notes.lower()


def test_total_liabilities_and_context_metrics_extraction():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    stab = analyze_financial_stability(stmts, ov)

    assert stab.total_liabilities is not None
    assert stab.total_liabilities.value == 1000000.0
    assert stab.total_liabilities.status == "reported"
    assert stab.current_liabilities.value == 400000.0
    assert stab.total_assets.value == 2000000.0
    assert stab.stockholders_equity.value == 1000000.0


def test_missing_debt_components_handled_safely():
    stmts = _build_mock_statements()
    # Strip out short-term and long-term debt items
    filtered_items = [
        it for it in stmts.balance_sheet.annual.items
        if "lease obligation" not in it.line_item.lower()
    ]
    stmts.balance_sheet.annual.items = filtered_items
    stmts.balance_sheet.annual.line_items = filtered_items

    ov = _build_mock_overview()
    stab = analyze_financial_stability(stmts, ov)

    assert stab.total_debt.value == 300000.0  # Total debt still intact
    assert stab.short_term_debt.value is None
    assert stab.short_term_debt.status == "unavailable"
    assert stab.long_term_debt.value is None
    assert stab.long_term_debt.status == "unavailable"


def test_zero_total_assets_equity_ratio_safe():
    stmts = _build_mock_statements()
    # Set total assets to 0.0
    for it in stmts.balance_sheet.annual.items:
        if it.line_item == "Total Assets":
            it.values = {p: 0.0 for p in it.values.keys()}

    ov = _build_mock_overview()
    stab = analyze_financial_stability(stmts, ov)

    assert stab.equity_ratio.value is None
    assert stab.equity_ratio.status == "zero_denominator"
    assert stab.equity_ratio.formatted == "N/A"


def test_negative_equity_equity_ratio_safe():
    stmts = _build_mock_statements()
    # Set stockholders equity to negative (-200k)
    for it in stmts.balance_sheet.annual.items:
        if it.line_item == "Stockholders Equity":
            it.values = {p: -200000.0 for p in it.values.keys()}

    ov = _build_mock_overview()
    stab = analyze_financial_stability(stmts, ov)

    # -200k / 2M = -10.0%
    assert stab.equity_ratio.value == -10.0
    assert stab.equity_ratio.status == "negative_equity"
    assert stab.equity_ratio.formatted == "-10.00%"
    assert "deficit" in stab.equity_ratio.notes.lower()


def test_zero_total_debt_and_stability_safe():
    stmts = _build_mock_statements()
    for it in stmts.balance_sheet.annual.items:
        if it.line_item in ["Total Debt", "Current Debt And Capital Lease Obligation", "Long Term Debt And Capital Lease Obligation"]:
            it.values = {p: 0.0 for p in it.values.keys()}

    ov = _build_mock_overview()
    stab = analyze_financial_stability(stmts, ov)

    assert stab.total_debt.value == 0.0
    assert stab.debt_to_equity.value == 0.0
    assert stab.debt_to_assets.value == 0.0
    assert stab.short_term_debt.value == 0.0
    assert stab.long_term_debt.value == 0.0
    assert "zero total debt" in stab.short_term_debt.notes.lower()


def test_debt_reconciliation_discrepancy_note():
    stmts = _build_mock_statements()
    # Set short-term debt (150k) + long-term debt (200k) = 350k, while total debt = 300k (discrepancy = 50k)
    for it in stmts.balance_sheet.annual.items:
        if it.line_item == "Current Debt And Capital Lease Obligation":
            it.values = {p: 150000.0 for p in it.values.keys()}

    ov = _build_mock_overview()
    stab = analyze_financial_stability(stmts, ov)

    # Values are NOT modified
    assert stab.total_debt.value == 300000.0
    assert stab.short_term_debt.value == 150000.0
    assert stab.long_term_debt.value == 200000.0
    # Clear discrepancy note exposed
    assert "differs from reported total debt" in stab.short_term_debt.notes.lower()
    assert "differs from reported total debt" in stab.long_term_debt.notes.lower()


# ── 5. Valuation Ratios Engine Tests ───────────────────────────────────────────

def test_valuation_ratios_profitable():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    prof_sec = analyze_profitability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)

    assert val_sec.trailing_pe.value == 25.0
    assert val_sec.trailing_pe.status in {"reported", "calculated"}
    assert val_sec.forward_pe.value == 20.0
    assert val_sec.forward_pe.status == "reported"
    assert val_sec.forward_pe.period == "Forward (NTM)"
    # P/B: Provider reported (5.0x)
    assert val_sec.price_to_book.value == 5.0
    assert val_sec.price_to_book.status in {"reported", "calculated"}
    assert val_sec.return_on_equity.value == prof_sec.return_on_equity.value


def test_valuation_ratios_loss_making_pe():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    ov.pe_ratio = None
    ov.trailing_pe = None
    ov.trailing_eps = None
    ov.current_price = 100.0

    # Mock diluted EPS as -5.0
    annual_income = stmts.income_statement.annual
    for item in annual_income.items:
        if getattr(item, "line_item", None) == "Diluted EPS":
            item.values["2023-12-31"] = -5.0

    prof_sec = analyze_profitability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)

    assert val_sec.trailing_pe.value is None
    assert val_sec.trailing_pe.status == "loss_making"
    assert "loss-making" in val_sec.trailing_pe.notes.lower()


def test_forward_pe_extraction():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    ov.forward_pe = 18.5
    ov.forward_eps = 27.0
    prof_sec = analyze_profitability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)

    assert val_sec.forward_pe.value == 18.5
    assert val_sec.forward_pe.formatted == "18.50x"
    assert val_sec.forward_pe.status == "reported"
    assert val_sec.forward_pe.period == "Forward (NTM)"
    assert "27.00" in val_sec.forward_pe.notes or "NTM" in val_sec.forward_pe.notes


def test_trailing_and_forward_pe_distinction():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    ov.trailing_pe = 28.0
    ov.forward_pe = 22.0
    prof_sec = analyze_profitability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)

    assert val_sec.trailing_pe.value == 28.0
    assert val_sec.trailing_pe.period == "TTM"
    assert val_sec.forward_pe.value == 22.0
    assert val_sec.forward_pe.period == "Forward (NTM)"
    assert val_sec.trailing_pe.value != val_sec.forward_pe.value


def test_negative_eps_handling():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    ov.pe_ratio = None
    ov.trailing_pe = None
    ov.trailing_eps = -2.5
    ov.current_price = 100.0

    prof_sec = analyze_profitability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)

    assert val_sec.trailing_pe.value is None
    assert val_sec.trailing_pe.status == "loss_making"


def test_zero_eps_handling():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    ov.pe_ratio = None
    ov.trailing_pe = None
    ov.trailing_eps = 0.0
    ov.current_price = 100.0

    prof_sec = analyze_profitability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)

    assert val_sec.trailing_pe.value is None
    assert val_sec.trailing_pe.status == "loss_making"


def test_provider_reported_pb_priority():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    ov.price_to_book = 4.70
    ov.book_value = 240.0
    prof_sec = analyze_profitability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)

    assert val_sec.price_to_book.value == 4.70
    assert val_sec.price_to_book.status == "reported"
    assert "reported" in val_sec.price_to_book.method


def test_infy_style_cross_currency_pb_protection():
    stmts = _build_mock_statements()
    stmts.currency = "USD"  # Balance sheet in USD
    ov = _build_mock_overview()
    ov.currency = "INR"      # Market cap in INR
    ov.price_to_book = None
    ov.book_value = None
    ov.market_cap = 4500000000000  # ₹4.5T
    # Equity in stmts is $1M
    prof_sec = analyze_profitability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)

    # Must NOT divide INR market cap by USD equity (which would yield 4,500,000x!)
    assert val_sec.price_to_book.value is None
    assert val_sec.price_to_book.status == "unavailable"
    assert "currency mismatch" in val_sec.price_to_book.notes.lower()


def test_negative_equity_pb_handling():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    ov.price_to_book = None
    ov.book_value = -50.0  # Negative book value per share

    prof_sec = analyze_profitability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)

    assert val_sec.price_to_book.value is None
    assert val_sec.price_to_book.status == "negative_equity"
    assert "negative" in val_sec.price_to_book.notes.lower()


def test_zero_book_value_handling():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    ov.price_to_book = None
    ov.book_value = 0.0

    prof_sec = analyze_profitability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)

    assert val_sec.price_to_book.value is None
    assert val_sec.price_to_book.status == "zero_denominator"


def test_historical_roe_calculation_using_average_equity():
    stmts = _build_mock_statements()
    hist_comp = build_historical_comparison(stmts)

    # Period 0 (2023): Net Income = 200k, Equity 2023 = 1M, Equity 2022 = 900k -> Avg Eq = 950k
    # ROE = 200,000 / 950,000 = 21.05%
    y0 = hist_comp.years[0]
    assert y0.period == "2023-12-31"
    assert y0.roe_pct == 21.05

    # Period 1 (2022): Net Income = 150k, Equity 2022 = 900k, Equity 2021 = 700k -> Avg Eq = 800k
    # ROE = 150,000 / 800,000 = 18.75%
    y1 = hist_comp.years[1]
    assert y1.period == "2022-12-31"
    assert y1.roe_pct == 18.75


def test_historical_roe_fallback_when_prior_equity_unavailable():
    stmts = _build_mock_statements()
    hist_comp = build_historical_comparison(stmts)

    # Period 2 (2021): Net Income = 100k, Equity 2021 = 700k (No prior period -> Ending equity)
    # ROE = 100,000 / 700,000 = 14.29%
    y2 = hist_comp.years[2]
    assert y2.period == "2021-12-31"
    assert y2.roe_pct == 14.29


def test_negative_or_zero_historical_equity_handling():
    stmts = _build_mock_statements()
    # Set equity of 2023 to negative (-100k)
    for it in stmts.balance_sheet.annual.items:
        if it.line_item == "Stockholders Equity":
            it.values["2023-12-31"] = -100000.0

    hist_comp = build_historical_comparison(stmts)
    # Average equity would be (-100k + 900k)/2 = 400k > 0 -> still computes
    # But if both are negative:
    for it in stmts.balance_sheet.annual.items:
        if it.line_item == "Stockholders Equity":
            it.values["2022-12-31"] = -50000.0

    hist_comp2 = build_historical_comparison(stmts)
    # Avg equity = (-100k + -50k)/2 = -75k < 0 -> must safely be None
    y0 = hist_comp2.years[0]
    assert y0.roe_pct is None


def test_roe_reuse_without_duplicate_calculation():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    prof_sec = analyze_profitability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)

    assert val_sec.return_on_equity is prof_sec.return_on_equity
    assert val_sec.return_on_equity.value == prof_sec.return_on_equity.value
    assert val_sec.return_on_equity.method == prof_sec.return_on_equity.method


# ── 6. Historical Comparison Matrix Tests ──────────────────────────────────────

def test_historical_comparison_matrix():
    stmts = _build_mock_statements()
    hist_comp = build_historical_comparison(stmts)

    assert len(hist_comp.periods) == 3
    assert hist_comp.periods[0] == "2023-12-31"
    assert len(hist_comp.years) == 3

    y0 = hist_comp.years[0]
    assert y0.period == "2023-12-31"
    assert y0.total_revenue == 1000000.0
    assert y0.net_income == 200000.0
    assert y0.gross_margin_pct == 40.0
    assert y0.free_cash_flow == 200000.0


# ── 7. Real-Data Peer Comparison Tests (Mandatory Correction #4) ──────────────

def test_peer_comparison_real_data():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    prof_sec = analyze_profitability(stmts, ov)
    stab_sec = analyze_financial_stability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)

    # Mock get_company_overview to return real comparable peer metrics
    def mock_peer_overview(ticker):
        return StockOverviewResponse(
            ticker=ticker,
            company_name=f"{ticker} Inc",
            market="NSE",
            exchange="NSE",
            current_price=1000.0,
            pe_ratio=30.0,
            market_cap=6000000.0,
            sector="Information Technology",
            retrieved_at="2026-11-18T12:00:00Z",
        )

    with patch("app.services.fundamental_service.get_company_overview", side_effect=mock_peer_overview):
        peer_sec = benchmark_peers(
            target_ticker="INFY.NS",
            target_market="NSE",
            target_sector="Information Technology",
            target_valuation=val_sec,
            target_profitability=prof_sec,
            target_stability=stab_sec,
            target_rev_yoy=25.0,
        )

        assert len(peer_sec.peers) > 0
        assert peer_sec.peer_median_pe == 30.0
        # Target PE is 25, peer median is 30 -> Below Peer Median (Discount)
        assert "Discount" in peer_sec.relative_valuation_position


def test_peer_comparison_graceful_on_peer_failure():
    # Final Safeguard 1: Peer retrieval failure must never break fundamental analysis
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    prof_sec = analyze_profitability(stmts, ov)
    stab_sec = analyze_financial_stability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)

    with patch("app.services.fundamental_service.get_company_overview", side_effect=Exception("Rate limit hit")):
        peer_sec = benchmark_peers(
            target_ticker="INFY.NS",
            target_market="NSE",
            target_sector="Information Technology",
            target_valuation=val_sec,
            target_profitability=prof_sec,
            target_stability=stab_sec,
            target_rev_yoy=25.0,
        )

        # Peer retrieval handled gracefully
        assert len(peer_sec.peers) > 0
        assert any(p.is_target for p in peer_sec.peers)
        assert all(p.data_status == "unavailable" for p in peer_sec.peers if not p.is_target)
        assert peer_sec.peer_median_pe is None


# ── 8. Data Integrity & Accounting Equation Check Tests ────────────────────────

def test_data_integrity_accounting_equation_balanced():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    audit = audit_data_integrity(stmts, ov)

    # Assets (2M) == Liabilities (1M) + Equity (1M)
    assert audit.balance_sheet_equation_holds is True
    assert audit.balance_sheet_discrepancy_pct == 0.0
    assert audit.is_consistent is True
    assert audit.data_quality_score >= 90.0


def test_data_integrity_accounting_equation_discrepancy_detected():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()

    # Artificially alter Liabilities to cause discrepancy
    annual_balance = stmts.balance_sheet.annual
    for item in annual_balance.items:
        if getattr(item, "line_item", None) == "Total Liabilities":
            item.values["2023-12-31"] = 1400000.0  # Assets = 2M, Liab+Equity = 2.4M (20% discrepancy)

    audit = audit_data_integrity(stmts, ov)
    assert audit.balance_sheet_equation_holds is False
    assert audit.balance_sheet_discrepancy_pct > 2.0
    assert audit.is_consistent is False
    assert any("equation discrepancy" in w.lower() for w in audit.audit_warnings)


# ── 9. Master Orchestrator Tests ───────────────────────────────────────────────

def test_run_fundamental_analysis_orchestration():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()

    res = run_fundamental_analysis("TEST.NS", stmts, ov)
    assert res.status == "success"
    assert res.ticker == "TEST.NS"
    assert res.revenue_and_earnings.revenue.value == 1000000.0
    assert res.profitability.return_on_equity.method == "average_equity"
    assert res.debt_and_stability.stability_rating == "Strong"
    assert res.valuation_ratios.price_to_book.value == 5.0
    assert len(res.historical_comparison.years) == 3
    assert res.data_integrity_audit.is_consistent is True
    assert len(res.executive_summary) > 0
    # Optional enhancements present and separated
    assert res.optional_enhancements is not None
    assert res.optional_enhancements.price_to_sales.value == 5.0


def test_run_fundamental_analysis_resilience_on_unexpected_error():
    # Final Safeguard 2: Never expose raw exception messages
    stmts = _build_mock_statements()
    ov = _build_mock_overview()

    with patch("app.services.fundamental_service.analyze_revenue_and_earnings", side_effect=Exception("Critical Internal Engine Failure")):
        res = run_fundamental_analysis("TEST.NS", stmts, ov)
        assert res.status == "partial"
        assert res.ticker == "TEST.NS"
        assert "Critical Internal Engine Failure" not in res.executive_summary
        assert "limited disclosures" in res.executive_summary.lower()


# ── 10. API Route & Workflow Integration Tests ─────────────────────────────────

def _register_and_login_fundamental_user(client, email: str = "fundamental_tester@example.com"):
    reg_payload = {
        "fullName": "Fundamental Analyst Tester",
        "email": email,
        "password": "Password123!",
        "confirmPassword": "Password123!",
    }
    client.post("/api/auth/register", json=reg_payload)

    login_payload = {
        "email": email,
        "password": "Password123!",
    }
    res = client.post("/api/auth/login", json=login_payload)
    assert res.status_code == 200
    return res.json()["data"]


def test_api_fundamental_endpoint_authenticated(client, monkeypatch):
    _register_and_login_fundamental_user(client, "fund_api_user@example.com")

    stmts = _build_mock_statements()
    ov = _build_mock_overview()

    monkeypatch.setattr("app.routes.stocks.get_company_overview", lambda ticker: ov)
    monkeypatch.setattr("app.routes.stocks.get_financial_statements", lambda ticker: stmts)

    res = client.get("/api/stocks/AAPL/fundamental")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["ticker"] == "AAPL"
    assert "revenue_and_earnings" in data
    assert "profitability" in data
    assert "debt_and_stability" in data
    assert "valuation_ratios" in data
    assert "historical_comparison" in data
    assert "peer_comparison" in data
    assert "data_integrity_audit" in data
    assert "optional_enhancements" in data
    assert data["profitability"]["return_on_equity"]["method"] == "average_equity"


def test_api_fundamental_endpoint_unauthenticated(client):
    from fastapi.testclient import TestClient
    from app.main import app
    unauth_client = TestClient(app)

    res = unauth_client.get("/api/stocks/AAPL/fundamental")
    assert res.status_code == 401


def test_research_workflow_persists_fundamental_analysis(client, db_session, monkeypatch):
    _register_and_login_fundamental_user(client, "workflow_fund_user@example.com")

    stmts = _build_mock_statements()
    ov = _build_mock_overview()

    from app.schemas.stock import HistoricalDataResponse, StockSummaryStats, ValidationReport, OHLCVCandle
    mock_history = HistoricalDataResponse(
        ticker="AAPL",
        period="1mo",
        interval="1d",
        count=2,
        data_source="yfinance",
        retrieved_at=datetime.utcnow().isoformat() + "Z",
        stats=StockSummaryStats(
            start_date="2024-01-01",
            end_date="2024-01-02",
            lowest_price=150.0,
            highest_price=155.0,
            average_volume=1000000.0,
            total_trading_days=2,
            period_change_pct=2.0,
        ),
        validation=ValidationReport(
            ticker="AAPL",
            total_raw_records=2,
            cleaned_records=2,
            duplicates_removed=0,
            invalid_records_removed=0,
            is_chronological=True,
            total_input_rows=2,
            valid_rows=2,
        ),
        candles=[
            OHLCVCandle(date="2024-01-01", open=150.0, high=155.0, low=149.0, close=152.0, volume=1000000),
            OHLCVCandle(date="2024-01-02", open=152.0, high=154.0, low=151.0, close=153.0, volume=1200000),
        ]
    )

    monkeypatch.setattr("app.services.research_service.get_company_overview", lambda ticker: ov)
    monkeypatch.setattr("app.services.research_service.get_historical_ohlcv", lambda ticker, period: mock_history)
    monkeypatch.setattr("app.services.research_service.get_financial_statements", lambda ticker: stmts)
    monkeypatch.setattr("app.services.fundamental_service.get_company_overview", lambda ticker: ov)

    req_payload = {
        "ticker": "AAPL",
        "market": "NASDAQ",
        "period": "1mo",
    }
    create_res = client.post("/api/research/tasks", json=req_payload)
    assert create_res.status_code == 201
    task_data = create_res.json()["task"]
    task_id = task_data["task_id"]

    # Poll task detail
    detail_res = client.get(f"/api/research/tasks/{task_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["task"]["status"] == "Completed"
    report = detail["report"]
    assert report is not None
    assert "fundamental_analysis" in report["report_content"]

    fund_content = report["report_content"]["fundamental_analysis"]
    assert fund_content["status"] == "success"
    assert "revenue_and_earnings" in fund_content
    assert "profitability" in fund_content
    assert "debt_and_stability" in fund_content
    assert "valuation_ratios" in fund_content
    assert "historical_comparison" in fund_content
    assert "peer_comparison" in fund_content
    assert "data_integrity_audit" in fund_content
    assert "optional_enhancements" in fund_content


# ── Module 3 Task 5: Annual Historical Financial Comparison Tests ─────────────

def test_task5_extraction_of_all_historical_metrics():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    hist_comp = build_historical_comparison(stmts, ov)

    assert len(hist_comp.years) == 3
    y0 = hist_comp.years[0]
    assert y0.total_revenue == 1000000.0
    assert y0.revenue == 1000000.0
    assert y0.gross_profit == 400000.0
    assert y0.operating_income == 250000.0
    assert y0.net_income == 200000.0
    assert y0.diluted_eps == 20.0
    assert y0.operating_cash_flow == 240000.0
    assert y0.capital_expenditures == -40000.0
    assert y0.free_cash_flow == 200000.0
    assert y0.total_assets == 2000000.0
    assert y0.total_liabilities == 1000000.0
    assert y0.stockholders_equity == 1000000.0
    assert y0.total_debt == 300000.0
    assert y0.gross_margin_pct == 40.0
    assert y0.operating_margin_pct == 25.0
    assert y0.net_margin_pct == 20.0
    assert y0.roa_pct == 10.0
    assert y0.roe_pct == 21.05


def test_task5_historical_diluted_eps():
    stmts = _build_mock_statements()
    hist_comp = build_historical_comparison(stmts)
    assert hist_comp.years[0].diluted_eps == 20.0
    assert hist_comp.years[1].diluted_eps == 15.0
    assert hist_comp.years[2].diluted_eps == 10.0


def test_task5_historical_total_liabilities():
    stmts = _build_mock_statements()
    hist_comp = build_historical_comparison(stmts)
    assert hist_comp.years[0].total_liabilities == 1000000.0
    assert hist_comp.years[1].total_liabilities == 900000.0
    assert hist_comp.years[2].total_liabilities == 800000.0


def test_task5_historical_operating_margin():
    stmts = _build_mock_statements()
    hist_comp = build_historical_comparison(stmts)
    # FY2023: 250k / 1000k = 25.0%
    assert hist_comp.years[0].operating_margin_pct == 25.0
    # FY2022: 160k / 800k = 20.0%
    assert hist_comp.years[1].operating_margin_pct == 20.0
    # FY2021: 120k / 600k = 20.0%
    assert hist_comp.years[2].operating_margin_pct == 20.0


def test_task5_historical_roa():
    stmts = _build_mock_statements()
    hist_comp = build_historical_comparison(stmts)
    # FY2023: 200k / 2000k = 10.0%
    assert hist_comp.years[0].roa_pct == 10.0
    # FY2022: 150k / 1800k = 8.33%
    assert hist_comp.years[1].roa_pct == 8.33
    # FY2021: 100k / 1500k = 6.67%
    assert hist_comp.years[2].roa_pct == 6.67


def test_task5_multi_year_revenue_yoy_growth():
    stmts = _build_mock_statements()
    hist_comp = build_historical_comparison(stmts)
    # FY2023 vs FY2022: (1000k - 800k) / 800k = +25.0%
    assert hist_comp.years[0].revenue_growth_yoy == 25.0
    # FY2022 vs FY2021: (800k - 600k) / 600k = +33.33%
    assert hist_comp.years[1].revenue_growth_yoy == 33.33
    # FY2021: oldest period -> None
    assert hist_comp.years[2].revenue_growth_yoy is None


def test_task5_multi_year_net_income_yoy_growth():
    stmts = _build_mock_statements()
    hist_comp = build_historical_comparison(stmts)
    # FY2023 vs FY2022: (200k - 150k) / 150k = +33.33%
    assert hist_comp.years[0].net_income_growth_yoy == 33.33
    # FY2022 vs FY2021: (150k - 100k) / 100k = +50.0%
    assert hist_comp.years[1].net_income_growth_yoy == 50.0
    # FY2021: oldest period -> None
    assert hist_comp.years[2].net_income_growth_yoy is None


def test_task5_correct_chronological_growth_calculation():
    stmts = _build_mock_statements()
    hist_comp = build_historical_comparison(stmts)
    # Ensure periods are newest-first
    assert hist_comp.periods == ["2023-12-31", "2022-12-31", "2021-12-31"]
    # The growth of 2023 must be positive (grew from 2022)
    assert hist_comp.years[0].revenue_growth_yoy > 0
    assert hist_comp.years[0].net_income_growth_yoy > 0


def test_task5_zero_previous_year_revenue():
    stmts = _build_mock_statements()
    for item in stmts.income_statement.annual.items:
        if item.line_item == "Total Revenue":
            item.values["2022-12-31"] = 0.0

    hist_comp = build_historical_comparison(stmts)
    # When previous year revenue is 0.0, growth must safely be None (no divide-by-zero)
    assert hist_comp.years[0].revenue_growth_yoy is None


def test_task5_zero_previous_year_net_income():
    stmts = _build_mock_statements()
    for item in stmts.income_statement.annual.items:
        if item.line_item == "Net Income":
            item.values["2022-12-31"] = 0.0

    hist_comp = build_historical_comparison(stmts)
    # When previous year net income is 0.0, growth must safely be None
    assert hist_comp.years[0].net_income_growth_yoy is None


def test_task5_negative_previous_period_growth_base_policy():
    stmts = _build_mock_statements()
    for item in stmts.income_statement.annual.items:
        if item.line_item == "Net Income":
            item.values["2022-12-31"] = -50000.0  # Loss in previous year

    hist_comp = build_historical_comparison(stmts)
    # When prior period is negative, conventional growth is marked None to prevent misleading interpretation
    assert hist_comp.years[0].net_income_growth_yoy is None


def test_task5_missing_intermediate_financial_periods():
    stmts = _build_mock_statements()
    # Remove cashflow for 2022
    for item in stmts.cash_flow.annual.items:
        item.values["2022-12-31"] = None

    hist_comp = build_historical_comparison(stmts)
    assert hist_comp.years[0].free_cash_flow == 200000.0
    assert hist_comp.years[1].free_cash_flow is None  # Handled safely
    assert hist_comp.years[2].free_cash_flow == 100000.0


def test_task5_negative_earnings_and_margin_behavior():
    stmts = _build_mock_statements()
    for item in stmts.income_statement.annual.items:
        if item.line_item == "Net Income":
            item.values["2023-12-31"] = -100000.0

    hist_comp = build_historical_comparison(stmts)
    y0 = hist_comp.years[0]
    assert y0.net_income == -100000.0
    assert y0.net_margin_pct == -10.0
    assert y0.roa_pct == -5.0


def test_task5_missing_assets_and_unavailable_roa():
    stmts = _build_mock_statements()
    for item in stmts.balance_sheet.annual.items:
        if item.line_item == "Total Assets":
            item.values["2023-12-31"] = None

    hist_comp = build_historical_comparison(stmts)
    assert hist_comp.years[0].total_assets is None
    assert hist_comp.years[0].roa_pct is None


def test_task5_historical_debt_extraction():
    stmts = _build_mock_statements()
    hist_comp = build_historical_comparison(stmts)
    assert hist_comp.years[0].total_debt == 300000.0
    assert hist_comp.years[1].total_debt == 250000.0
    assert hist_comp.years[2].total_debt == 200000.0


def test_task5_historical_fcf_consistency_with_task3():
    stmts = _build_mock_statements()
    hist_comp = build_historical_comparison(stmts)
    # FCF = OCF (240k) - |CapEx (-40k)| = 200k
    assert hist_comp.years[0].free_cash_flow == 200000.0


def test_task5_historical_roe_consistency_with_task4():
    stmts = _build_mock_statements()
    hist_comp = build_historical_comparison(stmts)
    # Dual-method average equity: Net 200k / Avg(1000k, 900k) = 21.05%
    assert hist_comp.years[0].roe_pct == 21.05


def test_task5_statement_reporting_currency_vs_trading_currency():
    stmts = _build_mock_statements()
    stmts.currency = "INR"
    stmts.financial_currency = "USD"
    ov = _build_mock_overview()
    ov.currency = "INR"
    ov.financial_currency = "USD"

    hist_comp = build_historical_comparison(stmts, ov)
    assert hist_comp.statement_currency == "USD"


def test_task5_legacy_report_schema_compatibility():
    # If legacy report only contains total_revenue, revenue alias must resolve
    y_leg1 = HistoricalStatementYear(period="2023", total_revenue=500000.0)
    assert y_leg1.revenue == 500000.0
    assert y_leg1.total_revenue == 500000.0

    # If legacy client only serialized revenue, total_revenue must resolve
    y_leg2 = HistoricalStatementYear(period="2023", revenue=750000.0)
    assert y_leg2.total_revenue == 750000.0
    assert y_leg2.revenue == 750000.0


def test_task5_summary_narrative_with_incomplete_data():
    empty_stmts = FinancialStatementsResponse(
        ticker="EMPTY",
        company_name="Empty Corp",
        currency="USD",
        data_source="yfinance",
        retrieved_at="2026-11-25T12:00:00Z",
        income_statement=FinancialSection(
            annual=StatementData(statement_type="income_statement", periods=[], line_items=[], items=[], available=False),
            quarterly=StatementData(statement_type="income_statement", periods=[], line_items=[], items=[], available=False),
        ),
        balance_sheet=FinancialSection(
            annual=StatementData(statement_type="balance_sheet", periods=[], line_items=[], items=[], available=False),
            quarterly=StatementData(statement_type="balance_sheet", periods=[], line_items=[], items=[], available=False),
        ),
        cash_flow=FinancialSection(
            annual=StatementData(statement_type="cash_flow", periods=[], line_items=[], items=[], available=False),
            quarterly=StatementData(statement_type="cash_flow", periods=[], line_items=[], items=[], available=False),
        ),
    )
    hist_empty = build_historical_comparison(empty_stmts)
    assert hist_empty.summary_narrative == "Historical statements not available."
    assert len(hist_empty.years) == 0


# ── 12. Task 6: Comprehensive Peer Benchmarking & Comparison Tests ─────────────

def _make_mock_peer_overview(sym: str, pe=20.0, price: float = 100.0, mcap: int = 500000):
    return StockOverviewResponse(
        ticker=sym,
        company_name=f"{sym} Corp",
        exchange="NSE",
        current_price=price,
        pe_ratio=pe,
        trailing_pe=pe,
        market_cap=mcap,
        retrieved_at="2026-11-25T12:00:00Z",
    )


def test_task6_exchange_normalization():
    assert _infer_market_from_exchange_and_symbol("INFY.NS", "NSI") == ("NSE", "NSE")
    assert _infer_market_from_exchange_and_symbol("AAPL", "NMS") == ("NASDAQ", "NASDAQ")
    assert _infer_market_from_exchange_and_symbol("IBM", "NYQ") == ("NYSE", "NYSE")
    assert _infer_market_from_exchange_and_symbol("INFY.BO", "BOM") == ("BSE", "BSE")


def test_task6_curated_peer_discovery():
    assert "INFY.NS" in CURATED_PEERS
    assert "TCS.NS" in CURATED_PEERS["INFY.NS"]
    assert "AAPL" in CURATED_PEERS
    assert "MSFT" in CURATED_PEERS["AAPL"]
    assert "RELIANCE.NS" in CURATED_PEERS


def test_task6_target_included_as_first_row():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    prof_sec = analyze_profitability(stmts, ov)
    stab_sec = analyze_financial_stability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)

    with patch("app.services.fundamental_service.get_company_overview", side_effect=_make_mock_peer_overview):
        peer_sec = benchmark_peers(
            target_ticker="INFY.NS",
            target_market="NSE",
            target_sector="Information Technology",
            target_valuation=val_sec,
            target_profitability=prof_sec,
            target_stability=stab_sec,
            target_rev_yoy=15.0,
            target_overview=ov,
        )

        assert len(peer_sec.peers) >= 2
        # Target must be first item
        target_item = peer_sec.peers[0]
        assert target_item.is_target is True
        assert target_item.ticker == "INFY.NS"
        assert target_item.data_status == "available"


def test_task6_peer_medians_exclude_target():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    prof_sec = analyze_profitability(stmts, ov)
    stab_sec = analyze_financial_stability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)

    # Peer 1 PE: 10, Peer 2 PE: 20 -> Peer Median should be 15.0
    # Target PE is 25.0; if target were included, median of (10, 20, 25) would be 20.0!
    pe_dict = {"TCS.NS": 10.0, "WIPRO.NS": 20.0, "HCLTECH.NS": None}

    def mock_overview(sym):
        return _make_mock_peer_overview(sym, pe=pe_dict.get(sym))

    with patch("app.services.fundamental_service.get_company_overview", side_effect=mock_overview):
        peer_sec = benchmark_peers(
            target_ticker="INFY.NS",
            target_market="NSE",
            target_sector="Information Technology",
            target_valuation=val_sec,
            target_profitability=prof_sec,
            target_stability=stab_sec,
            target_rev_yoy=15.0,
            target_overview=ov,
        )

        # Median of (10, 20) is 15.0
        assert peer_sec.peer_median_pe == 15.0


def test_task6_peer_medians_exclude_negative_pe():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    prof_sec = analyze_profitability(stmts, ov)
    stab_sec = analyze_financial_stability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)

    # One peer has negative PE (loss-making), should be excluded from median
    pe_dict = {"TCS.NS": 22.0, "WIPRO.NS": -15.0, "HCLTECH.NS": 26.0}

    def mock_overview(sym):
        return _make_mock_peer_overview(sym, pe=pe_dict.get(sym))

    with patch("app.services.fundamental_service.get_company_overview", side_effect=mock_overview):
        peer_sec = benchmark_peers(
            target_ticker="INFY.NS",
            target_market="NSE",
            target_sector="Information Technology",
            target_valuation=val_sec,
            target_profitability=prof_sec,
            target_stability=stab_sec,
            target_rev_yoy=15.0,
            target_overview=ov,
        )

        # Median of valid positive PEs (22.0, 26.0) is 24.0
        assert peer_sec.peer_median_pe == 24.0


def test_task6_relative_valuation_discount():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    prof_sec = analyze_profitability(stmts, ov)
    stab_sec = analyze_financial_stability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)

    # Target PE is 25.0, Peer Median is 35.0 -> Target < 35 * 0.9 (31.5) -> Discount
    def mock_overview(sym):
        return _make_mock_peer_overview(sym, pe=35.0)

    with patch("app.services.fundamental_service.get_company_overview", side_effect=mock_overview):
        peer_sec = benchmark_peers(
            target_ticker="INFY.NS", target_market="NSE", target_sector="Information Technology",
            target_valuation=val_sec, target_profitability=prof_sec, target_stability=stab_sec,
            target_rev_yoy=15.0, target_overview=ov,
        )
        assert "Discount" in peer_sec.relative_valuation_position


def test_task6_relative_valuation_premium():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    prof_sec = analyze_profitability(stmts, ov)
    stab_sec = analyze_financial_stability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)

    # Target PE is 25.0, Peer Median is 18.0 -> Target > 18 * 1.10 (19.8) -> Premium
    def mock_overview(sym):
        return _make_mock_peer_overview(sym, pe=18.0)

    with patch("app.services.fundamental_service.get_company_overview", side_effect=mock_overview):
        peer_sec = benchmark_peers(
            target_ticker="INFY.NS", target_market="NSE", target_sector="Information Technology",
            target_valuation=val_sec, target_profitability=prof_sec, target_stability=stab_sec,
            target_rev_yoy=15.0, target_overview=ov,
        )
        assert "Premium" in peer_sec.relative_valuation_position


def test_task6_relative_valuation_in_line():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    prof_sec = analyze_profitability(stmts, ov)
    stab_sec = analyze_financial_stability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)

    # Target PE is 25.0, Peer Median is 26.0 -> within +/- 10% -> In Line
    def mock_overview(sym):
        return _make_mock_peer_overview(sym, pe=26.0)

    with patch("app.services.fundamental_service.get_company_overview", side_effect=mock_overview):
        peer_sec = benchmark_peers(
            target_ticker="INFY.NS", target_market="NSE", target_sector="Information Technology",
            target_valuation=val_sec, target_profitability=prof_sec, target_stability=stab_sec,
            target_rev_yoy=15.0, target_overview=ov,
        )
        assert peer_sec.relative_valuation_position == "In Line"


def test_task6_relative_valuation_loss_making():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    prof_sec = analyze_profitability(stmts, ov)
    stab_sec = analyze_financial_stability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)
    # Set target valuation to loss-making
    val_sec.trailing_pe.status = "loss_making"
    val_sec.trailing_pe.value = None

    def mock_overview(sym):
        return _make_mock_peer_overview(sym, pe=25.0)

    with patch("app.services.fundamental_service.get_company_overview", side_effect=mock_overview):
        peer_sec = benchmark_peers(
            target_ticker="INFY.NS", target_market="NSE", target_sector="Information Technology",
            target_valuation=val_sec, target_profitability=prof_sec, target_stability=stab_sec,
            target_rev_yoy=15.0, target_overview=ov,
        )
        assert "Loss-Making" in peer_sec.relative_valuation_position


def test_task6_relative_profitability_positioning():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    prof_sec = analyze_profitability(stmts, ov)
    stab_sec = analyze_financial_stability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)

    # Target ROE is ~26.7% in mock. If peer median ROE is 18%, target outperforms.
    def mock_overview(sym):
        return _make_mock_peer_overview(sym, pe=25.0)

    with patch("app.services.fundamental_service.get_company_overview", side_effect=mock_overview), \
         patch("app.services.fundamental_service.yf.Ticker") as mock_ticker:
        mock_inst = MagicMock()
        mock_inst.info = {"returnOnEquity": 0.18, "operatingMargins": 0.15, "profitMargins": 0.12, "debtToEquity": 30.0}
        mock_ticker.return_value = mock_inst

        peer_sec = benchmark_peers(
            target_ticker="INFY.NS", target_market="NSE", target_sector="Information Technology",
            target_valuation=val_sec, target_profitability=prof_sec, target_stability=stab_sec,
            target_rev_yoy=15.0, target_overview=ov,
        )
        assert "Above" in peer_sec.relative_profitability_position or "Outperforming" in peer_sec.relative_profitability_position


def test_task6_relative_leverage_positioning():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    prof_sec = analyze_profitability(stmts, ov)
    stab_sec = analyze_financial_stability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)

    # In mock, target DE is 0.17x (tot_debt 50k / eq 300k).
    # If peers have DE of 60.0% (0.60x), target leverage is conservative (< 0.85 * 0.60).
    def mock_overview(sym):
        return _make_mock_peer_overview(sym, pe=25.0)

    with patch("app.services.fundamental_service.get_company_overview", side_effect=mock_overview), \
         patch("app.services.fundamental_service.yf.Ticker") as mock_ticker:
        mock_inst = MagicMock()
        mock_inst.info = {"returnOnEquity": 0.20, "debtToEquity": 60.0}
        mock_ticker.return_value = mock_inst

        peer_sec = benchmark_peers(
            target_ticker="INFY.NS", target_market="NSE", target_sector="Information Technology",
            target_valuation=val_sec, target_profitability=prof_sec, target_stability=stab_sec,
            target_rev_yoy=15.0, target_overview=ov,
        )
        assert peer_sec.relative_leverage_position == "Conservative"


def test_task6_individual_peer_failure_tolerance():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    prof_sec = analyze_profitability(stmts, ov)
    stab_sec = analyze_financial_stability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)

    # Simulate one peer failing, others succeeding
    def mock_overview(sym):
        if sym == "WIPRO.NS":
            raise Exception("Temporary 503 Provider Error")
        return _make_mock_peer_overview(sym, pe=22.0)

    with patch("app.services.fundamental_service.get_company_overview", side_effect=mock_overview):
        peer_sec = benchmark_peers(
            target_ticker="INFY.NS", target_market="NSE", target_sector="Information Technology",
            target_valuation=val_sec, target_profitability=prof_sec, target_stability=stab_sec,
            target_rev_yoy=15.0, target_overview=ov,
        )

        wipro_item = next((p for p in peer_sec.peers if p.ticker == "WIPRO.NS"), None)
        assert wipro_item is not None
        assert wipro_item.data_status == "unavailable"

        # Successful peers still provide medians
        assert peer_sec.peer_median_pe == 22.0
        assert peer_sec.data_status == "partial"


def test_task6_summary_narrative_rich_synthesis():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    prof_sec = analyze_profitability(stmts, ov)
    stab_sec = analyze_financial_stability(stmts, ov)
    val_sec = calculate_valuation_ratios(ov, stmts, prof_sec)

    def mock_overview(sym):
        return _make_mock_peer_overview(sym, pe=30.0)

    with patch("app.services.fundamental_service.get_company_overview", side_effect=mock_overview):
        peer_sec = benchmark_peers(
            target_ticker="INFY.NS", target_market="NSE", target_sector="Information Technology",
            target_valuation=val_sec, target_profitability=prof_sec, target_stability=stab_sec,
            target_rev_yoy=15.0, target_overview=ov,
        )
        assert "Benchmarked against" in peer_sec.summary_narrative
        assert "INFY.NS" not in peer_sec.summary_narrative.split("comparable")[1].split(".")[0]  # Only non-target peers in list
        assert "Trailing P/E" in peer_sec.summary_narrative or "valuation" in peer_sec.summary_narrative.lower()


def test_task6_legacy_report_schema_backward_compatibility():
    # Test that a serialized legacy peer section without new fields deserializes cleanly
    legacy_dict = {
        "target_ticker": "INFY.NS",
        "peers": [
            {
                "ticker": "TCS.NS",
                "company_name": "Tata Consultancy Services Ltd",
                "market": "NSE",
                "market_cap": 12000000.0,
                "pe_ratio": 28.5,
                "pb_ratio": 11.2,
                "roe": 42.1,
                "net_margin": 19.5,
                "debt_to_equity": 0.08,
                "revenue_growth_yoy": 6.8,
                "data_status": "available",
            }
        ],
        "peer_median_pe": 28.5,
        "peer_median_pb": 11.2,
        "peer_median_roe": 42.1,
        "peer_median_net_margin": 19.5,
        "peer_median_debt_to_equity": 0.08,
        "relative_valuation_position": "Below Peer Median (Discount)",
        "relative_profitability_position": "In Line",
        "summary_narrative": "Benchmarked against 1 peer.",
    }

    sec = PeerComparisonSection.model_validate(legacy_dict)
    assert sec.target_ticker == "INFY.NS"
    assert sec.peer_median_forward_pe is None
    assert sec.relative_leverage_position == "In Line"
    assert sec.data_status == "available"
    assert sec.peers[0].industry is None
    assert sec.peers[0].is_target is False


# ── Task 7: Data Integrity Audit Tests ────────────────────────────────────────

def test_task7_balanced_accounting_equation_multi_period():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    audit = audit_data_integrity(stmts, ov)

    assert audit.balance_sheet_equation_holds is True
    assert audit.balance_sheet_discrepancy_pct == 0.0
    assert len(audit.multi_period_balance_audits) == 3
    for period_audit in audit.multi_period_balance_audits:
        assert period_audit.equation_holds is True
        assert period_audit.status == "balanced"
        assert period_audit.discrepancy_pct == 0.0
        assert period_audit.total_assets == period_audit.total_liabilities + period_audit.stockholders_equity


def test_task7_accounting_equation_discrepancy_detected():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    # Artificially alter Total Assets in 2023-12-31 to 2,500,000 (Liabilities=1M, Equity=1M => Sum=2M, diff=500k, disc=20%)
    for item in stmts.balance_sheet.annual.items:
        if item.line_item == "Total Assets":
            item.values["2023-12-31"] = 2500000.0

    audit = audit_data_integrity(stmts, ov)
    assert audit.balance_sheet_equation_holds is False
    assert audit.is_consistent is False
    assert audit.balance_sheet_discrepancy_pct == 20.0
    assert any("Balance sheet mismatch in 2023-12-31" in item for item in audit.inconsistent_items)
    assert any(f.category == "consistency" and f.severity == "high" for f in audit.structured_findings)


def test_task7_missing_statement_detection():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    stmts.balance_sheet.annual = None

    audit = audit_data_integrity(stmts, ov)
    assert "Balance Sheet (Annual)" in audit.missing_line_items
    assert audit.category_scores.completeness < 70.0
    assert any("Missing Line Item: Total Assets" in f.title for f in audit.structured_findings)


def test_task7_missing_critical_line_items_detection():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    # Remove Operating Cash Flow from cashflow items
    stmts.cash_flow.annual.items = [
        it for it in stmts.cash_flow.annual.items if it.line_item != "Operating Cash Flow"
    ]

    audit = audit_data_integrity(stmts, ov)
    assert any("Operating Cash Flow" in it for it in audit.missing_line_items)
    assert any(f.title == "Missing Line Item: Operating Cash Flow" and f.severity == "high" for f in audit.structured_findings)


def test_task7_cross_statement_reconciliation_debt():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    # In 2023: Total Debt = 500,000, Short-term = 100,000, Long-term = 200,000 (Sum = 300,000 != 500,000)
    for item in stmts.balance_sheet.annual.items:
        if item.line_item == "Total Debt":
            item.values["2023-12-31"] = 500000.0

    audit = audit_data_integrity(stmts, ov)
    assert any("Debt breakdown variance" in item for item in audit.inconsistent_items)
    assert any(f.title.startswith("Debt Breakdown Mismatch") for f in audit.structured_findings)


def test_task7_cross_statement_reconciliation_gross_profit():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    # Add Cost of Revenue = 700,000 (while Revenue=1,000,000 and Gross Profit=400,000 => expected GP=300,000)
    cogs_item = FinancialStatementItem(
        line_item="Cost of Revenue", metric="cost_of_revenue",
        values={"2023-12-31": 700000.0, "2022-12-31": 480000.0, "2021-12-31": 360000.0}
    )
    stmts.income_statement.annual.items.append(cogs_item)

    audit = audit_data_integrity(stmts, ov)
    assert any("Gross profit variance in 2023-12-31" in item for item in audit.inconsistent_items)
    assert any(f.title.startswith("Gross Profit Calculation Discrepancy") for f in audit.structured_findings)


def test_task7_cross_statement_reconciliation_fcf():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    # Add Free Cash Flow = 100,000 (while OCF=240,000 and Capex=-40,000 => calculated FCF = 200,000)
    fcf_item = FinancialStatementItem(
        line_item="Free Cash Flow", metric="free_cash_flow",
        values={"2023-12-31": 100000.0, "2022-12-31": 150000.0, "2021-12-31": 100000.0}
    )
    stmts.cash_flow.annual.items.append(fcf_item)

    audit = audit_data_integrity(stmts, ov)
    assert any("FCF variance in 2023-12-31" in item for item in audit.inconsistent_items)


def test_task7_currency_mismatch_disclosure():
    stmts = _build_mock_statements()
    stmts.currency = "USD"
    ov = _build_mock_overview()
    ov.currency = "INR"

    audit = audit_data_integrity(stmts, ov)
    assert audit.currency_mismatch_detected is True
    assert audit.trading_currency == "INR"
    assert audit.reporting_currency == "USD"
    assert "Trading currency (INR) differs from financial statement reporting currency (USD)" in audit.currency_notes
    assert any(f.category == "currency" for f in audit.structured_findings)


def test_task7_period_alignment_and_synchronization():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    audit = audit_data_integrity(stmts, ov)
    assert audit.period_alignment_status == "aligned"
    assert len(audit.periods_audited) == 3
    assert audit.category_scores.period_alignment == 100.0

    # Partial alignment test: Remove cash flow periods and give a different period
    for it in stmts.cash_flow.annual.items:
        it.values = {"2019-12-31": 100000.0}
    audit_partial = audit_data_integrity(stmts, ov)
    assert audit_partial.period_alignment_status == "misaligned"


def test_task7_suspicious_negative_assets_critical_failure():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    for item in stmts.balance_sheet.annual.items:
        if item.line_item == "Total Assets":
            item.values["2023-12-31"] = -50000.0

    audit = audit_data_integrity(stmts, ov)
    assert any("Non-positive Total Assets" in s for s in audit.suspicious_values_detected)
    assert audit.overall_status == "fail"
    assert audit.category_scores.plausibility <= 50.0
    assert any(f.title.startswith("Non-Positive Total Assets") for f in audit.structured_findings)


def test_task7_suspicious_negative_revenue_and_cash():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    for item in stmts.income_statement.annual.items:
        if item.line_item == "Total Revenue":
            item.values["2023-12-31"] = -100000.0
    for item in stmts.balance_sheet.annual.items:
        if item.line_item == "Cash And Cash Equivalents":
            item.values["2023-12-31"] = -5000.0

    audit = audit_data_integrity(stmts, ov)
    assert any("Negative Revenue" in s for s in audit.suspicious_values_detected)
    assert any("Negative Cash and Cash Equivalents" in s for s in audit.suspicious_values_detected)


def test_task7_suspicious_extreme_gross_margin():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    for item in stmts.income_statement.annual.items:
        if item.line_item == "Gross Profit":
            item.values["2023-12-31"] = 2000000.0  # Revenue is 1,000,000 -> Gross Margin = 200%

    audit = audit_data_integrity(stmts, ov)
    assert any("Extreme Gross Margin (200.0%)" in s for s in audit.suspicious_values_detected)


def test_task7_negative_equity_warning():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    for item in stmts.balance_sheet.annual.items:
        if item.line_item == "Stockholders Equity":
            item.values["2023-12-31"] = -250000.0

    audit = audit_data_integrity(stmts, ov)
    assert any("negative" in w.lower() for w in audit.audit_warnings)
    assert any(f.title.startswith("Negative Stockholders Equity") for f in audit.structured_findings)


def test_task7_weighted_scoring_model_and_tiers():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    audit = audit_data_integrity(stmts, ov)

    assert audit.data_quality_score >= 85.0
    assert audit.data_quality_tier in ["High Quality", "Acceptable"]
    assert audit.overall_status == "pass"

    # Category bounds
    assert 0.0 <= audit.category_scores.completeness <= 100.0
    assert 0.0 <= audit.category_scores.consistency <= 100.0
    assert 0.0 <= audit.category_scores.plausibility <= 100.0
    assert 0.0 <= audit.category_scores.period_alignment <= 100.0

    # Calculate expected weighted score manually
    expected_weighted = round(
        audit.category_scores.completeness * 0.40 +
        audit.category_scores.consistency * 0.30 +
        audit.category_scores.plausibility * 0.20 +
        audit.category_scores.period_alignment * 0.10,
        1
    )
    assert audit.data_quality_score == expected_weighted


def test_task7_legacy_report_schema_deserialization():
    legacy_dict = {
        "is_consistent": True,
        "balance_sheet_equation_holds": True,
        "balance_sheet_discrepancy_pct": 0.0,
        "missing_line_items": [],
        "inconsistent_items": [],
        "audit_warnings": [],
        "data_quality_score": 95.0,
    }
    audit = DataIntegrityAudit.model_validate(legacy_dict)
    assert audit.is_consistent is True
    assert audit.data_quality_tier == "High Quality"
    assert audit.currency_mismatch_detected is False
    assert audit.period_alignment_status == "aligned"
    assert audit.periods_audited == []
    assert audit.multi_period_balance_audits == []
    assert audit.overall_status == "pass"


def test_task7_summary_narrative_factual_generation():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    audit = audit_data_integrity(stmts, ov)

    assert "Data integrity audit completed with overall rating:" in audit.summary_narrative
    assert "Data Quality Score:" in audit.summary_narrative
    assert "fundamental accounting equation" in audit.summary_narrative
    assert "holds across all 3 evaluated balance sheet periods" in audit.summary_narrative


def test_task7_full_pipeline_orchestrator_integration():
    stmts = _build_mock_statements()
    ov = _build_mock_overview()
    res = run_fundamental_analysis("TEST.NS", statements=stmts, overview=ov)

    assert res.status == "success"
    assert res.data_integrity_audit is not None
    assert res.data_integrity_audit.data_quality_tier in ["High Quality", "Acceptable"]
    assert res.data_integrity_audit.balance_sheet_equation_holds is True
    assert len(res.data_integrity_audit.multi_period_balance_audits) == 3
    assert res.data_integrity_audit.overall_status == "pass"
