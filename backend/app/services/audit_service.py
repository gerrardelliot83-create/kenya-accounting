"""
Audit Service

Comprehensive audit logging service for tracking all security-relevant events
and data changes across the application.

Features:
- Generic log() method for any audit event
- Specialized methods for CRUD operations (create, update, delete)
- Sensitive data access logging
- Automatic data sanitization to prevent logging sensitive values
- Support for old/new value tracking

Security Notes:
- Never logs plaintext sensitive data (passwords, tokens, encrypted fields)
- All audit logs are immutable (except retention policy cleanup)
- Logs include IP address and user agent for security investigations
- Flush after insert to ensure logs persist even if transaction fails
"""

from typing import Optional, Any, Dict
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog, AuditAction, AuditStatus


class AuditService:
    """Service for audit logging operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize audit service.

        Args:
            db: Database session
        """
        self.db = db

    async def log(
        self,
        action: str,
        user_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        status: str = AuditStatus.SUCCESS,
        details: Optional[dict] = None,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None
    ) -> AuditLog:
        """
        Create an audit log entry.

        This is the core logging method that all other logging methods use.
        It creates an audit log entry and flushes it to the database immediately.

        Args:
            action: Action performed (e.g., "login", "create_invoice", "update_contact")
            user_id: Optional user who performed the action
            resource_type: Optional type of resource affected (e.g., "invoice", "contact")
            resource_id: Optional ID of the affected resource
            status: Action status (success, failure, error)
            details: Optional additional context as dictionary
            error_message: Optional error message if action failed
            ip_address: Optional client IP address
            user_agent: Optional client user agent string
            session_id: Optional session ID for tracking
            old_values: Optional previous values for update operations
            new_values: Optional new values for create/update operations

        Returns:
            Created AuditLog model

        Note:
            This method flushes but does not commit. The caller controls transaction boundaries.
        """
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            details=details,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            old_values=old_values,
            new_values=new_values
        )

        self.db.add(audit_log)
        await self.db.flush()  # Flush to persist immediately, but don't commit

        return audit_log

    async def log_create(
        self,
        user_id: UUID,
        resource_type: str,
        resource_id: UUID,
        new_values: dict,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[dict] = None
    ) -> AuditLog:
        """
        Log a create operation.

        Automatically sanitizes sensitive fields from new_values.

        Args:
            user_id: User who performed the create
            resource_type: Type of resource created (e.g., "invoice", "contact")
            resource_id: ID of the created resource
            new_values: Dictionary of new values
            ip_address: Optional client IP address
            user_agent: Optional client user agent
            details: Optional additional context

        Returns:
            Created AuditLog model
        """
        return await self.log(
            action=f"create_{resource_type}",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            new_values=self._sanitize_values(new_values),
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )

    async def log_update(
        self,
        user_id: UUID,
        resource_type: str,
        resource_id: UUID,
        old_values: dict,
        new_values: dict,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[dict] = None
    ) -> AuditLog:
        """
        Log an update operation.

        Automatically sanitizes sensitive fields from both old and new values.

        Args:
            user_id: User who performed the update
            resource_type: Type of resource updated (e.g., "invoice", "contact")
            resource_id: ID of the updated resource
            old_values: Dictionary of previous values
            new_values: Dictionary of new values
            ip_address: Optional client IP address
            user_agent: Optional client user agent
            details: Optional additional context

        Returns:
            Created AuditLog model
        """
        return await self.log(
            action=f"update_{resource_type}",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=self._sanitize_values(old_values),
            new_values=self._sanitize_values(new_values),
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )

    async def log_delete(
        self,
        user_id: UUID,
        resource_type: str,
        resource_id: UUID,
        old_values: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[dict] = None
    ) -> AuditLog:
        """
        Log a delete operation.

        Automatically sanitizes sensitive fields from old_values if provided.

        Args:
            user_id: User who performed the delete
            resource_type: Type of resource deleted (e.g., "invoice", "contact")
            resource_id: ID of the deleted resource
            old_values: Optional dictionary of deleted values
            ip_address: Optional client IP address
            user_agent: Optional client user agent
            details: Optional additional context

        Returns:
            Created AuditLog model
        """
        return await self.log(
            action=f"delete_{resource_type}",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=self._sanitize_values(old_values) if old_values else None,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )

    async def log_view_sensitive(
        self,
        user_id: UUID,
        resource_type: str,
        resource_id: UUID,
        fields_accessed: list[str],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log access to sensitive/encrypted data.

        This logs that a user accessed sensitive data, but NOT the data itself.
        Use this when decrypting fields like email, phone, KRA PIN, etc.

        Args:
            user_id: User who accessed the data
            resource_type: Type of resource accessed (e.g., "contact")
            resource_id: ID of the accessed resource
            fields_accessed: List of sensitive field names accessed
            ip_address: Optional client IP address
            user_agent: Optional client user agent

        Returns:
            Created AuditLog model

        Example:
            await audit.log_view_sensitive(
                user_id=current_user.id,
                resource_type="contact",
                resource_id=contact.id,
                fields_accessed=["email", "phone", "kra_pin"],
                ip_address=request.client.host
            )
        """
        return await self.log(
            action=AuditAction.VIEW_SENSITIVE_DATA,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details={"fields_accessed": fields_accessed},
            ip_address=ip_address,
            user_agent=user_agent
        )

    async def log_workflow_transition(
        self,
        user_id: UUID,
        resource_type: str,
        resource_id: UUID,
        action: str,
        old_status: str,
        new_status: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[dict] = None
    ) -> AuditLog:
        """
        Log a workflow status transition.

        Use this for status changes like invoice issue, cancel, or onboarding approval.

        Args:
            user_id: User who performed the transition
            resource_type: Type of resource (e.g., "invoice", "application")
            resource_id: ID of the resource
            action: Action name (e.g., "issue_invoice", "approve_application")
            old_status: Previous status
            new_status: New status
            ip_address: Optional client IP address
            user_agent: Optional client user agent
            details: Optional additional context

        Returns:
            Created AuditLog model

        Example:
            await audit.log_workflow_transition(
                user_id=current_user.id,
                resource_type="invoice",
                resource_id=invoice.id,
                action="issue_invoice",
                old_status="draft",
                new_status="issued",
                ip_address=request.client.host
            )
        """
        transition_details = {
            "old_status": old_status,
            "new_status": new_status
        }

        # Merge with any additional details
        if details:
            transition_details.update(details)

        return await self.log(
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=transition_details,
            ip_address=ip_address,
            user_agent=user_agent
        )

    async def log_bulk_operation(
        self,
        user_id: UUID,
        action: str,
        resource_type: str,
        affected_count: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[dict] = None
    ) -> AuditLog:
        """
        Log a bulk operation affecting multiple resources.

        Use this for operations like bulk import, bulk delete, or batch processing.

        Args:
            user_id: User who performed the operation
            action: Action name (e.g., "bulk_import", "bulk_delete")
            resource_type: Type of resources affected
            affected_count: Number of resources affected
            ip_address: Optional client IP address
            user_agent: Optional client user agent
            details: Optional additional context

        Returns:
            Created AuditLog model
        """
        bulk_details = {"affected_count": affected_count}

        if details:
            bulk_details.update(details)

        return await self.log(
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            details=bulk_details,
            ip_address=ip_address,
            user_agent=user_agent
        )

    def _sanitize_values(self, values: Optional[dict]) -> Optional[dict]:
        """
        Remove sensitive fields from audit values.

        This prevents accidentally logging sensitive data like passwords,
        tokens, or unencrypted personal information.

        Args:
            values: Dictionary of values to sanitize

        Returns:
            Dictionary with sensitive fields redacted, or None if input was None

        Note:
            Sensitive fields are replaced with '[REDACTED]' string.
        """
        if not values:
            return None

        # List of sensitive field names that should never be logged
        sensitive_fields = [
            # Authentication & Security
            'password',
            'password_hash',
            'token',
            'access_token',
            'refresh_token',
            'secret',
            'secret_key',
            'api_key',

            # Personal Identifiable Information (encrypted fields)
            'kra_pin',
            'national_id',
            'bank_account',
            'phone_encrypted',
            'email_encrypted',
            'kra_pin_encrypted',

            # Payment Information
            'card_number',
            'cvv',
            'account_number',

            # Session & Auth
            'session_token',
            'csrf_token',
        ]

        # Create a copy to avoid modifying the original
        sanitized = {}

        for key, value in values.items():
            # Check if field name contains any sensitive keywords
            is_sensitive = any(
                sensitive_field in key.lower()
                for sensitive_field in sensitive_fields
            )

            if is_sensitive:
                sanitized[key] = '[REDACTED]'
            else:
                # Convert complex types to strings for JSON serialization
                if isinstance(value, (datetime, UUID)):
                    sanitized[key] = str(value)
                else:
                    sanitized[key] = value

        return sanitized

    async def cleanup_old_logs(
        self,
        retention_days: int = 365
    ) -> int:
        """
        Delete audit logs older than retention period.

        This is the ONLY method that can delete audit logs.
        Should be run periodically via scheduled task or admin command.

        Args:
            retention_days: Number of days to retain logs (default 365)

        Returns:
            Number of logs deleted

        Note:
            This method commits the transaction.

        Security Note:
            Only system administrators should be able to call this method.
            Consider additional authorization checks in the API endpoint.
        """
        cutoff = datetime.utcnow() - timedelta(days=retention_days)

        # Count logs to be deleted
        count_result = await self.db.execute(
            select(AuditLog.id).where(AuditLog.created_at < cutoff)
        )
        count = len(count_result.all())

        # Delete old logs
        await self.db.execute(
            delete(AuditLog).where(AuditLog.created_at < cutoff)
        )
        await self.db.commit()

        return count

    async def get_audit_logs(
        self,
        user_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        action: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> list[AuditLog]:
        """
        Query audit logs with filtering.

        This is primarily for admin/support staff to investigate security
        events or track data changes.

        Args:
            user_id: Optional filter by user
            resource_type: Optional filter by resource type
            resource_id: Optional filter by resource ID
            action: Optional filter by action
            status: Optional filter by status
            start_date: Optional filter by created_at >= start_date
            end_date: Optional filter by created_at <= end_date
            limit: Maximum number of logs to return (default 100)

        Returns:
            List of AuditLog models

        Security Note:
            Access to audit logs should be restricted to admins and support agents.
        """
        query = select(AuditLog)

        # Apply filters
        if user_id:
            query = query.where(AuditLog.user_id == user_id)

        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)

        if resource_id:
            query = query.where(AuditLog.resource_id == resource_id)

        if action:
            query = query.where(AuditLog.action == action)

        if status:
            query = query.where(AuditLog.status == status)

        if start_date:
            query = query.where(AuditLog.created_at >= start_date)

        if end_date:
            query = query.where(AuditLog.created_at <= end_date)

        # Order by created_at descending (newest first)
        query = query.order_by(AuditLog.created_at.desc())

        # Limit results
        query = query.limit(limit)

        # Execute query
        result = await self.db.execute(query)
        return list(result.scalars().all())


def get_audit_service(db: AsyncSession) -> AuditService:
    """
    Get audit service instance.

    Args:
        db: Database session

    Returns:
        AuditService instance
    """
    return AuditService(db)
