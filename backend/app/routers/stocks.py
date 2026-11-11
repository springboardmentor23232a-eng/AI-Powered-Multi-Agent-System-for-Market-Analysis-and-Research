from typing import List
from fastapi import APIRouter, Depends, Query
from app.models.user import User
from app.schemas.stock import StockSearchResult
from app.services.auth_service import get_current_user
from app.services.stock_data_service import StockDataService

router = APIRouter(prefix="/stocks", tags=["Stocks"])


@router.get("/search", response_model=List[StockSearchResult])
async def search_stocks(
    q: str = Query(..., min_length=1, description="Ticker symbol or company name"),
    current_user: User = Depends(get_current_user)
):
    """
    Search stocks across supported exchanges (NSE, BSE, NASDAQ, NYSE)
    using validated market data provider with verified catalog fallback.
    """
    results = await StockDataService.search_stocks(q)
    return results

