from fastapi import APIRouter, Depends, Query
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.stock import (
    StockSearchResponse,
    StockOverviewResponse,
    HistoricalDataResponse,
    FinancialStatementsResponse,
)
from app.schemas.fundamental import FundamentalAnalysisResponse
from app.services.stock_service import (
    search_stocks,
    get_company_overview,
    get_historical_ohlcv,
    get_financial_statements,
)
from app.services.fundamental_service import run_fundamental_analysis

router = APIRouter(
    prefix="/stocks",
    tags=["Stock Market Research"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/search", response_model=StockSearchResponse)
def search_stock_symbols(
    q: str = Query(..., min_length=1, description="Company name or stock ticker to search"),
    current_user: User = Depends(get_current_user),
) -> StockSearchResponse:
    """
    Search Indian & global stocks (Requires authenticated user).
    """
    return search_stocks(query=q)


@router.get("/{ticker}/overview", response_model=StockOverviewResponse)
def get_stock_overview(
    ticker: str,
    current_user: User = Depends(get_current_user),
) -> StockOverviewResponse:
    """
    Retrieve live fundamental overview (Requires authenticated user).
    """
    return get_company_overview(ticker=ticker)


@router.get("/{ticker}/history", response_model=HistoricalDataResponse)
def get_stock_history(
    ticker: str,
    period: str = Query("1mo", description="Historical duration: 1mo, 3mo, 6mo, 1y, 2y, 5y, max"),
    current_user: User = Depends(get_current_user),
) -> HistoricalDataResponse:
    """
    Retrieve historical OHLCV pricing data (Requires authenticated user).
    """
    return get_historical_ohlcv(ticker=ticker, period=period)


@router.get("/{ticker}/financials", response_model=FinancialStatementsResponse)
def get_stock_financials(
    ticker: str,
    current_user: User = Depends(get_current_user),
) -> FinancialStatementsResponse:
    """
    Retrieve financial statements (Income Statement, Balance Sheet, Cash Flow)
    with annual and quarterly breakdown (Requires authenticated user).
    """
    return get_financial_statements(ticker=ticker)


@router.get("/{ticker}/fundamental", response_model=FundamentalAnalysisResponse)
def get_stock_fundamental(
    ticker: str,
    current_user: User = Depends(get_current_user),
) -> FundamentalAnalysisResponse:
    """
    Execute comprehensive fundamental analysis (Module 3) for the given ticker.
    Analyzes revenue/earnings, profitability, debt/stability, valuation ratios,
    historical trends, peer comparison, and data integrity.
    """
    overview = get_company_overview(ticker=ticker)
    financials = get_financial_statements(ticker=ticker)
    return run_fundamental_analysis(ticker=ticker, financials=financials, overview=overview)
