from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import yfinance as yf
import models, schemas, auth
from database import engine, get_db
models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="Multi-Agent Stock Research Analyst API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def format_yf_ticker(ticker: str, market: str) -> str:
    clean = ticker.strip().upper()
    if market == "NSE" and not clean.endswith(".NS"):
        return f"{clean}.NS"
    if market == "BSE" and not clean.endswith(".BO"):
        return f"{clean}.BO"
    return clean
PERIOD_MAP = {
    "1 Month": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year": "1y",
    "5 Years": "5y",
}
@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = models.User(
        full_name=user.full_name,
        email=user.email,
        password_hash=auth.hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )  
    access_token = auth.create_access_token(data={"sub": str(user.user_id)})
    return {"access_token": access_token, "token_type": "bearer"}
@app.get("/users/me", response_model=schemas.UserResponse)
def get_my_profile(current_user: models.User = Depends(auth.get_current_user)):
    return current_user
@app.get("/users/preferences", response_model=schemas.UserPreferencesResponse)
def get_preferences(current_user: models.User = Depends(auth.get_current_user)):
    return current_user
@app.put("/users/preferences", response_model=schemas.UserPreferencesResponse)
def update_preferences(
    prefs: schemas.UserPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    current_user.preferred_market = prefs.preferred_market
    current_user.preferred_period = prefs.preferred_period
    db.commit()
    db.refresh(current_user)
    return current_user
@app.get("/stocks/", response_model=List[schemas.SavedStockResponse])
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return db.query(models.SavedStock).filter(
        models.SavedStock.user_id == current_user.user_id
    ).order_by(models.SavedStock.created_at.desc()).all()
@app.post("/stocks/save/")
def fetch_and_save_stock(
    payload: schemas.StockSaveRequest, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    clean_ticker = payload.ticker.strip().upper()
    
    existing = db.query(models.SavedStock).filter(
        models.SavedStock.user_id == current_user.user_id,
        models.SavedStock.ticker == clean_ticker
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Stock is already in your watchlist")
    yf_symbol = format_yf_ticker(clean_ticker, current_user.preferred_market)
    stock = yf.Ticker(yf_symbol)
    info = stock.info
    if "longName" not in info and "regularMarketPrice" not in info and "currentPrice" not in info:
        raise HTTPException(status_code=404, detail=f"Ticker '{yf_symbol}' not found on Yahoo Finance")
    new_saved_stock = models.SavedStock(
        user_id=current_user.user_id,
        ticker=clean_ticker
    )
    db.add(new_saved_stock)
    db.commit()
    db.refresh(new_saved_stock)    
    return {
        "message": "Stock successfully saved to watchlist!",
        "saved_stock_id": new_saved_stock.saved_stock_id,
        "ticker": new_saved_stock.ticker,
        "company_name": info.get("longName"),
        "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "created_at": new_saved_stock.created_at
    }
@app.delete("/stocks/{saved_stock_id}")
def remove_from_watchlist(
    saved_stock_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    stock_item = db.query(models.SavedStock).filter(
        models.SavedStock.saved_stock_id == saved_stock_id,
        models.SavedStock.user_id == current_user.user_id
    ).first()
    if not stock_item:
        raise HTTPException(status_code=404, detail="Stock not found in your watchlist")
    db.delete(stock_item)
    db.commit()
    return {"message": f"{stock_item.ticker} removed from watchlist"}
@app.post("/research/", response_model=schemas.ResearchTaskResponse)
def start_stock_research(
    request: schemas.ResearchTaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    market = request.market or current_user.preferred_market
    period = request.analysis_period or current_user.preferred_period
    clean_ticker = request.ticker.strip().upper()
    yf_symbol = format_yf_ticker(clean_ticker, market)
    task = models.ResearchTask(
        user_id=current_user.user_id,
        company_name=clean_ticker,
        ticker=clean_ticker,
        market=market,
        analysis_period=period,
        status="Processing"
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    try:
        stock = yf.Ticker(yf_symbol)
        info = stock.info
        hist = stock.history(period=PERIOD_MAP[period])
        if hist.empty:
            raise ValueError("No historical price data available for this ticker/market.")
        company_name = info.get("longName") or clean_ticker
        start_price = round(float(hist["Close"].iloc[0]), 2)
        end_price = round(float(hist["Close"].iloc[-1]), 2)
        pct_change = round(((end_price - start_price) / start_price) * 100, 2)
        high_price = round(float(hist["High"].max()), 2)
        low_price = round(float(hist["Low"].min()), 2)
        summary = (
            f"Research Report for {company_name} ({yf_symbol}) | Market: {market} | Period: {period}\n"
            f"- Starting Price: {start_price}\n"
            f"- Latest Close Price: {end_price} ({pct_change:+}%)\n"
            f"- Period High / Low: {high_price} / {low_price}\n"
            f"- Sector: {info.get('sector', 'N/A')} | Industry: {info.get('industry', 'N/A')}"
        )
        task.company_name = company_name
        task.status = "Completed"
        task.report_summary = summary
    except Exception as e:
        task.status = "Failed"
        task.report_summary = f"Research failed: {str(e)}"
    db.commit()
    db.refresh(task)
    return task
@app.get("/research/", response_model=List[schemas.ResearchTaskResponse])
def get_research_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return db.query(models.ResearchTask).filter(
        models.ResearchTask.user_id == current_user.user_id
    ).order_by(models.ResearchTask.created_at.desc()).all()
@app.get("/research/{task_id}", response_model=schemas.ResearchTaskResponse)
def get_research_report(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    task = db.query(models.ResearchTask).filter(
        models.ResearchTask.task_id == task_id,
        models.ResearchTask.user_id == current_user.user_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Research report not found")
    return task