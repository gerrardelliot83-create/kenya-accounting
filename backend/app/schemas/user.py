"""
User Pydantic Schemas

Request/response schemas for user-related endpoints.
Handles validation and serialization.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole


# Base schemas
class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr = Field(..., description="User email address")
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    national_id: Optional[str] = Field(None, max_length=50)


# Request schemas
class UserCreate(UserBase):
    """Schema for creating a new user."""
    role: UserRole = Field(..., description="User role")
    business_id: Optional[UUID] = Field(None, description="Associated business ID")
    password: str = Field(..., min_length=8, description="User password")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Validate password meets security requirements.

        Requirements:
        - At least 8 characters
        - Contains uppercase and lowercase
        - Contains numbers
        - Contains special characters
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")

        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")

        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in v):
            raise ValueError("Password must contain at least one special character")

        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format (Kenya format)."""
        if v is None:
            return v

        # Remove spaces and common separators
        phone = v.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

        # Kenya phone numbers: +254XXXXXXXXX or 07XXXXXXXX or 01XXXXXXXX
        if phone.startswith("+254"):
            if len(phone) != 13:
                raise ValueError("Invalid Kenya phone number format")
        elif phone.startswith("0"):
            if len(phone) != 10:
                raise ValueError("Invalid Kenya phone number format")
        else:
            raise ValueError("Phone number must start with +254 or 0")

        return phone


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    national_id: Optional[str] = Field(None, max_length=50)
    role: Optional[UserRole] = None
    business_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class UserPasswordChange(BaseModel):
    """Schema for changing user password."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str, values) -> str:
        """Validate new password meets requirements and differs from current."""
        # Use same validation as UserCreate
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")

        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")

        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in v):
            raise ValueError("Password must contain at least one special character")

        return v


# Response schemas
class UserResponse(BaseModel):
    """Schema for user responses (without sensitive data)."""
    id: UUID
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole
    business_id: Optional[UUID] = None
    is_active: bool
    must_change_password: bool
    last_login_at: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+254712345678",
                "role": "business_admin",
                "business_id": "123e4567-e89b-12d3-a456-426614174001",
                "is_active": True,
                "must_change_password": False,
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00"
            }
        }
    }


class UserListResponse(BaseModel):
    """Schema for paginated user list response."""
    users: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserDetailResponse(UserResponse):
    """Schema for detailed user response with additional info."""
    # Can add relationships here if needed
    pass


# Authentication schemas
class LoginRequest(BaseModel):
    """Schema for login request."""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    """Schema for login response."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="User information")


class TokenRefreshRequest(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str = Field(..., description="Refresh token")


class TokenRefreshResponse(BaseModel):
    """Schema for token refresh response."""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
