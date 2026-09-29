from pydantic import BaseModel, EmailStr, Field, field_validator

from app.modules.users.enums import UserRole
from app.modules.users.schemas import UserResponse


class RegisterRequest(BaseModel):
    """Payload for user self-registration."""

    email: EmailStr = Field(description="User email address")
    password: str = Field(min_length=8, max_length=128, description="Password must be at least 8 characters")
    first_name: str = Field(min_length=1, max_length=100, description="Given name")
    last_name: str = Field(min_length=1, max_length=100, description="Family name")
    role: UserRole = Field(default=UserRole.CUSTOMER, description="Initial role: CUSTOMER or SELLER")

    @field_validator("role")
    @classmethod
    def validate_public_registration_role(cls, v: UserRole) -> UserRole:
        """Prevent self-assigning ADMIN role through public registration endpoint."""
        if v == UserRole.ADMIN:
            raise ValueError("Admin accounts cannot be self-registered.")
        return v


class LoginRequest(BaseModel):
    """Credentials payload for authentication."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """Authentication token response with user profile."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class LogoutResponse(BaseModel):
    """Response returned upon successful logout."""

    message: str = "Successfully logged out"
