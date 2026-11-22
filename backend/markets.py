from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import get_current_user
from models import User

router = APIRouter(tags=["markets"])

# Regular trading sessions. Holidays are not included.
MARKETS = {
    "NSE": {
        "name": "National Stock Exchange of India",
        "country": "India",
        "currency": "INR",
        "timezone": "Asia/Kolkata",
        "open": time(9, 15),
        "close": time(15, 30),
        "ticker_example": "TCS.NS",
    },
    "BSE": {
        "name": "Bombay Stock Exchange",
        "country": "India",
        "currency": "INR",
        "timezone": "Asia/Kolkata",
        "open": time(9, 15),
        "close": time(15, 30),
        "ticker_example": "TCS.BO",
    },
    "NYSE": {
        "name": "New York Stock Exchange",
        "country": "United States",
        "currency": "USD",
        "timezone": "America/New_York",
        "open": time(9, 30),
        "close": time(16, 0),
        "ticker_example": "JPM",
    },
    "NASDAQ": {
        "name": "Nasdaq Stock Market",
        "country": "United States",
        "currency": "USD",
        "timezone": "America/New_York",
        "open": time(9, 30),
        "close": time(16, 0),
        "ticker_example": "AAPL",
    },
}


class MarketInfo(BaseModel):
    market: str
    name: str
    country: str
    currency: str
    timezone: str
    tz_label: str
    local_time: str
    hours: str
    ticker_example: str
    status: str  # "open" or "closed"
    reason: str
    next_open: str | None = None


def market_status(code: str, now_utc: datetime | None = None) -> dict:
    m = MARKETS[code]
    now = (now_utc or datetime.now(ZoneInfo("UTC"))).astimezone(ZoneInfo(m["timezone"]))
    is_weekday = now.weekday() < 5  # Monday to Friday

    opens_today = now.replace(hour=m["open"].hour, minute=m["open"].minute, second=0, microsecond=0)
    closes_today = now.replace(hour=m["close"].hour, minute=m["close"].minute, second=0, microsecond=0)

    if is_weekday and opens_today <= now < closes_today:
        state, reason = "open", "Regular trading session"
    elif is_weekday and now < opens_today:
        state, reason = "closed", "Opens later today"
    elif is_weekday:
        state, reason = "closed", "Closed for the day"
    else:
        state, reason = "closed", "Weekend"

    # Next opening time (skips weekends)
    if is_weekday and now < opens_today:
        next_open = opens_today
    else:
        next_open = opens_today + timedelta(days=1)
        while next_open.weekday() >= 5:
            next_open += timedelta(days=1)

    return {
        "market": code,
        "name": m["name"],
        "country": m["country"],
        "currency": m["currency"],
        "timezone": m["timezone"],
        "tz_label": now.tzname(),
        "local_time": now.strftime("%a %d %b %Y, %H:%M"),
        "hours": f"{m['open']:%H:%M} - {m['close']:%H:%M}",
        "ticker_example": m["ticker_example"],
        "status": state,
        "reason": reason,
        "next_open": next_open.strftime("%a %d %b, %H:%M") if state == "closed" else None,
    }


@router.get("/markets", response_model=list[MarketInfo])
def list_markets(current_user: User = Depends(get_current_user)):
    return [market_status(code) for code in MARKETS]