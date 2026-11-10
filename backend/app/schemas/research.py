import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ResearchRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=32)
    market: str = "NSE"
    period: str | None = Field(default=None, pattern=r"^\d+(d|mo|y)$")
    as_of: date | None = None  # replay mode

    def as_of_date_in_future(self) -> bool:
        return self.as_of is not None and self.as_of >= date.today()


class ResearchTaskOut(BaseModel):
    task_id: uuid.UUID
    ticker: str
    market: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}
