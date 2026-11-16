import re
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ConfigDict


class UserRegisterRequest(BaseModel):
    """
    Pydantic schema for incoming user registration request payload.
    Supports snake_case and camelCase aliases for seamless frontend compatibility.
    """
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    full_name: str = Field(
        ...,
        alias="fullName",
        min_length=2,
        max_length=100,
        description="User's full name (minimum 2 characters)",
        examples=["Jane Doe"]
    )
    email: EmailStr = Field(
        ...,
        description="Valid user email address",
        examples=["jane.doe@example.com"]
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Secure password (minimum 8 characters, at least 1 uppercase letter and 1 number)",
        examples=["SecurePass123!"]
    )
    confirm_password: str = Field(
        ...,
        alias="confirmPassword",
        min_length=8,
        max_length=128,
        description="Password confirmation matching password exactly",
        examples=["SecurePass123!"]
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter (A-Z).")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one numerical digit (0-9).")
        return v

    @model_validator(mode="after")
    def verify_password_match(self) -> "UserRegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Password and confirmation password do not match.")
        return self


class UserResponse(BaseModel):
    """
    Public representation of a registered user.
    Security: The password_hash is strictly excluded.
    """
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    full_name: str
    email: str
    created_at: datetime


class RegisterSuccessResponse(BaseModel):
    """
    Standardized API response returned upon successful user registration.
    """
    status: str = "success"
    message: str = "User registered successfully."
    data: UserResponse


class UserLoginRequest(BaseModel):
    """
    Pydantic schema for user authentication credentials.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., description="Account password")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class LoginSuccessResponse(BaseModel):
    """
    Standardized API response returned upon successful user authentication.
    """
    status: str = "success"
    message: str = "Login successful."
    data: UserResponse


class LogoutSuccessResponse(BaseModel):
    """
    Standardized API response returned upon logout.
    """
    status: str = "success"
    message: str = "Logged out successfully."


class CurrentUserResponse(BaseModel):
    """
    Standardized API response returning the authenticated user profile.
    """
    status: str = "success"
    data: UserResponse

