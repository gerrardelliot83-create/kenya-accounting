"""
Payment Pydantic Schemas

Request/response schemas for payment-related endpoints.
Handles validation and serialization for payment recording.
"""

from datetime import datetime, date
from typing import Optional
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.payment import PaymentMethod
from app.schemas.validators import sanitize_text_input


class PaymentBase(BaseModel):
    """Base payment schema with common fields."""
    invoice_id: UUID = Field(..., description="Invoice this payment applies to")
    amount: Decimal = Field(..., gt=0, description="Payment amount (must be positive)")
    payment_date: date = Field(..., description="Date payment was received")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    reference_number: Optional[str] = Field(None, max_length=100, description="Payment reference (M-Pesa code, cheque number, etc.)")
    notes: Optional[str] = Field(None, description="Additional payment notes")

    @field_validator("amount")
    @classmethod
    def validate_decimal_places(cls, v: Decimal) -> Decimal:
        """Ensure amount has at most 2 decimal places."""
        if v is None:
            return v
        return round(v, 2)

    @field_validator("payment_date")
    @classmethod
    def validate_payment_date(cls, v: date) -> date:
        """Validate payment date is not in the future."""
        if v > date.today():
            raise ValueError("Payment date cannot be in the future")
        return v

    @field_validator("reference_number", "notes")
    @classmethod
    def sanitize_text_fields(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize text fields to prevent XSS and SQL injection."""
        if v is None:
            return v
        return sanitize_text_input(v, allow_html=False)


class PaymentCreate(PaymentBase):
    """Schema for creating a new payment."""
    pass


class PaymentUpdate(BaseModel):
    """
    Schema for updating a payment.

    Note: In practice, payments should rarely be updated once created.
    This schema is provided for flexibility but use with caution.
    """
    amount: Optional[Decimal] = Field(None, gt=0, description="Payment amount")
    payment_date: Optional[date] = Field(None, description="Payment date")
    payment_method: Optional[PaymentMethod] = Field(None, description="Payment method")
    reference_number: Optional[str] = Field(None, max_length=100, description="Payment reference")
    notes: Optional[str] = Field(None, description="Payment notes")

    @field_validator("amount")
    @classmethod
    def validate_decimal_places(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Ensure amount has at most 2 decimal places."""
        if v is None:
            return v
        return round(v, 2)

    @field_validator("payment_date")
    @classmethod
    def validate_payment_date(cls, v: Optional[date]) -> Optional[date]:
        """Validate payment date is not in the future."""
        if v is None:
            return v
        if v > date.today():
            raise ValueError("Payment date cannot be in the future")
        return v

    @field_validator("reference_number", "notes")
    @classmethod
    def sanitize_text_fields(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize text fields to prevent XSS and SQL injection."""
        if v is None:
            return v
        return sanitize_text_input(v, allow_html=False)


class PaymentResponse(BaseModel):
    """Schema for payment responses."""
    id: UUID
    business_id: UUID
    invoice_id: UUID
    amount: Decimal
    payment_date: date
    payment_method: PaymentMethod
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "business_id": "123e4567-e89b-12d3-a456-426614174001",
                "invoice_id": "123e4567-e89b-12d3-a456-426614174002",
                "amount": "5000.00",
                "payment_date": "2025-01-15",
                "payment_method": "mpesa",
                "reference_number": "QRT12345678",
                "notes": "Payment received via M-Pesa",
                "created_at": "2025-01-15T10:30:00",
                "updated_at": "2025-01-15T10:30:00"
            }
        }
    }


class PaymentListResponse(BaseModel):
    """Schema for paginated payment list response."""
    payments: list[PaymentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PaymentSummary(BaseModel):
    """Schema for payment summary information."""
    total_payments: int = Field(..., description="Total number of payments")
    total_amount_paid: Decimal = Field(..., description="Total amount paid")
    invoice_total: Decimal = Field(..., description="Invoice total amount")
    balance_due: Decimal = Field(..., description="Remaining balance due")
