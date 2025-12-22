"""
Item/Service Model

Represents products and services offered by the business.
Used in invoices for line items.

Security Notes:
- All items are scoped to a specific business
- SKU uniqueness is enforced per business
- Supports soft deletion via is_active flag
"""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Index, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class ItemType(str, enum.Enum):
    """Item type enumeration."""
    PRODUCT = "product"
    SERVICE = "service"


class Item(Base):
    """
    Item/Service model for products and services catalog.

    Business Scoping:
    - All items belong to a specific business
    - SKU uniqueness is enforced per business
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

    # Item type (stored as VARCHAR, validated at app level)
    item_type = Column(
        String(20),
        nullable=False,
        default=ItemType.PRODUCT.value,
        index=True,
        comment="Type of item: product or service"
    )

    # Basic information
    name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Item/service name"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Detailed description"
    )

    # SKU (Stock Keeping Unit)
    sku = Column(
        String(100),
        nullable=True,
        comment="SKU or product code (unique per business)"
    )

    # Pricing
    unit_price = Column(
        DECIMAL(15, 2),
        nullable=False,
        comment="Unit price (before tax)"
    )

    tax_rate = Column(
        DECIMAL(5, 2),
        nullable=False,
        default=16.0,
        comment="Tax rate percentage (default 16% VAT)"
    )

    # Status
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether item is active (soft delete)"
    )

    # Relationships
    business = relationship(
        "Business",
        backref="items",
        foreign_keys=[business_id]
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_items_business_type', 'business_id', 'item_type'),
        Index('ix_items_business_active', 'business_id', 'is_active'),
        # Partial unique index: only enforce uniqueness when SKU is not NULL
        Index(
            'ix_items_business_sku',
            'business_id',
            'sku',
            unique=True,
            postgresql_where=(Column('sku').isnot(None))
        ),
        Index('ix_items_name_search', 'name'),
    )

    def __repr__(self) -> str:
        return f"<Item(id={self.id}, name={self.name}, type={self.item_type})>"

    @property
    def is_product(self) -> bool:
        """Check if item is a product."""
        return self.item_type == ItemType.PRODUCT

    @property
    def is_service(self) -> bool:
        """Check if item is a service."""
        return self.item_type == ItemType.SERVICE

    @property
    def price_with_tax(self) -> float:
        """Calculate price including tax."""
        return float(self.unit_price) * (1 + float(self.tax_rate) / 100)
