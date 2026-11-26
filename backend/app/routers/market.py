from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from ..deps import get_current_user
from ..models import User
from ..schemas import Market, Period, _clean_ticker
from ..services.tickers import normalize_ticker
from ..services import market_data as md
from ..agents import fundamental as fundamental_agent

router = APIRouter(prefix="/market", tags=["market"])


def _resolve(ticker: str, market: str) -> str:
    try:
        return normalize_ticker(_clean_ticker(ticker), market)
    except ValueError:
        raise HTTPException(422, "Invalid ticker format.")


def _call(fn, *args):
    try:
        return fn(*args)
    except md.DataUnavailable as e:
        raise HTTPException(404, str(e))
    except md.ProviderError as e:
        raise HTTPException(502, str(e))


@router.get("/{ticker}/history")
def history(ticker: str, market: Market = Query("NSE"), period: Period = Query("1y"),
            user: User = Depends(get_current_user)):
    t = _resolve(ticker, market)
    res = _call(md.get_history, t, period)
    rows = md.df_to_records(res.df)
    return {"ticker": t, "market": market, "period": period, "meta": res.meta,
            "validation": res.validation, "count": len(rows), "rows": rows}


@router.get("/{ticker}/quote")
def quote(ticker: str, market: Market = Query("NSE"), user: User = Depends(get_current_user)):
    t = _resolve(ticker, market)
    res = _call(md.get_history, t, "1y")          # 52-week range ke liye 1 saal
    try:
        prof = md.get_profile(t)["profile"]       # profile na mile to bhi quote chalega
    except md.MarketDataError:
        prof = None
    return md.build_quote(t, market, res, prof)


@router.get("/{ticker}/profile")
def profile(ticker: str, market: Market = Query("NSE"), user: User = Depends(get_current_user)):
    return _call(md.get_profile, _resolve(ticker, market))


@router.get("/{ticker}/financials")
def financials(ticker: str, market: Market = Query("NSE"), user: User = Depends(get_current_user)):
    return _call(md.get_financials, _resolve(ticker, market))


@router.get("/{ticker}/statements")
def statements(ticker: str, market: Market = Query("NSE"),
               frequency: Literal["annual", "quarterly"] = Query("annual"),
               user: User = Depends(get_current_user)):
    return _call(md.get_statements, _resolve(ticker, market), frequency)


@router.get("/{ticker}/fundamental")
def fundamental(ticker: str, market: Market = Query("NSE"),
                peers: str = Query("", max_length=200),
                user: User = Depends(get_current_user)):
    t = _resolve(ticker, market)
    peer_list, invalid = [], []
    for p in [x.strip() for x in peers.split(",") if x.strip()][:8]:
        try:
            peer_list.append(_resolve(p, market))
        except HTTPException:
            invalid.append(p)
    result = _call(fundamental_agent.analyze, t, market, peer_list)
    return {**result, "peers_invalid": invalid}
