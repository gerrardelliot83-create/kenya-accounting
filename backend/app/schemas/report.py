"""
Report Pydantic Schemas

Request/response schemas for financial report generation endpoints.
Supports Profit & Loss, Expense Summary, Aged Receivables, and Sales Summary reports.
"""

from datetime import datetime, date
from typing import Optional, List, Dict
from uuid import UUID
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ReportFormat(str, Enum):
    """Report output format enumeration."""
    JSON = "json"
    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"


class ReportType(str, Enum):
    """Report type enumeration."""
    PROFIT_LOSS = "profit_loss"
    EXPENSE_SUMMARY = "expense_summary"
    AGED_RECEIVABLES = "aged_receivables"
    SALES_SUMMARY = "sales_summary"


# Report Request Schemas
class ReportRequest(BaseModel):
    """Base report request schema."""
    report_type: ReportType = Field(
        ...,
        description="Type of report to generate"
    )
    start_date: date = Field(
        ...,
        description="Report start date (inclusive)"
    )
    end_date: date = Field(
        ...,
        description="Report end date (inclusive)"
    )
    format: ReportFormat = Field(
        default=ReportFormat.JSON,
        description="Output format: json, pdf, csv, or excel"
    )

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        """Validate end_date is after start_date."""
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


# Profit & Loss Report Schemas
class ExpenseCategoryTotal(BaseModel):
    """Expense total for a category."""
    category: str = Field(description="Expense category name")
    total: Decimal = Field(description="Total amount for category")
    percentage: Decimal = Field(description="Percentage of total expenses")
    count: int = Field(description="Number of expenses in category")


class ProfitLossResponse(BaseModel):
    """Response schema for Profit & Loss statement."""
    report_type: str = Field(default="Profit & Loss Statement")
    start_date: date
    end_date: date
    currency: str = Field(default="KES")

    # Revenue
    total_revenue: Decimal = Field(
        description="Total revenue from paid invoices"
    )

    # Expenses
    expenses_by_category: List[ExpenseCategoryTotal] = Field(
        description="Expenses broken down by category"
    )
    total_expenses: Decimal = Field(description="Total expenses")

    # Profit calculations
    gross_profit: Decimal = Field(
        description="Gross profit (revenue - cost of goods sold)"
    )
    net_profit: Decimal = Field(
        description="Net profit (revenue - all expenses)"
    )

    # Margins
    gross_margin_percentage: Decimal = Field(
        description="Gross margin as percentage of revenue"
    )
    net_margin_percentage: Decimal = Field(
        description="Net margin as percentage of revenue"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "report_type": "Profit & Loss Statement",
                "start_date": "2024-12-01",
                "end_date": "2024-12-31",
                "currency": "KES",
                "total_revenue": "500000.00",
                "expenses_by_category": [
                    {
                        "category": "Office Supplies",
                        "total": "25000.00",
                        "percentage": "20.00",
                        "count": 5
                    },
                    {
                        "category": "Utilities",
                        "total": "15000.00",
                        "percentage": "12.00",
                        "count": 3
                    }
                ],
                "total_expenses": "125000.00",
                "gross_profit": "375000.00",
                "net_profit": "375000.00",
                "gross_margin_percentage": "75.00",
                "net_margin_percentage": "75.00"
            }
        }
    }


# Expense Summary Report Schemas
class ExpenseSummaryResponse(BaseModel):
    """Response schema for Expense Summary report."""
    report_type: str = Field(default="Expense Summary")
    start_date: date
    end_date: date
    currency: str = Field(default="KES")

    categories: List[ExpenseCategoryTotal] = Field(
        description="Expenses by category with totals and percentages"
    )
    total_expenses: Decimal = Field(description="Total expenses for period")
    total_tax: Decimal = Field(description="Total tax amount (VAT/TOT)")
    expense_count: int = Field(description="Total number of expenses")

    # Additional insights
    average_expense: Decimal = Field(description="Average expense amount")
    largest_category: Optional[str] = Field(
        None,
        description="Category with highest spending"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "report_type": "Expense Summary",
                "start_date": "2024-12-01",
                "end_date": "2024-12-31",
                "currency": "KES",
                "categories": [
                    {
                        "category": "Office Supplies",
                        "total": "50000.00",
                        "percentage": "40.00",
                        "count": 10
                    },
                    {
                        "category": "Travel",
                        "total": "30000.00",
                        "percentage": "24.00",
                        "count": 5
                    }
                ],
                "total_expenses": "125000.00",
                "total_tax": "20000.00",
                "expense_count": 25,
                "average_expense": "5000.00",
                "largest_category": "Office Supplies"
            }
        }
    }


# Aged Receivables Report Schemas
class AgingBucket(BaseModel):
    """Aging bucket for receivables."""
    bucket_name: str = Field(description="Bucket name (e.g., '1-30 days')")
    amount: Decimal = Field(description="Total amount in bucket")
    invoice_count: int = Field(description="Number of invoices in bucket")
    percentage: Decimal = Field(description="Percentage of total receivables")


class AgedReceivablesResponse(BaseModel):
    """Response schema for Aged Receivables report."""
    report_type: str = Field(default="Aged Receivables")
    as_of_date: date = Field(description="Report date")
    currency: str = Field(default="KES")

    # Aging buckets
    current: AgingBucket = Field(description="Current (not yet due)")
    days_1_30: AgingBucket = Field(description="1-30 days overdue")
    days_31_60: AgingBucket = Field(description="31-60 days overdue")
    days_61_90: AgingBucket = Field(description="61-90 days overdue")
    days_over_90: AgingBucket = Field(description="Over 90 days overdue")

    # Summary
    total_receivables: Decimal = Field(description="Total outstanding receivables")
    total_invoice_count: int = Field(description="Total number of outstanding invoices")

    # Insights
    overdue_amount: Decimal = Field(description="Total overdue amount")
    overdue_percentage: Decimal = Field(description="Percentage of receivables that are overdue")

    model_config = {
        "json_schema_extra": {
            "example": {
                "report_type": "Aged Receivables",
                "as_of_date": "2024-12-31",
                "currency": "KES",
                "current": {
                    "bucket_name": "Current",
                    "amount": "150000.00",
                    "invoice_count": 5,
                    "percentage": "50.00"
                },
                "days_1_30": {
                    "bucket_name": "1-30 days",
                    "amount": "75000.00",
                    "invoice_count": 3,
                    "percentage": "25.00"
                },
                "days_31_60": {
                    "bucket_name": "31-60 days",
                    "amount": "50000.00",
                    "invoice_count": 2,
                    "percentage": "16.67"
                },
                "days_61_90": {
                    "bucket_name": "61-90 days",
                    "amount": "25000.00",
                    "invoice_count": 1,
                    "percentage": "8.33"
                },
                "days_over_90": {
                    "bucket_name": "Over 90 days",
                    "amount": "0.00",
                    "invoice_count": 0,
                    "percentage": "0.00"
                },
                "total_receivables": "300000.00",
                "total_invoice_count": 11,
                "overdue_amount": "150000.00",
                "overdue_percentage": "50.00"
            }
        }
    }


# Sales Summary Report Schemas
class CustomerSales(BaseModel):
    """Sales by customer."""
    customer_id: UUID
    customer_name: str
    total_sales: Decimal
    invoice_count: int
    percentage: Decimal = Field(description="Percentage of total sales")


class ItemSales(BaseModel):
    """Sales by item/service."""
    item_id: Optional[UUID] = Field(None, description="Item ID (None for custom items)")
    item_name: str
    quantity_sold: Decimal
    total_sales: Decimal
    percentage: Decimal = Field(description="Percentage of total sales")


class SalesSummaryResponse(BaseModel):
    """Response schema for Sales Summary report."""
    report_type: str = Field(default="Sales Summary")
    start_date: date
    end_date: date
    currency: str = Field(default="KES")

    # By customer
    by_customer: List[CustomerSales] = Field(
        description="Sales breakdown by customer"
    )
    top_customer: Optional[CustomerSales] = Field(
        None,
        description="Customer with highest sales"
    )

    # By item
    by_item: List[ItemSales] = Field(
        description="Sales breakdown by item/service"
    )
    top_item: Optional[ItemSales] = Field(
        None,
        description="Item with highest sales"
    )

    # Summary
    total_sales: Decimal = Field(description="Total sales for period")
    total_invoices: int = Field(description="Total number of invoices")
    average_invoice_value: Decimal = Field(description="Average invoice value")
    customer_count: int = Field(description="Number of unique customers")

    model_config = {
        "json_schema_extra": {
            "example": {
                "report_type": "Sales Summary",
                "start_date": "2024-12-01",
                "end_date": "2024-12-31",
                "currency": "KES",
                "by_customer": [
                    {
                        "customer_id": "123e4567-e89b-12d3-a456-426614174000",
                        "customer_name": "ABC Corporation",
                        "total_sales": "200000.00",
                        "invoice_count": 5,
                        "percentage": "40.00"
                    }
                ],
                "top_customer": {
                    "customer_id": "123e4567-e89b-12d3-a456-426614174000",
                    "customer_name": "ABC Corporation",
                    "total_sales": "200000.00",
                    "invoice_count": 5,
                    "percentage": "40.00"
                },
                "by_item": [
                    {
                        "item_id": "123e4567-e89b-12d3-a456-426614174001",
                        "item_name": "Consulting Services",
                        "quantity_sold": "50.00",
                        "total_sales": "250000.00",
                        "percentage": "50.00"
                    }
                ],
                "top_item": {
                    "item_id": "123e4567-e89b-12d3-a456-426614174001",
                    "item_name": "Consulting Services",
                    "quantity_sold": "50.00",
                    "total_sales": "250000.00",
                    "percentage": "50.00"
                },
                "total_sales": "500000.00",
                "total_invoices": 15,
                "average_invoice_value": "33333.33",
                "customer_count": 8
            }
        }
    }


# Export Response Schema
class ReportExportResponse(BaseModel):
    """Response schema for report export."""
    success: bool
    report_type: str
    format: str
    file_url: Optional[str] = Field(
        None,
        description="URL to download the exported file (for PDF/CSV/Excel)"
    )
    data: Optional[Dict] = Field(
        None,
        description="Report data (for JSON format)"
    )
    generated_at: datetime = Field(description="Timestamp when report was generated")
    expires_at: Optional[datetime] = Field(
        None,
        description="Expiry time for download URL"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "report_type": "profit_loss",
                "format": "pdf",
                "file_url": "https://storage.example.com/reports/pl-2024-12.pdf",
                "data": None,
                "generated_at": "2024-12-31T15:30:00",
                "expires_at": "2025-01-07T15:30:00"
            }
        }
    }
