"""
Tax Service

Business logic for Kenya tax compliance operations.
Handles VAT (16%) and TOT (1%) calculations with KRA filing requirements.

Kenya Tax Rules:
- VAT Rate: 16% (standard rate)
- VAT Threshold: KES 5 million annual turnover
- TOT Rate: 1% of gross turnover
- TOT Eligibility: KES 1-50 million annual turnover
- Filing Deadline: 20th of following month

Features:
- Tax settings management (VAT/TOT registration)
- VAT summary calculation (output VAT - input VAT)
- TOT summary calculation (1% of gross turnover)
- Filing guidance and deadlines
- VAT return export in iTax format

Security Notes:
- All operations are scoped to business_id
- VAT registration numbers are sensitive data
- Proper error handling with ValueError
"""

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import date, datetime, timedelta
from decimal import Decimal
import calendar

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tax_settings import TaxSettings
from app.models.invoice import Invoice, InvoiceStatus
from app.models.invoice_item import InvoiceItem
from app.models.expense import Expense
from app.schemas.tax import (
    TaxSettingsResponse,
    VATSummaryResponse,
    TOTSummaryResponse,
    FilingGuidanceResponse,
    VATReturnExport,
    TaxType,
    TaxPeriod
)


class TaxService:
    """Service for tax calculation and compliance operations."""

    # Kenya tax constants
    VAT_RATE = Decimal("16.00")  # 16% VAT
    TOT_RATE = Decimal("1.00")   # 1% TOT
    VAT_THRESHOLD = Decimal("5000000.00")  # KES 5M annual turnover
    TOT_MIN_THRESHOLD = Decimal("1000000.00")  # KES 1M
    TOT_MAX_THRESHOLD = Decimal("50000000.00")  # KES 50M

    def __init__(self, db: AsyncSession):
        """
        Initialize tax service.

        Args:
            db: Database session
        """
        self.db = db

    async def get_tax_settings(
        self,
        business_id: UUID
    ) -> Optional[TaxSettings]:
        """
        Get tax settings for a business, create default if not exists.

        Args:
            business_id: Business UUID

        Returns:
            TaxSettings model
        """
        result = await self.db.execute(
            select(TaxSettings).where(
                TaxSettings.business_id == business_id
            )
        )
        settings = result.scalar_one_or_none()

        # Create default settings if none exist
        if not settings:
            settings = TaxSettings(
                business_id=business_id,
                is_vat_registered=False,
                is_tot_eligible=False,
                financial_year_start_month=1
            )
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)

        return settings

    async def update_tax_settings(
        self,
        business_id: UUID,
        data: Dict[str, Any]
    ) -> TaxSettings:
        """
        Update tax settings for a business.

        Args:
            business_id: Business UUID
            data: Dictionary of fields to update

        Returns:
            Updated TaxSettings model

        Raises:
            ValueError: If data is invalid
        """
        settings = await self.get_tax_settings(business_id)

        # Validate business rules
        if data.get("is_vat_registered") and data.get("is_tot_eligible"):
            raise ValueError(
                "Business cannot be both VAT registered and TOT eligible. "
                "Choose one tax regime."
            )

        # Validate VAT registration number is provided if VAT registered
        if data.get("is_vat_registered"):
            if not data.get("vat_registration_number") and not settings.vat_registration_number:
                raise ValueError("VAT registration number is required when registering for VAT")

        # Update fields
        for key, value in data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)

        await self.db.commit()
        await self.db.refresh(settings)

        return settings

    async def calculate_vat_summary(
        self,
        business_id: UUID,
        start_date: date,
        end_date: date,
        period: TaxPeriod = TaxPeriod.MONTH
    ) -> VATSummaryResponse:
        """
        Calculate VAT summary for a period.

        VAT Calculation:
        - Output VAT: Sum of VAT collected from customers on sales (invoice tax_amount)
        - Input VAT: Sum of VAT paid on business expenses (expense tax_amount)
        - Net VAT: Output VAT - Input VAT (positive = owe KRA, negative = refund)

        Args:
            business_id: Business UUID
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            period: Tax period type

        Returns:
            VATSummaryResponse with VAT calculations
        """
        # Calculate Output VAT (from invoices that are issued or paid)
        output_vat_query = await self.db.execute(
            select(
                func.coalesce(func.sum(Invoice.tax_amount), 0).label("output_vat"),
                func.coalesce(func.sum(Invoice.total_amount), 0).label("total_sales")
            )
            .where(
                Invoice.business_id == business_id,
                Invoice.status.in_([
                    InvoiceStatus.ISSUED.value,
                    InvoiceStatus.PAID.value,
                    InvoiceStatus.PARTIALLY_PAID.value
                ]),
                Invoice.issue_date >= start_date,
                Invoice.issue_date <= end_date
            )
        )
        output_result = output_vat_query.first()
        output_vat = Decimal(str(output_result.output_vat or 0))
        total_sales = Decimal(str(output_result.total_sales or 0))

        # Calculate Input VAT (from expenses with VAT)
        input_vat_query = await self.db.execute(
            select(
                func.coalesce(func.sum(Expense.tax_amount), 0).label("input_vat"),
                func.coalesce(func.sum(Expense.amount + Expense.tax_amount), 0).label("total_expenses")
            )
            .where(
                Expense.business_id == business_id,
                Expense.is_active == True,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
                Expense.tax_amount > 0  # Only expenses with VAT
            )
        )
        input_result = input_vat_query.first()
        input_vat = Decimal(str(input_result.input_vat or 0))
        total_expenses = Decimal(str(input_result.total_expenses or 0))

        # Calculate Net VAT
        net_vat = output_vat - input_vat

        # Generate period description
        period_desc = self._format_period_description(start_date, end_date, period)

        return VATSummaryResponse(
            period=period_desc,
            start_date=start_date,
            end_date=end_date,
            output_vat=round(output_vat, 2),
            input_vat=round(input_vat, 2),
            net_vat=round(net_vat, 2),
            total_sales=round(total_sales, 2),
            total_expenses=round(total_expenses, 2),
            vat_rate=self.VAT_RATE,
            currency="KES"
        )

    async def calculate_tot_summary(
        self,
        business_id: UUID,
        start_date: date,
        end_date: date,
        period: TaxPeriod = TaxPeriod.MONTH
    ) -> TOTSummaryResponse:
        """
        Calculate TOT (Turnover Tax) summary for a period.

        TOT Calculation:
        - Gross Turnover: Sum of all invoice totals (regardless of payment status)
        - TOT Payable: Gross Turnover * 1% (0.01)

        Args:
            business_id: Business UUID
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            period: Tax period type

        Returns:
            TOTSummaryResponse with TOT calculations
        """
        # Calculate Gross Turnover (all issued/paid invoices)
        turnover_query = await self.db.execute(
            select(
                func.coalesce(func.sum(Invoice.total_amount), 0).label("gross_turnover")
            )
            .where(
                Invoice.business_id == business_id,
                Invoice.status.in_([
                    InvoiceStatus.ISSUED.value,
                    InvoiceStatus.PAID.value,
                    InvoiceStatus.PARTIALLY_PAID.value
                ]),
                Invoice.issue_date >= start_date,
                Invoice.issue_date <= end_date
            )
        )
        turnover_result = turnover_query.first()
        gross_turnover = Decimal(str(turnover_result.gross_turnover or 0))

        # Calculate TOT (1% of gross turnover)
        tot_payable = gross_turnover * (self.TOT_RATE / Decimal("100"))

        # Generate period description
        period_desc = self._format_period_description(start_date, end_date, period)

        return TOTSummaryResponse(
            period=period_desc,
            start_date=start_date,
            end_date=end_date,
            gross_turnover=round(gross_turnover, 2),
            tot_payable=round(tot_payable, 2),
            tot_rate=self.TOT_RATE,
            currency="KES"
        )

    async def get_filing_guidance(
        self,
        business_id: UUID
    ) -> FilingGuidanceResponse:
        """
        Get tax filing guidance and deadlines for a business.

        Args:
            business_id: Business UUID

        Returns:
            FilingGuidanceResponse with filing requirements
        """
        settings = await self.get_tax_settings(business_id)

        # Determine tax type
        if settings.is_vat_registered:
            tax_type = TaxType.VAT
        elif settings.is_tot_eligible:
            tax_type = TaxType.TOT
        else:
            tax_type = TaxType.NONE

        # Calculate next filing date (20th of next month)
        today = date.today()
        if today.day <= 20:
            # If before 20th, deadline is 20th of this month
            next_filing = date(today.year, today.month, 20)
        else:
            # If after 20th, deadline is 20th of next month
            if today.month == 12:
                next_filing = date(today.year + 1, 1, 20)
            else:
                next_filing = date(today.year, today.month + 1, 20)

        # Build requirements and notes based on tax type
        if tax_type == TaxType.VAT:
            requirements = [
                "VAT Return Form (iTax VAT 3)",
                "Sales invoices register",
                "Purchase invoices register with VAT details",
                "Bank statements for verification",
                "Payment proof for previous tax liability",
                "Credit/debit notes if applicable"
            ]
            helpful_notes = [
                "File by 20th of following month to avoid penalties",
                "Late filing penalty: KES 10,000 or 5% of tax due, whichever is higher",
                "Keep all records for at least 5 years",
                "Ensure all invoices have valid VAT registration numbers",
                "Input VAT is only claimable on business-related expenses"
            ]
        elif tax_type == TaxType.TOT:
            requirements = [
                "TOT Return Form (iTax TOT 1)",
                "Sales register/invoices",
                "Bank statements",
                "Payment proof for previous tax liability"
            ]
            helpful_notes = [
                "File by 20th of following month to avoid penalties",
                "Late filing penalty: KES 10,000 or 5% of tax due, whichever is higher",
                "TOT is 1% of gross turnover (changed from 3% in 2024)",
                "No input tax deductions allowed for TOT",
                "Keep all records for at least 5 years"
            ]
        else:
            requirements = [
                "Determine your annual turnover",
                "If turnover > KES 5M: Register for VAT",
                "If turnover KES 1-50M: Consider TOT registration",
                "Consult with KRA or tax advisor for guidance"
            ]
            helpful_notes = [
                "VAT registration is mandatory if turnover exceeds KES 5 million",
                "TOT is optional for businesses with turnover between KES 1-50 million",
                "You cannot be registered for both VAT and TOT simultaneously",
                "Visit KRA iTax portal to register: https://itax.kra.go.ke"
            ]
            next_filing = None  # No filing deadline if not registered

        return FilingGuidanceResponse(
            tax_type=tax_type,
            next_filing_date=next_filing,
            filing_frequency="Monthly",
            requirements=requirements,
            kra_portal_url="https://itax.kra.go.ke",
            helpful_notes=helpful_notes
        )

    async def export_vat_return(
        self,
        business_id: UUID,
        start_date: date,
        end_date: date
    ) -> VATReturnExport:
        """
        Export VAT return data in iTax format.

        Args:
            business_id: Business UUID
            start_date: Period start date
            end_date: Period end date

        Returns:
            VATReturnExport with iTax format fields

        Raises:
            ValueError: If business is not VAT registered
        """
        settings = await self.get_tax_settings(business_id)

        if not settings.is_vat_registered:
            raise ValueError("Business is not VAT registered. Cannot export VAT return.")

        if not settings.vat_registration_number:
            raise ValueError("VAT registration number not found.")

        # Get VAT summary
        vat_summary = await self.calculate_vat_summary(
            business_id,
            start_date,
            end_date,
            TaxPeriod.MONTH
        )

        # For now, assume all sales/purchases are standard rated
        # In a full implementation, you would query for zero-rated and exempt transactions
        standard_rated_sales = vat_summary.total_sales - vat_summary.output_vat
        standard_rated_purchases = vat_summary.total_expenses - vat_summary.input_vat

        return VATReturnExport(
            period_month=start_date.month,
            period_year=start_date.year,
            vat_registration_number=settings.vat_registration_number,
            standard_rated_sales=round(standard_rated_sales, 2),
            zero_rated_sales=Decimal("0.00"),
            exempt_sales=Decimal("0.00"),
            output_vat=vat_summary.output_vat,
            standard_rated_purchases=round(standard_rated_purchases, 2),
            zero_rated_purchases=Decimal("0.00"),
            exempt_purchases=Decimal("0.00"),
            input_vat=vat_summary.input_vat,
            net_vat=vat_summary.net_vat
        )

    def _format_period_description(
        self,
        start_date: date,
        end_date: date,
        period: TaxPeriod
    ) -> str:
        """
        Format a human-readable period description.

        Args:
            start_date: Period start
            end_date: Period end
            period: Period type

        Returns:
            Formatted period string
        """
        if period == TaxPeriod.MONTH:
            return f"{calendar.month_name[start_date.month]} {start_date.year}"
        elif period == TaxPeriod.QUARTER:
            quarter = (start_date.month - 1) // 3 + 1
            return f"Q{quarter} {start_date.year}"
        elif period == TaxPeriod.YEAR:
            return f"FY {start_date.year}"
        else:
            return f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"

    def settings_to_response(self, settings: TaxSettings) -> TaxSettingsResponse:
        """
        Convert TaxSettings model to TaxSettingsResponse schema.

        Args:
            settings: TaxSettings model

        Returns:
            TaxSettingsResponse schema
        """
        return TaxSettingsResponse(
            id=settings.id,
            business_id=settings.business_id,
            is_vat_registered=settings.is_vat_registered,
            vat_registration_number=settings.vat_registration_number,
            vat_registration_date=settings.vat_registration_date,
            is_tot_eligible=settings.is_tot_eligible,
            financial_year_start_month=settings.financial_year_start_month,
            tax_type=settings.tax_type,
            created_at=settings.created_at,
            updated_at=settings.updated_at
        )


def get_tax_service(db: AsyncSession) -> TaxService:
    """
    Get tax service instance.

    Args:
        db: Database session

    Returns:
        TaxService instance
    """
    return TaxService(db)
