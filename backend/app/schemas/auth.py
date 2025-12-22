"""
Authentication Pydantic Schemas

Request/response schemas for authentication endpoints.
Handles login, logout, token refresh, and password management.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """Schema for login request."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "admin@example.com",
                "password": "SecurePass123!"
            }
        }
    }


class LoginResponse(BaseModel):
    """Schema for login response."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="Authenticated user information")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "admin@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "role": "business_admin",
                    "is_active": True,
                    "must_change_password": False
                }
            }
        }
    }


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str = Field(..., description="JWT refresh token")

    model_config = {
        "json_schema_extra": {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    }


class RefreshTokenResponse(BaseModel):
    """Schema for token refresh response."""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
    }


class ChangePasswordRequest(BaseModel):
    """Schema for password change request."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Validate password meets security requirements.

        Requirements:
        - At least 8 characters
        - Contains uppercase letter
        - Contains lowercase letter
        - Contains number
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")

        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")

        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "current_password": "OldPass123",
                "new_password": "NewSecurePass456"
            }
        }
    }


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str = Field(..., description="Response message")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Operation completed successfully"
            }
        }
    }


class UserMeResponse(BaseModel):
    """Schema for current user information response."""
    user: UserResponse = Field(..., description="Current user information")

    model_config = {
        "json_schema_extra": {
            "example": {
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "admin@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "role": "business_admin",
                    "is_active": True,
                    "must_change_password": False
                }
            }
        }
    }
