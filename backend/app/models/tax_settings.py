"""
Tax Settings Model

Business-level tax configuration for Kenya tax compliance.
Supports VAT (Value Added Tax) and TOT (Turnover Tax) settings.

Kenya Tax Framework:
- VAT: 16% standard rate for businesses with turnover > 5M KES
- TOT: 3% turnover tax for businesses with turnover 1-50M KES (alternative to VAT)
- Financial year: Customizable start month (default January)

Security:
- VAT registration number is encrypted as it contains sensitive business data
- One-to-one relationship with business (unique constraint)
"""

from sqlalchemy import Column, String, Boolean, Integer, Date, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class TaxSettings(Base):
    """
    Tax settings model for business tax configuration.

    Features:
    - VAT registration tracking
    - TOT eligibility flag
    - Financial year configuration
    - One-to-one relationship with business

    Business Scoping:
    - Each business has one tax settings record
    - Queries must filter by business_id for security

    Encryption:
    - vat_registration_number: Encrypted sensitive tax identifier
    """

    # Override auto-generated table name (prevents 'tax_settingses')
    __tablename__ = 'tax_settings'

    # Business association (one-to-one)
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="Associated business (one-to-one relationship)"
    )

    # VAT (Value Added Tax) settings
    is_vat_registered = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Whether business is VAT registered"
    )

    vat_registration_number = Column(
        String(50),
        nullable=True,
        comment="VAT registration number (encrypted, KRA PIN format)"
    )

    vat_registration_date = Column(
        Date,
        nullable=True,
        comment="Date of VAT registration with KRA"
    )

    # TOT (Turnover Tax) settings - for businesses 1-50M KES
    is_tot_eligible = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Whether business is eligible for TOT (1-50M KES turnover)"
    )

    # Financial year configuration
    financial_year_start_month = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Financial year start month (1=January, 12=December)"
    )

    # Relationships
    business = relationship(
        "Business",
        backref="tax_settings",
        foreign_keys=[business_id],
        uselist=False
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_tax_settings_business_vat', 'business_id', 'is_vat_registered'),
        Index('ix_tax_settings_business_tot', 'business_id', 'is_tot_eligible'),
    )

    def __repr__(self) -> str:
        return f"<TaxSettings(id={self.id}, business_id={self.business_id}, vat={self.is_vat_registered}, tot={self.is_tot_eligible})>"

    @property
    def tax_type(self) -> str:
        """Get the current tax type for this business."""
        if self.is_vat_registered:
            return "VAT"
        elif self.is_tot_eligible:
            return "TOT"
        return "None"

    @property
    def requires_vat_registration_number(self) -> bool:
        """Check if VAT registration number is required."""
        return self.is_vat_registered

    def validate_financial_year_month(self) -> bool:
        """Validate financial year start month is between 1-12."""
        return 1 <= self.financial_year_start_month <= 12
