from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base fields shared by User schemas."""
    email: EmailStr
    full_name: str


class UserResponse(BaseModel):
    """
    Public user profile response schema.
    Returns the real authenticated user's profile from PostgreSQL.
    Never exposes hashed_password or secrets.
    """
    user_id: int = Field(validation_alias="id")
    full_name: str
    email: EmailStr
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )
