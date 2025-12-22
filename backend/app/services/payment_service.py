"""
Payment Service

Business logic for payment recording and management operations.
Handles payment CRUD and automatic invoice status updates.

Payment Rules:
- Payment amount must be positive
- Payment cannot exceed invoice balance due
- Cannot add payment to cancelled invoices
- When payment is created/deleted, invoice status is recalculated:
  - total_paid >= total_amount: status = "paid"
  - total_paid > 0 but < total_amount: status = "partially_paid"
  - total_paid = 0 and previously paid: status = "issued"

Security Notes:
- All operations are scoped to business_id
- Payments can only be linked to invoices in the same business
"""

from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID
from datetime import date
from decimal import Decimal

from sqlalchemy import select, update, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.payment import Payment, PaymentMethod
from app.models.invoice import Invoice, InvoiceStatus
from app.schemas.payment import PaymentResponse
from app.services.audit_service import AuditService


class PaymentService:
    """Service for payment database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize payment service.

        Args:
            db: Database session
        """
        self.db = db
        self.audit = AuditService(db)

    async def _recalculate_invoice_status(self, invoice_id: UUID, business_id: UUID) -> None:
        """
        Recalculate invoice status based on total payments.

        Updates invoice.amount_paid and invoice.status based on payment totals.
        This method should be called after any payment create/update/delete operation.

        Business Rules:
        - If total_paid >= total_amount: status = "paid"
        - If total_paid > 0 but < total_amount: status = "partially_paid"
        - If total_paid = 0 and invoice was previously paid/partially_paid: status = "issued"
        - Cannot change status of cancelled invoices

        Args:
            invoice_id: Invoice UUID
            business_id: Business UUID for security scoping
        """
        # Get invoice
        invoice_result = await self.db.execute(
            select(Invoice).where(
                Invoice.id == invoice_id,
                Invoice.business_id == business_id
            )
        )
        invoice = invoice_result.scalar_one_or_none()

        if not invoice:
            raise ValueError("Invoice not found")

        # Cannot update cancelled invoices
        if invoice.status == InvoiceStatus.CANCELLED.value:
            return

        # Calculate total paid from all payments
        total_paid_result = await self.db.execute(
            select(func.sum(Payment.amount)).where(
                Payment.invoice_id == invoice_id,
                Payment.business_id == business_id
            )
        )
        total_paid = total_paid_result.scalar() or Decimal("0.00")
        total_paid = Decimal(str(total_paid))

        # Determine new status based on payment amount
        total_amount = Decimal(str(invoice.total_amount))
        new_status = invoice.status

        if total_paid >= total_amount:
            # Fully paid
            new_status = InvoiceStatus.PAID.value
        elif total_paid > Decimal("0.00"):
            # Partially paid
            new_status = InvoiceStatus.PARTIALLY_PAID.value
        else:
            # No payments
            # If invoice was previously paid/partially_paid, revert to issued
            current_status = invoice.status if isinstance(invoice.status, str) else invoice.status.value
            if current_status in [InvoiceStatus.PAID.value, InvoiceStatus.PARTIALLY_PAID.value]:
                new_status = InvoiceStatus.ISSUED.value
            # Otherwise keep current status (e.g., draft, overdue)

        # Update invoice
        await self.db.execute(
            update(Invoice)
            .where(Invoice.id == invoice_id, Invoice.business_id == business_id)
            .values(
                amount_paid=total_paid,
                status=new_status
            )
        )
        # Flush to ensure the update is persisted before commit
        await self.db.flush()
        # Note: commit is handled by the calling method to ensure proper transaction handling

    async def create_payment(
        self,
        business_id: UUID,
        invoice_id: UUID,
        amount: Decimal,
        payment_date: date,
        payment_method: PaymentMethod,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> Payment:
        """
        Create a new payment and update invoice status.

        Args:
            business_id: Business UUID
            invoice_id: Invoice UUID
            amount: Payment amount (must be positive)
            payment_date: Date payment was received
            payment_method: Payment method
            reference_number: Optional payment reference
            notes: Optional notes
            user_id: Optional user ID for audit logging
            ip_address: Optional IP address for audit logging

        Returns:
            Created payment model

        Raises:
            ValueError: If validation fails or payment exceeds balance
        """
        # Verify invoice exists and belongs to business
        invoice_result = await self.db.execute(
            select(Invoice).where(
                Invoice.id == invoice_id,
                Invoice.business_id == business_id
            )
        )
        invoice = invoice_result.scalar_one_or_none()

        if not invoice:
            raise ValueError("Invoice not found or does not belong to this business")

        # Cannot add payment to cancelled invoices
        if invoice.status == InvoiceStatus.CANCELLED.value:
            raise ValueError("Cannot add payment to cancelled invoice")

        # Validate payment amount does not exceed balance due
        current_balance = invoice.balance_due
        if amount > current_balance:
            raise ValueError(
                f"Payment amount ({amount}) exceeds invoice balance due ({current_balance})"
            )

        # Create payment
        payment = Payment(
            business_id=business_id,
            invoice_id=invoice_id,
            amount=amount,
            payment_date=payment_date,
            payment_method=payment_method.value if hasattr(payment_method, 'value') else payment_method,
            reference_number=reference_number,
            notes=notes
        )

        self.db.add(payment)
        await self.db.flush()

        # Log the payment creation
        if user_id:
            await self.audit.log_create(
                user_id=user_id,
                resource_type="payment",
                resource_id=payment.id,
                new_values={
                    "invoice_id": str(invoice_id),
                    "amount": float(amount),
                    "payment_date": str(payment_date),
                    "payment_method": payment_method.value if hasattr(payment_method, 'value') else payment_method,
                    "reference_number": reference_number
                },
                ip_address=ip_address,
                details={"invoice_number": invoice.invoice_number}
            )

        # Recalculate invoice status
        await self._recalculate_invoice_status(invoice_id, business_id)

        # Commit the entire transaction (payment + invoice update)
        await self.db.commit()

        await self.db.refresh(payment)
        return payment

    async def get_payment_by_id(
        self,
        payment_id: UUID,
        business_id: UUID
    ) -> Optional[Payment]:
        """
        Get payment by ID with business scoping.

        Args:
            payment_id: Payment UUID
            business_id: Business UUID for security scoping

        Returns:
            Payment model or None if not found
        """
        result = await self.db.execute(
            select(Payment).where(
                Payment.id == payment_id,
                Payment.business_id == business_id
            )
        )
        return result.scalar_one_or_none()

    async def list_payments(
        self,
        business_id: UUID,
        page: int = 1,
        page_size: int = 50,
        invoice_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        payment_method: Optional[PaymentMethod] = None
    ) -> Tuple[List[Payment], int]:
        """
        List payments with pagination and filtering.

        Args:
            business_id: Business UUID for security scoping
            page: Page number (1-indexed)
            page_size: Number of items per page
            invoice_id: Optional filter by invoice
            start_date: Optional filter by payment_date >= start_date
            end_date: Optional filter by payment_date <= end_date
            payment_method: Optional filter by payment method

        Returns:
            Tuple of (payments list, total count)
        """
        # Build base query
        query = select(Payment).where(Payment.business_id == business_id)

        # Apply filters
        if invoice_id:
            query = query.where(Payment.invoice_id == invoice_id)

        if start_date:
            query = query.where(Payment.payment_date >= start_date)

        if end_date:
            query = query.where(Payment.payment_date <= end_date)

        if payment_method:
            method_value = payment_method.value if hasattr(payment_method, 'value') else payment_method
            query = query.where(Payment.payment_method == method_value)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Order by payment_date descending (newest first)
        query = query.order_by(Payment.payment_date.desc(), Payment.created_at.desc())

        # Execute query
        result = await self.db.execute(query)
        payments = result.scalars().all()

        return list(payments), total

    async def list_payments_for_invoice(
        self,
        invoice_id: UUID,
        business_id: UUID
    ) -> List[Payment]:
        """
        Get all payments for a specific invoice.

        Args:
            invoice_id: Invoice UUID
            business_id: Business UUID for security scoping

        Returns:
            List of payments for the invoice
        """
        result = await self.db.execute(
            select(Payment)
            .where(
                Payment.invoice_id == invoice_id,
                Payment.business_id == business_id
            )
            .order_by(Payment.payment_date.asc(), Payment.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_total_paid_for_invoice(
        self,
        invoice_id: UUID,
        business_id: UUID
    ) -> Decimal:
        """
        Calculate total amount paid for an invoice.

        Args:
            invoice_id: Invoice UUID
            business_id: Business UUID for security scoping

        Returns:
            Total amount paid as Decimal
        """
        result = await self.db.execute(
            select(func.sum(Payment.amount)).where(
                Payment.invoice_id == invoice_id,
                Payment.business_id == business_id
            )
        )
        total = result.scalar() or Decimal("0.00")
        return Decimal(str(total))

    async def delete_payment(
        self,
        payment_id: UUID,
        business_id: UUID,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Delete a payment and recalculate invoice status.

        Args:
            payment_id: Payment UUID
            business_id: Business UUID for security scoping
            user_id: Optional user ID for audit logging
            ip_address: Optional IP address for audit logging

        Returns:
            True if payment was deleted, False if not found

        Note: This will automatically recalculate the invoice status
        """
        # Get payment to verify it exists and get invoice_id
        payment = await self.get_payment_by_id(payment_id, business_id)

        if not payment:
            return False

        invoice_id = payment.invoice_id

        # Log the deletion
        if user_id:
            await self.audit.log_delete(
                user_id=user_id,
                resource_type="payment",
                resource_id=payment_id,
                old_values={
                    "invoice_id": str(payment.invoice_id),
                    "amount": float(payment.amount),
                    "payment_date": str(payment.payment_date),
                    "payment_method": payment.payment_method
                },
                ip_address=ip_address
            )

        # Delete payment
        await self.db.execute(
            delete(Payment).where(
                Payment.id == payment_id,
                Payment.business_id == business_id
            )
        )

        # Recalculate invoice status
        await self._recalculate_invoice_status(invoice_id, business_id)

        # Commit the entire transaction (delete + invoice update)
        await self.db.commit()

        return True

    def payment_to_response(self, payment: Payment) -> PaymentResponse:
        """
        Convert Payment model to PaymentResponse schema.

        Args:
            payment: Payment model

        Returns:
            PaymentResponse schema
        """
        return PaymentResponse(
            id=payment.id,
            business_id=payment.business_id,
            invoice_id=payment.invoice_id,
            amount=payment.amount,
            payment_date=payment.payment_date,
            payment_method=payment.payment_method,
            reference_number=payment.reference_number,
            notes=payment.notes,
            created_at=payment.created_at,
            updated_at=payment.updated_at
        )


def get_payment_service(db: AsyncSession) -> PaymentService:
    """
    Get payment service instance.

    Args:
        db: Database session

    Returns:
        PaymentService instance
    """
    return PaymentService(db)
