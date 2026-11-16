from typing import List
from app.schemas.agent_outputs import FinancialAnalysisOutput
from app.schemas.market_data import StockMarketData


class FinancialAnalysisAgent:
    """
    Specialist Agent responsible for fundamental analysis:
    valuation multiples, profitability margins, balance sheet leverage, and cash flow stability.
    """
    AGENT_NAME = "Financial & Valuation Analyst"

    @classmethod
    def analyze(cls, data: StockMarketData) -> FinancialAnalysisOutput:
        ticker = data.ticker
        funds = data.fundamentals

        key_findings: List[str] = []
        warnings: List[str] = []
        health_score_points = 50.0  # baseline out of 100
        available_metrics_count = 0
        confidence = 0.95

        # 1. Valuation Multiples (P/E, Forward P/E, P/B, EV/EBITDA)
        pe = funds.pe_ratio
        fwd_pe = funds.forward_pe
        pb = funds.price_to_book

        if pe is not None:
            available_metrics_count += 1
            if pe > 45:
                val_status = "OVERVALUED"
                key_findings.append(f"Trailing P/E of {pe:.1f}x indicates a premium valuation relative to historical market benchmarks.")
                health_score_points -= 5
            elif pe < 15:
                val_status = "UNDERVALUED"
                key_findings.append(f"Low trailing P/E of {pe:.1f}x suggests value territory or potential market skepticism on growth.")
                health_score_points += 10
            else:
                val_status = "FAIRLY_VALUED"
                key_findings.append(f"Trailing P/E of {pe:.1f}x reflects reasonable market valuation pricing.")
                health_score_points += 5
        else:
            val_status = "SPECULATIVE"
            warnings.append("Trailing P/E is not reported; the company may have negative net earnings.")
            confidence -= 0.15

        if fwd_pe is not None and pe is not None:
            available_metrics_count += 1
            if fwd_pe < pe:
                key_findings.append(f"Forward P/E of {fwd_pe:.1f}x versus trailing {pe:.1f}x signals expected earnings expansion.")
                health_score_points += 5
            else:
                key_findings.append(f"Forward P/E of {fwd_pe:.1f}x suggests potential earnings contraction ahead.")
                health_score_points -= 5

        # 2. Profitability Margins (Net Profit & Operating Margin)
        net_margin = funds.profit_margins
        op_margin = funds.operating_margins

        if net_margin is not None:
            available_metrics_count += 1
            if net_margin > 0.20:
                profit_grade = "HIGH"
                health_score_points += 15
                key_findings.append(f"Strong net profit margin of {net_margin * 100:.1f}% indicates pricing power and competitive moats.")
            elif net_margin > 0.08:
                profit_grade = "MODERATE"
                health_score_points += 10
                key_findings.append(f"Healthy net margin of {net_margin * 100:.1f}%.")
            elif net_margin > 0:
                profit_grade = "LOW"
                health_score_points += 2
                key_findings.append(f"Slim net margin of {net_margin * 100:.1f}%, leaving small cushion for cost inflation.")
            else:
                profit_grade = "NEGATIVE"
                health_score_points -= 15
                key_findings.append(f"Negative net profit margin ({net_margin * 100:.1f}%) highlights current operational unprofitability.")
        else:
            profit_grade = "MODERATE"
            warnings.append("Profit margin data is not disclosed.")
            confidence -= 0.10

        # 3. Growth Profile
        rev_growth = funds.revenue_growth
        if rev_growth is not None:
            available_metrics_count += 1
            growth_pct = rev_growth * 100
            if growth_pct > 15:
                key_findings.append(f"Robust top-line revenue expansion of {growth_pct:.1f}% year-over-year.")
                health_score_points += 10
            elif growth_pct > 0:
                key_findings.append(f"Modest revenue growth of {growth_pct:.1f}% year-over-year.")
                health_score_points += 5
            else:
                key_findings.append(f"Revenue contracted by {growth_pct:.1f}% year-over-year.")
                health_score_points -= 10
        else:
            warnings.append("Revenue growth data is not reported.")
            confidence -= 0.05

        # 4. Solvency & Balance Sheet Leverage
        debt_to_equity = funds.debt_to_equity
        total_cash = funds.total_cash
        total_debt = funds.total_debt

        if debt_to_equity is not None:
            available_metrics_count += 1
            if debt_to_equity < 50:
                solvency_risk = "LOW"
                health_score_points += 10
                key_findings.append(f"Conservative balance sheet with modest Debt-to-Equity ratio of {debt_to_equity:.1f}%.")
            elif debt_to_equity < 150:
                solvency_risk = "MODERATE"
                health_score_points += 2
                key_findings.append(f"Manageable debt burden with Debt-to-Equity of {debt_to_equity:.1f}%.")
            else:
                solvency_risk = "HIGH"
                health_score_points -= 15
                key_findings.append(f"Elevated balance sheet leverage (Debt-to-Equity: {debt_to_equity:.1f}%).")
        else:
            solvency_risk = "INSUFFICIENT_DATA"
            warnings.append("Debt-to-Equity leverage metric is unavailable.")
            confidence -= 0.10

        # 5. Free Cash Flow
        fcf = funds.free_cash_flow
        if fcf is not None:
            available_metrics_count += 1
            if fcf > 0:
                key_findings.append(f"Positive free cash flow generation of ${fcf:,.0f}, supporting capital returns and reinvestment.")
                health_score_points += 10
            else:
                key_findings.append(f"Negative free cash flow generation (${fcf:,.0f}), requiring external financing or cash reserves.")
                health_score_points -= 10
        else:
            warnings.append("Free cash flow figures are unlisted.")
            confidence -= 0.05

        # Compute Final Health Score
        final_health_score = round(max(5.0, min(95.0, health_score_points)), 1)
        if available_metrics_count < 2:
            val_status = "INSUFFICIENT_DATA"
            final_health_score = None
            confidence = 0.20

        # Narrative Synthesis
        narrative = (
            f"Financial analysis for {ticker} indicates a {val_status.replace('_', ' ').lower()} profile "
            f"with a {profit_grade.lower()} profitability rating. Solvency risk is classified as {solvency_risk.lower()}."
        )

        supporting_data = {
            "pe_ratio": pe,
            "forward_pe": fwd_pe,
            "price_to_book": pb,
            "profit_margins": net_margin,
            "operating_margins": op_margin,
            "revenue_growth": rev_growth,
            "debt_to_equity": debt_to_equity,
            "total_cash": total_cash,
            "total_debt": total_debt,
            "free_cash_flow": fcf,
            "dividend_yield": funds.dividend_yield,
        }

        return FinancialAnalysisOutput(
            agent_name=cls.AGENT_NAME,
            valuation_status=val_status,
            financial_health_score=final_health_score,
            profitability_grade=profit_grade,
            solvency_risk=solvency_risk,
            analysis=narrative,
            key_findings=key_findings,
            supporting_data=supporting_data,
            warnings_and_limitations=warnings,
            confidence_level=round(max(0.1, min(1.0, confidence)), 2),
        )

