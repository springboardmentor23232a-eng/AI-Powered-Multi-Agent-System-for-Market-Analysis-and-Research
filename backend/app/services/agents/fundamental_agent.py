import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.services.agents.base import BaseResearchAgent
from app.services.financial_calculations import (
    _safe_float,
    compute_cagr_pct,
    compute_growth_pct,
    compute_margin_pct,
    compute_pb_ratio,
    compute_pe_ratio,
    compute_roa_pct,
    compute_roe_pct,
    compute_stability_metrics,
    extract_statement_series,
    get_period_value,
)
from app.services.market_data_service import get_yf_symbol
from app.services.stock_data_service import VERIFIED_STOCKS

logger = logging.getLogger(__name__)

CURATED_PEERS: Dict[str, List[Dict[str, str]]] = {
    "AAPL": [
        {"ticker": "MSFT", "market": "NASDAQ"},
        {"ticker": "GOOGL", "market": "NASDAQ"},
        {"ticker": "NVDA", "market": "NASDAQ"},
    ],
    "MSFT": [
        {"ticker": "AAPL", "market": "NASDAQ"},
        {"ticker": "GOOGL", "market": "NASDAQ"},
        {"ticker": "ORCL", "market": "NYSE"},
    ],
    "GOOGL": [
        {"ticker": "MSFT", "market": "NASDAQ"},
        {"ticker": "META", "market": "NASDAQ"},
        {"ticker": "AAPL", "market": "NASDAQ"},
    ],
    "NVDA": [
        {"ticker": "AMD", "market": "NASDAQ"},
        {"ticker": "INTC", "market": "NASDAQ"},
        {"ticker": "QCOM", "market": "NASDAQ"},
    ],
    "AMD": [
        {"ticker": "NVDA", "market": "NASDAQ"},
        {"ticker": "INTC", "market": "NASDAQ"},
        {"ticker": "QCOM", "market": "NASDAQ"},
    ],
    "INFY": [
        {"ticker": "TCS", "market": "NSE"},
        {"ticker": "WIPRO", "market": "NSE"},
    ],
    "TCS": [
        {"ticker": "INFY", "market": "NSE"},
        {"ticker": "WIPRO", "market": "NSE"},
    ],
    "HDFCBANK": [
        {"ticker": "ICICIBANK", "market": "NSE"},
        {"ticker": "SBIN", "market": "NSE"},
        {"ticker": "KOTAKBANK", "market": "NSE"},
    ],
    "ICICIBANK": [
        {"ticker": "HDFCBANK", "market": "NSE"},
        {"ticker": "SBIN", "market": "NSE"},
        {"ticker": "KOTAKBANK", "market": "NSE"},
    ],
    "JPM": [
        {"ticker": "BAC", "market": "NYSE"},
        {"ticker": "V", "market": "NYSE"},
    ],
}


def _fmt_money(val: Optional[float], currency: str) -> str:
    if val is None:
        return "N/A"
    sym = "₹" if currency == "INR" else "$"
    abs_v = abs(val)
    sign = "-" if val < 0 else ""
    if currency == "INR":
        if abs_v >= 1e7:
            return f"{sign}{sym}{abs_v / 1e7:,.2f} Cr"
        return f"{sign}{sym}{abs_v:,.2f}"
    if abs_v >= 1e12:
        return f"{sign}{sym}{abs_v / 1e12:.2f}T"
    if abs_v >= 1e9:
        return f"{sign}{sym}{abs_v / 1e9:.2f}B"
    if abs_v >= 1e6:
        return f"{sign}{sym}{abs_v / 1e6:.2f}M"
    return f"{sign}{sym}{abs_v:,.2f}"


class FundamentalAnalysisAgent(BaseResearchAgent):
    """
    Module 3 Agent: Analyzes revenue & earnings, profitability, debt & stability,
    financial ratios (P/E, P/B, ROE, ROA), multi-year trends, peer comparisons,
    and identifies missing or inconsistent financial data.
    """

    @property
    def agent_name(self) -> str:
        return "fundamental_analysis_agent"

    def _resolve_peer_candidates(self, ticker: str, market: str, sector: str) -> List[Dict[str, str]]:
        clean_t = ticker.strip().upper()
        clean_m = market.strip().upper()
        if clean_t in CURATED_PEERS:
            return CURATED_PEERS[clean_t][:3]

        peers: List[Dict[str, str]] = []
        for s in VERIFIED_STOCKS:
            if s["ticker"].upper() == clean_t:
                continue
            if s["market"].upper() == clean_m and sector != "N/A" and s.get("sector") == sector:
                peers.append({"ticker": s["ticker"], "market": s["market"]})
        if not peers:
            for s in VERIFIED_STOCKS:
                if s["ticker"].upper() != clean_t and s["market"].upper() == clean_m:
                    peers.append({"ticker": s["ticker"], "market": s["market"]})
        return peers[:3]

    def _fetch_peer_comparison(self, ticker: str, market: str, sector: str) -> List[Dict[str, Any]]:
        """Fetch comparable valuation and profitability metrics for sector peers."""
        import yfinance as yf

        candidates = self._resolve_peer_candidates(ticker, market, sector)
        peers_data: List[Dict[str, Any]] = []
        for peer in candidates:
            yf_sym = get_yf_symbol(peer["ticker"], peer["market"])
            try:
                p_info = yf.Ticker(yf_sym).info or {}
                if not p_info:
                    continue
                roe_raw = _safe_float(p_info.get("returnOnEquity"))
                pm_raw = _safe_float(p_info.get("profitMargins"))
                rg_raw = _safe_float(p_info.get("revenueGrowth"))
                pe_raw = _safe_float(p_info.get("trailingPE") or p_info.get("forwardPE"))
                pb_raw = _safe_float(p_info.get("priceToBook"))
                peers_data.append({
                    "ticker": peer["ticker"],
                    "market": peer["market"],
                    "company_name": p_info.get("shortName") or p_info.get("longName") or peer["ticker"],
                    "currency": p_info.get("currency") or ("INR" if peer["market"] in ["NSE", "BSE"] else "USD"),
                    "current_price": _safe_float(p_info.get("currentPrice") or p_info.get("regularMarketPrice")),
                    "market_cap": _safe_float(p_info.get("marketCap")),
                    "pe_ratio": round(pe_raw, 2) if pe_raw is not None else None,
                    "pb_ratio": round(pb_raw, 2) if pb_raw is not None else None,
                    "roe_pct": round(roe_raw * 100.0, 2) if roe_raw is not None else None,
                    "profit_margin_pct": round(pm_raw * 100.0, 2) if pm_raw is not None else None,
                    "revenue_growth_pct": round(rg_raw * 100.0, 2) if rg_raw is not None else None,
                })
            except Exception as e:
                logger.warning(f"Skipping peer {yf_sym} due to fetch error: {e}")
        return peers_data

    async def analyze(
        self,
        ticker: str,
        market: str,
        period: str,
        market_data: Dict[str, Any],
        include_peers: bool = True,
    ) -> Dict[str, Any]:
        analyzed_at = datetime.now(timezone.utc).isoformat()
        profile = market_data.get("profile") or {}
        raw_info = market_data.get("raw_info") or {}
        statements = market_data.get("financial_statements") or {}

        income_stmt = statements.get("income_statement") or {}
        balance_stmt = statements.get("balance_sheet") or {}
        cash_stmt = statements.get("cash_flow") or {}

        currency = profile.get("currency") or ("INR" if market in ["NSE", "BSE"] else "USD")
        current_price = _safe_float(profile.get("current_price"))
        market_cap = _safe_float(profile.get("market_cap"))

        # Extract core time series from financial statements (newest -> oldest)
        revenue_series = extract_statement_series(income_stmt, ["Total Revenue", "Operating Revenue"])
        gross_profit_series = extract_statement_series(income_stmt, ["Gross Profit"])
        op_income_series = extract_statement_series(income_stmt, ["Operating Income", "Total Operating Income As Reported", "EBIT"])
        ebitda_series = extract_statement_series(income_stmt, ["EBITDA", "Normalized EBITDA"])
        net_income_series = extract_statement_series(
            income_stmt, ["Net Income", "Net Income Common Stockholders", "Net Income Continuous Operations"]
        )
        eps_series = extract_statement_series(income_stmt, ["Diluted EPS", "Basic EPS"])
        interest_exp_series = extract_statement_series(income_stmt, ["Interest Expense", "Interest Expense Non Operating"])

        equity_series = extract_statement_series(
            balance_stmt, ["Stockholders Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"]
        )
        total_assets_series = extract_statement_series(balance_stmt, ["Total Assets"])
        total_debt_series = extract_statement_series(balance_stmt, ["Total Debt", "Long Term Debt"])
        cash_series = extract_statement_series(
            balance_stmt, ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"]
        )
        ca_series = extract_statement_series(balance_stmt, ["Current Assets"])
        cl_series = extract_statement_series(balance_stmt, ["Current Liabilities"])
        inv_series = extract_statement_series(balance_stmt, ["Inventory"])

        ocf_series = extract_statement_series(
            cash_stmt, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"]
        )
        capex_series = extract_statement_series(cash_stmt, ["Capital Expenditure", "Purchase Of PPE"])
        fcf_series = extract_statement_series(cash_stmt, ["Free Cash Flow"])

        # Latest vs Prior metrics
        latest_rev = get_period_value(revenue_series, 0)
        prev_rev = get_period_value(revenue_series, 1)
        rev_yoy = compute_growth_pct(latest_rev, prev_rev)
        if rev_yoy is None and raw_info.get("revenueGrowth") is not None:
            rev_yoy = round(float(raw_info["revenueGrowth"]) * 100.0, 2)

        valid_revs = [r for r in revenue_series if r is not None]
        rev_cagr = (
            compute_cagr_pct(valid_revs[0], valid_revs[-1], len(valid_revs) - 1)
            if len(valid_revs) >= 2
            else None
        )

        latest_ni = get_period_value(net_income_series, 0)
        prev_ni = get_period_value(net_income_series, 1)
        ni_yoy = compute_growth_pct(latest_ni, prev_ni)
        if ni_yoy is None and raw_info.get("earningsGrowth") is not None:
            ni_yoy = round(float(raw_info["earningsGrowth"]) * 100.0, 2)

        latest_gp = get_period_value(gross_profit_series, 0)
        latest_ebit = get_period_value(op_income_series, 0)
        prev_ebit = get_period_value(op_income_series, 1)
        latest_ebitda = get_period_value(ebitda_series, 0)
        latest_eps = get_period_value(eps_series, 0) or _safe_float(raw_info.get("trailingEps"))

        # Profitability Margins
        gross_margin = compute_margin_pct(latest_gp, latest_rev)
        if gross_margin is None and raw_info.get("grossMargins") is not None:
            gross_margin = round(float(raw_info["grossMargins"]) * 100.0, 2)

        operating_margin = compute_margin_pct(latest_ebit, latest_rev)
        if operating_margin is None and raw_info.get("operatingMargins") is not None:
            operating_margin = round(float(raw_info["operatingMargins"]) * 100.0, 2)

        net_margin = compute_margin_pct(latest_ni, latest_rev)
        if net_margin is None and raw_info.get("profitMargins") is not None:
            net_margin = round(float(raw_info["profitMargins"]) * 100.0, 2)

        prev_net_margin = compute_margin_pct(prev_ni, prev_rev)
        if net_margin is not None and prev_net_margin is not None:
            diff_m = net_margin - prev_net_margin
            margin_trend = "Expanding" if diff_m > 0.5 else ("Contracting" if diff_m < -0.5 else "Stable")
        else:
            margin_trend = "Insufficient Prior Period Data"

        latest_assets = get_period_value(total_assets_series, 0)
        roa_pct = compute_roa_pct(latest_ni, latest_assets)

        # Debt & Stability
        latest_equity = get_period_value(equity_series, 0)
        stability = compute_stability_metrics(
            total_debt=get_period_value(total_debt_series, 0) or _safe_float(raw_info.get("totalDebt")),
            cash_and_equivalents=get_period_value(cash_series, 0) or _safe_float(raw_info.get("totalCash")),
            stockholders_equity=latest_equity,
            current_assets=get_period_value(ca_series, 0),
            current_liabilities=get_period_value(cl_series, 0),
            inventory=get_period_value(inv_series, 0),
            operating_income=latest_ebit,
            interest_expense=get_period_value(interest_exp_series, 0),
            operating_cash_flow=get_period_value(ocf_series, 0) or _safe_float(raw_info.get("operatingCashflow")),
            capex=get_period_value(capex_series, 0),
            free_cash_flow_direct=get_period_value(fcf_series, 0) or _safe_float(raw_info.get("freeCashflow")),
        )
        if stability["current_ratio"] is None and raw_info.get("currentRatio") is not None:
            stability["current_ratio"] = round(float(raw_info["currentRatio"]), 2)
        if stability["debt_to_equity"] is None and raw_info.get("debtToEquity") is not None:
            # yfinance debtToEquity is expressed as percentage (e.g. 84.28 => 0.84x)
            stability["debt_to_equity"] = round(float(raw_info["debtToEquity"]) / 100.0, 2)

        dte = stability["debt_to_equity"]
        if dte is None:
            stability_rating = "Undetermined"
        elif dte <= 0.6 and (stability["current_ratio"] is None or stability["current_ratio"] >= 1.2):
            stability_rating = "Strong"
        elif dte <= 1.5:
            stability_rating = "Moderate"
        else:
            stability_rating = "Leveraged"
        stability["stability_rating"] = stability_rating

        # Financial Ratios (P/E, P/B, ROE)
        pe_ratio = compute_pe_ratio(
            current_price=current_price,
            diluted_eps=latest_eps,
            market_cap=market_cap,
            net_income=latest_ni,
            provider_pe=raw_info.get("trailingPE") or raw_info.get("forwardPE"),
        )
        pb_ratio = compute_pb_ratio(
            market_cap=market_cap,
            stockholders_equity=latest_equity,
            current_price=current_price,
            book_value_per_share=raw_info.get("bookValue"),
            provider_pb=raw_info.get("priceToBook"),
        )
        roe_ratio = compute_roe_pct(
            net_income=latest_ni,
            stockholders_equity=latest_equity,
            provider_roe=raw_info.get("returnOnEquity"),
        )

        # Historical Multi-Year Financial Comparison
        income_periods = income_stmt.get("periods") or []
        bs_periods = balance_stmt.get("periods") or []
        cf_periods = cash_stmt.get("periods") or []
        historical_comparison: List[Dict[str, Any]] = []

        for idx, p_date in enumerate(income_periods):
            rev = get_period_value(revenue_series, idx)
            prev_r = get_period_value(revenue_series, idx + 1)
            gp = get_period_value(gross_profit_series, idx)
            ebit = get_period_value(op_income_series, idx)
            ni = get_period_value(net_income_series, idx)

            # Match balance sheet & cash flow period by index/year prefix
            yr = p_date[:4]
            bs_idx = next((i for i, d in enumerate(bs_periods) if d.startswith(yr)), idx if idx < len(bs_periods) else None)
            cf_idx = next((i for i, d in enumerate(cf_periods) if d.startswith(yr)), idx if idx < len(cf_periods) else None)

            eq = get_period_value(equity_series, bs_idx) if bs_idx is not None else None
            dbt = get_period_value(total_debt_series, bs_idx) if bs_idx is not None else None
            fcf_v = get_period_value(fcf_series, cf_idx) if cf_idx is not None else None
            if fcf_v is None and cf_idx is not None:
                o_v = get_period_value(ocf_series, cf_idx)
                c_v = get_period_value(capex_series, cf_idx)
                if o_v is not None and c_v is not None:
                    fcf_v = round(o_v - abs(c_v), 2)

            historical_comparison.append({
                "fiscal_period": p_date,
                "revenue": rev,
                "revenue_growth_pct": compute_growth_pct(rev, prev_r),
                "operating_income": ebit,
                "net_income": ni,
                "gross_margin_pct": compute_margin_pct(gp, rev),
                "operating_margin_pct": compute_margin_pct(ebit, rev),
                "net_margin_pct": compute_margin_pct(ni, rev),
                "total_debt": dbt,
                "stockholders_equity": eq,
                "free_cash_flow": fcf_v,
                "roe_pct": round((ni / eq) * 100.0, 2) if (ni is not None and eq is not None and eq > 0) else None,
            })

        # Peer Comparison
        peer_comparison = (
            self._fetch_peer_comparison(ticker, market, profile.get("sector", "N/A"))
            if include_peers
            else []
        )

        # Identify Missing or Inconsistent Financial Information
        data_gaps: List[str] = []
        if not income_periods:
            data_gaps.append("Income statement data was unavailable from the financial feed.")
        elif len(income_periods) < 2:
            data_gaps.append("Fewer than 2 fiscal periods available; multi-year revenue/earnings growth could not be computed.")
        if not bs_periods:
            data_gaps.append("Balance sheet data was unavailable; leverage and book-value metrics may rely on provider summaries.")
        if not cf_periods:
            data_gaps.append("Cash flow statement data was unavailable; Free Cash Flow could not be directly verified.")
        if latest_equity is not None and latest_equity <= 0:
            data_gaps.append("Total Stockholders' Equity is zero or negative, rendering P/B and ROE non-meaningful.")
        if latest_eps is not None and latest_eps <= 0:
            data_gaps.append("Latest Diluted EPS is zero or negative, rendering P/E valuation non-meaningful.")
        if stability["interest_coverage"] is None:
            data_gaps.append("Interest expense line item missing or zero; Interest Coverage ratio unavailable.")
        if pe_ratio["status"] == "COMPUTED" and raw_info.get("trailingPE"):
            prov_pe = float(raw_info["trailingPE"])
            if prov_pe > 0 and abs(pe_ratio["value"] - prov_pe) / prov_pe > 0.25:
                data_gaps.append(
                    f"Computed FY P/E ({pe_ratio['value']}) differs from provider TTM P/E ({prov_pe:.2f}) due to trailing vs fiscal-year EPS timing."
                )
        if include_peers and not peer_comparison:
            data_gaps.append("Comparable peer financial data could not be retrieved for cross-company benchmarking.")

        # Grounded Analytical Narrative
        company_label = profile.get("company_name") or ticker
        rev_str = _fmt_money(latest_rev, currency)
        ni_str = _fmt_money(latest_ni, currency)
        fcf_str = _fmt_money(stability["free_cash_flow"], currency)
        debt_str = _fmt_money(stability["total_debt"], currency)
        cash_str = _fmt_money(stability["cash_and_equivalents"], currency)

        rev_growth_clause = (
            f"representing {rev_yoy:+.2f}% YoY growth" if rev_yoy is not None else "with YoY growth unavailable due to limited prior-period revenue"
        )
        ni_growth_clause = (
            f"({ni_yoy:+.2f}% YoY)" if ni_yoy is not None else ""
        )
        pe_clause = f"P/E of {pe_ratio['value']}x" if pe_ratio["value"] is not None else "P/E unavailable"
        pb_clause = f"P/B of {pb_ratio['value']}x" if pb_ratio["value"] is not None else "P/B unavailable"
        roe_clause = f"ROE of {roe_ratio['value']}%" if roe_ratio["value"] is not None else "ROE unavailable"

        narrative = (
            f"Revenue & Earnings: {company_label} ({ticker}) reported latest annual revenue of {rev_str} ({rev_growth_clause}) "
            f"and net income of {ni_str} {ni_growth_clause}. "
            f"Profitability: Gross margin stands at {gross_margin if gross_margin is not None else 'N/A'}%, "
            f"operating margin at {operating_margin if operating_margin is not None else 'N/A'}%, and net profit margin at "
            f"{net_margin if net_margin is not None else 'N/A'}% (margin trajectory: {margin_trend}). "
            f"Financial Stability: Total debt is {debt_str} against cash & equivalents of {cash_str}, yielding a "
            f"Debt-to-Equity ratio of {stability['debt_to_equity'] if stability['debt_to_equity'] is not None else 'N/A'}x, "
            f"Current Ratio of {stability['current_ratio'] if stability['current_ratio'] is not None else 'N/A'}x, and Free Cash Flow of {fcf_str} "
            f"(overall stability rating: {stability_rating}). "
            f"Valuation: Key multiples reflect {pe_clause}, {pb_clause}, and {roe_clause}."
        )

        return {
            "agent_name": self.agent_name,
            "analyzed_at": analyzed_at,
            "ticker": ticker,
            "market": market,
            "currency": currency,
            "revenue_and_earnings": {
                "latest_period": income_periods[0] if income_periods else None,
                "latest_revenue": latest_rev,
                "previous_revenue": prev_rev,
                "revenue_yoy_growth_pct": rev_yoy,
                "revenue_cagr_pct": rev_cagr,
                "latest_net_income": latest_ni,
                "previous_net_income": prev_ni,
                "earnings_yoy_growth_pct": ni_yoy,
                "operating_income": latest_ebit,
                "ebitda": latest_ebitda,
                "diluted_eps": round(latest_eps, 4) if latest_eps is not None else None,
            },
            "profitability": {
                "gross_margin_pct": gross_margin,
                "operating_margin_pct": operating_margin,
                "net_margin_pct": net_margin,
                "roa_pct": roa_pct,
                "margin_trend": margin_trend,
            },
            "debt_and_stability": stability,
            "financial_ratios": {
                "pe_ratio": pe_ratio,
                "pb_ratio": pb_ratio,
                "roe_pct": roe_ratio,
                "forward_pe": round(float(raw_info["forwardPE"]), 2) if raw_info.get("forwardPE") else None,
                "ev_to_ebitda": round(float(raw_info["enterpriseToEbitda"]), 2) if raw_info.get("enterpriseToEbitda") else None,
                "dividend_yield_pct": (
                    round(float(raw_info["dividendYield"]) * 100.0, 2)
                    if raw_info.get("dividendYield") is not None and float(raw_info["dividendYield"]) < 1
                    else (_safe_float(raw_info.get("dividendYield")))
                ),
            },
            "historical_comparison": historical_comparison,
            "peer_comparison": peer_comparison,
            "data_gaps": data_gaps,
            "explanation": narrative,
        }

