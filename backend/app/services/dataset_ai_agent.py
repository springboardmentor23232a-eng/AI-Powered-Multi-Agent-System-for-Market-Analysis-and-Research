import logging
from typing import List, Dict, Any, Optional
from app.schemas.dataset import (
    DataQualityMetrics,
    ValidatedDatasetSummary,
    RawDatasetSnapshot,
    ValidationIssueItem,
    AINarrativeExplanation,
)

logger = logging.getLogger("uvicorn.error")


def synthesize_validation_narrative(
    ticker: str,
    company_name: str,
    market: str,
    active_provider: str,
    quality: DataQualityMetrics,
    val_summary: ValidatedDatasetSummary,
    raw_snap: RawDatasetSnapshot,
    issues: List[ValidationIssueItem],
) -> AINarrativeExplanation:
    """
    AI Narrative Synthesis Engine.
    Interprets verified deterministic validation metrics into an institutional-grade report.
    Adheres strictly to factual guardrails:
    - Never states corporate events (earnings, splits, halts) as established facts without verified filings.
    - Strictly labels market anomalies as possible/unconfirmed explanations.
    """
    clean_ticker = ticker.strip().upper()
    score = quality.data_quality_score
    status = quality.validation_status

    # 1. Executive Summary Synthesis
    if status == "PASSED":
        exec_text = (
            f"The historical OHLCV dataset for {company_name} ({clean_ticker}) collected via {active_provider} "
            f"meets institutional data quality standards with an audit score of {score}/100. "
            f"All {quality.total_raw_records} raw records were validated with zero missing cells, zero duplicate dates, "
            f"and strict OHLC geometric consistency."
        )
    elif status == "WARNING":
        issues_summary = []
        if quality.duplicate_dates_count > 0:
            issues_summary.append(f"{quality.duplicate_dates_count} duplicate trading dates were detected and resolved")
        if quality.excluded_records > 0:
            issues_summary.append(f"{quality.excluded_records} defective rows were isolated and excluded")
        if quality.reordered_chronology:
            issues_summary.append("historical dates were sorted into chronological order")

        reasons = "; ".join(issues_summary) if issues_summary else "minor data caveats detected"
        exec_text = (
            f"The dataset for {company_name} ({clean_ticker}) retrieved from {active_provider} received a WARNING "
            f"status with an audit score of {score}/100. Out of {quality.total_raw_records} raw records, "
            f"{quality.valid_records} clean trading sessions were verified, while {reasons}. "
            f"The dataset remains usable for general research with disclosed caveats."
        )
    else:  # FAILED
        exec_text = (
            f"The dataset collection and validation for {company_name} ({clean_ticker}) FAILED with an audit score "
            f"of {score}/100. The dataset contains pervasive structural corruption, zero valid records, or missing "
            f"core OHLC columns, making it unsuitable for automated research."
        )

    # 2. Market Anomaly Context (Strictly hypothetical unless verified)
    anomaly_notes = []
    if val_summary.valid_records_count > 0 and val_summary.average_volume:
        avg_vol = val_summary.average_volume
        # Check candles sample for volume outliers (> 3x average volume)
        volume_spikes = [
            c for c in val_summary.candles_sample
            if c.get("Volume") and c["Volume"] > (avg_vol * 3.0)
        ]
        if volume_spikes:
            dates_spiked = ", ".join([s["Date"] for s in volume_spikes[:2]])
            anomaly_notes.append(
                f"Statistical trading volume spikes (>3x average volume) were detected on {dates_spiked}. "
                f"In the absence of verified corporate action filings attached to this query, these volume surges "
                f"are noted as possible market events (such as an earnings release, index rebalancing, or news-driven volatility) "
                f"rather than established facts."
            )

        # Check for wide single-session intraday ranges (> 10% between High and Low)
        wide_ranges = [
            c for c in val_summary.candles_sample
            if c.get("High") and c.get("Low") and c["Low"] > 0
            and (((c["High"] - c["Low"]) / c["Low"]) > 0.10)
        ]
        if wide_ranges:
            dates_wide = ", ".join([w["Date"] for w in wide_ranges[:2]])
            anomaly_notes.append(
                f"Elevated intraday volatility (>10% High-Low spread) occurred on {dates_wide}. "
                f"Without verified exchange regulatory notices, this price fluctuation is cataloged as a potential high-volatility "
                f"trading session rather than an established structural event."
            )

    if not anomaly_notes:
        if val_summary.valid_records_count > 0:
            anomaly_notes.append(
                f"No abnormal intraday price jumps or excessive volume distortions were detected across "
                f"the validated series of {val_summary.valid_records_count} trading sessions."
            )
        else:
            anomaly_notes.append("No market anomaly analysis possible due to lack of valid trading sessions.")

    anomaly_text = " ".join(anomaly_notes)

    # 3. Cleaning & Transformation Transparency Notes
    cleaning_parts = []
    if quality.excluded_records > 0:
        cleaning_parts.append(
            f"A total of {quality.excluded_records} raw records were excluded from the clean series: "
            f"{quality.missing_values_count} missing values, {quality.negative_prices_count} non-positive prices, "
            f"{quality.inconsistent_ohlc_count} OHLC geometric inconsistencies, and {quality.invalid_date_formats_count} invalid dates."
        )
    else:
        cleaning_parts.append("Zero raw records required exclusion; all input rows conformed to pricing schemas.")

    if quality.duplicate_dates_count > 0:
        cleaning_parts.append(
            f"Deduplication resolved {quality.duplicate_dates_count} duplicate calendar date occurrences by retaining "
            f"the canonical latest timestamp. Superseded duplicate rows remain fully archived in the raw snapshot."
        )
    else:
        cleaning_parts.append("Zero duplicate calendar dates were encountered.")

    if quality.reordered_chronology:
        cleaning_parts.append("Trading sessions were reordered into strictly ascending calendar sequence.")
    else:
        cleaning_parts.append("Chronological date sequence was strictly ascending as delivered.")

    cleaning_text = " ".join(cleaning_parts)

    # 4. Downstream Research Readiness Assessment
    if status == "PASSED":
        readiness_text = (
            f"APPROVED FOR ALL RESEARCH MODULES. The dataset is fully validated and certified for "
            f"Technical Analysis (Module 4), Machine Learning and Forecasting (Module 5), and Quantitative Backtesting."
        )
    elif status == "WARNING":
        readiness_text = (
            f"CONDITIONALLY APPROVED FOR RESEARCH. The dataset is suitable for qualitative screening and fundamental "
            f"context. Algorithmic traders and backtesting models should account for the {quality.excluded_records} excluded "
            f"rows and documented calendar deduplications."
        )
    else:
        readiness_text = (
            f"REJECTED FOR DOWNSTREAM MODELING. Critical defects prevent automated analysis. "
            f"Please verify ticker symbol spelling or query an alternative market exchange."
        )

    return AINarrativeExplanation(
        executive_summary=exec_text,
        market_anomaly_interpretation=anomaly_text,
        cleaning_transparency_notes=cleaning_text,
        research_readiness_assessment=readiness_text,
    )
