from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, SavedStock, SavedStockMetadata
from app.schemas import WatchlistCreate, WatchlistOut

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])

@router.get("", response_model=list[WatchlistOut])
def list_stocks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stocks = db.query(SavedStock).filter(SavedStock.user_id == user.id).order_by(SavedStock.created_at.desc()).all()
    return [WatchlistOut(id=stock.id, ticker=stock.ticker, company_name=stock.company_name, market=stock.market, provider_symbol=(stock.stock_metadata.provider_symbol if stock.stock_metadata else None), created_at=stock.created_at) for stock in stocks]

@router.post("", response_model=WatchlistOut, status_code=201)
def add_stock(payload: WatchlistCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ticker = payload.ticker.strip().upper()
    exists = db.query(SavedStock).filter_by(user_id=user.id, ticker=ticker).first()
    if exists:
        raise HTTPException(409, "This stock is already in your watchlist.")
    stock = SavedStock(user_id=user.id, company_name=payload.company_name or ticker, ticker=ticker, market=payload.market or "NASDAQ")
    db.add(stock)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "This stock is already in your watchlist.")
    db.refresh(stock)
    if payload.company_name or payload.market or payload.provider_symbol:
        db.add(SavedStockMetadata(saved_stock_id=stock.id, company_name=payload.company_name, market=payload.market or stock.market, provider_symbol=payload.provider_symbol))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "This stock metadata already exists.")
    return WatchlistOut(id=stock.id, ticker=stock.ticker, company_name=stock.company_name, market=stock.market, provider_symbol=payload.provider_symbol, created_at=stock.created_at)

@router.delete("/{stock_id}")
def remove_stock(stock_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        stock = db.query(SavedStock).filter(SavedStock.id == stock_id, SavedStock.user_id == user.id).first()
    except ValueError:
        stock = None
    if stock is None:
        stock = db.query(SavedStock).filter(SavedStock.ticker == stock_id.strip().upper(), SavedStock.user_id == user.id).first()
    if not stock:
        raise HTTPException(404, "Saved stock not found.")
    db.delete(stock)
    db.commit()
    return {"message": "Stock removed from watchlist."}
