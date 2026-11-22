from typing import List
from app.schemas.agent_outputs import MarketResearchOutput
from app.schemas.market_data import StockMarketData


class MarketResearchAgent:
    """
    Specialist Agent responsible for macroeconomic context, company profile,
    market capitalization classification, sector dynamics, and business model synthesis.
    """
    AGENT_NAME = "Market Research Specialist"

    @classmethod
    def analyze(cls, data: StockMarketData) -> MarketResearchOutput:
        ticker = data.ticker
        profile = data.profile
        price = data.price

        key_findings: List[str] = []
        warnings: List[str] = []
        confidence = 0.95

        # 1. Market Cap Categorization
        market_cap = price.market_cap
        if market_cap:
            if market_cap >= 200_000_000_000:
                cap_category = "Mega-Cap"
            elif market_cap >= 10_000_000_000:
                cap_category = "Large-Cap"
            elif market_cap >= 2_000_000_000:
                cap_category = "Mid-Cap"
            elif market_cap >= 300_000_000:
                cap_category = "Small-Cap"
            else:
                cap_category = "Micro-Cap"
            key_findings.append(f"Classified as a {cap_category} equity with a market valuation of ${market_cap:,.0f} {price.currency}.")
        else:
            cap_category = "Unknown"
            warnings.append("Market capitalization data is not available from market provider.")
            confidence -= 0.15

        # 2. Sector and Industry Positioning
        sector = profile.sector
        industry = profile.industry
        if sector and industry:
            key_findings.append(f"Operates in the {sector} sector, specifically within the {industry} industry.")
        elif sector:
            key_findings.append(f"Operates in the {sector} sector; industry subcategory is unlisted.")
            warnings.append("Specific industry subcategory was not provided.")
            confidence -= 0.05
        else:
            warnings.append("Sector and industry classification data are missing.")
            confidence -= 0.15

        # 3. Beta & Volatility Profile
        beta = profile.beta
        if beta is not None:
            if beta > 1.3:
                beta_desc = f"high market volatility (Beta: {beta:.2f})"
            elif beta < 0.8:
                beta_desc = f"defensive, lower-than-market volatility (Beta: {beta:.2f})"
            else:
                beta_desc = f"market-aligned volatility (Beta: {beta:.2f})"
            key_findings.append(f"Exhibits {beta_desc}.")
        else:
            warnings.append("Beta volatility coefficient is not reported.")
            confidence -= 0.05

        # 4. Business Summary Check
        summary = profile.business_summary
        if summary:
            # First two sentences of summary for concise context
            sentences = [s.strip() for s in summary.split(".") if s.strip()]
            concise_summary = ". ".join(sentences[:2]) + "." if sentences else summary
            key_findings.append(f"Core Business: {concise_summary}")
        else:
            warnings.append("Company business summary is unavailable.")
            confidence -= 0.10

        # Construct Narrative Analysis
        analysis_parts = [
            f"{profile.company_name} ({ticker}) is a {cap_category} entity based in {profile.country or 'an unspecified jurisdiction'}."
        ]
        if sector:
            analysis_parts.append(f"Positioned within {sector} ({industry or 'Broad Industry'}), the company's risk profile reflects general industry exposure.")
        if beta is not None:
            analysis_parts.append(f"Its beta coefficient of {beta:.2f} suggests an investor should expect {'amplified' if beta > 1.0 else 'dampened'} sensitivity to broader market swings.")

        narrative_analysis = " ".join(analysis_parts)

        supporting_data = {
            "market_cap": market_cap,
            "currency": price.currency,
            "sector": sector,
            "industry": industry,
            "country": profile.country,
            "beta": beta,
            "website": profile.website,
        }

        return MarketResearchOutput(
            agent_name=cls.AGENT_NAME,
            ticker=ticker,
            company_name=profile.company_name,
            sector=sector,
            industry=industry,
            market_cap_category=cap_category,
            analysis=narrative_analysis,
            key_findings=key_findings,
            supporting_data=supporting_data,
            warnings_and_limitations=warnings,
            confidence_level=round(max(0.1, min(1.0, confidence)), 2),
        )

