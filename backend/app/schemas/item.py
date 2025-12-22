"""
Item/Service Pydantic Schemas

Request/response schemas for item-related endpoints.
Handles validation and serialization.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.item import ItemType
from app.schemas.validators import sanitize_text_input, validate_sku


# Base schemas
class ItemBase(BaseModel):
    """Base item schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Item/service name")
    item_type: ItemType = Field(default=ItemType.PRODUCT, description="Item type")
    description: Optional[str] = Field(None, description="Detailed description")
    sku: Optional[str] = Field(None, max_length=100, description="SKU or product code")
    unit_price: Decimal = Field(..., ge=0, description="Unit price (before tax)")
    tax_rate: Decimal = Field(default=Decimal("16.0"), ge=0, le=100, description="Tax rate percentage")

    @field_validator("unit_price", "tax_rate")
    @classmethod
    def validate_decimal_places(cls, v: Decimal) -> Decimal:
        """Ensure decimal values have at most 2 decimal places."""
        if v is None:
            return v

        # Round to 2 decimal places
        return round(v, 2)

    @field_validator("sku")
    @classmethod
    def validate_sku_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate SKU format (alphanumeric, hyphens, underscores allowed)."""
        return validate_sku(v)

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize description to prevent XSS and SQL injection."""
        return sanitize_text_input(v, allow_html=False)


# Request schemas
class ItemCreate(ItemBase):
    """Schema for creating a new item."""
    pass


class ItemUpdate(BaseModel):
    """Schema for updating an item."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    item_type: Optional[ItemType] = None
    description: Optional[str] = None
    sku: Optional[str] = Field(None, max_length=100)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None

    @field_validator("unit_price", "tax_rate")
    @classmethod
    def validate_decimal_places(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Ensure decimal values have at most 2 decimal places."""
        if v is None:
            return v
        return round(v, 2)

    @field_validator("sku")
    @classmethod
    def validate_sku_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate SKU format."""
        return validate_sku(v)

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize description to prevent XSS and SQL injection."""
        return sanitize_text_input(v, allow_html=False)


# Response schemas
class ItemResponse(BaseModel):
    """Schema for item responses."""
    id: UUID
    business_id: UUID
    name: str
    item_type: ItemType
    description: Optional[str] = None
    sku: Optional[str] = None
    unit_price: Decimal
    tax_rate: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "business_id": "123e4567-e89b-12d3-a456-426614174001",
                "name": "Consulting Services",
                "item_type": "service",
                "description": "Professional consulting services",
                "sku": "CONSULT-001",
                "unit_price": "5000.00",
                "tax_rate": "16.00",
                "is_active": True,
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00"
            }
        }
    }


class ItemListResponse(BaseModel):
    """Schema for paginated item list response."""
    items: list[ItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
