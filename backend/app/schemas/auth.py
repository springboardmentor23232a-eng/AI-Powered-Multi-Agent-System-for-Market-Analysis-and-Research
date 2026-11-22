from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from app.schemas.user import UserResponse
from app.security import validate_password_strength


class UserRegisterRequest(BaseModel):
    """Payload for registering a new user account."""
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of user")
    email: EmailStr = Field(..., description="Valid unique email address")
    password: str = Field(..., min_length=8, max_length=72, description="Password meeting complexity requirements")
    confirm_password: str = Field(..., min_length=8, max_length=72, description="Must match password")

    @model_validator(mode="after")
    def validate_registration(self):
        # 1. Verify passwords match
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")

        # 2. Verify password complexity
        validate_password_strength(self.password)

        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "New User",
                "email": "user@example.com",
                "password": "StrongPassword@2026",
                "confirm_password": "StrongPassword@2026",
            }
        }
    )


class UserLoginRequest(BaseModel):
    """Payload for logging into an existing account."""
    email: EmailStr = Field(..., description="Registered user email")
    password: str = Field(..., description="User plaintext password")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "StrongPassword@2026",
            }
        }
    )


class TokenResponse(BaseModel):
    """Authentication response containing JWT token and user profile."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token lifespan in seconds")
    user: UserResponse


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
