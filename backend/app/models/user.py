"""
User Model

Represents system users synchronized with Supabase Auth.
Supports multiple user roles for different portals.

Security Notes:
- Email, phone, and national_id are encrypted at rest
- RLS policies must be enabled on this table
- Audit all user access and modifications
"""

from sqlalchemy import Column, String, Boolean, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class UserRole(str, enum.Enum):
    """User roles matching security.py definitions."""
    SYSTEM_ADMIN = "system_admin"
    BUSINESS_ADMIN = "business_admin"
    BOOKKEEPER = "bookkeeper"
    ONBOARDING_AGENT = "onboarding_agent"
    SUPPORT_AGENT = "support_agent"


class User(Base):
    """
    User model synchronized with Supabase Auth.

    Encryption:
    - email_encrypted: Encrypted email address
    - phone_encrypted: Encrypted phone number
    - national_id_encrypted: Encrypted national ID

    RLS Policy:
    - Users can only see their own data
    - System admins can see all users
    - Business admins can see users in their business
    - Support agents can see users for support purposes
    """

    # Supabase Auth integration
    # This ID should match the Supabase Auth user ID
    # We override the default UUID generation to use Supabase's ID
    # id is inherited from Base

    # Encrypted personal information
    email_encrypted = Column(
        String,
        nullable=False,
        unique=True,
        index=True,
        comment="Encrypted email address"
    )

    phone_encrypted = Column(
        String,
        nullable=True,
        comment="Encrypted phone number"
    )

    national_id_encrypted = Column(
        String,
        nullable=True,
        comment="Encrypted national ID"
    )

    # User profile
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)

    # Authentication
    password_hash = Column(
        String(255),
        nullable=True,
        comment="Bcrypt password hash"
    )

    # Role and permissions
    # Use values_callable to store enum values (lowercase) instead of names (uppercase)
    role = Column(
        SQLEnum(
            UserRole,
            name="user_role",
            values_callable=lambda obj: [e.value for e in obj]
        ),
        nullable=False,
        default=UserRole.BUSINESS_ADMIN,
        index=True
    )

    # Business association (for business_admin and bookkeeper)
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Associated business for business users"
    )

    # Account status
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether user account is active"
    )

    must_change_password = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Force password change on next login"
    )

    # Last login tracking
    last_login_at = Column(
        String,  # Store as ISO string from Supabase
        nullable=True,
        comment="Last successful login timestamp"
    )

    # Relationships
    business = relationship(
        "Business",
        back_populates="users",
        foreign_keys=[business_id]
    )

    audit_logs = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_users_business_role', 'business_id', 'role'),
        Index('ix_users_active_role', 'is_active', 'role'),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, role={self.role})>"

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or "Unknown"

    @property
    def is_business_user(self) -> bool:
        """Check if user is associated with a business."""
        return self.business_id is not None

    @property
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.role in [UserRole.SYSTEM_ADMIN, UserRole.BUSINESS_ADMIN]
