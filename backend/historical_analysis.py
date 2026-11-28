
import math
from datetime import date

from fundamental_agent.yahoo_adapter import FIELD_MAP


def get_value(statement, names, period):
    periods = statement.get("periods", [])

    # Reject ambiguous duplicate reporting periods
    if periods.count(period) != 1:
        return None

    index = periods.index(period)

    for name in names:
        for row in statement.get("rows", []):
            if row.get("item") != name:
                continue

            values = row.get("values", [])

            if index >= len(values):
                continue

            try:
                value = float(values[index])

                if math.isfinite(value):
                    return value

            except (TypeError, ValueError, OverflowError):
                continue

    return None


def percentage(numerator, denominator):
    if numerator is None or denominator is None:
        return None

    if denominator <= 0:
        return None

    return round(numerator / denominator * 100, 2)


def consecutive_years(previous, current):
    try:
        start = date.fromisoformat(previous[:10])
        end = date.fromisoformat(current[:10])

        return 330 <= (end - start).days <= 400

    except (ValueError, TypeError):
        return False


def growth(current, previous):
    if current is None or previous is None:
        return None

    if previous <= 0:
        return None

    return round((current - previous) / previous * 100, 2)


def generate_trend(records, field, label):
    available = [
        row for row in records
        if row.get(field) is not None
    ]

    if len(available) < 2:
        return f"Insufficient historical data to compare {label}."

    first = available[0]
    last = available[-1]

    start = first[field]
    end = last[field]

    if end > start:
        direction = "increased"
    elif end < start:
        direction = "decreased"
    else:
        direction = "remained unchanged"

    change = growth(end, start)

    message = (
        f"{label.capitalize()} {direction} between "
        f"{first['period']} and {last['period']}"
    )

    if change is not None:
        message += f" (overall change: {change:+.2f}%)"

    return message + "."


def analyze_historical_performance(financials):

    income = financials.get("income_statement") or {}
    balance = financials.get("balance_sheet") or {}
    cash_flow = financials.get("cash_flow") or {}

    periods = sorted(set(
        income.get("periods", [])
        + balance.get("periods", [])
        + cash_flow.get("periods", [])
    ))

    if not periods:
        return {
            "status": "unavailable",
            "message": "No historical financial statements are available.",
            "records": [],
            "trends": {},
        }

    records = []

    for period in periods:

        raw = {}

        # Reuse existing Yahoo Finance field mappings
        for field, (statement, names) in FIELD_MAP.items():
            raw[field] = get_value(
                financials.get(statement) or {},
                names,
                period
            )

        revenue = raw["revenue"]
        net_income = raw["net_income"]
        gross_profit = raw["gross_profit"]
        ebitda = raw["ebitda"]
        debt = raw["total_debt"]
        equity = raw["equity"]

        missing_fields = [
            field for field, value in raw.items()
            if value is None
        ]

        record = {
            "period": period,
            "revenue": revenue,
            "net_income": net_income,
            "gross_profit": gross_profit,
            "ebitda": ebitda,
            "total_debt": debt,
            "equity": equity,

            "gross_margin": percentage(
                gross_profit, revenue
            ),

            "net_margin": percentage(
                net_income, revenue
            ),

            "ebitda_margin": percentage(
                ebitda, revenue
            ),

            "operating_cash_flow": raw["operating_cash_flow"],

            "debt_equity": (
                round(debt / equity, 2)
                if debt is not None
                and equity is not None
                and equity > 0
                else None
            ),

            "revenue_growth": None,
            "earnings_growth": None,
            "roe": None,
            "missing_fields": missing_fields,
        }

        # Compare with the previous financial year
        if records:
            previous = records[-1]

            if consecutive_years(previous["period"], period):

                record["revenue_growth"] = growth(
                    revenue,
                    previous["revenue"]
                )

                record["earnings_growth"] = growth(
                    net_income,
                    previous["net_income"]
                )

                previous_equity = previous["equity"]

                if (
                    equity is not None
                    and previous_equity is not None
                    and equity > 0
                    and previous_equity > 0
                ):
                    average_equity = (
                        equity + previous_equity
                    ) / 2

                    record["roe"] = percentage(
                        net_income,
                        average_equity
                    )

        records.append(record)

    trends = {
        "revenue": generate_trend(
            records, "revenue", "revenue"
        ),
        "earnings": generate_trend(
            records, "net_income", "net income"
        ),
        "debt": generate_trend(
            records, "total_debt", "total debt"
        ),
        "cash_flow": generate_trend(
            records, "operating_cash_flow",
            "operating cash flow"
        ),
    }

    return {
        "status": "ok" if len(records) >= 2 else "partial",
        "currency": financials.get("currency"),
        "period_count": len(records),
        "records": records,
        "trends": trends,
    }
