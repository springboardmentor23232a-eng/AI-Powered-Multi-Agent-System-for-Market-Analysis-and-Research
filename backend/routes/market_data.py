
import yfinance as yf
import pandas as pd

from fastapi import APIRouter, HTTPException, Query
from yfinance import Search
from datetime import datetime, timezone

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
# GET HISTORICAL OHLCV DATA
# ==========================================

@router.get("/{ticker}/ohlcv")
def get_stock_ohlcv(
    ticker: str,
    period: str = Query(
        default="1y",
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
            interval="1d",
            auto_adjust=False
        )

        if history.empty:
            raise HTTPException(
                status_code=404,
                detail="OHLCV data is unavailable."
            )

        columns = ["Open", "High", "Low", "Close", "Volume"]

        # Keep all five OHLCV fields and remove missing values
        ohlcv = history[columns].dropna().copy()

        # Remove duplicate dates
        ohlcv = ohlcv[
            ~ohlcv.index.duplicated(keep="last")
        ]

        # Validate price relationships
        invalid_prices = (
            (ohlcv["High"] < ohlcv["Low"]) |
            (ohlcv["High"] < ohlcv[["Open", "Close"]].max(axis=1)) |
            (ohlcv["Low"] > ohlcv[["Open", "Close"]].min(axis=1))
        )

        # Remove records with invalid prices
        ohlcv = ohlcv[~invalid_prices]

        # Remove records with negative volume
        ohlcv = ohlcv[ohlcv["Volume"] >= 0]

        if ohlcv.empty:
            raise HTTPException(
                status_code=404,
                detail="No valid OHLCV records available."
            )

        result = []

        for date, row in ohlcv.iterrows():
            result.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"])
            })

        return {
    "ticker": ticker,
    "period": period,
    "data_source": "Yahoo Finance (via yfinance)",
    "retrieved_at": datetime.now(timezone.utc).isoformat(),
    "total_records": len(result),
    "ohlcv_data": result
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
            detail="Unable to fetch OHLCV data."
        )


# ==========================================
# GET COMPANY PROFILE
# ==========================================

@router.get("/{ticker}/profile")
def get_company_profile(
    ticker: str,
    exchange: str | None = None
):
    try:
        if exchange:
            ticker = format_ticker(ticker, exchange)
        else:
            ticker = ticker.strip().upper()

        stock = yf.Ticker(ticker)

        info = stock.info

        if not info or not info.get("longName"):
            raise HTTPException(
                status_code=404,
                detail="Company profile is unavailable."
            )

        profile_fields = {
            "company_name": "longName",
            "sector": "sector",
            "industry": "industry",
            "website": "website",
            "country": "country",
            "city": "city",
            "exchange": "exchange",
            "currency": "currency",
            "market_cap": "marketCap",
            "employees": "fullTimeEmployees",
            "business_description": "longBusinessSummary"
        }

        profile = {
            key: info.get(value)
            for key, value in profile_fields.items()
            if info.get(value) is not None
        }

        return {
            "ticker": ticker,
            "data_source": "Yahoo Finance (via yfinance)",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "profile": profile
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch company profile."
        )



# ==========================================
# GET COMPANY FINANCIAL STATEMENTS
# ==========================================

@router.get("/{ticker}/financials")
def get_company_financials(
    ticker: str,
    frequency: str = Query(
        default="annual",
        pattern="^(annual|quarterly)$"
    ),
    exchange: str | None = None
):
    try:
        if exchange:
            ticker = format_ticker(ticker, exchange)
        else:
            ticker = ticker.strip().upper()

        stock = yf.Ticker(ticker)

        # Select annual or quarterly statements
        if frequency == "annual":
            income_statement = stock.financials
            balance_sheet = stock.balance_sheet
            cash_flow = stock.cashflow
        else:
            income_statement = stock.quarterly_financials
            balance_sheet = stock.quarterly_balance_sheet
            cash_flow = stock.quarterly_cashflow

        # Convert DataFrame into JSON-friendly records
        def format_statement(statement):

            if statement is None or statement.empty:
                return []

            records = []

            for period in statement.columns:

                line_items = {}

                for item, value in statement[period].items():

                    if pd.isna(value):
                        line_items[str(item)] = None
                    else:
                        line_items[str(item)] = float(value)

                records.append({
                    "period": period.strftime("%Y-%m-%d"),
                    "line_items": line_items
                })

            return records

        return {
            "ticker": ticker,
            "frequency": frequency,
            "data_source": "Yahoo Finance (via yfinance)",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),

            "financial_statements": {
                "income_statement": format_statement(
                    income_statement
                ),
                "balance_sheet": format_statement(
                    balance_sheet
                ),
                "cash_flow_statement": format_statement(
                    cash_flow
                )
            }
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch company financial statements."
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
