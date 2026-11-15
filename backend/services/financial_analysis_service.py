
from statistics import mean, stdev


def analyze_stock_data(stock_data: dict):
    """
    Calculate financial metrics from historical stock data.
    """

    historical_data = stock_data["historical_data"]

    if not historical_data:
        raise ValueError("Historical data is empty.")

    closing_prices = [
        item["close"] for item in historical_data
    ]

    daily_returns = []

    for i in range(1, len(closing_prices)):
        previous_price = closing_prices[i - 1]
        current_price = closing_prices[i]

        if previous_price != 0:
            daily_return = (
                (current_price - previous_price) / previous_price
            ) * 100

            daily_returns.append(daily_return)

    first_price = closing_prices[0]
    latest_price = closing_prices[-1]

    period_return = (
        (latest_price - first_price) / first_price
    ) * 100 if first_price != 0 else 0

    volatility = (
        stdev(daily_returns)
        if len(daily_returns) >= 2
        else 0
    )

    # Calculate Simple Moving Averages
    sma_20 = (
        mean(closing_prices[-20:])
        if len(closing_prices) >= 20
        else None
    )

    sma_50 = (
        mean(closing_prices[-50:])
        if len(closing_prices) >= 50
        else None
    )

    # Identify stock trend
    if sma_20 is None or sma_50 is None:
        trend = "Insufficient Data"

    elif sma_20 > sma_50:
        trend = "Bullish"

    elif sma_20 < sma_50:
        trend = "Bearish"

    else:
        trend = "Neutral"

    # Classify stock risk based on daily return volatility
    if volatility < 1:
        risk_level = "Low"

    elif volatility <= 3:
        risk_level = "Medium"

    else:
        risk_level = "High"

    # Generate a rule-based analytical signal
    if sma_20 is None or sma_50 is None:
        signal = "Insufficient Data"

    elif sma_20 > sma_50 and risk_level != "High":
        signal = "Buy"

    elif sma_20 < sma_50 and risk_level == "High":
        signal = "Sell"

    else:
        signal = "Hold"

    return {
        "ticker": stock_data["ticker"],
        "company_name": stock_data["company_name"],
        "currency": stock_data["currency"],
        "current_price": stock_data["current_price"],
        "period_return": round(period_return, 2),
        "average_price": round(mean(closing_prices), 2),
        "highest_price": round(max(closing_prices), 2),
        "lowest_price": round(min(closing_prices), 2),
        "volatility": round(volatility, 2),
        "sma_20": round(sma_20, 2) if sma_20 is not None else None,
        "sma_50": round(sma_50, 2) if sma_50 is not None else None,
        "trend": trend,
        "risk_level": risk_level,
        "signal": signal,
        "average_volume": round(
            mean(item["volume"] for item in historical_data)
        ),
        "total_records": len(historical_data)
    }


def generate_research_report(analysis: dict):
    """
    Generate a readable stock research report.
    """

    currency = analysis["currency"] or ""

    report = f"""
STOCK RESEARCH REPORT
=====================

Company: {analysis["company_name"]}
Ticker: {analysis["ticker"]}
Currency: {currency}

1. CURRENT MARKET OVERVIEW
--------------------------
Current Price: {currency} {analysis["current_price"]}
Period Return: {analysis["period_return"]}%

2. PRICE ANALYSIS
-----------------
Average Closing Price: {currency} {analysis["average_price"]}
Highest Closing Price: {currency} {analysis["highest_price"]}
Lowest Closing Price: {currency} {analysis["lowest_price"]}

SMA 20 (Short-term): {currency} {analysis["sma_20"]}
SMA 50 (Medium-term): {currency} {analysis["sma_50"]}
Trend Classification: {analysis["trend"]}

3. TRADING ACTIVITY
-------------------
Average Trading Volume: {analysis["average_volume"]}

4. RISK ANALYSIS
----------------
Daily Return Volatility: {analysis["volatility"]}%
Risk Classification: {analysis["risk_level"]}
Analytical Signal: {analysis["signal"]}

5. DATA SUMMARY
---------------
Historical Records Analyzed: {analysis["total_records"]}

6. RESEARCH SUMMARY
-------------------
The stock recorded a period return of {analysis["period_return"]}%.
Its daily return volatility was {analysis["volatility"]}%.
The analysis is based on {analysis["total_records"]} historical trading records.

Note: This report is based on historical market data and
statistical calculations. It is not a guaranteed prediction
or personalized investment recommendation.
"""

    return report.strip()
