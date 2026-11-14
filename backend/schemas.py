from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional,Literal
AllowedMarket=Literal["NSE","BSE","NASDAQ", "NYSE"]
AllowedPeriod=Literal["1 Month","3 Months","6 Months","1 Year","5 Years","5 Years"]
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
class UserResponse(BaseModel):
    user_id: int
    full_name: str
    email: str
    preferred_market: str
    preferred_period: str
    created_at: datetime
    class Config:
        from_attributes = True
class Token(BaseModel):
    access_token: str
    token_type: str
class UserPreferencesUpdate(BaseModel):
    preferred_market: AllowedMarket
    preferred_period: AllowedPeriod
class UserPreferencesResponse(BaseModel):
    preferred_market: str
    preferred_period: str
    class Config:
        from_attributes = True
class StockSaveRequest(BaseModel):
    user_id: int
    ticker: str
class SavedStockResponse(BaseModel):
    saved_stock_id: int
    ticker: str
    created_at: datetime
    class Config:
        from_attributes = True
class ResearchTaskCreate(BaseModel):
    ticker: str
    market:Optional[AllowedMarket] = None
    analysis_period: Optional[AllowedPeriod] = None
class ResearchTaskResponse(BaseModel):
    task_id: int
    company_name: str
    ticker: str
    market: str
    analysis_period: str
    status: str
    report_summary: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True