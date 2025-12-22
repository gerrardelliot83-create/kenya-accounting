"""
Audit Log Model

Tracks all security-relevant events and data changes in the system.

Security Notes:
- All authentication attempts must be logged
- All data modifications must be logged
- Audit logs are immutable (no updates/deletes except by retention policy)
- Access to audit logs is restricted to admins and support agents
"""

from sqlalchemy import Column, String, Text, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class AuditLog(Base):
    """
    Audit log for tracking all security and data events.

    MANDATORY LOGGING:
    - Authentication attempts (success/failure)
    - Authorization failures
    - Sensitive data access (viewing encrypted fields)
    - Data modifications (create, update, delete)
    - Admin actions
    - Configuration changes

    RLS Policy:
    - Only system_admin and support_agent can read
    - System creates entries (application service account)
    - No updates or deletes allowed (immutable)
    """

    # User who performed the action
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who performed the action (null for system actions)"
    )

    # Action details
    action = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Action performed (e.g., login, create_business, update_user)"
    )

    # Resource affected
    resource_type = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Type of resource (e.g., user, business, transaction)"
    )

    resource_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="ID of the affected resource"
    )

    # Action outcome
    status = Column(
        String(20),
        nullable=False,
        default="success",
        index=True,
        comment="Action outcome: success, failure, error"
    )

    # Additional context
    details = Column(
        JSON,
        nullable=True,
        comment="Additional details about the action (JSON)"
    )

    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if action failed"
    )

    # Request context
    ip_address = Column(
        String(45),  # IPv6 max length
        nullable=True,
        index=True,
        comment="IP address of the request"
    )

    user_agent = Column(
        Text,
        nullable=True,
        comment="User agent string from request"
    )

    # Session tracking
    session_id = Column(
        String(255),
        nullable=True,
        index=True,
        comment="Session ID for tracking related actions"
    )

    # Data changes (for modification tracking)
    old_values = Column(
        JSON,
        nullable=True,
        comment="Previous values for update operations"
    )

    new_values = Column(
        JSON,
        nullable=True,
        comment="New values for create/update operations"
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="audit_logs"
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_audit_logs_user_action', 'user_id', 'action'),
        Index('ix_audit_logs_resource', 'resource_type', 'resource_id'),
        Index('ix_audit_logs_status_action', 'status', 'action'),
        Index('ix_audit_logs_created_at', 'created_at'),
        Index('ix_audit_logs_ip_created', 'ip_address', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, status={self.status})>"

    @property
    def is_security_event(self) -> bool:
        """Check if this is a security-related event."""
        security_actions = [
            "login",
            "login_failed",
            "logout",
            "password_change",
            "password_reset",
            "unauthorized_access",
            "permission_denied",
        ]
        return self.action in security_actions

    @property
    def is_data_modification(self) -> bool:
        """Check if this event modified data."""
        return self.action.startswith(("create_", "update_", "delete_"))

    @property
    def is_failure(self) -> bool:
        """Check if this action failed."""
        return self.status in ["failure", "error"]


# Common action constants for consistency
class AuditAction:
    """Standard audit action names."""

    # Authentication
    LOGIN = "login"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"

    # Authorization
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PERMISSION_DENIED = "permission_denied"

    # User management
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    ACTIVATE_USER = "activate_user"
    DEACTIVATE_USER = "deactivate_user"

    # Business management
    CREATE_BUSINESS = "create_business"
    UPDATE_BUSINESS = "update_business"
    DELETE_BUSINESS = "delete_business"

    # Data access
    VIEW_SENSITIVE_DATA = "view_sensitive_data"
    EXPORT_DATA = "export_data"

    # System
    SYSTEM_CONFIG_CHANGE = "system_config_change"

    # Generic CRUD actions
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"

    # Support ticket actions
    CREATE_TICKET = "create_ticket"
    UPDATE_TICKET = "update_ticket"
    ASSIGN_TICKET = "assign_ticket"
    ADD_MESSAGE = "add_message"


class AuditStatus:
    """Standard audit status values."""

    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"
