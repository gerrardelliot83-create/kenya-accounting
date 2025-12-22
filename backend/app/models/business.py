"""
Business Model

Represents businesses registered in the system.
Each business is a tenant with its own data.

Security Notes:
- KRA PIN, bank account, and tax certificate number are encrypted at rest
- RLS policies enforce tenant isolation
- All changes must be audited
"""

from sqlalchemy import Column, String, Boolean, Text, Index
from sqlalchemy.orm import relationship

from app.db.base import Base


class Business(Base):
    """
    Business/Company model.

    Encryption:
    - kra_pin_encrypted: Encrypted KRA PIN
    - bank_account_encrypted: Encrypted bank account number
    - tax_certificate_encrypted: Encrypted tax certificate number

    RLS Policy:
    - Business admins can only see their own business
    - System admins can see all businesses
    - Onboarding agents can see businesses they're onboarding
    - Support agents can see businesses for support purposes
    """

    # Business information
    name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Business/company name"
    )

    # Encrypted sensitive information
    kra_pin_encrypted = Column(
        String,
        nullable=True,
        unique=True,
        index=True,
        comment="Encrypted KRA PIN"
    )

    bank_account_encrypted = Column(
        String,
        nullable=True,
        comment="Encrypted bank account number"
    )

    tax_certificate_encrypted = Column(
        String,
        nullable=True,
        comment="Encrypted tax certificate number"
    )

    # Tax registration status
    vat_registered = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether business is VAT registered"
    )

    tot_registered = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether business is TOT registered"
    )

    # Address information
    address = Column(Text, nullable=True, comment="Physical address")
    city = Column(String(100), nullable=True, comment="City")
    country = Column(
        String(100),
        nullable=False,
        default="Kenya",
        comment="Country (default Kenya)"
    )
    postal_code = Column(String(20), nullable=True, comment="Postal code")

    # Contact information
    phone = Column(String(20), nullable=True, comment="Business phone number")
    email = Column(String(255), nullable=True, comment="Business email")
    website = Column(String(255), nullable=True, comment="Business website")

    # Business details
    industry = Column(String(100), nullable=True, comment="Industry/sector")
    business_type = Column(
        String(50),
        nullable=True,
        comment="Business type (e.g., sole proprietor, limited company)"
    )

    # Onboarding status
    onboarding_status = Column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
        comment="Onboarding status: pending, in_progress, completed, rejected"
    )

    onboarding_completed_at = Column(
        String,  # ISO timestamp
        nullable=True,
        comment="When onboarding was completed"
    )

    # Account status
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether business account is active"
    )

    # Subscription information (for future use)
    subscription_tier = Column(
        String(50),
        nullable=False,
        default="basic",
        comment="Subscription tier"
    )

    subscription_expires_at = Column(
        String,  # ISO timestamp
        nullable=True,
        comment="Subscription expiration date"
    )

    # Relationships
    users = relationship(
        "User",
        back_populates="business",
        foreign_keys="User.business_id"
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_businesses_onboarding_status', 'onboarding_status', 'is_active'),
        Index('ix_businesses_subscription', 'subscription_tier', 'is_active'),
    )

    def __repr__(self) -> str:
        return f"<Business(id={self.id}, name={self.name})>"

    @property
    def is_fully_onboarded(self) -> bool:
        """Check if business has completed onboarding."""
        return self.onboarding_status == "completed"

    @property
    def is_tax_compliant(self) -> bool:
        """Check if business has necessary tax registrations."""
        # At minimum, should have KRA PIN
        return bool(self.kra_pin_encrypted)

    @property
    def full_address(self) -> str:
        """Get formatted full address."""
        parts = [
            self.address,
            self.city,
            self.postal_code,
            self.country
        ]
        return ", ".join(filter(None, parts))
