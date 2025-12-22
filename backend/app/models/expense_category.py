"""
Expense Category Model

Represents expense categories for business expense tracking.
Supports both system-defined and custom user-defined categories.

System Categories (is_system=True):
- Cannot be deleted or modified by users
- Provided by default for all businesses
- Kenya-relevant categories included

Custom Categories (is_system=False):
- Created by business users
- Can be edited and soft-deleted
- Business-specific categorization
"""

from sqlalchemy import Column, String, Text, ForeignKey, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class ExpenseCategory(Base):
    """
    Expense category model for categorizing expenses.

    Features:
    - System categories: Pre-defined, cannot be deleted
    - Custom categories: User-defined, business-specific
    - Soft delete support for custom categories
    - Description for clarity on category usage

    Business Scoping:
    - System categories are shared across all businesses (business_id can be null)
    - Custom categories belong to a specific business
    """

    # Business association (null for system categories)
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Associated business (null for system categories)"
    )

    # Category details
    name = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Category name (e.g., 'Office Supplies', 'Travel & Transport')"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Category description"
    )

    # System category flag
    is_system = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Whether this is a system-defined category (cannot be deleted)"
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
        backref="expense_categories",
        foreign_keys=[business_id]
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_expense_categories_business', 'business_id', 'is_active'),
        Index('ix_expense_categories_system', 'is_system', 'is_active'),
        Index('ix_expense_categories_name', 'business_id', 'name', unique=True),
    )

    def __repr__(self) -> str:
        category_type = "system" if self.is_system else "custom"
        return f"<ExpenseCategory(id={self.id}, name={self.name}, type={category_type})>"

    @property
    def is_deletable(self) -> bool:
        """Check if category can be deleted (only custom categories)."""
        return not self.is_system
