"""
Invoice Pydantic Schemas

Request/response schemas for invoice-related endpoints.
Handles validation and serialization with status workflow enforcement.
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.invoice import InvoiceStatus
from app.schemas.validators import sanitize_text_input


# Invoice Item schemas
class InvoiceItemBase(BaseModel):
    """Base invoice item schema."""
    item_id: Optional[UUID] = Field(None, description="Optional catalog item reference")
    description: str = Field(..., min_length=1, max_length=500, description="Item description")
    quantity: Decimal = Field(default=Decimal("1.0"), gt=0, description="Quantity")
    unit_price: Decimal = Field(..., ge=0, description="Unit price (before tax)")
    tax_rate: Decimal = Field(default=Decimal("16.0"), ge=0, le=100, description="Tax rate percentage")

    @field_validator("quantity", "unit_price", "tax_rate")
    @classmethod
    def validate_decimal_places(cls, v: Decimal) -> Decimal:
        """Ensure decimal values have at most 2 decimal places."""
        if v is None:
            return v
        return round(v, 2)

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v: str) -> str:
        """Sanitize description to prevent XSS and SQL injection."""
        sanitized = sanitize_text_input(v, allow_html=False)
        if not sanitized:
            raise ValueError("Description cannot be empty after sanitization")
        return sanitized


class InvoiceItemCreate(InvoiceItemBase):
    """Schema for creating invoice line items."""
    pass


class InvoiceItemResponse(InvoiceItemBase):
    """Schema for invoice line item responses."""
    id: UUID
    invoice_id: UUID
    line_total: Decimal
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


# Invoice schemas
class InvoiceBase(BaseModel):
    """Base invoice schema with common fields."""
    contact_id: UUID = Field(..., description="Customer contact ID")
    due_date: Optional[date] = Field(None, description="Payment due date")
    notes: Optional[str] = Field(None, description="Additional notes or terms")

    @field_validator("notes")
    @classmethod
    def sanitize_notes(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize notes to prevent XSS and SQL injection."""
        return sanitize_text_input(v, allow_html=False)


class InvoiceCreate(InvoiceBase):
    """Schema for creating a new invoice."""
    line_items: List[InvoiceItemCreate] = Field(
        ...,
        min_length=1,
        description="Invoice line items (at least one required)"
    )

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v: Optional[date]) -> Optional[date]:
        """Validate due date is not in the past."""
        if v is None:
            return v

        if v < date.today():
            raise ValueError("Due date cannot be in the past")

        return v


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice (only allowed in draft status)."""
    contact_id: Optional[UUID] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None
    line_items: Optional[List[InvoiceItemCreate]] = Field(
        None,
        min_length=1,
        description="Updated line items"
    )

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v: Optional[date]) -> Optional[date]:
        """Validate due date is not in the past."""
        if v is None:
            return v

        if v < date.today():
            raise ValueError("Due date cannot be in the past")

        return v

    @field_validator("notes")
    @classmethod
    def sanitize_notes(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize notes to prevent XSS and SQL injection."""
        return sanitize_text_input(v, allow_html=False)


class InvoiceIssueRequest(BaseModel):
    """Schema for issuing an invoice."""
    issue_date: Optional[date] = Field(None, description="Issue date (defaults to today)")

    @field_validator("issue_date")
    @classmethod
    def validate_issue_date(cls, v: Optional[date]) -> Optional[date]:
        """Validate issue date is not in the future."""
        if v is None:
            return v

        if v > date.today():
            raise ValueError("Issue date cannot be in the future")

        return v


# Response schemas
class InvoiceResponse(BaseModel):
    """Schema for invoice responses."""
    id: UUID
    business_id: UUID
    contact_id: UUID
    invoice_number: str
    status: InvoiceStatus
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal = Field(default=Decimal("0.00"), description="Total amount paid")
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "business_id": "123e4567-e89b-12d3-a456-426614174001",
                "contact_id": "123e4567-e89b-12d3-a456-426614174002",
                "invoice_number": "INV-2025-00001",
                "status": "issued",
                "issue_date": "2025-01-01",
                "due_date": "2025-01-31",
                "subtotal": "10000.00",
                "tax_amount": "1600.00",
                "total_amount": "11600.00",
                "amount_paid": "5000.00",
                "notes": "Payment due within 30 days",
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00"
            }
        }
    }


class InvoiceDetailResponse(InvoiceResponse):
    """Schema for detailed invoice response with line items."""
    line_items: List[InvoiceItemResponse] = Field(default_factory=list)


class InvoiceListResponse(BaseModel):
    """Schema for paginated invoice list response."""
    invoices: list[InvoiceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class InvoicePDFResponse(BaseModel):
    """Schema for PDF generation response (placeholder)."""
    invoice_id: UUID
    invoice_number: str
    pdf_url: Optional[str] = Field(None, description="URL to download PDF (future)")
    invoice_data: InvoiceDetailResponse = Field(..., description="Invoice data for PDF generation")
