from typing import Optional
from pydantic import BaseModel


class StockSearchResult(BaseModel):
    ticker: str
    company_name: str
    market: str
    exchange: Optional[str] = None
    currency: Optional[str] = "USD"
    sector: Optional[str] = None
    type: Optional[str] = "EQUITY"

