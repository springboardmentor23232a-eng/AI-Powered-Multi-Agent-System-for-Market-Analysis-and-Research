import yfinance as yf
from fastapi import APIRouter, Depends, HTTPException, Query
from ..deps import get_current_user
from ..models import User
from ..services.tickers import EXCHANGE_TO_MARKET

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/search")
def search_stocks(q: str = Query(min_length=1, max_length=50),
                  user: User = Depends(get_current_user)):
    try:
        quotes = yf.Search(q, max_results=15).quotes
    except Exception:
        raise HTTPException(502, "Stock search service unavailable. Please try again.")
    results = []
    for x in quotes:
        market = EXCHANGE_TO_MARKET.get(x.get("exchange"))
        if x.get("quoteType") != "EQUITY" or not market:
            continue
        results.append({
            "ticker": x["symbol"],
            "company_name": x.get("longname") or x.get("shortname"),
            "market": market,
        })
    return results