"""
Contact Model

Represents customers and suppliers for the business.
Supports encrypted storage of sensitive personal information.

Security Notes:
- Email, phone, and KRA PIN are encrypted at rest
- All contacts are scoped to a specific business
- Supports soft deletion via is_active flag
"""

from sqlalchemy import Column, String, Boolean, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class ContactType(str, enum.Enum):
    """Contact type enumeration."""
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    BOTH = "both"


class Contact(Base):
    """
    Contact model for customers and suppliers.

    Encryption:
    - email_encrypted: Encrypted email address
    - phone_encrypted: Encrypted phone number
    - kra_pin_encrypted: Encrypted KRA PIN (optional)

    Business Scoping:
    - All contacts belong to a specific business
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

    # Contact type (stored as VARCHAR, validated at app level)
    contact_type = Column(
        String(20),
        nullable=False,
        default=ContactType.CUSTOMER.value,
        index=True,
        comment="Type of contact: customer, supplier, or both"
    )

    # Basic information
    name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Contact name (individual or company)"
    )

    # Encrypted sensitive information
    email_encrypted = Column(
        String,
        nullable=True,
        comment="Encrypted email address"
    )

    phone_encrypted = Column(
        String,
        nullable=True,
        comment="Encrypted phone number"
    )

    kra_pin_encrypted = Column(
        String,
        nullable=True,
        comment="Encrypted KRA PIN (for tax purposes)"
    )

    # Additional information
    address = Column(
        Text,
        nullable=True,
        comment="Physical address"
    )

    notes = Column(
        Text,
        nullable=True,
        comment="Additional notes about the contact"
    )

    # Status
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether contact is active (soft delete)"
    )

    # Relationships
    business = relationship(
        "Business",
        backref="contacts",
        foreign_keys=[business_id]
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_contacts_business_type', 'business_id', 'contact_type'),
        Index('ix_contacts_business_active', 'business_id', 'is_active'),
        Index('ix_contacts_name_search', 'name'),
    )

    def __repr__(self) -> str:
        return f"<Contact(id={self.id}, name={self.name}, type={self.contact_type})>"

    @property
    def is_customer(self) -> bool:
        """Check if contact is a customer."""
        return self.contact_type in [ContactType.CUSTOMER, ContactType.BOTH]

    @property
    def is_supplier(self) -> bool:
        """Check if contact is a supplier."""
        return self.contact_type in [ContactType.SUPPLIER, ContactType.BOTH]
