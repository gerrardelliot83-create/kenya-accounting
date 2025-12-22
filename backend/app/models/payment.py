"""
Payment Model

Represents payments received against invoices.
Payments update invoice status and track the payment lifecycle.

Business Rules:
- Payment amount must be positive
- Payment cannot exceed invoice balance due
- Cannot add payment to cancelled invoices
- Payments automatically update invoice status (partially_paid/paid)
"""

from sqlalchemy import Column, String, Date, Text, ForeignKey, Index, DECIMAL, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class PaymentMethod(str, enum.Enum):
    """Payment method enumeration."""
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    MPESA = "mpesa"
    CARD = "card"
    CHEQUE = "cheque"
    OTHER = "other"


class Payment(Base):
    """
    Payment model for recording payments against invoices.

    Business Scoping:
    - All payments belong to a specific business
    - Queries must filter by business_id for security

    Invoice Integration:
    - Payments are linked to invoices via invoice_id
    - When payments are created/deleted, invoice status is recalculated
    - Payment amount cannot exceed invoice balance due
    """

    # Business association
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Associated business"
    )

    # Invoice reference
    invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Invoice this payment applies to"
    )

    # Payment details
    amount = Column(
        DECIMAL(15, 2),
        nullable=False,
        comment="Payment amount (must be positive)"
    )

    payment_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Date payment was received"
    )

    payment_method = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Payment method (cash, bank_transfer, mpesa, card, cheque, other)"
    )

    # Optional reference information
    reference_number = Column(
        String(100),
        nullable=True,
        comment="Payment reference (M-Pesa code, cheque number, transaction ID, etc.)"
    )

    notes = Column(
        Text,
        nullable=True,
        comment="Additional payment notes"
    )

    # Relationships
    business = relationship(
        "Business",
        backref="payments",
        foreign_keys=[business_id]
    )

    invoice = relationship(
        "Invoice",
        backref="payments",
        foreign_keys=[invoice_id]
    )

    # Constraints
    __table_args__ = (
        # Amount must be positive
        CheckConstraint('amount > 0', name='check_payment_amount_positive'),

        # Indexes for common queries
        Index('ix_payments_business_date', 'business_id', 'payment_date'),
        Index('ix_payments_invoice', 'invoice_id', 'payment_date'),
        Index('ix_payments_method', 'payment_method'),
    )

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, invoice_id={self.invoice_id}, amount={self.amount})>"
