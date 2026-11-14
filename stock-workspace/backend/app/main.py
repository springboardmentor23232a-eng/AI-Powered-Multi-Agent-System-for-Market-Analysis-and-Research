from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import schemas, stocks
from .config import COOKIE_NAME, COOKIE_SECURE, CORS_ORIGINS, JWT_EXPIRE_MINUTES, MARKETS
from .database import Base, engine, get_db
from .models import ResearchTask, SavedStock, User
from .reports import run_research
from .security import create_token, current_user, hash_password, verify_password

Base.metadata.create_all(engine)

app = FastAPI(title="Multi-Agent Stock Research Analyst - Module 1")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


# ---------- Auth ----------
@app.post("/api/auth/register", status_code=201)
def register(data: schemas.RegisterIn, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "This email is already registered")
    db.add(User(full_name=data.full_name, email=email, password_hash=hash_password(data.password)))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "This email is already registered")
    return {"message": "Registration successful. You can now sign in."}


@app.post("/api/auth/login", response_model=schemas.UserOut)
def login(data: schemas.LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not verify_password(data.password, user.password_hash if user else None):
        raise HTTPException(401, "Incorrect email or password")
    response.set_cookie(COOKIE_NAME, create_token(user.user_id), httponly=True, secure=COOKIE_SECURE,
                        samesite="lax", max_age=JWT_EXPIRE_MINUTES * 60, path="/")
    return user


@app.post("/api/auth/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")


@app.get("/api/auth/me", response_model=schemas.UserOut)
def me(user: User = Depends(current_user)):
    return user


# ---------- Preferences ----------
@app.put("/api/preferences", response_model=schemas.UserOut)
def save_preferences(data: schemas.PreferencesIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    user.market, user.analysis_period = data.market, data.analysis_period
    db.commit()
    return user


# ---------- Stock search ----------
@app.get("/api/stocks/search")
def search_stocks(q: str = Query("", max_length=50), market: str = Query("NSE"), user: User = Depends(current_user)):
    if market not in MARKETS:
        raise HTTPException(422, "Unsupported market")
    return stocks.search(q, market)


# ---------- Watchlist ----------
@app.get("/api/watchlist", response_model=list[schemas.SavedOut])
def get_watchlist(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.scalars(select(SavedStock).where(SavedStock.user_id == user.user_id)
                      .order_by(SavedStock.created_at.desc())).all()


@app.post("/api/watchlist", response_model=schemas.SavedOut, status_code=201)
def add_watch(data: schemas.WatchIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    ticker = data.ticker.strip().upper()
    name = stocks.lookup(ticker, data.market)
    if not name:
        raise HTTPException(404, f"{ticker} is not a supported {data.market} symbol")
    if db.scalar(select(SavedStock).where(SavedStock.user_id == user.user_id, SavedStock.ticker == ticker)):
        raise HTTPException(409, f"{ticker} is already in your watchlist")
    item = SavedStock(user_id=user.user_id, ticker=ticker, company_name=name, market=data.market)
    db.add(item)
    db.commit()
    return item


@app.delete("/api/watchlist/{saved_stock_id}", status_code=204)
def remove_watch(saved_stock_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(SavedStock).where(SavedStock.saved_stock_id == saved_stock_id,
                                              SavedStock.user_id == user.user_id))
    if not item:
        raise HTTPException(404, "Saved stock not found")
    db.delete(item)
    db.commit()


# ---------- Research history ----------
@app.get("/api/research", response_model=list[schemas.TaskOut])
def list_research(user: User = Depends(current_user), db: Session = Depends(get_db)):
    # Identity comes from the verified JWT, never from a client-supplied user_id.
    return db.scalars(select(ResearchTask).where(ResearchTask.user_id == user.user_id)
                      .order_by(ResearchTask.created_at.desc())).all()


@app.post("/api/research", response_model=schemas.TaskOut, status_code=202)
def start_research(data: schemas.ResearchIn, bg: BackgroundTasks, user: User = Depends(current_user),
                   db: Session = Depends(get_db)):
    market = data.market or user.market
    period = data.analysis_period or user.analysis_period
    ticker = data.ticker.strip().upper()
    name = stocks.lookup(ticker, market)
    if not name:
        raise HTTPException(404, f"{ticker} is not a supported {market} symbol")
    task = ResearchTask(user_id=user.user_id, ticker=ticker, company_name=name, market=market,
                        analysis_period=period, status="Pending")
    db.add(task)
    db.commit()
    bg.add_task(run_research, task.task_id)
    return task


@app.get("/api/research/{task_id}", response_model=schemas.TaskDetail)
def get_research(task_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    task = db.scalar(select(ResearchTask).where(ResearchTask.task_id == task_id, ResearchTask.user_id == user.user_id))
    if not task:
        raise HTTPException(404, "Research task not found")
    return task
