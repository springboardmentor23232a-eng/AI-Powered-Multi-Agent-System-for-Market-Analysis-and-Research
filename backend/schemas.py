
from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator
from datetime import datetime


# 1. Registration schema
class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    confirm_password: str

    # Check whether both passwords match
    @model_validator(mode="after")
    def check_passwords(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


# 2. Login schema
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# 3. User response schema
class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    is_active: bool
    created_at: datetime

    # Allows Pydantic to read data from SQLAlchemy objects
    model_config = ConfigDict(from_attributes=True)


# 4. JWT token response schema
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
# 5. Google login schema
class GoogleLoginRequest(BaseModel):
    credential: str


# Research task creation schema
class ResearchTaskCreate(BaseModel):
    company_name: str
    ticker: str
    market: str
    analysis_period: str


# Research task response schema
class ResearchTaskResponse(BaseModel):
    research_id: int
    user_id: int
    company_name: str
    ticker: str
    market: str
    analysis_period: str
    status: str
    report_content: str | None
    research_date: datetime

    model_config = ConfigDict(from_attributes=True)

# Research task update schema
class ResearchTaskUpdate(BaseModel):
    status: str
    report_content: str | None = None

    
# User preferences update schema
class UserPreferenceUpdate(BaseModel):
    market: str = Field(default="NSI")
    analysis_period: str = Field(default="1y")


# User preferences response schema
class UserPreferenceResponse(BaseModel):
    preference_id: int
    user_id: int
    market: str
    analysis_period: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
