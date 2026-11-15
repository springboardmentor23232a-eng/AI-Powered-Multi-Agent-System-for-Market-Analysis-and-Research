
import yfinance as yf

from fastapi import APIRouter, HTTPException, Query
from yfinance import Search


router = APIRouter(
    prefix="/market-data",
    tags=["Market Data"]
)


# ==========================================
# HELPER: CONVERT TICKER BASED ON EXCHANGE
# ==========================================

def format_ticker(ticker: str, exchange: str):
    ticker = ticker.strip().upper()
    exchange = exchange.strip().upper()

    if exchange == "NSI":
        if ticker.startswith("^"):
            return ticker

        if not ticker.endswith(".NS"):
            ticker += ".NS"

    elif exchange == "BSE":
        if not ticker.endswith(".BO"):
            ticker += ".BO"

    elif exchange in ["NMS", "NASDAQ", "NYQ", "NYSE"]:
        pass

    else:
        raise ValueError("Unsupported stock exchange.")

    return ticker


# ==========================================
# GET CURRENT STOCK PRICE
# ==========================================

@router.get("/{ticker}")
def get_stock_price(
    ticker: str,
    exchange: str | None = None
):
    try:
        if exchange:
            ticker = format_ticker(ticker, exchange)
        else:
            ticker = ticker.strip().upper()

        stock = yf.Ticker(ticker)

        history = stock.history(
            period="5d",
            interval="1d"
        )

        if history.empty:
            raise HTTPException(
                status_code=404,
                detail="Stock price data is unavailable."
            )

        history = history.dropna(subset=["Close"])

        if history.empty:
            raise HTTPException(
                status_code=404,
                detail="No valid price data available."
            )

        latest_price = float(history["Close"].iloc[-1])

        previous_price = (
            float(history["Close"].iloc[-2])
            if len(history) >= 2 else None
        )

        percentage_change = None

        if previous_price is not None and previous_price != 0:
            percentage_change = (
                (latest_price - previous_price) / previous_price
            ) * 100

        company_name = ticker

        if not ticker.startswith("^"):
            company_name = stock.info.get("longName", ticker)

        return {
            "ticker": ticker,
            "company_name": company_name,
            "current_price": round(latest_price, 2),
            "previous_close": (
                round(previous_price, 2)
                if previous_price is not None else None
            ),
            "percentage_change": (
                round(percentage_change, 2)
                if percentage_change is not None else None
            )
        }

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch stock market data."
        )


# ==========================================
# GET HISTORICAL STOCK DATA
# ==========================================

@router.get("/{ticker}/history")
def get_stock_history(
    ticker: str,
    period: str = Query(
        default="1mo",
        pattern="^(1mo|3mo|6mo|1y|5y)$"
    ),
    exchange: str | None = None
):
    try:
        if exchange:
            ticker = format_ticker(ticker, exchange)
        else:
            ticker = ticker.strip().upper()

        stock = yf.Ticker(ticker)

        history = stock.history(
            period=period,
            interval="1d"
        )

        if history.empty:
            raise HTTPException(
                status_code=404,
                detail="Historical stock data is unavailable."
            )

        history = history.dropna(subset=["Close"])

        result = [
            {
                "date": date.strftime("%Y-%m-%d"),
                "price": round(float(row["Close"]), 2)
            }
            for date, row in history.iterrows()
        ]

        return {
            "ticker": ticker,
            "period": period,
            "history": result
        }

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch historical stock data."
        )


# ==========================================
# SEARCH COMPANIES
# ==========================================

@router.get("/search/company")
def search_company(
    q: str = Query(..., min_length=2)
):
    try:
        search = Search(q, max_results=10)

        results = []

        supported_exchanges = [
            "NSI",
            "BSE",
            "NMS",
            "NASDAQ",
            "NYQ"
        ]

        for item in search.quotes:

            if item.get("quoteType") != "EQUITY":
                continue

            if item.get("exchange") not in supported_exchanges:
                continue

            results.append({
                "ticker": item.get("symbol"),
                "company_name": (
                    item.get("longname")
                    or item.get("shortname")
                ),
                "exchange": item.get("exchange")
            })

        return {"results": results}

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to search for companies."
        )
