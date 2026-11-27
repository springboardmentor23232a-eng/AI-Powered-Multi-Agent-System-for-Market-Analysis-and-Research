from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .database import Base, engine, get_db
from .models import User, Preference, WatchlistItem, ResearchRequest, MarketBar
from .security import hash_password, verify_password, create_token, current_user
from .market_data import search_stocks, fetch_history, fetch_profile, fetch_financials, MarketDataError

@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Multi-Agent Stock Research Analyst API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = ""
class LoginIn(BaseModel):
    email: EmailStr
    password: str
class PreferenceIn(BaseModel):
    market: str
    period: str
class WatchIn(BaseModel):
    symbol: str
    name: str = ""
    market: str

def user_dict(u):
    return {"id": u.id, "email": u.email, "full_name": u.full_name}

def fail_market(exc):
    raise HTTPException(status_code=502, detail=str(exc))

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/auth/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == data.email.lower())):
        raise HTTPException(409, "An account with this email already exists")
    u = User(email=data.email.lower(), full_name=data.full_name, password_hash=hash_password(data.password))
    db.add(u); db.flush(); db.add(Preference(user_id=u.id)); db.commit()
    return {"access_token": create_token(u.id), "token_type": "bearer", "user": user_dict(u)}

@app.post("/api/auth/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    u = db.scalar(select(User).where(User.email == data.email.lower()))
    if not u or not verify_password(data.password, u.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return {"access_token": create_token(u.id), "token_type": "bearer", "user": user_dict(u)}

@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return user_dict(user)

@app.get("/api/preferences")
def get_preferences(db: Session = Depends(get_db), user: User = Depends(current_user)):
    p = db.scalar(select(Preference).where(Preference.user_id == user.id))
    if not p:
        p = Preference(user_id=user.id); db.add(p); db.commit(); db.refresh(p)
    return {"market": p.market, "period": p.period}

@app.put("/api/preferences")
def put_preferences(data: PreferenceIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if data.market not in {"NSE","BSE","NASDAQ","NYSE"} or data.period not in {"1mo","3mo","6mo","1y","5y"}:
        raise HTTPException(422, "Invalid market or analysis period")
    p = db.scalar(select(Preference).where(Preference.user_id == user.id))
    if not p: p = Preference(user_id=user.id); db.add(p)
    p.market, p.period = data.market, data.period
    db.commit()
    return {"market": p.market, "period": p.period}

@app.get("/api/watchlist")
def get_watchlist(db: Session = Depends(get_db), user: User = Depends(current_user)):
    items = db.scalars(select(WatchlistItem).where(WatchlistItem.user_id == user.id).order_by(WatchlistItem.added_at.desc())).all()
    return [{"id": x.id, "symbol": x.symbol, "name": x.name, "market": x.market, "added_at": x.added_at.isoformat()} for x in items]

@app.post("/api/watchlist")
def add_watch(data: WatchIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = WatchlistItem(user_id=user.id, symbol=data.symbol.upper(), name=data.name, market=data.market.upper())
    db.add(item)
    try: db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(409, "This stock is already in your watchlist")
    db.refresh(item)
    return {"id": item.id, "symbol": item.symbol, "name": item.name, "market": item.market}

@app.delete("/api/watchlist/{stock_id}")
def delete_watch(stock_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = db.scalar(select(WatchlistItem).where(WatchlistItem.id == stock_id, WatchlistItem.user_id == user.id))
    if not item: raise HTTPException(404, "Watchlist item not found")
    db.delete(item); db.commit(); return {"deleted": True}

@app.get("/api/research/history")
def research_history(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.scalars(select(ResearchRequest).where(ResearchRequest.user_id == user.id).order_by(ResearchRequest.created_at.desc())).all()
    return [{"id": x.id, "symbol": x.symbol, "name": x.name, "market": x.market, "period": x.period,
             "status": x.status, "created_at": x.created_at.isoformat(), "report": x.report} for x in rows]

@app.post("/api/research")
def create_research(data: WatchIn, period: str = Query("3mo"), db: Session = Depends(get_db), user: User = Depends(current_user)):
    if period not in {"1mo","3mo","6mo","1y","5y"}: raise HTTPException(422, "Invalid period")
    # This records a request only. AI-agent analysis is intentionally not implemented in this milestone.
    task = ResearchRequest(user_id=user.id, symbol=data.symbol.upper(), name=data.name, market=data.market.upper(), period=period, status="Pending")
    db.add(task); db.commit(); db.refresh(task)
    return {"id": task.id, "status": task.status, "message": "Research request recorded; AI analysis is not enabled in this milestone."}

@app.get("/api/stocks/search")
def stock_search(q: str = Query(min_length=1), market: str = "NSE", user: User = Depends(current_user)):
    try: return {"results": search_stocks(q, market)}
    except MarketDataError as exc: fail_market(exc)

@app.get("/api/stocks/{symbol}/history")
def stock_history(symbol: str, market: str = "NSE", period: str = "3mo", db: Session = Depends(get_db), user: User = Depends(current_user)):
    try:
        result = fetch_history(symbol, market, period)
        # Persist the returned market data in PostgreSQL; Yahoo Finance is the upstream provider, not the database.
        for bar in result["data"]:
            dt = datetime.fromisoformat(bar["date"])
            exists = db.scalar(select(MarketBar).where(MarketBar.symbol == result["symbol"], MarketBar.market == market, MarketBar.date == dt))
            if not exists:
                db.add(MarketBar(symbol=result["symbol"], market=market, date=dt, open=bar["open"], high=bar["high"],
                                 low=bar["low"], close=bar["close"], volume=bar["volume"]))
        db.commit()
        return result
    except MarketDataError as exc: fail_market(exc)

@app.get("/api/stocks/{symbol}/profile")
def stock_profile(symbol: str, market: str = "NSE", user: User = Depends(current_user)):
    try: return fetch_profile(symbol, market)
    except Exception as exc: fail_market(exc)

@app.get("/api/stocks/{symbol}/financials")
def stock_financials(symbol: str, market: str = "NSE", user: User = Depends(current_user)):
    try: return fetch_financials(symbol, market)
    except Exception as exc: fail_market(exc)

@app.get("/api/market-data/audit")
def audit(user: User = Depends(current_user)):
    return {"provider": "Yahoo Finance via yfinance", "database": "PostgreSQL",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "note": "Audit metadata for provider and retrieval. No live market values are synthesized."}
