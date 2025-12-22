"""
PDF Generation Service

Business logic for generating professional PDF documents from HTML templates.
Uses WeasyPrint for HTML-to-PDF conversion and Jinja2 for template rendering.

Features:
- Invoice PDF generation with Kenya tax compliance
- Payment receipt PDF generation
- Financial report PDFs (P&L, Expense Summary, Aged Receivables)
- Professional formatting with Kenyan locale (KES currency)
- Page numbers and proper styling

Security Notes:
- All operations are scoped to business_id
- Validates data before rendering
- Proper error handling for missing data
"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
import os
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from jinja2 import Environment, FileSystemLoader, Template
from weasyprint import HTML

from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.business import Business
from app.models.contact import Contact


class PDFService:
    """Service for PDF document generation."""

    def __init__(self, db: AsyncSession):
        """
        Initialize PDF service.

        Args:
            db: Database session
        """
        self.db = db

        # Setup Jinja2 template environment
        template_dir = Path(__file__).parent.parent / "templates"
        self.template_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )

        # Add custom filters
        self.template_env.filters['format_currency'] = self._format_currency
        self.template_env.filters['format_date'] = self._format_date
        self.template_env.filters['format_number'] = self._format_number
        self.template_env.filters['format_percentage'] = self._format_percentage

    def _format_currency(self, value: Decimal) -> str:
        """
        Format decimal as Kenyan currency (KES with commas).

        Args:
            value: Decimal amount

        Returns:
            Formatted string (e.g., "KES 1,234.56")
        """
        if value is None:
            return "KES 0.00"

        amount = Decimal(str(value))
        # Format with commas for thousands
        return f"KES {amount:,.2f}"

    def _format_number(self, value: Decimal) -> str:
        """
        Format decimal as number with commas.

        Args:
            value: Decimal number

        Returns:
            Formatted string (e.g., "1,234.56")
        """
        if value is None:
            return "0.00"

        amount = Decimal(str(value))
        return f"{amount:,.2f}"

    def _format_date(self, value: date) -> str:
        """
        Format date in readable format.

        Args:
            value: Date object

        Returns:
            Formatted date string (e.g., "December 9, 2025")
        """
        if value is None:
            return "N/A"

        if isinstance(value, str):
            value = datetime.fromisoformat(value).date()

        return value.strftime("%B %d, %Y")

    def _format_percentage(self, value: Decimal) -> str:
        """
        Format decimal as percentage.

        Args:
            value: Decimal percentage

        Returns:
            Formatted string (e.g., "16.00%")
        """
        if value is None:
            return "0.00%"

        amount = Decimal(str(value))
        return f"{amount:.2f}%"

    async def _get_business(self, business_id: UUID) -> Optional[Business]:
        """
        Get business by ID.

        Args:
            business_id: Business UUID

        Returns:
            Business model or None
        """
        result = await self.db.execute(
            select(Business).where(Business.id == business_id)
        )
        return result.scalar_one_or_none()

    async def generate_invoice_pdf(
        self,
        invoice_id: UUID,
        business_id: UUID
    ) -> bytes:
        """
        Generate PDF for an invoice.

        Args:
            invoice_id: Invoice UUID
            business_id: Business UUID for security scoping

        Returns:
            PDF bytes

        Raises:
            ValueError: If invoice or business not found
        """
        # Get invoice with line items and contact
        result = await self.db.execute(
            select(Invoice)
            .where(Invoice.id == invoice_id, Invoice.business_id == business_id)
            .options(selectinload(Invoice.line_items))
        )
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise ValueError("Invoice not found")

        # Get business
        business = await self._get_business(business_id)
        if not business:
            raise ValueError("Business not found")

        # Get contact
        contact_result = await self.db.execute(
            select(Contact).where(Contact.id == invoice.contact_id)
        )
        contact = contact_result.scalar_one_or_none()

        if not contact:
            raise ValueError("Contact not found")

        # Prepare template data
        template_data = {
            'business': {
                'business_name': business.name,
                'kra_pin': business.kra_pin_encrypted or 'N/A',  # Would decrypt in production
                'address': business.full_address,
                'phone': business.phone or '',
                'email': business.email or ''
            },
            'contact': {
                'name': contact.name,
                'company_name': contact.name,
                'address': contact.address or '',
            },
            'invoice': {
                'invoice_number': invoice.invoice_number,
                'issue_date': invoice.issue_date,
                'due_date': invoice.due_date,
                'status': invoice.status,
                'subtotal': invoice.subtotal,
                'tax_amount': invoice.tax_amount,
                'total': invoice.total_amount,
                'amount_paid': invoice.amount_paid or Decimal("0.00"),
                'balance_due': invoice.balance_due,
                'notes': invoice.notes or '',
                'line_items': [
                    {
                        'description': item.description,
                        'quantity': item.quantity,
                        'unit_price': item.unit_price,
                        'tax_rate': item.tax_rate,
                        'total': item.line_total
                    }
                    for item in invoice.line_items
                ]
            },
            'generated_at': datetime.now()
        }

        # Render template
        template = self.template_env.get_template('invoice.html')
        html_content = template.render(**template_data)

        # Generate PDF
        pdf_bytes = HTML(string=html_content).write_pdf()

        return pdf_bytes

    async def generate_receipt_pdf(
        self,
        payment_id: UUID,
        business_id: UUID
    ) -> bytes:
        """
        Generate receipt PDF for a payment.

        Args:
            payment_id: Payment UUID
            business_id: Business UUID for security scoping

        Returns:
            PDF bytes

        Raises:
            ValueError: If payment or business not found
        """
        # Get payment with invoice and contact
        result = await self.db.execute(
            select(Payment)
            .where(Payment.id == payment_id, Payment.business_id == business_id)
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise ValueError("Payment not found")

        # Get business
        business = await self._get_business(business_id)
        if not business:
            raise ValueError("Business not found")

        # Get invoice
        invoice_result = await self.db.execute(
            select(Invoice).where(Invoice.id == payment.invoice_id)
        )
        invoice = invoice_result.scalar_one_or_none()

        if not invoice:
            raise ValueError("Invoice not found")

        # Get contact
        contact_result = await self.db.execute(
            select(Contact).where(Contact.id == invoice.contact_id)
        )
        contact = contact_result.scalar_one_or_none()

        if not contact:
            raise ValueError("Contact not found")

        # Prepare template data
        template_data = {
            'business': {
                'business_name': business.name,
                'kra_pin': business.kra_pin_encrypted or 'N/A',
                'address': business.full_address,
                'phone': business.phone or '',
                'email': business.email or ''
            },
            'contact': {
                'name': contact.name,
                'company_name': contact.name,
                'address': contact.address or '',
            },
            'payment': {
                'id': str(payment.id),
                'amount': payment.amount,
                'payment_date': payment.payment_date,
                'payment_method': payment.payment_method.replace('_', ' ').title(),
                'reference_number': payment.reference_number or 'N/A',
                'notes': payment.notes or ''
            },
            'invoice': {
                'invoice_number': invoice.invoice_number,
                'total_amount': invoice.total_amount,
                'amount_paid': invoice.amount_paid or Decimal("0.00"),
                'balance_due': invoice.balance_due
            },
            'generated_at': datetime.now()
        }

        # Render template
        template = self.template_env.get_template('receipt.html')
        html_content = template.render(**template_data)

        # Generate PDF
        pdf_bytes = HTML(string=html_content).write_pdf()

        return pdf_bytes

    async def generate_profit_loss_pdf(
        self,
        business_id: UUID,
        start_date: date,
        end_date: date
    ) -> bytes:
        """
        Generate P&L report PDF.

        Args:
            business_id: Business UUID
            start_date: Report start date
            end_date: Report end date

        Returns:
            PDF bytes

        Raises:
            ValueError: If business not found
        """
        # Get business
        business = await self._get_business(business_id)
        if not business:
            raise ValueError("Business not found")

        # Get report data from report service
        from app.services.report_service import ReportService
        report_service = ReportService(self.db)
        report = await report_service.generate_profit_loss(
            business_id=business_id,
            start_date=start_date,
            end_date=end_date
        )

        # Prepare template data
        template_data = {
            'business': {
                'business_name': business.name,
                'kra_pin': business.kra_pin_encrypted or 'N/A',
                'address': business.full_address
            },
            'report': report.model_dump(),
            'generated_at': datetime.now()
        }

        # Render template
        template = self.template_env.get_template('profit_loss.html')
        html_content = template.render(**template_data)

        # Generate PDF
        pdf_bytes = HTML(string=html_content).write_pdf()

        return pdf_bytes

    async def generate_expense_summary_pdf(
        self,
        business_id: UUID,
        start_date: date,
        end_date: date
    ) -> bytes:
        """
        Generate expense summary PDF.

        Args:
            business_id: Business UUID
            start_date: Report start date
            end_date: Report end date

        Returns:
            PDF bytes

        Raises:
            ValueError: If business not found
        """
        # Get business
        business = await self._get_business(business_id)
        if not business:
            raise ValueError("Business not found")

        # Get report data from report service
        from app.services.report_service import ReportService
        report_service = ReportService(self.db)
        report = await report_service.generate_expense_summary(
            business_id=business_id,
            start_date=start_date,
            end_date=end_date
        )

        # Prepare template data
        template_data = {
            'business': {
                'business_name': business.name,
                'kra_pin': business.kra_pin_encrypted or 'N/A',
                'address': business.full_address
            },
            'report': report.model_dump(),
            'generated_at': datetime.now()
        }

        # Render template
        template = self.template_env.get_template('expense_summary.html')
        html_content = template.render(**template_data)

        # Generate PDF
        pdf_bytes = HTML(string=html_content).write_pdf()

        return pdf_bytes

    async def generate_aged_receivables_pdf(
        self,
        business_id: UUID,
        as_of_date: date
    ) -> bytes:
        """
        Generate aged receivables PDF.

        Args:
            business_id: Business UUID
            as_of_date: Report date

        Returns:
            PDF bytes

        Raises:
            ValueError: If business not found
        """
        # Get business
        business = await self._get_business(business_id)
        if not business:
            raise ValueError("Business not found")

        # Get report data from report service
        from app.services.report_service import ReportService
        report_service = ReportService(self.db)
        report = await report_service.generate_aged_receivables(
            business_id=business_id,
            as_of_date=as_of_date
        )

        # Prepare template data
        template_data = {
            'business': {
                'business_name': business.name,
                'kra_pin': business.kra_pin_encrypted or 'N/A',
                'address': business.full_address
            },
            'report': report.model_dump(),
            'generated_at': datetime.now()
        }

        # Render template
        template = self.template_env.get_template('aged_receivables.html')
        html_content = template.render(**template_data)

        # Generate PDF
        pdf_bytes = HTML(string=html_content).write_pdf()

        return pdf_bytes


def get_pdf_service(db: AsyncSession) -> PDFService:
    """
    Get PDF service instance.

    Args:
        db: Database session

    Returns:
        PDFService instance
    """
    return PDFService(db)
