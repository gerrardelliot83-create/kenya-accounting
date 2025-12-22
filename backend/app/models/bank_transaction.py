"""
Bank Transaction Model

Represents individual bank transactions parsed from imported statements.
Supports automatic reconciliation with expenses and invoices.

Reconciliation Status:
- unmatched: No match found
- suggested: Potential match identified (with confidence score)
- matched: Confirmed match with expense/invoice
- ignored: User manually marked to ignore

Security:
- Description, reference, and raw_data are encrypted
- All operations scoped to business_id
- Foreign key constraints ensure data integrity
"""

from sqlalchemy import Column, String, Date, ForeignKey, Index, DECIMAL, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
import enum
from decimal import Decimal
from typing import Optional

from app.db.base import Base


class ReconciliationStatus(str, enum.Enum):
    """Bank transaction reconciliation status enumeration."""
    UNMATCHED = "unmatched"
    SUGGESTED = "suggested"
    MATCHED = "matched"
    IGNORED = "ignored"


class BankTransaction(Base):
    """
    Bank transaction model for imported bank statement transactions.

    Features:
    - Parsed transaction data with date, amounts, and descriptions
    - Automatic reconciliation matching with expenses and invoices
    - Confidence scoring for suggested matches
    - Support for both debit and credit transactions
    - Running balance tracking
    - Encrypted sensitive fields

    Business Scoping:
    - All transactions belong to a specific business
    - Linked to parent bank_import for audit trail
    - Queries must filter by business_id for security

    Encryption:
    - description: Encrypted transaction description
    - reference: Encrypted transaction reference/code
    - raw_data: Encrypted original row data for audit

    Reconciliation:
    - Can match to either an expense OR an invoice (not both)
    - Confidence score (0-100) for suggested matches
    - Manual override supported via status change
    """

    # Business association
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Associated business"
    )

    # Import tracking
    bank_import_id = Column(
        UUID(as_uuid=True),
        ForeignKey("bank_imports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent bank import"
    )

    # Transaction details
    transaction_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Date of the transaction"
    )

    description = Column(
        String(1000),
        nullable=False,
        comment="Transaction description (encrypted)"
    )

    reference = Column(
        String(200),
        nullable=True,
        comment="Transaction reference/code (encrypted)"
    )

    # Financial amounts
    debit_amount = Column(
        DECIMAL(15, 2),
        nullable=True,
        comment="Debit/withdrawal amount (money out)"
    )

    credit_amount = Column(
        DECIMAL(15, 2),
        nullable=True,
        comment="Credit/deposit amount (money in)"
    )

    balance = Column(
        DECIMAL(15, 2),
        nullable=True,
        comment="Account balance after transaction"
    )

    # Audit data
    raw_data = Column(
        JSON,
        nullable=True,
        comment="Original row data from import (encrypted)"
    )

    # Reconciliation tracking
    reconciliation_status = Column(
        SQLEnum(ReconciliationStatus, name="reconciliation_status_enum", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ReconciliationStatus.UNMATCHED,
        index=True,
        comment="Reconciliation status"
    )

    matched_expense_id = Column(
        UUID(as_uuid=True),
        ForeignKey("expenses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Matched expense (for debits)"
    )

    matched_invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Matched invoice payment (for credits)"
    )

    match_confidence = Column(
        DECIMAL(5, 2),
        nullable=True,
        comment="Match confidence score (0-100)"
    )

    # Relationships
    business = relationship(
        "Business",
        backref="bank_transactions",
        foreign_keys=[business_id]
    )

    bank_import = relationship(
        "BankImport",
        back_populates="transactions",
        foreign_keys=[bank_import_id]
    )

    matched_expense = relationship(
        "Expense",
        backref="bank_transactions",
        foreign_keys=[matched_expense_id]
    )

    matched_invoice = relationship(
        "Invoice",
        backref="bank_transactions",
        foreign_keys=[matched_invoice_id]
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_bank_transactions_business_date', 'business_id', 'transaction_date'),
        Index('ix_bank_transactions_business_status', 'business_id', 'reconciliation_status'),
        Index('ix_bank_transactions_import_status', 'bank_import_id', 'reconciliation_status'),
        Index('ix_bank_transactions_business_unmatched', 'business_id', 'reconciliation_status', 'transaction_date'),
    )

    def __repr__(self) -> str:
        amount = self.debit_amount if self.debit_amount else self.credit_amount
        txn_type = "DR" if self.debit_amount else "CR"
        return f"<BankTransaction(id={self.id}, date={self.transaction_date}, {txn_type} {amount}, status={self.reconciliation_status})>"

    @property
    def transaction_amount(self) -> Optional[Decimal]:
        """Get the transaction amount (debit or credit)."""
        return self.debit_amount if self.debit_amount else self.credit_amount

    @property
    def is_debit(self) -> bool:
        """Check if transaction is a debit (money out)."""
        return self.debit_amount is not None and self.debit_amount > 0

    @property
    def is_credit(self) -> bool:
        """Check if transaction is a credit (money in)."""
        return self.credit_amount is not None and self.credit_amount > 0

    @property
    def is_matched(self) -> bool:
        """Check if transaction has been matched."""
        return self.reconciliation_status == ReconciliationStatus.MATCHED

    @property
    def is_suggested(self) -> bool:
        """Check if transaction has a suggested match."""
        return self.reconciliation_status == ReconciliationStatus.SUGGESTED

    @property
    def is_unmatched(self) -> bool:
        """Check if transaction is unmatched."""
        return self.reconciliation_status == ReconciliationStatus.UNMATCHED

    @property
    def matched_record_id(self) -> Optional[UUID]:
        """Get the ID of the matched record (expense or invoice)."""
        return self.matched_expense_id or self.matched_invoice_id

    @property
    def matched_record_type(self) -> Optional[str]:
        """Get the type of matched record (expense or invoice)."""
        if self.matched_expense_id:
            return "expense"
        elif self.matched_invoice_id:
            return "invoice"
        return None
