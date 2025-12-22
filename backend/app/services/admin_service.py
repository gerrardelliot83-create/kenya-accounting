"""
Admin Service

Business logic for system administrator operations.
Handles business directory, internal user management, audit logs, and analytics.

Security Notes:
- All operations require system_admin role
- Sensitive data is masked before returning to API
- All admin actions are logged to audit trail
"""

from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import select, update, func, and_, or_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.user import User, UserRole
from app.models.business import Business
from app.models.audit_log import AuditLog, AuditAction, AuditStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.support_ticket import SupportTicket, TicketStatus
from app.schemas.admin import (
    InternalUserCreate,
    InternalUserUpdate,
    AuditLogFilters,
    mask_kra_pin,
    mask_phone,
    mask_bank_account,
    mask_email
)
from app.core.security import hash_password


class AdminService:
    """Service for system administrator database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize admin service.

        Args:
            db: Database session
        """
        self.db = db

    # ========================================================================
    # BUSINESS MANAGEMENT
    # ========================================================================

    async def get_businesses(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Business], int]:
        """
        Get all businesses with metrics (paginated).

        Args:
            page: Page number
            page_size: Items per page
            status_filter: Filter by onboarding_status
            search: Search in business name

        Returns:
            Tuple of (businesses, total_count)
        """
        query = select(Business)

        # Apply filters
        if status_filter:
            query = query.where(Business.onboarding_status == status_filter)

        if search:
            search_term = f"%{search}%"
            query = query.where(Business.name.ilike(search_term))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination and ordering
        query = query.order_by(Business.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.db.execute(query)
        businesses = result.scalars().all()

        return list(businesses), total

    async def get_business(self, business_id: UUID) -> Optional[Business]:
        """
        Get a business by ID.

        Args:
            business_id: Business UUID

        Returns:
            Business instance or None if not found
        """
        result = await self.db.execute(
            select(Business).where(Business.id == business_id)
        )
        return result.scalar_one_or_none()

    async def get_business_users(self, business_id: UUID) -> List[User]:
        """
        Get all users for a specific business.

        Args:
            business_id: Business UUID

        Returns:
            List of users
        """
        result = await self.db.execute(
            select(User)
            .where(User.business_id == business_id)
            .order_by(User.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_business_metrics(self, business_id: UUID) -> Dict[str, Any]:
        """
        Get metrics for a specific business.

        Args:
            business_id: Business UUID

        Returns:
            Dictionary with business metrics
        """
        # Get user count
        user_count_result = await self.db.execute(
            select(func.count(User.id)).where(User.business_id == business_id)
        )
        user_count = user_count_result.scalar_one()

        # Get invoice count
        invoice_count_result = await self.db.execute(
            select(func.count(Invoice.id)).where(Invoice.business_id == business_id)
        )
        invoice_count = invoice_count_result.scalar_one()

        # Get total revenue (from paid invoices)
        revenue_result = await self.db.execute(
            select(func.sum(Invoice.total_amount))
            .where(
                and_(
                    Invoice.business_id == business_id,
                    Invoice.status == InvoiceStatus.PAID.value
                )
            )
        )
        total_revenue = float(revenue_result.scalar_one() or 0.0)

        return {
            "user_count": user_count,
            "invoice_count": invoice_count,
            "total_revenue": total_revenue
        }

    async def deactivate_business(
        self,
        business_id: UUID,
        admin_id: UUID,
        ip_address: Optional[str] = None
    ) -> Optional[Business]:
        """
        Deactivate a business (soft disable).

        Args:
            business_id: Business UUID
            admin_id: Admin performing the action
            ip_address: Admin's IP address for audit

        Returns:
            Updated business or None if not found
        """
        business = await self.get_business(business_id)
        if not business:
            return None

        # Update business status
        business.is_active = False

        # Log audit entry
        await self._log_audit(
            user_id=admin_id,
            action="deactivate_business",
            resource_type="business",
            resource_id=business_id,
            details={"business_name": business.name},
            ip_address=ip_address
        )

        await self.db.commit()
        await self.db.refresh(business)

        return business

    # ========================================================================
    # INTERNAL USER MANAGEMENT
    # ========================================================================

    async def get_internal_users(
        self,
        page: int = 1,
        page_size: int = 20,
        role_filter: Optional[UserRole] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[User], int]:
        """
        Get internal users (agents and admins) with pagination.

        Internal users are those with roles: onboarding_agent, support_agent, system_admin.

        Args:
            page: Page number
            page_size: Items per page
            role_filter: Filter by role
            is_active: Filter by active status

        Returns:
            Tuple of (users, total_count)
        """
        # Define internal roles
        internal_roles = [
            UserRole.ONBOARDING_AGENT,
            UserRole.SUPPORT_AGENT,
            UserRole.SYSTEM_ADMIN
        ]

        query = select(User).where(User.role.in_(internal_roles))

        # Apply filters
        if role_filter:
            query = query.where(User.role == role_filter)

        if is_active is not None:
            query = query.where(User.is_active == is_active)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination and ordering
        query = query.order_by(User.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.db.execute(query)
        users = result.scalars().all()

        return list(users), total

    async def get_internal_user(self, user_id: UUID) -> Optional[User]:
        """
        Get an internal user by ID.

        Args:
            user_id: User UUID

        Returns:
            User instance or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_internal_user(
        self,
        user_data: InternalUserCreate,
        created_by: UUID,
        ip_address: Optional[str] = None
    ) -> User:
        """
        Create a new internal user (onboarding_agent, support_agent, or system_admin).

        Args:
            user_data: User creation data
            created_by: Admin creating the user
            ip_address: Admin's IP address for audit

        Returns:
            Created user instance

        Note:
            - User will be created with a random password
            - must_change_password will be set to True
            - User will receive email with login instructions
        """
        # Create user with encrypted sensitive fields
        # For MVP, we'll store email directly (encryption can be added later)
        user = User(
            email_encrypted=user_data.email,  # TODO: Encrypt in production
            phone_encrypted=user_data.phone if user_data.phone else None,  # TODO: Encrypt
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role,
            is_active=True,
            must_change_password=True,
            business_id=None  # Internal users are not associated with a business
        )

        # Generate a random password (user must change on first login)
        import secrets
        temp_password = secrets.token_urlsafe(16)
        user.password_hash = hash_password(temp_password)

        self.db.add(user)
        await self.db.flush()

        # Log audit entry
        await self._log_audit(
            user_id=created_by,
            action=AuditAction.CREATE_USER,
            resource_type="user",
            resource_id=user.id,
            details={
                "email": user_data.email,
                "role": user_data.role.value,
                "created_by": str(created_by)
            },
            ip_address=ip_address
        )

        await self.db.commit()
        await self.db.refresh(user)

        # TODO: Send email with temporary password

        return user

    async def update_internal_user(
        self,
        user_id: UUID,
        update_data: InternalUserUpdate,
        updated_by: UUID,
        ip_address: Optional[str] = None
    ) -> Optional[User]:
        """
        Update an internal user.

        Args:
            user_id: User UUID
            update_data: Update data
            updated_by: Admin performing the update
            ip_address: Admin's IP address for audit

        Returns:
            Updated user or None if not found
        """
        user = await self.get_internal_user(user_id)
        if not user:
            return None

        changes = {}

        # Track changes for audit
        if update_data.first_name is not None and update_data.first_name != user.first_name:
            changes["first_name"] = {"old": user.first_name, "new": update_data.first_name}
            user.first_name = update_data.first_name

        if update_data.last_name is not None and update_data.last_name != user.last_name:
            changes["last_name"] = {"old": user.last_name, "new": update_data.last_name}
            user.last_name = update_data.last_name

        if update_data.phone is not None:
            changes["phone"] = {"old": "***", "new": "***"}  # Don't log actual phone
            user.phone_encrypted = update_data.phone  # TODO: Encrypt

        if update_data.is_active is not None and update_data.is_active != user.is_active:
            changes["is_active"] = {"old": user.is_active, "new": update_data.is_active}
            user.is_active = update_data.is_active

        # Log audit if there were changes
        if changes:
            await self._log_audit(
                user_id=updated_by,
                action=AuditAction.UPDATE_USER,
                resource_type="user",
                resource_id=user_id,
                details={"changes": changes},
                ip_address=ip_address
            )

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def deactivate_internal_user(
        self,
        user_id: UUID,
        deactivated_by: UUID,
        ip_address: Optional[str] = None
    ) -> Optional[User]:
        """
        Deactivate an internal user.

        Args:
            user_id: User UUID
            deactivated_by: Admin performing the deactivation
            ip_address: Admin's IP address for audit

        Returns:
            Updated user or None if not found
        """
        update_data = InternalUserUpdate(is_active=False)
        return await self.update_internal_user(user_id, update_data, deactivated_by, ip_address)

    # ========================================================================
    # AUDIT LOG QUERIES
    # ========================================================================

    async def get_audit_logs(
        self,
        filters: Optional[AuditLogFilters] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[AuditLog], int]:
        """
        Query audit logs with filters and pagination.

        Args:
            filters: Optional filters
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (audit_logs, total_count)
        """
        query = select(AuditLog).options(
            selectinload(AuditLog.user)
        )

        # Apply filters
        if filters:
            if filters.user_id:
                query = query.where(AuditLog.user_id == filters.user_id)

            if filters.action:
                query = query.where(AuditLog.action == filters.action)

            if filters.resource_type:
                query = query.where(AuditLog.resource_type == filters.resource_type)

            if filters.status:
                query = query.where(AuditLog.status == filters.status)

            if filters.start_date:
                query = query.where(AuditLog.created_at >= filters.start_date)

            if filters.end_date:
                query = query.where(AuditLog.created_at <= filters.end_date)

            if filters.ip_address:
                query = query.where(AuditLog.ip_address == filters.ip_address)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination and ordering (most recent first)
        query = query.order_by(AuditLog.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.db.execute(query)
        logs = result.scalars().all()

        return list(logs), total

    async def get_audit_log(self, log_id: UUID) -> Optional[AuditLog]:
        """
        Get a single audit log entry by ID.

        Args:
            log_id: Audit log UUID

        Returns:
            AuditLog instance or None if not found
        """
        result = await self.db.execute(
            select(AuditLog)
            .options(selectinload(AuditLog.user))
            .where(AuditLog.id == log_id)
        )
        return result.scalar_one_or_none()

    # ========================================================================
    # ANALYTICS & DASHBOARD
    # ========================================================================

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Get admin dashboard statistics.

        Returns:
            Dictionary with comprehensive system metrics
        """
        # Business metrics
        total_businesses_result = await self.db.execute(
            select(func.count(Business.id))
        )
        total_businesses = total_businesses_result.scalar_one()

        active_businesses_result = await self.db.execute(
            select(func.count(Business.id)).where(Business.is_active == True)
        )
        active_businesses = active_businesses_result.scalar_one()

        pending_onboarding_result = await self.db.execute(
            select(func.count(Business.id)).where(Business.onboarding_status == "pending")
        )
        pending_onboarding = pending_onboarding_result.scalar_one()

        completed_onboarding_result = await self.db.execute(
            select(func.count(Business.id)).where(Business.onboarding_status == "completed")
        )
        completed_onboarding = completed_onboarding_result.scalar_one()

        # User metrics
        total_users_result = await self.db.execute(
            select(func.count(User.id))
        )
        total_users = total_users_result.scalar_one()

        active_users_result = await self.db.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        active_users = active_users_result.scalar_one()

        # User counts by role
        role_counts = {}
        for role in UserRole:
            role_count_result = await self.db.execute(
                select(func.count(User.id)).where(User.role == role)
            )
            role_counts[role.value] = role_count_result.scalar_one()

        # Invoice metrics
        total_invoices_result = await self.db.execute(
            select(func.count(Invoice.id))
        )
        total_invoices = total_invoices_result.scalar_one()

        # Invoices this month
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        invoices_this_month_result = await self.db.execute(
            select(func.count(Invoice.id))
            .where(Invoice.created_at >= month_start)
        )
        invoices_this_month = invoices_this_month_result.scalar_one()

        # Total revenue (from paid invoices)
        total_revenue_result = await self.db.execute(
            select(func.sum(Invoice.total_amount))
            .where(Invoice.status == InvoiceStatus.PAID.value)
        )
        total_revenue = float(total_revenue_result.scalar_one() or 0.0)

        # Revenue this month
        revenue_this_month_result = await self.db.execute(
            select(func.sum(Invoice.total_amount))
            .where(
                and_(
                    Invoice.status == InvoiceStatus.PAID.value,
                    Invoice.updated_at >= month_start
                )
            )
        )
        revenue_this_month = float(revenue_this_month_result.scalar_one() or 0.0)

        # Activity metrics (this week)
        week_start = now - timedelta(days=7)

        new_businesses_this_week_result = await self.db.execute(
            select(func.count(Business.id))
            .where(Business.created_at >= week_start)
        )
        new_businesses_this_week = new_businesses_this_week_result.scalar_one()

        new_users_this_week_result = await self.db.execute(
            select(func.count(User.id))
            .where(User.created_at >= week_start)
        )
        new_users_this_week = new_users_this_week_result.scalar_one()

        # Active support tickets
        active_support_tickets_result = await self.db.execute(
            select(func.count(SupportTicket.id))
            .where(
                SupportTicket.status.in_([
                    TicketStatus.OPEN.value,
                    TicketStatus.IN_PROGRESS.value
                ])
            )
        )
        active_support_tickets = active_support_tickets_result.scalar_one()

        return {
            "total_businesses": total_businesses,
            "active_businesses": active_businesses,
            "pending_onboarding": pending_onboarding,
            "completed_onboarding": completed_onboarding,
            "total_users": total_users,
            "active_users": active_users,
            "business_admins": role_counts.get(UserRole.BUSINESS_ADMIN.value, 0),
            "bookkeepers": role_counts.get(UserRole.BOOKKEEPER.value, 0),
            "support_agents": role_counts.get(UserRole.SUPPORT_AGENT.value, 0),
            "onboarding_agents": role_counts.get(UserRole.ONBOARDING_AGENT.value, 0),
            "system_admins": role_counts.get(UserRole.SYSTEM_ADMIN.value, 0),
            "total_invoices": total_invoices,
            "invoices_this_month": invoices_this_month,
            "total_revenue": total_revenue,
            "revenue_this_month": revenue_this_month,
            "new_businesses_this_week": new_businesses_this_week,
            "new_users_this_week": new_users_this_week,
            "active_support_tickets": active_support_tickets
        }

    async def get_system_health(self) -> Dict[str, Any]:
        """
        Get system health and performance metrics.

        Returns:
            Dictionary with system health metrics
        """
        # Database status (basic check - if we can query, it's healthy)
        database_status = "healthy"

        # Total records (sample count across key tables)
        business_count = await self.db.execute(select(func.count(Business.id)))
        user_count = await self.db.execute(select(func.count(User.id)))
        invoice_count = await self.db.execute(select(func.count(Invoice.id)))

        total_records = (
            business_count.scalar_one() +
            user_count.scalar_one() +
            invoice_count.scalar_one()
        )

        # Audit metrics
        total_audit_logs_result = await self.db.execute(
            select(func.count(AuditLog.id))
        )
        total_audit_logs = total_audit_logs_result.scalar_one()

        # Failed logins in last 24 hours
        day_ago = datetime.utcnow() - timedelta(days=1)
        failed_logins_result = await self.db.execute(
            select(func.count(AuditLog.id))
            .where(
                and_(
                    AuditLog.action == "login_failed",
                    AuditLog.created_at >= day_ago
                )
            )
        )
        failed_logins_24h = failed_logins_result.scalar_one()

        # Security events in last 24 hours (failed logins + permission denied)
        security_events_result = await self.db.execute(
            select(func.count(AuditLog.id))
            .where(
                and_(
                    AuditLog.action.in_(["login_failed", "permission_denied", "unauthorized_access"]),
                    AuditLog.created_at >= day_ago
                )
            )
        )
        security_events_24h = security_events_result.scalar_one()

        # API calls in last 24 hours (all audit log entries)
        api_calls_result = await self.db.execute(
            select(func.count(AuditLog.id))
            .where(AuditLog.created_at >= day_ago)
        )
        api_calls_24h = api_calls_result.scalar_one()

        # Active sessions (count distinct session_ids in last hour)
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        active_sessions_result = await self.db.execute(
            select(func.count(func.distinct(AuditLog.session_id)))
            .where(
                and_(
                    AuditLog.session_id.isnot(None),
                    AuditLog.created_at >= hour_ago
                )
            )
        )
        active_sessions = active_sessions_result.scalar_one()

        return {
            "database_status": database_status,
            "total_records": total_records,
            "total_audit_logs": total_audit_logs,
            "failed_logins_24h": failed_logins_24h,
            "security_events_24h": security_events_24h,
            "api_calls_24h": api_calls_24h,
            "active_sessions": active_sessions,
            "uptime_hours": None,  # Would require external monitoring
            "last_backup": None  # Would require backup system integration
        }

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def _log_audit(
        self,
        user_id: UUID,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        status: str = "success"
    ) -> None:
        """
        Log admin action to audit trail.

        Args:
            user_id: User performing action
            action: Action performed
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            details: Additional details
            ip_address: User's IP address
            status: Action status (success, failure, error)
        """
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            status=status
        )
        self.db.add(audit_entry)
