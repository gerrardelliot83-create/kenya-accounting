"""
Tax Pydantic Schemas

Request/response schemas for Kenya tax compliance endpoints.
Supports VAT (16%) and TOT (1%) calculations with KRA filing requirements.

Kenya Tax Framework:
- VAT: 16% standard rate for businesses with turnover > KES 5M
- TOT: 1% turnover tax for businesses with KES 1-50M turnover (alternative to VAT)
- Filing deadline: 20th of following month for both VAT and TOT
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class TaxPeriod(str, Enum):
    """Tax calculation period enumeration."""
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class TaxType(str, Enum):
    """Tax type enumeration for Kenya."""
    VAT = "VAT"  # Value Added Tax (16%)
    TOT = "TOT"  # Turnover Tax (1%)
    NONE = "None"


# Tax Settings Schemas
class TaxSettingsBase(BaseModel):
    """Base tax settings schema."""
    is_vat_registered: bool = Field(
        default=False,
        description="Whether business is VAT registered with KRA"
    )
    vat_registration_number: Optional[str] = Field(
        None,
        max_length=50,
        description="VAT registration number (KRA PIN format)"
    )
    vat_registration_date: Optional[date] = Field(
        None,
        description="Date of VAT registration"
    )
    is_tot_eligible: bool = Field(
        default=False,
        description="Whether business is eligible for TOT (KES 1-50M turnover)"
    )
    financial_year_start_month: int = Field(
        default=1,
        ge=1,
        le=12,
        description="Financial year start month (1=January, 12=December)"
    )

    @field_validator("vat_registration_number")
    @classmethod
    def validate_vat_number(cls, v: Optional[str], info) -> Optional[str]:
        """Validate VAT registration number format."""
        if v is None:
            return v
        # Basic validation - can be enhanced for Kenya-specific format
        v = v.strip().upper()
        if len(v) < 5 or len(v) > 50:
            raise ValueError("VAT registration number must be between 5 and 50 characters")
        return v

    @field_validator("vat_registration_date")
    @classmethod
    def validate_vat_date(cls, v: Optional[date]) -> Optional[date]:
        """Validate VAT registration date is not in the future."""
        if v and v > date.today():
            raise ValueError("VAT registration date cannot be in the future")
        return v


class TaxSettingsCreate(TaxSettingsBase):
    """Schema for creating tax settings."""
    pass


class TaxSettingsUpdate(BaseModel):
    """Schema for updating tax settings."""
    is_vat_registered: Optional[bool] = None
    vat_registration_number: Optional[str] = Field(None, max_length=50)
    vat_registration_date: Optional[date] = None
    is_tot_eligible: Optional[bool] = None
    financial_year_start_month: Optional[int] = Field(None, ge=1, le=12)

    @field_validator("vat_registration_number")
    @classmethod
    def validate_vat_number(cls, v: Optional[str]) -> Optional[str]:
        """Validate VAT registration number format."""
        if v is None:
            return v
        v = v.strip().upper()
        if len(v) < 5 or len(v) > 50:
            raise ValueError("VAT registration number must be between 5 and 50 characters")
        return v

    @field_validator("vat_registration_date")
    @classmethod
    def validate_vat_date(cls, v: Optional[date]) -> Optional[date]:
        """Validate VAT registration date is not in the future."""
        if v and v > date.today():
            raise ValueError("VAT registration date cannot be in the future")
        return v


class TaxSettingsResponse(TaxSettingsBase):
    """Schema for tax settings responses."""
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime
    tax_type: str = Field(description="Current tax type: VAT, TOT, or None")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "business_id": "123e4567-e89b-12d3-a456-426614174001",
                "is_vat_registered": True,
                "vat_registration_number": "P051234567A",
                "vat_registration_date": "2024-01-15",
                "is_tot_eligible": False,
                "financial_year_start_month": 1,
                "tax_type": "VAT",
                "created_at": "2024-01-10T10:00:00",
                "updated_at": "2024-01-10T10:00:00"
            }
        }
    }


# VAT Summary Schemas
class VATSummaryRequest(BaseModel):
    """Request schema for VAT summary calculation."""
    period: TaxPeriod = Field(
        default=TaxPeriod.MONTH,
        description="Calculation period: month, quarter, or year"
    )
    start_date: date = Field(
        ...,
        description="Start date for VAT calculation (inclusive)"
    )
    end_date: date = Field(
        ...,
        description="End date for VAT calculation (inclusive)"
    )

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        """Validate end_date is after start_date."""
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class VATSummaryResponse(BaseModel):
    """Response schema for VAT summary."""
    period: str = Field(description="Period description (e.g., 'December 2024')")
    start_date: date
    end_date: date
    output_vat: Decimal = Field(
        description="Output VAT (collected from customers on sales)"
    )
    input_vat: Decimal = Field(
        description="Input VAT (paid on business expenses)"
    )
    net_vat: Decimal = Field(
        description="Net VAT payable to KRA (output - input). Positive = owe KRA, negative = refund"
    )
    total_sales: Decimal = Field(description="Total sales for period")
    total_expenses: Decimal = Field(description="Total expenses with VAT for period")
    vat_rate: Decimal = Field(default=Decimal("16.00"), description="VAT rate percentage")
    currency: str = Field(default="KES", description="Currency code")

    model_config = {
        "json_schema_extra": {
            "example": {
                "period": "December 2024",
                "start_date": "2024-12-01",
                "end_date": "2024-12-31",
                "output_vat": "48000.00",
                "input_vat": "12000.00",
                "net_vat": "36000.00",
                "total_sales": "300000.00",
                "total_expenses": "75000.00",
                "vat_rate": "16.00",
                "currency": "KES"
            }
        }
    }


# TOT Summary Schemas
class TOTSummaryRequest(BaseModel):
    """Request schema for TOT summary calculation."""
    period: TaxPeriod = Field(
        default=TaxPeriod.MONTH,
        description="Calculation period: month, quarter, or year"
    )
    start_date: date = Field(
        ...,
        description="Start date for TOT calculation (inclusive)"
    )
    end_date: date = Field(
        ...,
        description="End date for TOT calculation (inclusive)"
    )

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        """Validate end_date is after start_date."""
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class TOTSummaryResponse(BaseModel):
    """Response schema for TOT summary."""
    period: str = Field(description="Period description (e.g., 'December 2024')")
    start_date: date
    end_date: date
    gross_turnover: Decimal = Field(
        description="Gross turnover (total sales) for period"
    )
    tot_payable: Decimal = Field(
        description="TOT payable to KRA (1% of gross turnover)"
    )
    tot_rate: Decimal = Field(default=Decimal("1.00"), description="TOT rate percentage")
    currency: str = Field(default="KES", description="Currency code")

    model_config = {
        "json_schema_extra": {
            "example": {
                "period": "December 2024",
                "start_date": "2024-12-01",
                "end_date": "2024-12-31",
                "gross_turnover": "2500000.00",
                "tot_payable": "25000.00",
                "tot_rate": "1.00",
                "currency": "KES"
            }
        }
    }


# Filing Guidance Schema
class FilingGuidanceResponse(BaseModel):
    """Response schema for tax filing guidance."""
    tax_type: TaxType = Field(description="Current tax type for business")
    next_filing_date: Optional[date] = Field(
        description="Next filing deadline (20th of following month)"
    )
    filing_frequency: str = Field(
        default="Monthly",
        description="Filing frequency"
    )
    requirements: List[str] = Field(
        description="List of filing requirements and documents needed"
    )
    kra_portal_url: str = Field(
        default="https://itax.kra.go.ke",
        description="KRA iTax portal URL"
    )
    helpful_notes: List[str] = Field(
        description="Additional helpful notes for filing"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "tax_type": "VAT",
                "next_filing_date": "2025-01-20",
                "filing_frequency": "Monthly",
                "requirements": [
                    "VAT Return Form (iTax VAT 3)",
                    "Sales invoices register",
                    "Purchase invoices register",
                    "Bank statements",
                    "Payment proof for previous tax liability"
                ],
                "kra_portal_url": "https://itax.kra.go.ke",
                "helpful_notes": [
                    "File by 20th of following month to avoid penalties",
                    "Late filing penalty: KES 10,000 or 5% of tax due, whichever is higher",
                    "Keep all records for at least 5 years"
                ]
            }
        }
    }


# VAT Return Export Schema
class VATReturnExport(BaseModel):
    """Schema for VAT return data export in iTax format."""
    period_month: int = Field(description="Month number (1-12)")
    period_year: int = Field(description="Year")
    vat_registration_number: str = Field(description="VAT registration number")

    # Sales (Output VAT)
    standard_rated_sales: Decimal = Field(description="Standard rated sales (16%)")
    zero_rated_sales: Decimal = Field(default=Decimal("0.00"), description="Zero rated sales")
    exempt_sales: Decimal = Field(default=Decimal("0.00"), description="Exempt sales")
    output_vat: Decimal = Field(description="Total output VAT")

    # Purchases (Input VAT)
    standard_rated_purchases: Decimal = Field(description="Standard rated purchases (16%)")
    zero_rated_purchases: Decimal = Field(default=Decimal("0.00"), description="Zero rated purchases")
    exempt_purchases: Decimal = Field(default=Decimal("0.00"), description="Exempt purchases")
    input_vat: Decimal = Field(description="Total input VAT")

    # Summary
    net_vat: Decimal = Field(description="Net VAT payable/refundable")

    model_config = {
        "json_schema_extra": {
            "example": {
                "period_month": 12,
                "period_year": 2024,
                "vat_registration_number": "P051234567A",
                "standard_rated_sales": "300000.00",
                "zero_rated_sales": "0.00",
                "exempt_sales": "0.00",
                "output_vat": "48000.00",
                "standard_rated_purchases": "75000.00",
                "zero_rated_purchases": "0.00",
                "exempt_purchases": "0.00",
                "input_vat": "12000.00",
                "net_vat": "36000.00"
            }
        }
    }
