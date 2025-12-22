"""
Business Pydantic Schemas

Request/response schemas for business-related endpoints.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# Base schemas
class BusinessBase(BaseModel):
    """Base business schema with common fields."""
    name: str = Field(..., max_length=255, description="Business name")
    kra_pin: Optional[str] = Field(None, max_length=20, description="KRA PIN")
    bank_account_number: Optional[str] = Field(None, description="Bank account number")
    tax_certificate_number: Optional[str] = Field(None, description="Tax certificate number")
    vat_registered: bool = Field(default=False, description="VAT registration status")
    tot_registered: bool = Field(default=False, description="TOT registration status")
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    country: str = Field(default="Kenya", max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    business_type: Optional[str] = Field(None, max_length=50)


# Request schemas
class BusinessCreate(BusinessBase):
    """Schema for creating a new business."""

    @field_validator("kra_pin")
    @classmethod
    def validate_kra_pin(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate KRA PIN format.

        Kenya KRA PIN format: A[0-9]{9}[A-Z] (e.g., A001234567B)
        """
        if v is None:
            return v

        # Remove spaces
        pin = v.replace(" ", "").upper()

        # Validate format
        if len(pin) != 11:
            raise ValueError("KRA PIN must be 11 characters (e.g., A001234567B)")

        if not pin[0].isalpha():
            raise ValueError("KRA PIN must start with a letter")

        if not pin[1:10].isdigit():
            raise ValueError("KRA PIN must have 9 digits after the first letter")

        if not pin[10].isalpha():
            raise ValueError("KRA PIN must end with a letter")

        return pin

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


class BusinessUpdate(BaseModel):
    """Schema for updating a business."""
    name: Optional[str] = Field(None, max_length=255)
    kra_pin: Optional[str] = Field(None, max_length=20)
    bank_account_number: Optional[str] = None
    tax_certificate_number: Optional[str] = None
    vat_registered: Optional[bool] = None
    tot_registered: Optional[bool] = None
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    business_type: Optional[str] = Field(None, max_length=50)
    onboarding_status: Optional[str] = None
    is_active: Optional[bool] = None


class BusinessOnboardingUpdate(BaseModel):
    """Schema for updating business onboarding status."""
    onboarding_status: str = Field(
        ...,
        description="Onboarding status: pending, in_progress, completed, rejected"
    )

    @field_validator("onboarding_status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate onboarding status."""
        valid_statuses = ["pending", "in_progress", "completed", "rejected"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v


# Response schemas
class BusinessResponse(BaseModel):
    """Schema for business responses (without sensitive data)."""
    id: UUID
    name: str
    vat_registered: bool
    tot_registered: bool
    address: Optional[str] = None
    city: Optional[str] = None
    country: str
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    business_type: Optional[str] = None
    onboarding_status: str
    onboarding_completed_at: Optional[str] = None
    is_active: bool
    subscription_tier: str
    subscription_expires_at: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Example Business Ltd",
                "vat_registered": True,
                "tot_registered": False,
                "city": "Nairobi",
                "country": "Kenya",
                "onboarding_status": "completed",
                "is_active": True,
                "subscription_tier": "basic",
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00"
            }
        }
    }


class BusinessDetailResponse(BusinessResponse):
    """
    Schema for detailed business response with sensitive data.

    Only accessible by authorized users (business admin, system admin).
    """
    kra_pin: Optional[str] = None
    bank_account_number: Optional[str] = None
    tax_certificate_number: Optional[str] = None


class BusinessListResponse(BaseModel):
    """Schema for paginated business list response."""
    businesses: list[BusinessResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
