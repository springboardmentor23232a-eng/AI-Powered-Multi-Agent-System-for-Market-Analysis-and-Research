from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    full_name: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime


class UserUpdateProfileRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, description="Updated full name")
