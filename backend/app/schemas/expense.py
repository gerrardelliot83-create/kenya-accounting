"""
Expense Pydantic Schemas

Request/response schemas for expense-related endpoints.
Handles validation and serialization with proper decimal handling.
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from app.schemas.validators import sanitize_text_input


class PaymentMethod(str, Enum):
    """Payment method enumeration."""
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    MPESA = "mpesa"
    CARD = "card"
    OTHER = "other"


# Expense Category schemas
class ExpenseCategoryBase(BaseModel):
    """Base expense category schema."""
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, max_length=500, description="Category description")

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        """Sanitize category name."""
        sanitized = sanitize_text_input(v, allow_html=False)
        if not sanitized:
            raise ValueError("Category name cannot be empty after sanitization")
        return sanitized

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize description."""
        return sanitize_text_input(v, allow_html=False)


class ExpenseCategoryCreate(ExpenseCategoryBase):
    """Schema for creating an expense category."""
    pass


class ExpenseCategoryUpdate(BaseModel):
    """Schema for updating an expense category."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize category name."""
        if v is None:
            return None
        sanitized = sanitize_text_input(v, allow_html=False)
        if not sanitized:
            raise ValueError("Category name cannot be empty after sanitization")
        return sanitized

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize description."""
        return sanitize_text_input(v, allow_html=False)


class ExpenseCategoryResponse(ExpenseCategoryBase):
    """Schema for expense category responses."""
    id: UUID
    business_id: Optional[UUID]
    is_system: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


# Expense schemas
class ExpenseBase(BaseModel):
    """Base expense schema with common fields."""
    category: str = Field(..., min_length=1, max_length=100, description="Expense category")
    description: str = Field(..., min_length=1, max_length=1000, description="Expense description")
    amount: Decimal = Field(..., gt=0, description="Expense amount (must be positive)")
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="Tax amount (VAT/TOT)")
    expense_date: date = Field(..., description="Date expense was incurred")
    vendor_name: Optional[str] = Field(None, max_length=200, description="Vendor/supplier name")
    receipt_url: Optional[str] = Field(None, max_length=500, description="URL to receipt document")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    reference_number: Optional[str] = Field(None, max_length=100, description="Transaction reference")
    notes: Optional[str] = Field(None, max_length=2000, description="Additional notes")

    @field_validator("amount", "tax_amount")
    @classmethod
    def validate_decimal_places(cls, v: Decimal) -> Decimal:
        """Ensure decimal values have at most 2 decimal places."""
        if v is None:
            return v
        return round(v, 2)

    @field_validator("category")
    @classmethod
    def sanitize_category(cls, v: str) -> str:
        """Sanitize category."""
        sanitized = sanitize_text_input(v, allow_html=False)
        if not sanitized:
            raise ValueError("Category cannot be empty after sanitization")
        return sanitized

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v: str) -> str:
        """Sanitize description."""
        sanitized = sanitize_text_input(v, allow_html=False)
        if not sanitized:
            raise ValueError("Description cannot be empty after sanitization")
        return sanitized

    @field_validator("vendor_name")
    @classmethod
    def sanitize_vendor_name(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize vendor name."""
        return sanitize_text_input(v, allow_html=False)

    @field_validator("notes")
    @classmethod
    def sanitize_notes(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize notes."""
        return sanitize_text_input(v, allow_html=False)

    @field_validator("expense_date")
    @classmethod
    def validate_expense_date(cls, v: date) -> date:
        """Validate expense date is not in the future."""
        if v > date.today():
            raise ValueError("Expense date cannot be in the future")
        return v


class ExpenseCreate(ExpenseBase):
    """Schema for creating a new expense."""
    pass


class ExpenseUpdate(BaseModel):
    """Schema for updating an expense."""
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    amount: Optional[Decimal] = Field(None, gt=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    expense_date: Optional[date] = None
    vendor_name: Optional[str] = Field(None, max_length=200)
    receipt_url: Optional[str] = Field(None, max_length=500)
    payment_method: Optional[PaymentMethod] = None
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=2000)

    @field_validator("amount", "tax_amount")
    @classmethod
    def validate_decimal_places(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Ensure decimal values have at most 2 decimal places."""
        if v is None:
            return v
        return round(v, 2)

    @field_validator("category")
    @classmethod
    def sanitize_category(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize category."""
        if v is None:
            return None
        sanitized = sanitize_text_input(v, allow_html=False)
        if not sanitized:
            raise ValueError("Category cannot be empty after sanitization")
        return sanitized

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize description."""
        if v is None:
            return None
        sanitized = sanitize_text_input(v, allow_html=False)
        if not sanitized:
            raise ValueError("Description cannot be empty after sanitization")
        return sanitized

    @field_validator("vendor_name")
    @classmethod
    def sanitize_vendor_name(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize vendor name."""
        return sanitize_text_input(v, allow_html=False)

    @field_validator("notes")
    @classmethod
    def sanitize_notes(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize notes."""
        return sanitize_text_input(v, allow_html=False)

    @field_validator("expense_date")
    @classmethod
    def validate_expense_date(cls, v: Optional[date]) -> Optional[date]:
        """Validate expense date is not in the future."""
        if v is None:
            return v
        if v > date.today():
            raise ValueError("Expense date cannot be in the future")
        return v


# Response schemas
class ExpenseResponse(BaseModel):
    """Schema for expense responses."""
    id: UUID
    business_id: UUID
    category: str
    description: str
    amount: Decimal
    tax_amount: Decimal
    expense_date: date
    vendor_name: Optional[str]
    receipt_url: Optional[str]
    payment_method: str
    reference_number: Optional[str]
    is_reconciled: bool
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "business_id": "123e4567-e89b-12d3-a456-426614174001",
                "category": "office_supplies",
                "description": "Office stationery and supplies",
                "amount": "5000.00",
                "tax_amount": "800.00",
                "expense_date": "2025-12-01",
                "vendor_name": "ABC Stationery Ltd",
                "receipt_url": "https://storage.example.com/receipts/receipt-123.pdf",
                "payment_method": "mpesa",
                "reference_number": "SH12345678",
                "is_reconciled": False,
                "notes": "Monthly office supplies",
                "is_active": True,
                "created_at": "2025-12-01T10:00:00",
                "updated_at": "2025-12-01T10:00:00"
            }
        }
    }

    @property
    def total_amount(self) -> Decimal:
        """Calculate total amount including tax."""
        return self.amount + self.tax_amount


class ExpenseListResponse(BaseModel):
    """Schema for paginated expense list response."""
    expenses: List[ExpenseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ExpenseSummaryByCategoryResponse(BaseModel):
    """Schema for expense summary by category."""
    category: str
    total_amount: Decimal
    total_tax: Decimal
    expense_count: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "category": "office_supplies",
                "total_amount": "25000.00",
                "total_tax": "4000.00",
                "expense_count": 5
            }
        }
    }


class ExpenseSummaryResponse(BaseModel):
    """Schema for overall expense summary."""
    start_date: date
    end_date: date
    total_expenses: Decimal
    total_tax: Decimal
    expense_count: int
    by_category: List[ExpenseSummaryByCategoryResponse]

    model_config = {
        "json_schema_extra": {
            "example": {
                "start_date": "2025-12-01",
                "end_date": "2025-12-31",
                "total_expenses": "150000.00",
                "total_tax": "24000.00",
                "expense_count": 25,
                "by_category": [
                    {
                        "category": "office_supplies",
                        "total_amount": "25000.00",
                        "total_tax": "4000.00",
                        "expense_count": 5
                    }
                ]
            }
        }
    }
