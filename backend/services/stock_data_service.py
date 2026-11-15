
import yfinance as yf


def collect_stock_data(ticker: str, market: str, period: str):
    """
    Collect historical stock market data for research.
    """

    ticker = ticker.strip().upper()
    market = market.strip().upper()
    period = period.strip().lower()

    # Validate supported analysis periods
    allowed_periods = {"1mo", "3mo", "6mo", "1y", "5y"}

    if period not in allowed_periods:
        raise ValueError("Unsupported analysis period.")

    # Handle different stock exchanges
    if market == "NSI":
        if not ticker.endswith(".NS"):
            ticker += ".NS"

    elif market == "BSE":
        if not ticker.endswith(".BO"):
            ticker += ".BO"

    elif market in ["NMS", "NASDAQ", "NYQ", "NYSE"]:
        # US stocks do not require an exchange suffix
        pass

    else:
        raise ValueError("Unsupported stock exchange.")

    # Fetch stock data
    stock = yf.Ticker(ticker)

    history = stock.history(
        period=period,
        interval="1d"
    )

    if history.empty:
        raise ValueError("No historical stock data available.")

    history = history.dropna(subset=["Close"])

    if history.empty:
        raise ValueError("No valid closing prices available.")

    # Collect stock information
    stock_info = stock.info

    latest_price = float(history["Close"].iloc[-1])

    previous_close = (
        float(history["Close"].iloc[-2])
        if len(history) >= 2 else None
    )

    percentage_change = None

    if previous_close is not None and previous_close != 0:
        percentage_change = (
            (latest_price - previous_close) / previous_close
        ) * 100

    return {
        "ticker": ticker,
        "company_name": stock_info.get("longName", ticker),
        "currency": stock_info.get("currency"),
        "current_price": round(latest_price, 2),
        "previous_close": (
            round(previous_close, 2)
            if previous_close is not None else None
        ),
        "percentage_change": (
            round(percentage_change, 2)
            if percentage_change is not None else None
        ),
        "historical_data": [
            {
                "date": date.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"])
            }
            for date, row in history.iterrows()
        ]
    }
