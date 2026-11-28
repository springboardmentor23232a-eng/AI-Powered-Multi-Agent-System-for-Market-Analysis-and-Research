
import math
from collections import Counter
from datetime import date


def assess_data_quality(financials, historical, ratio_data):

    issues = []
    checks = []

    def add_issue(category, field, message, severity="warning"):
        issues.append({
            "category": category,
            "field": field,
            "message": message,
            "severity": severity,
        })

    statements = [
        "income_statement",
        "balance_sheet",
        "cash_flow",
    ]

    latest_periods = {}

    # 1. Validate financial statements
    for name in statements:

        statement = financials.get(name) or {}
        periods = statement.get("periods", [])
        rows = statement.get("rows", [])

        if not periods or not rows:
            add_issue(
                "missing_data",
                name,
                f"{name} is unavailable."
            )
            continue

        # Duplicate reporting periods
        duplicates = [
            period
            for period, count in Counter(periods).items()
            if count > 1
        ]

        for period in duplicates:
            add_issue(
                "inconsistent_data",
                name,
                f"Duplicate reporting period: {period}.",
                "error"
            )

        # Validate reporting dates
        valid_periods = []

        for period in periods:
            try:
                valid_periods.append(
                    date.fromisoformat(period)
                )
            except (ValueError, TypeError):
                add_issue(
                    "inconsistent_data",
                    name,
                    f"Invalid reporting date: {period}.",
                    "error"
                )

        if valid_periods:
            latest_periods[name] = max(valid_periods)

        # Validate numerical values
        for row in rows:

            item = row.get("item", "Unknown field")
            values = row.get("values", [])

            if len(values) != len(periods):
                add_issue(
                    "inconsistent_data",
                    item,
                    f"{name}: number of values does not "
                    "match the number of reporting periods.",
                    "error"
                )

            for value in values:

                if value is None:
                    continue

                try:
                    valid = math.isfinite(float(value))
                except (ValueError, TypeError, OverflowError):
                    valid = False

                if not valid:
                    add_issue(
                        "invalid_value",
                        item,
                        f"{name} contains a non-finite "
                        "or non-numeric value.",
                        "error"
                    )
                    break

    checks.append("Financial statement structure")

    # 2. Check reporting period consistency
    if len(set(latest_periods.values())) > 1:
        add_issue(
            "inconsistent_data",
            "reporting_periods",
            "The latest reporting dates differ "
            "across financial statements."
        )

    checks.append("Reporting period consistency")

    # 3. Validate historical financial records
    records = historical.get("records", [])

    usable_records = []

    for row in records:

        period = row["period"]
        missing = row.get("missing_fields", [])

        if missing:
            add_issue(
                "missing_data",
                period,
                f"Missing financial fields for {period}: "
                + ", ".join(missing)
            )

        if any(
            row.get(key) is not None
            for key in [
                "revenue",
                "net_income",
                "total_debt",
                "equity",
                "operating_cash_flow",
            ]
        ):
            usable_records.append(row)

        # Negative revenue or debt
        for field in ["revenue", "total_debt"]:

            value = row.get(field)

            if value is not None and value < 0:
                add_issue(
                    "inconsistent_data",
                    field,
                    f"{field} is negative for {period}. "
                    "Verify the source figures."
                )

    checks.append("Historical financial data")

    # 4. Check historical coverage
    if len(usable_records) < 2:
        add_issue(
            "insufficient_data",
            "historical",
            "Fewer than two usable annual reporting "
            "periods are available."
        )

    checks.append("Historical data coverage")

    # 5. Check financial ratio availability
    for field, value in ratio_data.get("ratios", {}).items():

        if value is None:
            reason = ratio_data.get(
                "ratio_reasons", {}
            ).get(
                field,
                "Required data is unavailable."
            )

            add_issue(
                "ratio_unavailable",
                field,
                reason
            )

    checks.append("Financial ratio availability")

    # 6. Check currency information
    if not financials.get("currency"):
        add_issue(
            "missing_data",
            "currency",
            "Financial reporting currency is unavailable."
        )

    checks.append("Currency availability")

    # Generate summary
    errors = sum(
        issue["severity"] == "error"
        for issue in issues
    )

    warnings = sum(
        issue["severity"] == "warning"
        for issue in issues
    )

    if errors:
        status = "inconsistent"
    elif warnings:
        status = "partial"
    else:
        status = "complete"

    return {
        "status": status,
        "checks_performed": checks,
        "total_periods": len(records),
        "usable_periods": len(usable_records),
        "error_count": errors,
        "warning_count": warnings,
        "issues": issues,
        "note": (
            "Data quality checks assess availability "
            "and internal consistency, not the accuracy "
            "of the original financial statements."
        ),
    }
