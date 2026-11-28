
import math
import yfinance as yf


def valid_number(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError, OverflowError):
        return None


def get_statement_value(statement, names, index=0):
    for name in names:
        for row in statement.get("rows", []):
            if row["item"] == name:
                values = row.get("values", [])

                if len(values) > index:
                    value = valid_number(values[index])

                    if value is not None:
                        return value

    return None


def calculate_financial_ratios(ticker, financials):

    ratios = {
        "pe_ratio": None,
        "pb_ratio": None,
        "roe": None,
    }

    reasons = {}

    # Retrieve market valuation data
    try:
        info = yf.Ticker(ticker).info or {}
    except Exception:
        info = {}

    price = valid_number(info.get("currentPrice"))

    if price is None:
        price = valid_number(info.get("regularMarketPrice"))

    eps = valid_number(info.get("trailingEps"))
    book_value = valid_number(info.get("bookValue"))

    currency = info.get("currency")
    financial_currency = info.get("financialCurrency")

    # Price-to-Earnings ratio
    if price is None or price <= 0:
        reasons["pe_ratio"] = "Valid share price is unavailable."

    elif eps is None:
        reasons["pe_ratio"] = "Trailing earnings per share is unavailable."

    elif eps <= 0:
        reasons["pe_ratio"] = "P/E is not meaningful for non-positive earnings."

    elif not currency or currency != financial_currency:
        reasons["pe_ratio"] = "Currency compatibility could not be confirmed."

    else:
        ratios["pe_ratio"] = round(price / eps, 2)

    # Price-to-Book ratio
    if price is None or price <= 0:
        reasons["pb_ratio"] = "Valid share price is unavailable."

    elif book_value is None:
        reasons["pb_ratio"] = "Book value per share is unavailable."

    elif book_value <= 0:
        reasons["pb_ratio"] = "P/B is not meaningful for non-positive book value."

    elif not currency or currency != financial_currency:
        reasons["pb_ratio"] = "Currency compatibility could not be confirmed."

    else:
        ratios["pb_ratio"] = round(price / book_value, 2)

    # Return on Equity
    income = financials.get("income_statement") or {}
    balance = financials.get("balance_sheet") or {}

    net_income = get_statement_value(
        income,
        ["Net Income", "Net Income Common Stockholders"]
    )

    equity_names = [
        "Stockholders Equity",
        "Common Stock Equity"
    ]

    current_equity = get_statement_value(
        balance, equity_names, 0
    )

    previous_equity = get_statement_value(
        balance, equity_names, 1
    )

    income_periods = income.get("periods", [])
    balance_periods = balance.get("periods", [])

    if net_income is None:
        reasons["roe"] = "Annual net income is unavailable."

    elif current_equity is None or previous_equity is None:
        reasons["roe"] = "Current or previous shareholders' equity is unavailable."

    elif (
        not income_periods
        or len(balance_periods) < 2
        or income_periods[0] != balance_periods[0]
    ):
        reasons["roe"] = "Financial statement periods do not match."

    elif current_equity <= 0 or previous_equity <= 0:
        reasons["roe"] = "ROE may be misleading with non-positive equity."

    else:
        average_equity = (current_equity + previous_equity) / 2

        ratios["roe"] = round(
            (net_income / average_equity) * 100, 2
        )

    return {
        "ratios": ratios,
        "ratio_reasons": reasons,
    }
