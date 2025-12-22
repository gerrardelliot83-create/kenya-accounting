"""
Expense Model

Represents business expenses with comprehensive tracking for Kenya SMB accounting.
Supports categorization, reconciliation, and various payment methods including M-Pesa.

Expense Categories:
- System categories: Office Supplies, Travel & Transport, Utilities, Rent, etc.
- Custom categories: User-defined categories per business

Payment Methods:
- cash: Cash payments
- bank_transfer: Bank transfers
- mpesa: M-Pesa mobile money
- card: Credit/Debit card
- other: Other payment methods
"""

from sqlalchemy import Column, String, Date, Text, ForeignKey, Index, DECIMAL, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Expense(Base):
    """
    Expense model for business expense tracking.

    Features:
    - Comprehensive expense categorization
    - Support for Kenya-specific payment methods (M-Pesa)
    - Tax amount tracking for VAT/TOT calculations
    - Receipt URL for document storage
    - Reconciliation status tracking
    - Vendor tracking for supplier management

    Business Scoping:
    - All expenses belong to a specific business
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

    # Categorization
    category = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Expense category (e.g., office_supplies, travel, utilities)"
    )

    # Description and details
    description = Column(
        Text,
        nullable=False,
        comment="Expense description"
    )

    # Financial amounts
    amount = Column(
        DECIMAL(15, 2),
        nullable=False,
        comment="Expense amount (must be positive)"
    )

    tax_amount = Column(
        DECIMAL(15, 2),
        nullable=False,
        default=0.00,
        comment="Tax amount (VAT/TOT)"
    )

    # Date tracking
    expense_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Date expense was incurred"
    )

    # Vendor information
    vendor_name = Column(
        String(200),
        nullable=True,
        index=True,
        comment="Vendor/supplier name"
    )

    # Receipt/document tracking
    receipt_url = Column(
        String(500),
        nullable=True,
        comment="URL to receipt or invoice document"
    )

    # Payment details
    payment_method = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Payment method: cash, bank_transfer, mpesa, card, other"
    )

    reference_number = Column(
        String(100),
        nullable=True,
        comment="Transaction reference (e.g., M-Pesa code, bank reference)"
    )

    # Reconciliation tracking
    is_reconciled = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Whether expense has been reconciled with bank statement"
    )

    # Additional notes
    notes = Column(
        Text,
        nullable=True,
        comment="Additional notes or comments"
    )

    # Soft delete support
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Soft delete flag"
    )

    # Relationships
    business = relationship(
        "Business",
        backref="expenses",
        foreign_keys=[business_id]
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_expenses_business_date', 'business_id', 'expense_date'),
        Index('ix_expenses_business_category', 'business_id', 'category'),
        Index('ix_expenses_business_vendor', 'business_id', 'vendor_name'),
        Index('ix_expenses_business_reconciled', 'business_id', 'is_reconciled'),
        Index('ix_expenses_business_active', 'business_id', 'is_active'),
        Index('ix_expenses_date_range', 'business_id', 'expense_date', 'category'),
    )

    def __repr__(self) -> str:
        return f"<Expense(id={self.id}, category={self.category}, amount={self.amount}, date={self.expense_date})>"

    @property
    def total_amount(self) -> float:
        """Calculate total amount including tax."""
        return float(self.amount) + float(self.tax_amount)

    @property
    def is_mpesa_payment(self) -> bool:
        """Check if expense was paid via M-Pesa."""
        return self.payment_method == "mpesa"
