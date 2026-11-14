import yfinance as yf
from fastapi import APIRouter, Query, HTTPException, status
from typing import List
from app.schemas import StockSearchResponse, StockSearchResult

router = APIRouter(prefix="/api/stocks", tags=["Stock Search"])

# Curated reference cache of verified tickers across NSE, BSE, NASDAQ, NYSE
VERIFIED_TICKERS = [
    {
        "ticker": "TCS.NS",
        "name": "Tata Consultancy Services Limited",
        "market": "NSE",
        "exchange": "NSE (India)",
        "currency": "INR",
        "currency_symbol": "₹",
        "is_us_market": False,
    },
    {
        "ticker": "INFY.NS",
        "name": "Infosys Limited",
        "market": "NSE",
        "exchange": "NSE (India)",
        "currency": "INR",
        "currency_symbol": "₹",
        "is_us_market": False,
    },
    {
        "ticker": "RELIANCE.NS",
        "name": "Reliance Industries Limited",
        "market": "NSE",
        "exchange": "NSE (India)",
        "currency": "INR",
        "currency_symbol": "₹",
        "is_us_market": False,
    },
    {
        "ticker": "HDFCBANK.NS",
        "name": "HDFC Bank Limited",
        "market": "NSE",
        "exchange": "NSE (India)",
        "currency": "INR",
        "currency_symbol": "₹",
        "is_us_market": False,
    },
    {
        "ticker": "AAPL",
        "name": "Apple Inc.",
        "market": "NASDAQ",
        "exchange": "NASDAQ (US)",
        "currency": "USD",
        "currency_symbol": "$",
        "is_us_market": True,
    },
    {
        "ticker": "MSFT",
        "name": "Microsoft Corporation",
        "market": "NASDAQ",
        "exchange": "NASDAQ (US)",
        "currency": "USD",
        "currency_symbol": "$",
        "is_us_market": True,
    },
    {
        "ticker": "TSLA",
        "name": "Tesla, Inc.",
        "market": "NASDAQ",
        "exchange": "NASDAQ (US)",
        "currency": "USD",
        "currency_symbol": "$",
        "is_us_market": True,
    },
    {
        "ticker": "NVDA",
        "name": "NVIDIA Corporation",
        "market": "NASDAQ",
        "exchange": "NASDAQ (US)",
        "currency": "USD",
        "currency_symbol": "$",
        "is_us_market": True,
    },
    {
        "ticker": "GOOGL",
        "name": "Alphabet Inc.",
        "market": "NASDAQ",
        "exchange": "NASDAQ (US)",
        "currency": "USD",
        "currency_symbol": "$",
        "is_us_market": True,
    },
    {
        "ticker": "AMZN",
        "name": "Amazon.com Inc.",
        "market": "NASDAQ",
        "exchange": "NASDAQ (US)",
        "currency": "USD",
        "currency_symbol": "$",
        "is_us_market": True,
    },
]


def resolve_market_and_currency(ticker_symbol: str, raw_exchange: str = ""):
    """Classifies exchange, currency, and US market status for yfinance tickers."""
    sym = ticker_symbol.upper()
    ex = raw_exchange.upper()

    if sym.endswith(".NS") or "NSI" in ex or "NSE" in ex:
        return "NSE", "NSE (India)", "INR", "₹", False
    elif sym.endswith(".BO") or "BSE" in ex:
        return "BSE", "BSE (India)", "INR", "₹", False
    elif "NYQ" in ex or "NYSE" in ex:
        return "NYSE", "NYSE (US)", "USD", "$", True
    elif "NMS" in ex or "NGM" in ex or "NCM" in ex or "NASDAQ" in ex:
        return "NASDAQ", "NASDAQ (US)", "USD", "$", True
    else:
        # Default fallback: if single token ticker without dot, assume US Market
        if "." not in sym:
            return "NASDAQ", "US Exchange", "USD", "$", True
        return "Global", "International", "USD", "$", True


@router.get("/search", response_model=StockSearchResponse)
def search_stocks(q: str = Query(..., min_length=1, max_length=50, description="Company name or ticker")):
    """
    Searches stocks powered by yfinance live dataset.
    Validates company symbols, retrieves real-time pricing, currency, and flags US market equities.
    """
    search_term = q.strip().upper()
    if not search_term:
        return StockSearchResponse(query=q, count=0, results=[])

    matched_results: List[StockSearchResult] = []
    seen_tickers = set()

    # 1. Fast lookup from verified reference list
    for item in VERIFIED_TICKERS:
        t_clean = item["ticker"].split(".")[0]
        if (search_term in item["ticker"]) or (search_term in t_clean) or (search_term in item["name"].upper()):
            try:
                # Fetch fast real-time price from yfinance
                yf_ticker = yf.Ticker(item["ticker"])
                fast_price = yf_ticker.fast_info.get("lastPrice")
                prev_close = yf_ticker.fast_info.get("previousClose")
                change_pct = None
                if fast_price and prev_close:
                    change_pct = round(((fast_price - prev_close) / prev_close) * 100, 2)
            except Exception:
                fast_price = None
                change_pct = None

            res = StockSearchResult(
                ticker=item["ticker"],
                name=item["name"],
                market=item["market"],
                exchange=item["exchange"],
                currency=item["currency"],
                currency_symbol=item["currency_symbol"],
                current_price=round(fast_price, 2) if fast_price else None,
                change_percent=change_pct,
                is_us_market=item["is_us_market"],
            )
            matched_results.append(res)
            seen_tickers.add(item["ticker"])

    # 2. Dynamic live search via yfinance API
    try:
        yf_search = yf.Search(q.strip(), max_results=6)
        if hasattr(yf_search, "quotes") and yf_search.quotes:
            for quote in yf_search.quotes:
                sym = quote.get("symbol")
                if not sym or sym in seen_tickers:
                    continue

                quote_type = quote.get("quoteType", "")
                if quote_type not in ["EQUITY", "ETF", ""]:
                    continue

                short_name = quote.get("shortname") or quote.get("longname") or f"{sym} Equity"
                raw_ex = quote.get("exchange", "")
                market, exchange, currency, curr_sym, is_us = resolve_market_and_currency(sym, raw_ex)

                # Fetch real-time price
                try:
                    t_obj = yf.Ticker(sym)
                    price = t_obj.fast_info.get("lastPrice")
                    p_close = t_obj.fast_info.get("previousClose")
                    chg = None
                    if price and p_close:
                        chg = round(((price - p_close) / p_close) * 100, 2)
                except Exception:
                    price = None
                    chg = None

                matched_results.append(StockSearchResult(
                    ticker=sym,
                    name=short_name,
                    market=market,
                    exchange=exchange,
                    currency=currency,
                    currency_symbol=curr_sym,
                    current_price=round(price, 2) if price else None,
                    change_percent=chg,
                    is_us_market=is_us,
                ))
                seen_tickers.add(sym)
    except Exception as e:
        # Graceful fallback if external search encounters network or rate limits
        pass

    # 3. Direct ticker fallback: if user typed a specific ticker like 'AAPL' or 'TCS'
    if not matched_results and len(search_term) <= 10:
        for candidate_ticker in [search_term, f"{search_term}.NS"]:
            try:
                candidate = yf.Ticker(candidate_ticker)
                fast_p = candidate.fast_info.get("lastPrice")
                if fast_p:
                    short_n = candidate.info.get("shortName") or f"{candidate_ticker} Equity"
                    market, exchange, currency, curr_sym, is_us = resolve_market_and_currency(candidate_ticker)
                    matched_results.append(StockSearchResult(
                        ticker=candidate_ticker,
                        name=short_n,
                        market=market,
                        exchange=exchange,
                        currency=currency,
                        currency_symbol=curr_sym,
                        current_price=round(fast_p, 2),
                        change_percent=None,
                        is_us_market=is_us,
                    ))
                    break
            except Exception:
                continue

    return StockSearchResponse(
        query=q,
        count=len(matched_results),
        results=matched_results
    )
