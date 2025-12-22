"""
Bank Import Pydantic Schemas

Request/response schemas for bank import and reconciliation endpoints.
Handles validation and serialization for bank statement imports.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from app.schemas.validators import sanitize_text_input


class FileType(str, Enum):
    """File type enumeration."""
    CSV = "csv"
    PDF = "pdf"


class ImportStatus(str, Enum):
    """Import status enumeration."""
    PENDING = "pending"
    PARSING = "parsing"
    MAPPING = "mapping"
    IMPORTING = "importing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReconciliationStatus(str, Enum):
    """Reconciliation status enumeration."""
    UNMATCHED = "unmatched"
    SUGGESTED = "suggested"
    MATCHED = "matched"
    IGNORED = "ignored"


# ============================================================================
# Bank Import Schemas
# ============================================================================

class BankImportCreate(BaseModel):
    """Schema for creating a bank import."""
    file_name: str = Field(..., min_length=1, max_length=255, description="Original filename")
    file_type: FileType = Field(..., description="File format: csv or pdf")
    source_bank: Optional[str] = Field(None, max_length=100, description="Bank name (e.g., Equity, KCB)")

    @field_validator("file_name")
    @classmethod
    def sanitize_file_name(cls, v: str) -> str:
        """Sanitize filename."""
        sanitized = sanitize_text_input(v, allow_html=False)
        if not sanitized:
            raise ValueError("Filename cannot be empty after sanitization")
        return sanitized

    @field_validator("source_bank")
    @classmethod
    def sanitize_source_bank(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize bank name."""
        return sanitize_text_input(v, allow_html=False)


class BankImportResponse(BaseModel):
    """Schema for bank import responses."""
    id: UUID
    business_id: UUID
    file_name: str
    file_type: str
    source_bank: Optional[str]
    status: str
    column_mapping: Optional[Dict[str, str]]
    total_rows: int
    imported_rows: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "business_id": "123e4567-e89b-12d3-a456-426614174001",
                "file_name": "equity_statement_dec2025.csv",
                "file_type": "csv",
                "source_bank": "Equity Bank",
                "status": "completed",
                "column_mapping": {
                    "date": "Transaction Date",
                    "description": "Details",
                    "debit": "Withdrawals",
                    "credit": "Deposits",
                    "balance": "Balance"
                },
                "total_rows": 150,
                "imported_rows": 150,
                "error_message": None,
                "created_at": "2025-12-07T10:00:00",
                "updated_at": "2025-12-07T10:05:00"
            }
        }
    }

    @property
    def import_progress(self) -> float:
        """Calculate import progress percentage."""
        if self.total_rows == 0:
            return 0.0
        return round((self.imported_rows / self.total_rows) * 100, 2)


class BankImportListResponse(BaseModel):
    """Schema for paginated bank import list response."""
    imports: List[BankImportResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Column Mapping Schemas
# ============================================================================

class ColumnMappingRequest(BaseModel):
    """Schema for configuring column mapping."""
    date_column: str = Field(..., min_length=1, description="Column name for transaction date")
    description_column: str = Field(..., min_length=1, description="Column name for description")
    debit_column: Optional[str] = Field(None, description="Column name for debit amount")
    credit_column: Optional[str] = Field(None, description="Column name for credit amount")
    balance_column: Optional[str] = Field(None, description="Column name for balance")
    reference_column: Optional[str] = Field(None, description="Column name for transaction reference")

    @field_validator("date_column", "description_column", "debit_column", "credit_column", "balance_column", "reference_column")
    @classmethod
    def sanitize_column_name(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize column name."""
        if v is None:
            return None
        sanitized = sanitize_text_input(v, allow_html=False)
        if v and not sanitized:
            raise ValueError("Column name cannot be empty after sanitization")
        return sanitized

    @classmethod
    def validate_at_least_one_amount(cls, values):
        """Validate that at least one amount column is specified."""
        if not values.get("debit_column") and not values.get("credit_column"):
            raise ValueError("At least one of debit_column or credit_column must be specified")
        return values


class DetectedColumn(BaseModel):
    """Schema for detected column information."""
    column_name: str
    confidence: float = Field(..., ge=0, le=100, description="Detection confidence (0-100)")
    sample_values: List[str] = Field(..., max_length=5, description="Sample values from this column")


class ColumnDetectionResponse(BaseModel):
    """Schema for automatic column detection results."""
    date_column: Optional[DetectedColumn]
    description_column: Optional[DetectedColumn]
    debit_column: Optional[DetectedColumn]
    credit_column: Optional[DetectedColumn]
    balance_column: Optional[DetectedColumn]
    reference_column: Optional[DetectedColumn]
    all_columns: List[str] = Field(..., description="All available columns in the file")


# ============================================================================
# Bank Transaction Schemas
# ============================================================================

class BankTransactionResponse(BaseModel):
    """Schema for bank transaction responses."""
    id: UUID
    business_id: UUID
    bank_import_id: UUID
    transaction_date: date
    description: str
    reference: Optional[str]
    debit_amount: Optional[Decimal]
    credit_amount: Optional[Decimal]
    balance: Optional[Decimal]
    reconciliation_status: str
    matched_expense_id: Optional[UUID]
    matched_invoice_id: Optional[UUID]
    match_confidence: Optional[Decimal]
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "business_id": "123e4567-e89b-12d3-a456-426614174001",
                "bank_import_id": "123e4567-e89b-12d3-a456-426614174002",
                "transaction_date": "2025-12-05",
                "description": "M-PESA Payment - ABC Suppliers Ltd",
                "reference": "SH12345678",
                "debit_amount": "5000.00",
                "credit_amount": None,
                "balance": "45000.00",
                "reconciliation_status": "matched",
                "matched_expense_id": "123e4567-e89b-12d3-a456-426614174003",
                "matched_invoice_id": None,
                "match_confidence": "95.50",
                "created_at": "2025-12-07T10:00:00",
                "updated_at": "2025-12-07T10:00:00"
            }
        }
    }

    @property
    def transaction_amount(self) -> Optional[Decimal]:
        """Get the transaction amount."""
        return self.debit_amount if self.debit_amount else self.credit_amount

    @property
    def transaction_type(self) -> str:
        """Get the transaction type (debit or credit)."""
        return "debit" if self.debit_amount else "credit"


class BankTransactionListResponse(BaseModel):
    """Schema for paginated bank transaction list response."""
    transactions: List[BankTransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Reconciliation Schemas
# ============================================================================

class ReconciliationMatch(BaseModel):
    """Schema for a potential reconciliation match."""
    record_type: str = Field(..., description="Type of matched record: expense or invoice")
    record_id: UUID = Field(..., description="ID of matched record")
    record_date: date = Field(..., description="Date of matched record")
    record_amount: Decimal = Field(..., description="Amount of matched record")
    record_description: str = Field(..., description="Description of matched record")
    confidence: Decimal = Field(..., ge=0, le=100, description="Match confidence (0-100)")
    match_reasons: List[str] = Field(..., description="Reasons for the match")


class ReconciliationSuggestion(BaseModel):
    """Schema for reconciliation suggestions for a transaction."""
    transaction_id: UUID
    transaction_date: date
    transaction_description: str
    transaction_amount: Decimal
    suggested_matches: List[ReconciliationMatch]

    model_config = {
        "json_schema_extra": {
            "example": {
                "transaction_id": "123e4567-e89b-12d3-a456-426614174000",
                "transaction_date": "2025-12-05",
                "transaction_description": "M-PESA Payment - ABC Suppliers",
                "transaction_amount": "5000.00",
                "suggested_matches": [
                    {
                        "record_type": "expense",
                        "record_id": "123e4567-e89b-12d3-a456-426614174001",
                        "record_date": "2025-12-05",
                        "record_amount": "5000.00",
                        "record_description": "Office supplies from ABC Suppliers",
                        "confidence": "95.50",
                        "match_reasons": [
                            "Exact amount match",
                            "Same date",
                            "Description contains 'ABC Suppliers'"
                        ]
                    }
                ]
            }
        }
    }


class MatchRequest(BaseModel):
    """Schema for confirming a reconciliation match."""
    record_type: str = Field(..., description="Type of record: expense or invoice")
    record_id: UUID = Field(..., description="ID of record to match")

    @field_validator("record_type")
    @classmethod
    def validate_record_type(cls, v: str) -> str:
        """Validate record type."""
        if v not in ["expense", "invoice"]:
            raise ValueError("record_type must be 'expense' or 'invoice'")
        return v


class UnmatchRequest(BaseModel):
    """Schema for unmatching a transaction."""
    reason: Optional[str] = Field(None, max_length=500, description="Reason for unmatching")

    @field_validator("reason")
    @classmethod
    def sanitize_reason(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize reason."""
        return sanitize_text_input(v, allow_html=False)


class IgnoreRequest(BaseModel):
    """Schema for ignoring a transaction."""
    reason: Optional[str] = Field(None, max_length=500, description="Reason for ignoring")

    @field_validator("reason")
    @classmethod
    def sanitize_reason(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize reason."""
        return sanitize_text_input(v, allow_html=False)


# ============================================================================
# Statistics Schemas
# ============================================================================

class ReconciliationStats(BaseModel):
    """Schema for reconciliation statistics."""
    total_transactions: int
    matched_count: int
    suggested_count: int
    unmatched_count: int
    ignored_count: int
    matched_percentage: float
    total_debit_amount: Decimal
    total_credit_amount: Decimal
    matched_debit_amount: Decimal
    matched_credit_amount: Decimal

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_transactions": 150,
                "matched_count": 120,
                "suggested_count": 15,
                "unmatched_count": 10,
                "ignored_count": 5,
                "matched_percentage": 80.0,
                "total_debit_amount": "250000.00",
                "total_credit_amount": "180000.00",
                "matched_debit_amount": "220000.00",
                "matched_credit_amount": "150000.00"
            }
        }
    }
