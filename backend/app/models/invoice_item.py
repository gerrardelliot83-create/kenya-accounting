"""
Invoice Item Model

Represents line items within an invoice.
Each line item can reference a catalog item or be a custom entry.
"""

from sqlalchemy import Column, String, Text, ForeignKey, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class InvoiceItem(Base):
    """
    Invoice line item model.

    Each invoice can have multiple line items.
    Line items can reference catalog items or be custom entries.
    """

    # Invoice association
    invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent invoice"
    )

    # Optional item reference
    item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Optional reference to catalog item"
    )

    # Line item details
    description = Column(
        String(500),
        nullable=False,
        comment="Item description"
    )

    quantity = Column(
        DECIMAL(10, 2),
        nullable=False,
        default=1.0,
        comment="Quantity"
    )

    unit_price = Column(
        DECIMAL(15, 2),
        nullable=False,
        comment="Price per unit (before tax)"
    )

    tax_rate = Column(
        DECIMAL(5, 2),
        nullable=False,
        default=16.0,
        comment="Tax rate percentage (default 16% VAT)"
    )

    line_total = Column(
        DECIMAL(15, 2),
        nullable=False,
        comment="Total for this line (quantity * unit_price * (1 + tax_rate/100))"
    )

    # Relationships
    invoice = relationship(
        "Invoice",
        back_populates="line_items",
        foreign_keys=[invoice_id]
    )

    item = relationship(
        "Item",
        backref="invoice_items",
        foreign_keys=[item_id]
    )

    def __repr__(self) -> str:
        return f"<InvoiceItem(id={self.id}, invoice={self.invoice_id}, description={self.description})>"

    @property
    def subtotal(self) -> float:
        """Calculate subtotal before tax."""
        return float(self.quantity) * float(self.unit_price)

    @property
    def tax_amount(self) -> float:
        """Calculate tax amount."""
        return self.subtotal * (float(self.tax_rate) / 100)

    @property
    def total(self) -> float:
        """Calculate total including tax."""
        return self.subtotal + self.tax_amount

    def calculate_line_total(self) -> float:
        """
        Calculate and return the line total.
        This should be called before saving to ensure line_total is correct.
        """
        return self.total
