"""
Business Application Model

Represents business onboarding applications with encrypted sensitive data.
Tracks the complete onboarding workflow from draft to approval.

Application Workflow:
1. draft: Application created but not yet submitted
2. submitted: Application submitted for review by agent
3. under_review: Agent actively reviewing the application
4. approved: Application approved and business account created
5. rejected: Application rejected with reason
6. info_requested: More information requested from applicant

Security Notes:
- ALL sensitive fields MUST be encrypted (kra_pin, phone, email, national_id, bank_account)
- RLS policies enforce agent-only access for active applications
- Audit logging required for ALL status changes
- Never log decrypted sensitive data
"""

import enum
from sqlalchemy import Column, String, Boolean, Text, ForeignKey, Index, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class OnboardingStatus(str, enum.Enum):
    """Onboarding application status enumeration."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    INFO_REQUESTED = "info_requested"


class BusinessType(str, enum.Enum):
    """Business type enumeration."""
    SOLE_PROPRIETOR = "sole_proprietor"
    PARTNERSHIP = "partnership"
    LIMITED_COMPANY = "limited_company"


class BusinessApplication(Base):
    """
    Business application model for onboarding workflow.

    Features:
    - Encrypted sensitive data (KRA PIN, phone, email, national ID, bank account)
    - Status workflow tracking
    - Agent assignment and review tracking
    - Approval creates actual business record
    - Rejection reason tracking
    - Information request support

    Agent Scoping:
    - Applications are viewable by all onboarding agents and system admins
    - Created_by tracks which agent initiated the application
    - Reviewed_by tracks which agent approved/rejected

    Encryption:
    - kra_pin_encrypted: Business KRA PIN
    - phone_encrypted: Business phone number
    - email_encrypted: Business email address
    - owner_national_id_encrypted: Owner's national ID
    - owner_phone_encrypted: Owner's phone number
    - owner_email_encrypted: Owner's email address
    - bank_account_encrypted: Business bank account number
    """

    # Business information
    business_name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Name of the business"
    )

    business_type = Column(
        String(50),
        nullable=True,
        comment="Type: sole_proprietor, partnership, limited_company"
    )

    # Encrypted sensitive information (MANDATORY ENCRYPTION)
    kra_pin_encrypted = Column(
        Text,
        nullable=True,
        comment="Encrypted KRA PIN (MANDATORY ENCRYPTION)"
    )

    phone_encrypted = Column(
        Text,
        nullable=True,
        comment="Encrypted business phone (MANDATORY ENCRYPTION)"
    )

    email_encrypted = Column(
        Text,
        nullable=True,
        comment="Encrypted business email (MANDATORY ENCRYPTION)"
    )

    owner_national_id_encrypted = Column(
        Text,
        nullable=True,
        comment="Encrypted owner national ID (MANDATORY ENCRYPTION)"
    )

    owner_phone_encrypted = Column(
        Text,
        nullable=True,
        comment="Encrypted owner phone (MANDATORY ENCRYPTION)"
    )

    owner_email_encrypted = Column(
        Text,
        nullable=True,
        comment="Encrypted owner email (MANDATORY ENCRYPTION)"
    )

    bank_account_encrypted = Column(
        Text,
        nullable=True,
        comment="Encrypted bank account number (MANDATORY ENCRYPTION)"
    )

    # Location information
    county = Column(
        String(100),
        nullable=True,
        comment="County where business is located"
    )

    sub_county = Column(
        String(100),
        nullable=True,
        comment="Sub-county where business is located"
    )

    # Owner information
    owner_name = Column(
        String(255),
        nullable=True,
        comment="Name of business owner/director"
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

    # Application status tracking
    status = Column(
        SQLEnum(OnboardingStatus, name="onboarding_status_enum", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=OnboardingStatus.DRAFT,
        index=True,
        comment="Application status"
    )

    submitted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Timestamp when application was submitted"
    )

    reviewed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Timestamp when application was reviewed"
    )

    # Review tracking
    reviewed_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Agent who reviewed the application"
    )

    rejection_reason = Column(
        Text,
        nullable=True,
        comment="Reason for rejection (required if rejected)"
    )

    info_request_note = Column(
        Text,
        nullable=True,
        comment="Note requesting additional information"
    )

    # Agent tracking
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Onboarding agent who created the application"
    )

    # Approved business tracking (after approval)
    approved_business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Business ID created after approval"
    )

    # Additional metadata
    notes = Column(
        Text,
        nullable=True,
        comment="Internal notes for onboarding agents"
    )

    # Relationships
    reviewer = relationship(
        "User",
        backref="reviewed_applications",
        foreign_keys=[reviewed_by]
    )

    creator = relationship(
        "User",
        backref="created_applications",
        foreign_keys=[created_by]
    )

    approved_business = relationship(
        "Business",
        backref="onboarding_application",
        foreign_keys=[approved_business_id]
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_business_applications_status_submitted', 'status', 'submitted_at'),
        Index('ix_business_applications_status_created', 'status', 'created_at'),
        Index('ix_business_applications_created_by_status', 'created_by', 'status'),
    )

    def __repr__(self) -> str:
        return f"<BusinessApplication(id={self.id}, business_name={self.business_name}, status={self.status})>"

    @property
    def is_draft(self) -> bool:
        """Check if application is in draft status."""
        return self.status == OnboardingStatus.DRAFT

    @property
    def is_submitted(self) -> bool:
        """Check if application has been submitted."""
        return self.status in [
            OnboardingStatus.SUBMITTED,
            OnboardingStatus.UNDER_REVIEW,
            OnboardingStatus.APPROVED,
            OnboardingStatus.REJECTED,
            OnboardingStatus.INFO_REQUESTED
        ]

    @property
    def is_pending_review(self) -> bool:
        """Check if application is pending review."""
        return self.status in [OnboardingStatus.SUBMITTED, OnboardingStatus.INFO_REQUESTED]

    @property
    def is_under_review(self) -> bool:
        """Check if application is actively being reviewed."""
        return self.status == OnboardingStatus.UNDER_REVIEW

    @property
    def is_approved(self) -> bool:
        """Check if application has been approved."""
        return self.status == OnboardingStatus.APPROVED

    @property
    def is_rejected(self) -> bool:
        """Check if application has been rejected."""
        return self.status == OnboardingStatus.REJECTED

    @property
    def is_finalized(self) -> bool:
        """Check if application has been finalized (approved or rejected)."""
        return self.status in [OnboardingStatus.APPROVED, OnboardingStatus.REJECTED]

    @property
    def has_reviewer(self) -> bool:
        """Check if application has been assigned a reviewer."""
        return self.reviewed_by is not None

    @property
    def can_be_submitted(self) -> bool:
        """Check if application can be submitted."""
        return self.status in [OnboardingStatus.DRAFT, OnboardingStatus.INFO_REQUESTED]

    @property
    def can_be_reviewed(self) -> bool:
        """Check if application can be reviewed."""
        return self.status in [OnboardingStatus.SUBMITTED, OnboardingStatus.UNDER_REVIEW]

    @property
    def requires_action(self) -> bool:
        """Check if application requires action from applicant."""
        return self.status == OnboardingStatus.INFO_REQUESTED
