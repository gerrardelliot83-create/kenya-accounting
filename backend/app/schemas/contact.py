"""
Contact Pydantic Schemas

Request/response schemas for contact-related endpoints.
Handles validation and serialization with encryption.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.contact import ContactType
from app.schemas.validators import sanitize_text_input, validate_kenya_phone, validate_kra_pin


# Base schemas
class ContactBase(BaseModel):
    """Base contact schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Contact name")
    contact_type: ContactType = Field(default=ContactType.CUSTOMER, description="Contact type")
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    kra_pin: Optional[str] = Field(None, max_length=50, description="KRA PIN")
    address: Optional[str] = Field(None, description="Physical address")
    notes: Optional[str] = Field(None, description="Additional notes")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format (Kenya format)."""
        return validate_kenya_phone(v)

    @field_validator("kra_pin")
    @classmethod
    def validate_kra_pin_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate KRA PIN format."""
        return validate_kra_pin(v)

    @field_validator("address", "notes")
    @classmethod
    def sanitize_text_fields(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize text fields to prevent XSS and SQL injection."""
        return sanitize_text_input(v, allow_html=False)


# Request schemas
class ContactCreate(ContactBase):
    """Schema for creating a new contact."""
    pass


class ContactUpdate(BaseModel):
    """Schema for updating a contact."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_type: Optional[ContactType] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    kra_pin: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        return validate_kenya_phone(v)

    @field_validator("kra_pin")
    @classmethod
    def validate_kra_pin_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate KRA PIN format."""
        return validate_kra_pin(v)

    @field_validator("address", "notes")
    @classmethod
    def sanitize_text_fields(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize text fields to prevent XSS and SQL injection."""
        return sanitize_text_input(v, allow_html=False)


# Response schemas
class ContactResponse(BaseModel):
    """Schema for contact responses."""
    id: UUID
    business_id: UUID
    name: str
    contact_type: ContactType
    email: Optional[str] = None
    phone: Optional[str] = None
    kra_pin: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "business_id": "123e4567-e89b-12d3-a456-426614174001",
                "name": "John Doe",
                "contact_type": "customer",
                "email": "john@example.com",
                "phone": "+254712345678",
                "kra_pin": "A012345678X",
                "address": "123 Main St, Nairobi",
                "notes": "Preferred customer",
                "is_active": True,
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00"
            }
        }
    }


class ContactListResponse(BaseModel):
    """Schema for paginated contact list response."""
    contacts: list[ContactResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
