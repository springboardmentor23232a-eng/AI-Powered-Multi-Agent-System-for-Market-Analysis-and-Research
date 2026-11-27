import hashlib
import json
import logging
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd

from app.schemas.dataset import (
    ValidationIssueItem,
    RawDatasetSnapshot,
    ValidatedDatasetSummary,
    DataQualityMetrics,
    FiftyTwoWeekMetrics,
)

logger = logging.getLogger("uvicorn.error")

REQUIRED_OHLCV_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


def normalize_dataset_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Normalizes incoming DataFrame column names to standard canonical titlecase.
    Maps common provider variations ('open', 'OPEN', 'adj close', etc.).
    """
    col_mapping = {}
    normalized_cols = []

    for col in df.columns:
        c_str = str(col).strip()
        c_lower = c_str.lower()

        if c_lower in {"open"}:
            col_mapping[col] = "Open"
            normalized_cols.append("Open")
        elif c_lower in {"high"}:
            col_mapping[col] = "High"
            normalized_cols.append("High")
        elif c_lower in {"low"}:
            col_mapping[col] = "Low"
            normalized_cols.append("Low")
        elif c_lower in {"close", "adj close", "adjclose"}:
            # Keep original Close if present, map Adj Close if Close missing
            if "Close" not in normalized_cols:
                col_mapping[col] = "Close"
                normalized_cols.append("Close")
            else:
                col_mapping[col] = c_str
        elif c_lower in {"volume", "vol"}:
            col_mapping[col] = "Volume"
            normalized_cols.append("Volume")
        elif c_lower in {"date", "datetime", "timestamp"}:
            col_mapping[col] = "Date"
            normalized_cols.append("Date")
        else:
            col_mapping[col] = c_str

    renamed_df = df.rename(columns=col_mapping).copy()
    return renamed_df, list(renamed_df.columns)


def compute_sha256_hash(data: Any) -> str:
    """
    Computes deterministic SHA-256 checksum of raw source data.
    """
    try:
        serialized = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()
    except Exception:
        return hashlib.sha256(str(data).encode("utf-8")).hexdigest()


def calculate_data_quality_score(
    total_raw: int,
    defective_rows_count: int,
    duplicate_dates_count: int,
    reordered_chronology: bool,
) -> Tuple[float, float, float, float]:
    """
    Explicit, reproducible mathematical Data Quality Scoring Formula.
    Prevents double-counting by charging at most once per defective row.
    Returns: (final_score, fatal_defect_penalty, duplicate_penalty, chronology_penalty)
    """
    if total_raw <= 0:
        return 0.0, 100.0, 0.0, 0.0

    fatal_ratio = defective_rows_count / total_raw
    dup_ratio = duplicate_dates_count / total_raw

    fatal_penalty = round(min(60.0, fatal_ratio * 100.0 * 1.2), 2)
    dup_penalty = round(min(25.0, dup_ratio * 100.0 * 0.5), 2)
    chron_penalty = 5.0 if reordered_chronology else 0.0

    total_penalty = round(min(100.0, fatal_penalty + dup_penalty + chron_penalty), 2)
    final_score = round(max(0.0, 100.0 - total_penalty), 2)

    return final_score, fatal_penalty, dup_penalty, chron_penalty


def determine_validation_status(
    total_raw: int,
    valid_count: int,
    excluded_count: int,
    duplicate_dates_count: int,
    reordered_chronology: bool,
    missing_core_columns: bool,
    quality_score: float,
) -> str:
    """
    Mutually exclusive, non-overlapping status policy:
    - FAILED: empty dataset, zero valid records, missing required OHLC columns, or score below 70.
    - WARNING: usable dataset (N_valid > 0 and not FAILED) with ANY duplicate dates, excluded records,
      corrections, or chronological reordering, regardless of whether score is >= 98.
    - PASSED: score >= 98, zero duplicates, zero excluded records, zero corrections,
      and all required OHLCV columns valid.
    """
    # 1. FAILED rule
    if total_raw == 0 or valid_count == 0 or missing_core_columns or quality_score < 70.0:
        return "FAILED"

    # 2. WARNING rule (usable dataset with any documented defect or correction)
    if (
        duplicate_dates_count > 0
        or excluded_count > 0
        or reordered_chronology
    ):
        return "WARNING"

    # 3. PASSED rule (only 100% pristine records with score >= 98)
    if (
        quality_score >= 98.0
        and excluded_count == 0
        and duplicate_dates_count == 0
        and not reordered_chronology
        and valid_count == total_raw
    ):
        return "PASSED"

    # Fallback to WARNING if score is between 70 and 98 without exclusions
    return "WARNING"


def compute_fifty_two_week_metrics(valid_df: pd.DataFrame) -> FiftyTwoWeekMetrics:
    """
    Calculates 52-week pricing metrics with strict minimum 250 valid trading days enforcement.
    If fewer than 250 valid trading days exist, returns null with explicit coverage explanation.
    """
    valid_trading_days = len(valid_df)

    if valid_trading_days < 250:
        return FiftyTwoWeekMetrics(
            status="unavailable",
            high=None,
            low=None,
            range_pct=None,
            valid_trading_days=valid_trading_days,
            notes=f"Insufficient historical coverage: requires >= 250 valid trading days; current dataset contains {valid_trading_days} valid trading days.",
        )

    # 250 or more valid trading sessions available
    last_250 = valid_df.tail(250)
    high_52 = round(float(last_250["High"].max()), 2)
    low_52 = round(float(last_250["Low"].min()), 2)
    range_pct = round(((high_52 - low_52) / low_52) * 100, 2) if low_52 > 0 else 0.0

    return FiftyTwoWeekMetrics(
        status="verified",
        high=high_52,
        low=low_52,
        range_pct=range_pct,
        valid_trading_days=valid_trading_days,
        notes=f"52-week metrics verified over {valid_trading_days} valid trading sessions.",
    )


def validate_and_process_dataset(
    raw_input_df: Optional[pd.DataFrame],
    ticker: str,
    data_source: str,
    retrieval_timestamp: str,
) -> Tuple[RawDatasetSnapshot, ValidatedDatasetSummary, DataQualityMetrics, List[ValidationIssueItem]]:
    """
    Core Deterministic Validation Engine (Zero LLM involvement).
    - Preserves source data in immutable raw snapshot.
    - Executes 10 deterministic checks with non-overlapping primary defect hierarchy.
    - Emits exhaustive audit log of every modified or excluded row.
    - Determines mutually exclusive status and calculates quality score.
    """
    clean_ticker = ticker.strip().upper()
    issues: List[ValidationIssueItem] = []

    # 1. Handle Empty Input Dataset
    if raw_input_df is None or not isinstance(raw_input_df, pd.DataFrame) or raw_input_df.empty:
        raw_snap = RawDatasetSnapshot(
            total_records=0,
            columns=[],
            sha256_hash=compute_sha256_hash([]),
            retrieved_at=retrieval_timestamp,
            data_source=data_source,
            records_sample=[],
        )
        val_sum = ValidatedDatasetSummary(
            valid_records_count=0,
            start_date=None,
            end_date=None,
            highest_price=None,
            lowest_price=None,
            average_volume=None,
            period_change_pct=None,
            fifty_two_week_metrics=FiftyTwoWeekMetrics(
                status="unavailable",
                high=None,
                low=None,
                range_pct=None,
                valid_trading_days=0,
                notes="Cannot compute 52-week metrics on empty dataset.",
            ),
            candles_sample=[],
        )
        quality = DataQualityMetrics(
            total_raw_records=0,
            valid_records=0,
            excluded_records=0,
            duplicate_dates_count=0,
            missing_values_count=0,
            missing_values_by_column={},
            negative_prices_count=0,
            negative_volumes_count=0,
            inconsistent_ohlc_count=0,
            invalid_date_formats_count=0,
            reordered_chronology=False,
            data_quality_score=0.0,
            fatal_defect_penalty=100.0,
            duplicate_penalty=0.0,
            chronology_penalty=0.0,
            validation_status="FAILED",
        )
        issues.append(
            ValidationIssueItem(
                row_index=0,
                date=None,
                column="ALL",
                issue_type="EMPTY_DATASET",
                severity="ERROR",
                raw_values={},
                message=f"No market data was returned by data provider '{data_source}' for ticker '{clean_ticker}'.",
                action_taken="DATASET_REJECTED",
            )
        )
        return raw_snap, val_sum, quality, issues

    total_raw_records = len(raw_input_df)

    # 2. Extract Raw Snapshot (Immutable)
    norm_df, columns_list = normalize_dataset_columns(raw_input_df)

    # Convert index to Date column if DateTimeIndex
    if "Date" not in norm_df.columns:
        if isinstance(norm_df.index, (pd.DatetimeIndex, pd.Index)):
            norm_df["Date"] = norm_df.index
            norm_df = norm_df.reset_index(drop=True)

    # Capture raw row records
    raw_records_list: List[Dict[str, Any]] = []
    for r_idx, row in norm_df.iterrows():
        r_dict = {}
        for c in norm_df.columns:
            val = row[c]
            if isinstance(val, (pd.Timestamp, pd.Period)):
                r_dict[c] = val.strftime("%Y-%m-%d")
            elif pd.isna(val) or (isinstance(val, float) and (np.isinf(val) or np.isnan(val))):
                r_dict[c] = None
            else:
                r_dict[c] = val
        r_dict["_raw_row_id"] = int(r_idx)
        raw_records_list.append(r_dict)

    sha256_checksum = compute_sha256_hash(raw_records_list)
    raw_snap = RawDatasetSnapshot(
        total_records=total_raw_records,
        columns=columns_list,
        sha256_hash=sha256_checksum,
        retrieved_at=retrieval_timestamp,
        data_source=data_source,
        records_sample=raw_records_list[:15],
    )

    # 3. Check for Required Columns
    missing_cols = [c for c in REQUIRED_OHLCV_COLUMNS if c not in norm_df.columns]
    missing_core_columns = len(missing_cols) > 0
    if missing_core_columns:
        for mc in missing_cols:
            issues.append(
                ValidationIssueItem(
                    row_index=-1,
                    date=None,
                    column=mc,
                    issue_type="MISSING_CORE_COLUMN",
                    severity="ERROR",
                    raw_values={},
                    message=f"Required OHLCV column '{mc}' is missing from provider schema.",
                    action_taken="DATASET_REJECTED",
                )
            )

    # 4. Row-by-Row Deterministic Evaluation with Non-Overlapping Defect Hierarchy
    missing_by_column: Dict[str, int] = {c: 0 for c in REQUIRED_OHLCV_COLUMNS}
    defective_row_indices = set()
    excluded_row_indices = set()

    missing_values_count = 0
    negative_prices_count = 0
    negative_volumes_count = 0
    inconsistent_ohlc_count = 0
    invalid_date_formats_count = 0

    parsed_rows = []

    for idx, row in norm_df.iterrows():
        raw_vals = raw_records_list[idx]
        has_fatal_defect = False
        primary_defect_tier = None

        # Tier 1: Date Parsing
        raw_date_val = row.get("Date")
        date_str = None
        if raw_date_val is None or pd.isna(raw_date_val):
            has_fatal_defect = True
            primary_defect_tier = "Tier 1: Unparseable Date"
            invalid_date_formats_count += 1
            issues.append(
                ValidationIssueItem(
                    row_index=idx,
                    date=None,
                    column="Date",
                    issue_type="INVALID_DATE_FORMAT",
                    severity="ERROR",
                    raw_values=raw_vals,
                    message="Trading date is missing or unparseable.",
                    action_taken="FLAGGED_AND_EXCLUDED",
                )
            )
        else:
            try:
                dt = pd.to_datetime(raw_date_val)
                date_str = dt.strftime("%Y-%m-%d")
            except Exception:
                has_fatal_defect = True
                primary_defect_tier = "Tier 1: Unparseable Date"
                invalid_date_formats_count += 1
                issues.append(
                    ValidationIssueItem(
                        row_index=idx,
                        date=str(raw_date_val),
                        column="Date",
                        issue_type="INVALID_DATE_FORMAT",
                        severity="ERROR",
                        raw_values=raw_vals,
                        message=f"Invalid date format '{raw_date_val}' could not be standardized.",
                        action_taken="FLAGGED_AND_EXCLUDED",
                    )
                )

        # Tier 2: Missing Values / Non-Numeric
        row_has_missing = False
        for col in REQUIRED_OHLCV_COLUMNS:
            val = row.get(col)
            if val is None or pd.isna(val) or (isinstance(val, float) and (np.isinf(val) or np.isnan(val))):
                missing_by_column[col] += 1
                row_has_missing = True
                if not has_fatal_defect:
                    has_fatal_defect = True
                    primary_defect_tier = "Tier 2: Missing Value"
                missing_values_count += 1
                issues.append(
                    ValidationIssueItem(
                        row_index=idx,
                        date=date_str,
                        column=col,
                        issue_type="MISSING_VALUE",
                        severity="ERROR",
                        raw_values=raw_vals,
                        message=f"Missing or non-numeric value in column '{col}'.",
                        action_taken="FLAGGED_AND_EXCLUDED",
                    )
                )

        # If already defective at Tier 1 or 2, exclude row and skip numeric checks
        if has_fatal_defect:
            defective_row_indices.add(idx)
            excluded_row_indices.add(idx)
            continue

        # Convert numerics
        try:
            o_val = float(row["Open"])
            h_val = float(row["High"])
            l_val = float(row["Low"])
            c_val = float(row["Close"])
            v_val = int(float(row["Volume"]))
        except (ValueError, TypeError) as cast_err:
            defective_row_indices.add(idx)
            excluded_row_indices.add(idx)
            issues.append(
                ValidationIssueItem(
                    row_index=idx,
                    date=date_str,
                    column="NUMERIC_PARSE",
                    issue_type="INVALID_NUMERIC",
                    severity="ERROR",
                    raw_values=raw_vals,
                    message=f"Numerical casting error: {cast_err}",
                    action_taken="FLAGGED_AND_EXCLUDED",
                )
            )
            continue

        # Tier 3: Positivity & Non-negative volume
        if o_val <= 0 or h_val <= 0 or l_val <= 0 or c_val <= 0:
            defective_row_indices.add(idx)
            excluded_row_indices.add(idx)
            negative_prices_count += 1
            issues.append(
                ValidationIssueItem(
                    row_index=idx,
                    date=date_str,
                    column="PRICE",
                    issue_type="NEGATIVE_PRICE",
                    severity="ERROR",
                    raw_values=raw_vals,
                    message=f"Non-positive price detected (Open={o_val}, High={h_val}, Low={l_val}, Close={c_val}).",
                    action_taken="FLAGGED_AND_EXCLUDED",
                )
            )
            continue

        if v_val < 0:
            defective_row_indices.add(idx)
            excluded_row_indices.add(idx)
            negative_volumes_count += 1
            issues.append(
                ValidationIssueItem(
                    row_index=idx,
                    date=date_str,
                    column="Volume",
                    issue_type="NEGATIVE_VOLUME",
                    severity="ERROR",
                    raw_values=raw_vals,
                    message=f"Negative volume detected ({v_val}).",
                    action_taken="FLAGGED_AND_EXCLUDED",
                )
            )
            continue

        # Tier 4: Geometric OHLC Inconsistencies
        # High must be >= Low
        if h_val < l_val - 1e-4:
            defective_row_indices.add(idx)
            excluded_row_indices.add(idx)
            inconsistent_ohlc_count += 1
            issues.append(
                ValidationIssueItem(
                    row_index=idx,
                    date=date_str,
                    column="High/Low",
                    issue_type="HIGH_LESS_THAN_LOW",
                    severity="ERROR",
                    raw_values=raw_vals,
                    message=f"Geometric violation: High ({h_val}) is lower than Low ({l_val}).",
                    action_taken="FLAGGED_AND_EXCLUDED",
                )
            )
            continue

        # Open and Close must lie within [Low, High]
        if o_val > h_val + 1e-4 or c_val > h_val + 1e-4 or o_val < l_val - 1e-4 or c_val < l_val - 1e-4:
            defective_row_indices.add(idx)
            excluded_row_indices.add(idx)
            inconsistent_ohlc_count += 1
            issues.append(
                ValidationIssueItem(
                    row_index=idx,
                    date=date_str,
                    column="OHLC_BOUNDS",
                    issue_type="OHLC_INCONSISTENCY",
                    severity="ERROR",
                    raw_values=raw_vals,
                    message=f"OHLC inconsistency: Open ({o_val}) or Close ({c_val}) outside [Low={l_val}, High={h_val}].",
                    action_taken="FLAGGED_AND_EXCLUDED",
                )
            )
            continue

        # Row passed individual cell checks
        parsed_rows.append({
            "source_row_id": idx,
            "Date": date_str,
            "Open": round(o_val, 2),
            "High": round(h_val, 2),
            "Low": round(l_val, 2),
            "Close": round(c_val, 2),
            "Volume": v_val,
        })

    # 5. Duplicate Date Detection (No Silent Retention / Deletion)
    clean_candidates_df = pd.DataFrame(parsed_rows) if parsed_rows else pd.DataFrame()
    duplicate_dates_count = 0
    final_valid_rows = []

    if not clean_candidates_df.empty and "Date" in clean_candidates_df.columns:
        dup_mask = clean_candidates_df.duplicated(subset=["Date"], keep=False)
        duplicate_rows_df = clean_candidates_df[dup_mask]

        if not duplicate_rows_df.empty:
            duplicate_dates_count = len(duplicate_rows_df)
            # Group by date to log each conflicting/duplicate occurrence
            for dup_date, grp in duplicate_rows_df.groupby("Date"):
                rows_in_grp = grp.to_dict(orient="records")
                for i, d_row in enumerate(rows_in_grp):
                    is_canonical = (i == len(rows_in_grp) - 1)  # latest kept
                    action_taken = "DUPLICATE_CANONICAL_RETAINED" if is_canonical else "DUPLICATE_SUPERSEDED_EXCLUDED"
                    issues.append(
                        ValidationIssueItem(
                            row_index=d_row["source_row_id"],
                            date=dup_date,
                            column="Date",
                            issue_type="DUPLICATE_DATE",
                            severity="WARNING",
                            raw_values=raw_records_list[d_row["source_row_id"]],
                            message=f"Duplicate date record {i+1} of {len(rows_in_grp)} for trading date '{dup_date}'.",
                            action_taken=action_taken,
                        )
                    )
                    if not is_canonical:
                        excluded_row_indices.add(d_row["source_row_id"])

            # Deduplicate by keeping last canonical row
            deduped_df = clean_candidates_df.drop_duplicates(subset=["Date"], keep="last")
        else:
            deduped_df = clean_candidates_df

        # 6. Chronological Order Verification
        reordered_chronology = False
        if len(deduped_df) > 1:
            is_monotonic = deduped_df["Date"].is_monotonic_increasing
            if not is_monotonic:
                reordered_chronology = True
                deduped_df = deduped_df.sort_values(by="Date", ascending=True)
                issues.append(
                    ValidationIssueItem(
                        row_index=-1,
                        date=None,
                        column="Date",
                        issue_type="CHRONOLOGY_REORDERED",
                        severity="WARNING",
                        raw_values={},
                        message="Historical dates were out of sequence; automatically sorted in ascending order.",
                        action_taken="CHRONOLOGY_REORDERED",
                    )
                )

        final_valid_rows = deduped_df.to_dict(orient="records")
    else:
        reordered_chronology = False

    valid_count = len(final_valid_rows)
    excluded_count = total_raw_records - valid_count

    # 7. Calculate Deterministic Quality Score
    defective_count = len(defective_row_indices)
    quality_score, fatal_pen, dup_pen, chron_pen = calculate_data_quality_score(
        total_raw=total_raw_records,
        defective_rows_count=defective_count,
        duplicate_dates_count=duplicate_dates_count,
        reordered_chronology=reordered_chronology,
    )

    # 8. Determine Mutually Exclusive Validation Status
    val_status = determine_validation_status(
        total_raw=total_raw_records,
        valid_count=valid_count,
        excluded_count=excluded_count,
        duplicate_dates_count=duplicate_dates_count,
        reordered_chronology=reordered_chronology,
        missing_core_columns=missing_core_columns,
        quality_score=quality_score,
    )

    quality_metrics = DataQualityMetrics(
        total_raw_records=total_raw_records,
        valid_records=valid_count,
        excluded_records=excluded_count,
        duplicate_dates_count=duplicate_dates_count,
        missing_values_count=missing_values_count,
        missing_values_by_column=missing_by_column,
        negative_prices_count=negative_prices_count,
        negative_volumes_count=negative_volumes_count,
        inconsistent_ohlc_count=inconsistent_ohlc_count,
        invalid_date_formats_count=invalid_date_formats_count,
        reordered_chronology=reordered_chronology,
        data_quality_score=quality_score,
        fatal_defect_penalty=fatal_pen,
        duplicate_penalty=dup_pen,
        chronology_penalty=chron_pen,
        validation_status=val_status,
    )

    # 9. Compute Validated Summary Statistics and 52-Week Metrics
    if valid_count > 0:
        valid_df_final = pd.DataFrame(final_valid_rows)
        start_d = str(final_valid_rows[0]["Date"])
        end_d = str(final_valid_rows[-1]["Date"])
        h_price = round(float(valid_df_final["High"].max()), 2)
        l_price = round(float(valid_df_final["Low"].min()), 2)
        avg_v = round(float(valid_df_final["Volume"].mean()), 2)
        first_c = float(final_valid_rows[0]["Close"])
        last_c = float(final_valid_rows[-1]["Close"])
        pct_chg = round(((last_c - first_c) / first_c) * 100, 2) if first_c > 0 else 0.0

        # Conditional 52-week metrics (strict >= 250 valid trading days)
        fifty_two_metrics = compute_fifty_two_week_metrics(valid_df_final)

        val_summary = ValidatedDatasetSummary(
            valid_records_count=valid_count,
            start_date=start_d,
            end_date=end_d,
            highest_price=h_price,
            lowest_price=l_price,
            average_volume=avg_v,
            period_change_pct=pct_chg,
            fifty_two_week_metrics=fifty_two_metrics,
            candles_sample=final_valid_rows[:15],
        )
    else:
        val_summary = ValidatedDatasetSummary(
            valid_records_count=0,
            start_date=None,
            end_date=None,
            highest_price=None,
            lowest_price=None,
            average_volume=None,
            period_change_pct=None,
            fifty_two_week_metrics=FiftyTwoWeekMetrics(
                status="unavailable",
                high=None,
                low=None,
                range_pct=None,
                valid_trading_days=0,
                notes="Cannot compute 52-week metrics: zero valid records in dataset.",
            ),
            candles_sample=[],
        )

    return raw_snap, val_summary, quality_metrics, issues
