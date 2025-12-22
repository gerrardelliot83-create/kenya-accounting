"""
Invoice Service

Business logic for invoice management operations.
Handles invoice CRUD with strict status workflow enforcement and auto number generation.

Invoice Number Format: INV-{year}-{sequence} (e.g., INV-2025-00001)

Status Workflow:
- draft -> issued -> paid OR cancelled
- Issued invoices can become paid or cancelled
- Paid and cancelled are terminal states

Security Notes:
- All operations are scoped to business_id
- Status transitions are strictly enforced
- Only draft invoices can be edited
"""

from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import select, update, func, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.invoice import Invoice, InvoiceStatus
from app.models.invoice_item import InvoiceItem
from app.models.contact import Contact
from app.schemas.invoice import InvoiceResponse, InvoiceDetailResponse, InvoiceItemResponse
from app.services.audit_service import AuditService


class InvoiceService:
    """Service for invoice database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize invoice service.

        Args:
            db: Database session
        """
        self.db = db
        self.audit = AuditService(db)

    async def _generate_invoice_number(self, business_id: UUID) -> str:
        """
        Generate unique invoice number in format INV-{year}-{sequence}.

        The sequence resets annually for each business.
        Uses SELECT FOR UPDATE to prevent race conditions.

        Args:
            business_id: Business UUID

        Returns:
            Generated invoice number (e.g., INV-2025-00001)
        """
        current_year = datetime.utcnow().year

        # Use SELECT FOR UPDATE to lock the row and prevent race conditions
        # Get the highest sequence number for this business and year
        result = await self.db.execute(
            select(Invoice.invoice_number)
            .where(
                Invoice.business_id == business_id,
                Invoice.invoice_number.like(f"INV-{current_year}-%")
            )
            .order_by(Invoice.invoice_number.desc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        max_number = result.scalar_one_or_none()

        if max_number:
            # Extract sequence from last invoice number (INV-2025-00001 -> 00001)
            sequence = int(max_number.split("-")[-1]) + 1
        else:
            # First invoice for this year
            sequence = 1

        # Format with zero padding (5 digits)
        return f"INV-{current_year}-{sequence:05d}"

    def _calculate_invoice_totals(self, line_items: List[InvoiceItem]) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Calculate invoice totals from line items.

        Args:
            line_items: List of invoice line items

        Returns:
            Tuple of (subtotal, tax_amount, total_amount)
        """
        subtotal = Decimal("0.00")
        tax_amount = Decimal("0.00")

        for item in line_items:
            item_subtotal = item.quantity * item.unit_price
            item_tax = item_subtotal * (item.tax_rate / Decimal("100"))

            subtotal += item_subtotal
            tax_amount += item_tax

        total_amount = subtotal + tax_amount

        return (
            round(subtotal, 2),
            round(tax_amount, 2),
            round(total_amount, 2)
        )

    async def get_invoice_by_id(
        self,
        invoice_id: UUID,
        business_id: UUID,
        include_line_items: bool = False
    ) -> Optional[Invoice]:
        """
        Get invoice by ID with business scoping.

        Args:
            invoice_id: Invoice UUID
            business_id: Business UUID for security scoping
            include_line_items: Whether to load line items

        Returns:
            Invoice model or None if not found
        """
        query = select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.business_id == business_id
        )

        if include_line_items:
            query = query.options(selectinload(Invoice.line_items))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_invoice_by_number(
        self,
        invoice_number: str,
        business_id: UUID
    ) -> Optional[Invoice]:
        """
        Get invoice by invoice number with business scoping.

        Args:
            invoice_number: Invoice number
            business_id: Business UUID for security scoping

        Returns:
            Invoice model or None if not found
        """
        result = await self.db.execute(
            select(Invoice).where(
                Invoice.invoice_number == invoice_number,
                Invoice.business_id == business_id
            )
        )
        return result.scalar_one_or_none()

    async def list_invoices(
        self,
        business_id: UUID,
        page: int = 1,
        page_size: int = 50,
        status: Optional[InvoiceStatus] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        contact_id: Optional[UUID] = None
    ) -> Tuple[List[Invoice], int]:
        """
        List invoices with pagination and filtering.

        Args:
            business_id: Business UUID for security scoping
            page: Page number (1-indexed)
            page_size: Number of items per page
            status: Optional filter by status
            start_date: Optional filter by issue_date >= start_date
            end_date: Optional filter by issue_date <= end_date
            contact_id: Optional filter by contact

        Returns:
            Tuple of (invoices list, total count)
        """
        # Build base query
        query = select(Invoice).where(Invoice.business_id == business_id)

        # Apply filters
        if status:
            query = query.where(Invoice.status == status)

        if start_date:
            query = query.where(Invoice.issue_date >= start_date)

        if end_date:
            query = query.where(Invoice.issue_date <= end_date)

        if contact_id:
            query = query.where(Invoice.contact_id == contact_id)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Order by created_at descending (newest first)
        query = query.order_by(Invoice.created_at.desc())

        # Execute query
        result = await self.db.execute(query)
        invoices = result.scalars().all()

        return list(invoices), total

    async def create_invoice(
        self,
        business_id: UUID,
        contact_id: UUID,
        line_items_data: List[Dict[str, Any]],
        due_date: Optional[date] = None,
        notes: Optional[str] = None,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> Invoice:
        """
        Create a new invoice in draft status.

        Args:
            business_id: Business UUID
            contact_id: Customer contact UUID
            line_items_data: List of line item dictionaries
            due_date: Optional payment due date
            notes: Optional notes
            user_id: Optional user ID for audit logging
            ip_address: Optional IP address for audit logging

        Returns:
            Created invoice model

        Raises:
            ValueError: If contact not found or line items invalid
        """
        # Verify contact exists and belongs to business
        contact_result = await self.db.execute(
            select(Contact).where(
                Contact.id == contact_id,
                Contact.business_id == business_id,
                Contact.is_active == True
            )
        )
        contact = contact_result.scalar_one_or_none()
        if not contact:
            raise ValueError("Contact not found or inactive")

        # Verify all item_ids belong to the business (if provided)
        item_ids = [item.get("item_id") for item in line_items_data if item.get("item_id")]
        if item_ids:
            from app.models.item import Item
            item_result = await self.db.execute(
                select(Item.id).where(
                    Item.id.in_(item_ids),
                    Item.business_id == business_id
                )
            )
            valid_item_ids = {row[0] for row in item_result.all()}
            invalid_items = set(item_ids) - valid_item_ids
            if invalid_items:
                raise ValueError(f"Invalid item references: items do not belong to this business")

        # Generate invoice number
        invoice_number = await self._generate_invoice_number(business_id)

        # Create invoice (draft status, no issue_date yet)
        invoice = Invoice(
            business_id=business_id,
            contact_id=contact_id,
            invoice_number=invoice_number,
            status=InvoiceStatus.DRAFT,
            issue_date=None,  # Set when issued
            due_date=due_date,
            subtotal=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("0.00"),
            notes=notes
        )

        self.db.add(invoice)
        await self.db.flush()  # Get invoice ID

        # Create line items
        line_items = []
        for item_data in line_items_data:
            # Calculate line total
            quantity = Decimal(str(item_data["quantity"]))
            unit_price = Decimal(str(item_data["unit_price"]))
            tax_rate = Decimal(str(item_data.get("tax_rate", "16.0")))

            subtotal = quantity * unit_price
            tax = subtotal * (tax_rate / Decimal("100"))
            line_total = subtotal + tax

            line_item = InvoiceItem(
                invoice_id=invoice.id,
                item_id=item_data.get("item_id"),
                description=item_data["description"],
                quantity=quantity,
                unit_price=unit_price,
                tax_rate=tax_rate,
                line_total=round(line_total, 2)
            )
            line_items.append(line_item)
            self.db.add(line_item)

        # Calculate totals
        subtotal, tax_amount, total_amount = self._calculate_invoice_totals(line_items)
        invoice.subtotal = subtotal
        invoice.tax_amount = tax_amount
        invoice.total_amount = total_amount

        # Log the creation
        if user_id:
            await self.audit.log_create(
                user_id=user_id,
                resource_type="invoice",
                resource_id=invoice.id,
                new_values={
                    "invoice_number": invoice.invoice_number,
                    "contact_id": str(invoice.contact_id),
                    "status": invoice.status.value if hasattr(invoice.status, 'value') else invoice.status,
                    "subtotal": float(invoice.subtotal),
                    "tax_amount": float(invoice.tax_amount),
                    "total_amount": float(invoice.total_amount),
                    "due_date": str(invoice.due_date) if invoice.due_date else None,
                    "line_items_count": len(line_items)
                },
                ip_address=ip_address
            )

        await self.db.commit()
        await self.db.refresh(invoice)

        return invoice

    async def update_invoice(
        self,
        invoice_id: UUID,
        business_id: UUID,
        data: Dict[str, Any],
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> Optional[Invoice]:
        """
        Update invoice fields (only allowed in draft status).

        Args:
            invoice_id: Invoice UUID
            business_id: Business UUID for security scoping
            data: Dictionary of fields to update
            user_id: Optional user ID for audit logging
            ip_address: Optional IP address for audit logging

        Returns:
            Updated invoice or None if not found

        Raises:
            ValueError: If invoice is not editable or data invalid
        """
        # Get existing invoice
        invoice = await self.get_invoice_by_id(invoice_id, business_id, include_line_items=True)
        if not invoice:
            return None

        # Check if invoice is editable
        if not invoice.is_editable:
            raise ValueError(f"Invoice with status '{invoice.status}' cannot be edited")

        # Capture old values for audit logging
        old_values = {
            "status": invoice.status.value if hasattr(invoice.status, 'value') else invoice.status,
            "subtotal": float(invoice.subtotal),
            "tax_amount": float(invoice.tax_amount),
            "total_amount": float(invoice.total_amount),
            "due_date": str(invoice.due_date) if invoice.due_date else None,
            "notes": invoice.notes,
            "line_items_count": len(invoice.line_items)
        }

        # Handle line items update if provided
        if "line_items" in data:
            # Verify all item_ids belong to the business (if provided)
            item_ids = [item.get("item_id") for item in data["line_items"] if item.get("item_id")]
            if item_ids:
                from app.models.item import Item
                item_result = await self.db.execute(
                    select(Item.id).where(
                        Item.id.in_(item_ids),
                        Item.business_id == business_id
                    )
                )
                valid_item_ids = {row[0] for row in item_result.all()}
                invalid_items = set(item_ids) - valid_item_ids
                if invalid_items:
                    raise ValueError(f"Invalid item references: items do not belong to this business")

            # Delete existing line items
            for item in invoice.line_items:
                await self.db.delete(item)

            # Create new line items
            line_items = []
            for item_data in data["line_items"]:
                quantity = Decimal(str(item_data["quantity"]))
                unit_price = Decimal(str(item_data["unit_price"]))
                tax_rate = Decimal(str(item_data.get("tax_rate", "16.0")))

                subtotal = quantity * unit_price
                tax = subtotal * (tax_rate / Decimal("100"))
                line_total = subtotal + tax

                line_item = InvoiceItem(
                    invoice_id=invoice.id,
                    item_id=item_data.get("item_id"),
                    description=item_data["description"],
                    quantity=quantity,
                    unit_price=unit_price,
                    tax_rate=tax_rate,
                    line_total=round(line_total, 2)
                )
                line_items.append(line_item)
                self.db.add(line_item)

            # Recalculate totals
            subtotal, tax_amount, total_amount = self._calculate_invoice_totals(line_items)
            data["subtotal"] = subtotal
            data["tax_amount"] = tax_amount
            data["total_amount"] = total_amount
            del data["line_items"]

        # Update timestamp
        data["updated_at"] = datetime.utcnow()

        # Update invoice
        await self.db.execute(
            update(Invoice)
            .where(Invoice.id == invoice_id, Invoice.business_id == business_id)
            .values(**data)
        )

        # Log the update
        if user_id:
            await self.audit.log_update(
                user_id=user_id,
                resource_type="invoice",
                resource_id=invoice_id,
                old_values=old_values,
                new_values={k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                           for k, v in data.items() if k != "updated_at"},
                ip_address=ip_address
            )

        await self.db.commit()

        # Refresh and return
        await self.db.refresh(invoice)
        return invoice

    async def issue_invoice(
        self,
        invoice_id: UUID,
        business_id: UUID,
        issue_date: Optional[date] = None,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> Optional[Invoice]:
        """
        Issue an invoice (change status from draft to issued).

        Args:
            invoice_id: Invoice UUID
            business_id: Business UUID for security scoping
            issue_date: Optional issue date (defaults to today)
            user_id: Optional user ID for audit logging
            ip_address: Optional IP address for audit logging

        Returns:
            Updated invoice or None if not found

        Raises:
            ValueError: If invoice cannot transition to issued status
        """
        invoice = await self.get_invoice_by_id(invoice_id, business_id)
        if not invoice:
            return None

        # Check if transition is allowed
        if not invoice.can_transition_to(InvoiceStatus.ISSUED):
            raise ValueError(
                f"Cannot issue invoice with status '{invoice.status}'. "
                f"Only draft invoices can be issued."
            )

        # Capture old status for audit
        old_status = invoice.status.value if hasattr(invoice.status, 'value') else invoice.status

        # Set issue date if not provided
        if issue_date is None:
            issue_date = date.today()

        # Update invoice
        await self.db.execute(
            update(Invoice)
            .where(Invoice.id == invoice_id, Invoice.business_id == business_id)
            .values(
                status=InvoiceStatus.ISSUED,
                issue_date=issue_date,
                updated_at=datetime.utcnow()
            )
        )

        # Log the workflow transition
        if user_id:
            await self.audit.log_workflow_transition(
                user_id=user_id,
                resource_type="invoice",
                resource_id=invoice_id,
                action="issue_invoice",
                old_status=old_status,
                new_status=InvoiceStatus.ISSUED.value,
                ip_address=ip_address,
                details={
                    "invoice_number": invoice.invoice_number,
                    "issue_date": str(issue_date)
                }
            )

        await self.db.commit()

        await self.db.refresh(invoice)
        return invoice

    async def cancel_invoice(
        self,
        invoice_id: UUID,
        business_id: UUID,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> Optional[Invoice]:
        """
        Cancel an invoice.

        Args:
            invoice_id: Invoice UUID
            business_id: Business UUID for security scoping
            user_id: Optional user ID for audit logging
            ip_address: Optional IP address for audit logging

        Returns:
            Updated invoice or None if not found

        Raises:
            ValueError: If invoice cannot be cancelled
        """
        invoice = await self.get_invoice_by_id(invoice_id, business_id)
        if not invoice:
            return None

        # Check if transition is allowed
        if not invoice.can_transition_to(InvoiceStatus.CANCELLED):
            raise ValueError(
                f"Cannot cancel invoice with status '{invoice.status}'. "
                f"Only draft, issued, or overdue invoices can be cancelled."
            )

        # Capture old status for audit
        old_status = invoice.status.value if hasattr(invoice.status, 'value') else invoice.status

        # Update invoice
        await self.db.execute(
            update(Invoice)
            .where(Invoice.id == invoice_id, Invoice.business_id == business_id)
            .values(
                status=InvoiceStatus.CANCELLED,
                updated_at=datetime.utcnow()
            )
        )

        # Log the workflow transition
        if user_id:
            await self.audit.log_workflow_transition(
                user_id=user_id,
                resource_type="invoice",
                resource_id=invoice_id,
                action="cancel_invoice",
                old_status=old_status,
                new_status=InvoiceStatus.CANCELLED.value,
                ip_address=ip_address,
                details={"invoice_number": invoice.invoice_number}
            )

        await self.db.commit()

        await self.db.refresh(invoice)
        return invoice

    def invoice_to_response(self, invoice: Invoice) -> InvoiceResponse:
        """
        Convert Invoice model to InvoiceResponse schema.

        Args:
            invoice: Invoice model

        Returns:
            InvoiceResponse schema
        """
        return InvoiceResponse(
            id=invoice.id,
            business_id=invoice.business_id,
            contact_id=invoice.contact_id,
            invoice_number=invoice.invoice_number,
            status=invoice.status,
            issue_date=invoice.issue_date,
            due_date=invoice.due_date,
            subtotal=invoice.subtotal,
            tax_amount=invoice.tax_amount,
            total_amount=invoice.total_amount,
            amount_paid=invoice.amount_paid or Decimal("0.00"),
            notes=invoice.notes,
            created_at=invoice.created_at,
            updated_at=invoice.updated_at
        )

    def invoice_to_detail_response(self, invoice: Invoice) -> InvoiceDetailResponse:
        """
        Convert Invoice model to InvoiceDetailResponse schema with line items.

        Args:
            invoice: Invoice model with line_items loaded

        Returns:
            InvoiceDetailResponse schema
        """
        line_items = [
            InvoiceItemResponse(
                id=item.id,
                invoice_id=item.invoice_id,
                item_id=item.item_id,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                tax_rate=item.tax_rate,
                line_total=item.line_total,
                created_at=item.created_at
            )
            for item in invoice.line_items
        ]

        return InvoiceDetailResponse(
            id=invoice.id,
            business_id=invoice.business_id,
            contact_id=invoice.contact_id,
            invoice_number=invoice.invoice_number,
            status=invoice.status,
            issue_date=invoice.issue_date,
            due_date=invoice.due_date,
            subtotal=invoice.subtotal,
            tax_amount=invoice.tax_amount,
            total_amount=invoice.total_amount,
            amount_paid=invoice.amount_paid or Decimal("0.00"),
            notes=invoice.notes,
            created_at=invoice.created_at,
            updated_at=invoice.updated_at,
            line_items=line_items
        )

    async def update_payment_status(
        self,
        invoice_id: UUID,
        business_id: UUID,
        amount_paid: Decimal
    ) -> Optional[Invoice]:
        """
        Update invoice payment status based on amount paid.

        This method recalculates and updates the invoice status based on total payments.
        Called by PaymentService after payment create/update/delete operations.

        Args:
            invoice_id: Invoice UUID
            business_id: Business UUID for security scoping
            amount_paid: Total amount paid

        Returns:
            Updated invoice or None if not found

        Note: This method is typically called by PaymentService, not directly by endpoints.
        """
        invoice = await self.get_invoice_by_id(invoice_id, business_id)
        if not invoice:
            return None

        # Cannot update cancelled invoices
        if invoice.status == InvoiceStatus.CANCELLED.value:
            return invoice

        # Determine new status based on payment amount
        amount_paid = Decimal(str(amount_paid))
        total_amount = Decimal(str(invoice.total_amount))
        new_status = invoice.status

        if amount_paid >= total_amount:
            # Fully paid
            new_status = InvoiceStatus.PAID.value
        elif amount_paid > Decimal("0.00"):
            # Partially paid
            new_status = InvoiceStatus.PARTIALLY_PAID.value
        else:
            # No payments - revert to issued if previously paid
            current_status = invoice.status if isinstance(invoice.status, str) else invoice.status.value
            if current_status in [InvoiceStatus.PAID.value, InvoiceStatus.PARTIALLY_PAID.value]:
                new_status = InvoiceStatus.ISSUED.value

        # Update invoice
        await self.db.execute(
            update(Invoice)
            .where(Invoice.id == invoice_id, Invoice.business_id == business_id)
            .values(
                amount_paid=amount_paid,
                status=new_status,
                updated_at=datetime.utcnow()
            )
        )
        await self.db.commit()

        await self.db.refresh(invoice)
        return invoice

    async def get_amount_paid(
        self,
        invoice_id: UUID,
        business_id: UUID
    ) -> Decimal:
        """
        Get total amount paid for an invoice.

        Args:
            invoice_id: Invoice UUID
            business_id: Business UUID for security scoping

        Returns:
            Total amount paid as Decimal

        Note: This queries the invoice.amount_paid field which is kept in sync by PaymentService.
        """
        invoice = await self.get_invoice_by_id(invoice_id, business_id)
        if not invoice:
            return Decimal("0.00")

        return Decimal(str(invoice.amount_paid)) if invoice.amount_paid else Decimal("0.00")


def get_invoice_service(db: AsyncSession) -> InvoiceService:
    """
    Get invoice service instance.

    Args:
        db: Database session

    Returns:
        InvoiceService instance
    """
    return InvoiceService(db)
