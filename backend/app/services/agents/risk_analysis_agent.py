from typing import List
from app.schemas.agent_outputs import RiskAnalysisOutput
from app.schemas.market_data import StockMarketData


class RiskAnalysisAgent:
    """
    Specialist Agent acting as the Adversary / Chief Risk Officer.
    Stress-tests assumptions, assesses downside vulnerabilities, debt leverage,
    valuation stretch, market volatility, and models the bear-case scenario.
    """
    AGENT_NAME = "Risk & Downside Analyst"

    @classmethod
    def analyze(cls, data: StockMarketData) -> RiskAnalysisOutput:
        ticker = data.ticker
        funds = data.fundamentals
        price = data.price
        profile = data.profile
        tech = data.technicals

        key_findings: List[str] = []
        risk_factors: List[str] = []
        warnings: List[str] = []
        risk_points = 2.0  # base risk
        confidence = 0.90

        # 1. Valuation Risk Assessment
        pe = funds.pe_ratio
        if pe is not None:
            if pe > 50:
                risk_points += 2.5
                factor = f"Valuation Stretch: P/E ratio of {pe:.1f}x leaves zero margin of safety against earnings disappointments."
                risk_factors.append(factor)
                key_findings.append(factor)
            elif pe > 30:
                risk_points += 1.0
                factor = f"Premium Valuation: P/E ratio of {pe:.1f}x prices in sustained high growth expectations."
                risk_factors.append(factor)
        else:
            risk_points += 2.0
            factor = "Unprofitability Risk: Lack of positive net earnings (unreported or negative P/E)."
            risk_factors.append(factor)
            key_findings.append(factor)

        # 2. Balance Sheet & Solvency Risk
        debt_to_equity = funds.debt_to_equity
        if debt_to_equity is not None:
            if debt_to_equity > 150:
                risk_points += 2.5
                factor = f"High Debt Leverage: Debt-to-Equity of {debt_to_equity:.1f}% increases financial vulnerability in higher-rate environments."
                risk_factors.append(factor)
                key_findings.append(factor)
            elif debt_to_equity > 80:
                risk_points += 1.0
                factor = f"Moderate Leverage: Debt-to-Equity of {debt_to_equity:.1f}% warrants debt service monitoring."
                risk_factors.append(factor)
        else:
            warnings.append("Debt-to-Equity data was missing; balance sheet leverage risk could not be fully quantified.")
            confidence -= 0.10

        # 3. Free Cash Flow Risk
        fcf = funds.free_cash_flow
        if fcf is not None and fcf < 0:
            risk_points += 2.0
            factor = f"Cash Burn Risk: Negative free cash flow (${fcf:,.0f}) may necessitate dilutive equity offerings or debt issuance."
            risk_factors.append(factor)
            key_findings.append(factor)

        # 4. Volatility (Beta)
        beta = profile.beta
        if beta is not None:
            if beta > 1.4:
                risk_points += 1.5
                factor = f"Elevated Market Volatility: High Beta of {beta:.2f} implies significant price drawdowns during market corrections."
                risk_factors.append(factor)
                key_findings.append(factor)
        else:
            warnings.append("Beta volatility metric is unlisted.")
            confidence -= 0.05

        # 5. Technical Breakdown Risk
        if tech.trend_signal == "BEARISH":
            risk_points += 1.0
            factor = "Technical Deterioration: Stock trades below moving average support in a downward trajectory."
            risk_factors.append(factor)
            key_findings.append(factor)

        # 6. Negative Margin Growth
        rev_growth = funds.revenue_growth
        if rev_growth is not None and rev_growth < 0:
            risk_points += 1.5
            factor = f"Top-Line Contraction: Revenue declined by {rev_growth * 100:.1f}% year-over-year."
            risk_factors.append(factor)
            key_findings.append(factor)

        # Final Risk Score & Tier
        final_risk_score = round(max(1.0, min(9.5, risk_points)), 1)
        if final_risk_score >= 7.5:
            risk_level = "CRITICAL"
        elif final_risk_score >= 5.5:
            risk_level = "HIGH"
        elif final_risk_score >= 3.5:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        # Bear Case Scenario Formulation
        current_price = price.current_price or 0.0
        support = tech.support_level or (current_price * 0.8)
        bear_drop_pct = round(((current_price - support) / current_price * 100), 1) if current_price > 0 else 20.0

        primary_threat = risk_factors[0] if risk_factors else "macroeconomic demand slowdown"
        bear_case = (
            f"In a downside stress scenario driven by {primary_threat.lower()}, {ticker} could experience "
            f"valuation compression towards its 6-month support channel near ${support:.2f} (~{bear_drop_pct}% downside). "
            f"Investors should watch for debt refinancing friction, margin degradation, or multiple contraction."
        )

        narrative = (
            f"Risk analysis classifies {ticker} as a {risk_level} risk investment (Risk Score: {final_risk_score}/10). "
            f"Identified {len(risk_factors)} primary risk vectors requiring ongoing monitoring."
        )

        supporting_data = {
            "risk_score": final_risk_score,
            "risk_level": risk_level,
            "factors_count": len(risk_factors),
            "debt_to_equity": debt_to_equity,
            "beta": beta,
            "pe_ratio": pe,
            "estimated_downside_support": support,
        }

        return RiskAnalysisOutput(
            agent_name=cls.AGENT_NAME,
            risk_level=risk_level,
            risk_score=final_risk_score,
            primary_risk_factors=risk_factors,
            bear_case_scenario=bear_case,
            analysis=narrative,
            key_findings=key_findings,
            supporting_data=supporting_data,
            warnings_and_limitations=warnings,
            confidence_level=round(max(0.1, min(1.0, confidence)), 2),
        )

