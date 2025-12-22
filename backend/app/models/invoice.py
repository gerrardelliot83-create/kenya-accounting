"""
Invoice Model

Represents invoices issued by the business to customers.
Implements strict status workflow and automatic number generation.

Status Workflow:
- draft -> issued -> paid OR cancelled
- Issued invoices can become paid or cancelled
- Paid and cancelled are terminal states

Invoice Number Format:
- INV-{year}-{sequence} (e.g., INV-2024-00001)
"""

from sqlalchemy import Column, String, Date, Text, ForeignKey, Index, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class InvoiceStatus(str, enum.Enum):
    """Invoice status enumeration with strict workflow."""
    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class Invoice(Base):
    """
    Invoice model for customer invoices.

    Status Workflow:
    - draft: Can be edited freely
    - issued: Locked for editing, awaiting payment
    - partially_paid: Some payment received
    - paid: Fully paid, terminal state
    - overdue: Issued but past due date
    - cancelled: Cancelled, terminal state

    Business Scoping:
    - All invoices belong to a specific business
    - Queries must filter by business_id for security
    """

    # Business association
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Associated business"
    )

    # Customer reference
    contact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Customer contact"
    )

    # Invoice identification
    invoice_number = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Auto-generated invoice number (INV-YYYY-NNNNN)"
    )

    # Status (stored as VARCHAR, validated at app level)
    status = Column(
        String(20),
        nullable=False,
        default=InvoiceStatus.DRAFT.value,
        index=True,
        comment="Invoice status with workflow enforcement"
    )

    # Dates
    issue_date = Column(
        Date,
        nullable=True,
        index=True,
        comment="Date invoice was issued (set when status changes to issued)"
    )

    due_date = Column(
        Date,
        nullable=True,
        index=True,
        comment="Payment due date"
    )

    # Financial totals
    subtotal = Column(
        DECIMAL(15, 2),
        nullable=False,
        default=0.00,
        comment="Subtotal before tax"
    )

    tax_amount = Column(
        DECIMAL(15, 2),
        nullable=False,
        default=0.00,
        comment="Total tax amount"
    )

    total_amount = Column(
        DECIMAL(15, 2),
        nullable=False,
        default=0.00,
        comment="Total amount including tax"
    )

    # Payment tracking
    amount_paid = Column(
        DECIMAL(15, 2),
        nullable=False,
        default=0.00,
        comment="Total amount paid towards this invoice"
    )

    # Additional information
    notes = Column(
        Text,
        nullable=True,
        comment="Additional notes or terms"
    )

    # Relationships
    business = relationship(
        "Business",
        backref="invoices",
        foreign_keys=[business_id]
    )

    contact = relationship(
        "Contact",
        backref="invoices",
        foreign_keys=[contact_id]
    )

    line_items = relationship(
        "InvoiceItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="InvoiceItem.created_at"
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_invoices_business_status', 'business_id', 'status'),
        Index('ix_invoices_business_dates', 'business_id', 'issue_date', 'due_date'),
        Index('ix_invoices_contact', 'contact_id', 'status'),
        Index('ix_invoices_number_unique', 'invoice_number', unique=True),
    )

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, number={self.invoice_number}, status={self.status})>"

    @property
    def balance_due(self):
        """Calculate remaining balance due on the invoice."""
        from decimal import Decimal
        total = Decimal(str(self.total_amount)) if self.total_amount else Decimal("0.00")
        paid = Decimal(str(self.amount_paid)) if self.amount_paid else Decimal("0.00")
        return total - paid

    @property
    def is_editable(self) -> bool:
        """Check if invoice can be edited."""
        current_status = self.status if isinstance(self.status, str) else self.status.value
        return current_status == InvoiceStatus.DRAFT.value

    @property
    def is_locked(self) -> bool:
        """Check if invoice is locked from editing."""
        current_status = self.status if isinstance(self.status, str) else self.status.value
        return current_status in [InvoiceStatus.ISSUED.value, InvoiceStatus.PAID.value,
                                  InvoiceStatus.PARTIALLY_PAID.value, InvoiceStatus.OVERDUE.value]

    @property
    def is_terminal(self) -> bool:
        """Check if invoice is in a terminal state."""
        current_status = self.status if isinstance(self.status, str) else self.status.value
        return current_status in [InvoiceStatus.PAID.value, InvoiceStatus.CANCELLED.value]

    def can_transition_to(self, new_status: InvoiceStatus) -> bool:
        """
        Check if invoice can transition to a new status.

        Workflow rules:
        - draft -> issued, cancelled
        - issued -> paid, partially_paid, overdue, cancelled
        - partially_paid -> paid, overdue
        - overdue -> paid, cancelled
        - paid/cancelled are terminal (no transitions allowed)
        - Same-status transitions are NOT allowed (must be an actual state change)
        """
        # Get current status as string for comparison
        current_status = self.status if isinstance(self.status, str) else self.status.value
        new_status_value = new_status.value if hasattr(new_status, 'value') else new_status

        # Same-status transitions are not allowed
        if current_status == new_status_value:
            return False

        # Terminal states cannot transition
        if self.is_terminal:
            return False

        # Define allowed transitions (using string values for comparison)
        allowed_transitions = {
            InvoiceStatus.DRAFT.value: [InvoiceStatus.ISSUED.value, InvoiceStatus.CANCELLED.value],
            InvoiceStatus.ISSUED.value: [InvoiceStatus.PAID.value, InvoiceStatus.PARTIALLY_PAID.value,
                                         InvoiceStatus.OVERDUE.value, InvoiceStatus.CANCELLED.value],
            InvoiceStatus.PARTIALLY_PAID.value: [InvoiceStatus.PAID.value, InvoiceStatus.OVERDUE.value],
            InvoiceStatus.OVERDUE.value: [InvoiceStatus.PAID.value, InvoiceStatus.CANCELLED.value],
        }

        return new_status_value in allowed_transitions.get(current_status, [])
