"""
Admin Portal API Endpoints

System administrator endpoints for business directory, internal user management,
audit logs, and analytics.

Permissions:
- system_admin: Full access to all admin operations

Security:
- All endpoints require system_admin role
- Sensitive business data is masked before returning
- All admin actions are logged to audit trail
"""

from typing import Optional
from uuid import UUID
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db, require_role
from app.models.user import User, UserRole
from app.core.security import UserRole as SecurityUserRole
from app.schemas.admin import (
    # Business schemas
    BusinessListItem,
    BusinessListResponse,
    BusinessDetail,
    BusinessUserListItem,
    BusinessUserListResponse,
    # User management schemas
    InternalUserCreate,
    InternalUserUpdate,
    InternalUserResponse,
    InternalUserListResponse,
    # Audit log schemas
    AuditLogResponse,
    AuditLogListResponse,
    AuditLogFilters,
    # Analytics schemas
    AdminDashboardStats,
    SystemHealthMetrics,
    # Masking utilities
    mask_kra_pin,
    mask_phone,
    mask_bank_account,
    mask_email
)
from app.services.admin_service import AdminService


router = APIRouter()


# ============================================================================
# BUSINESS DIRECTORY ENDPOINTS
# ============================================================================

@router.get("/businesses", response_model=BusinessListResponse)
async def list_all_businesses(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by onboarding status"),
    search: Optional[str] = Query(None, max_length=200, description="Search in business name"),
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    List all businesses in the system (system admins only).

    Returns paginated list of businesses with key metrics.
    Supports filtering by onboarding status and searching by name.
    """
    admin_service = AdminService(db)

    # Get businesses
    businesses, total = await admin_service.get_businesses(
        page=page,
        page_size=page_size,
        status_filter=status,
        search=search
    )

    # Build response items with metrics
    business_items = []
    for business in businesses:
        # Get metrics for each business
        metrics = await admin_service.get_business_metrics(business.id)

        item = BusinessListItem(
            id=business.id,
            name=business.name,
            business_type=business.business_type,
            onboarding_status=business.onboarding_status,
            is_active=business.is_active,
            created_at=business.created_at,
            user_count=metrics["user_count"],
            invoice_count=metrics["invoice_count"]
        )
        business_items.append(item)

    # Calculate total pages
    total_pages = ceil(total / page_size) if total > 0 else 0

    return BusinessListResponse(
        businesses=business_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/businesses/{business_id}", response_model=BusinessDetail)
async def get_business_details(
    business_id: UUID,
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed business information with masked sensitive data.

    Returns full business profile with:
    - Masked KRA PIN, phone, email, bank account
    - Tax registration status
    - Subscription information
    - Business metrics (users, invoices, revenue)
    """
    admin_service = AdminService(db)

    # Get business
    business = await admin_service.get_business(business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    # Get metrics
    metrics = await admin_service.get_business_metrics(business_id)

    # Build response with masked sensitive data
    # Note: We need to decrypt encrypted fields first, then mask them
    # For MVP, assuming fields are stored as-is (encryption to be added)
    response = BusinessDetail(
        id=business.id,
        name=business.name,
        business_type=business.business_type,
        industry=business.industry,
        onboarding_status=business.onboarding_status,
        is_active=business.is_active,
        # Masked sensitive fields
        kra_pin_masked=mask_kra_pin(business.kra_pin_encrypted),
        phone_masked=mask_phone(business.phone),
        email_masked=mask_email(business.email),
        bank_account_masked=mask_bank_account(business.bank_account_encrypted),
        # Tax registration
        vat_registered=business.vat_registered,
        tot_registered=business.tot_registered,
        # Address information (non-sensitive)
        address=business.address,
        city=business.city,
        country=business.country,
        postal_code=business.postal_code,
        website=business.website,
        # Subscription
        subscription_tier=business.subscription_tier,
        subscription_expires_at=business.subscription_expires_at,
        # Metadata
        onboarding_completed_at=business.onboarding_completed_at,
        created_at=business.created_at,
        updated_at=business.updated_at,
        # Metrics
        user_count=metrics["user_count"],
        invoice_count=metrics["invoice_count"],
        total_revenue=metrics["total_revenue"]
    )

    return response


@router.get("/businesses/{business_id}/users", response_model=BusinessUserListResponse)
async def get_business_users(
    business_id: UUID,
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    List all users for a specific business.

    Returns user list with masked email addresses.
    """
    admin_service = AdminService(db)

    # Verify business exists
    business = await admin_service.get_business(business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    # Get users
    users = await admin_service.get_business_users(business_id)

    # Build response with masked data
    user_items = []
    for user in users:
        item = BusinessUserListItem(
            id=user.id,
            full_name=user.full_name,
            email_masked=mask_email(user.email_encrypted),
            role=user.role,
            is_active=user.is_active,
            last_login_at=user.last_login_at,
            created_at=user.created_at
        )
        user_items.append(item)

    return BusinessUserListResponse(
        users=user_items,
        total=len(user_items)
    )


@router.post("/businesses/{business_id}/deactivate", response_model=BusinessDetail)
async def deactivate_business(
    business_id: UUID,
    request: Request,
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate a business (soft disable).

    This prevents the business from accessing the system but preserves all data.
    """
    # Get IP address for audit
    ip_address = request.client.host if request.client else None

    admin_service = AdminService(db)

    # Deactivate business
    business = await admin_service.deactivate_business(
        business_id=business_id,
        admin_id=current_user.id,
        ip_address=ip_address
    )

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    # Get metrics for response
    metrics = await admin_service.get_business_metrics(business_id)

    # Build response with masked data
    response = BusinessDetail(
        id=business.id,
        name=business.name,
        business_type=business.business_type,
        industry=business.industry,
        onboarding_status=business.onboarding_status,
        is_active=business.is_active,
        kra_pin_masked=mask_kra_pin(business.kra_pin_encrypted),
        phone_masked=mask_phone(business.phone),
        email_masked=mask_email(business.email),
        bank_account_masked=mask_bank_account(business.bank_account_encrypted),
        vat_registered=business.vat_registered,
        tot_registered=business.tot_registered,
        address=business.address,
        city=business.city,
        country=business.country,
        postal_code=business.postal_code,
        website=business.website,
        subscription_tier=business.subscription_tier,
        subscription_expires_at=business.subscription_expires_at,
        onboarding_completed_at=business.onboarding_completed_at,
        created_at=business.created_at,
        updated_at=business.updated_at,
        user_count=metrics["user_count"],
        invoice_count=metrics["invoice_count"],
        total_revenue=metrics["total_revenue"]
    )

    return response


# ============================================================================
# INTERNAL USER MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/users", response_model=InternalUserListResponse)
async def list_internal_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    List internal users (onboarding agents, support agents, system admins).

    Returns paginated list of internal users with masked sensitive data.
    Excludes business users (business_admin, bookkeeper).
    """
    admin_service = AdminService(db)

    # Get internal users
    users, total = await admin_service.get_internal_users(
        page=page,
        page_size=page_size,
        role_filter=role,
        is_active=is_active
    )

    # Build response with masked data
    user_items = []
    for user in users:
        item = InternalUserResponse(
            id=user.id,
            email_masked=mask_email(user.email_encrypted),
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            phone_masked=mask_phone(user.phone_encrypted) if user.phone_encrypted else None,
            last_login_at=user.last_login_at,
            must_change_password=user.must_change_password,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        user_items.append(item)

    # Calculate total pages
    total_pages = ceil(total / page_size) if total > 0 else 0

    return InternalUserListResponse(
        users=user_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/users", response_model=InternalUserResponse, status_code=status.HTTP_201_CREATED)
async def create_internal_user(
    user_data: InternalUserCreate,
    request: Request,
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new internal user (onboarding_agent, support_agent, or system_admin).

    The user will be created with:
    - Random temporary password
    - must_change_password flag set to True
    - Email notification with login instructions (TODO)

    Only internal roles can be created through this endpoint.
    Business users must be created through the onboarding process.
    """
    # Get IP address for audit
    ip_address = request.client.host if request.client else None

    admin_service = AdminService(db)

    # Create user
    user = await admin_service.create_internal_user(
        user_data=user_data,
        created_by=current_user.id,
        ip_address=ip_address
    )

    # Build response with masked data
    response = InternalUserResponse(
        id=user.id,
        email_masked=mask_email(user.email_encrypted),
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        phone_masked=mask_phone(user.phone_encrypted) if user.phone_encrypted else None,
        last_login_at=user.last_login_at,
        must_change_password=user.must_change_password,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

    return response


@router.get("/users/{user_id}", response_model=InternalUserResponse)
async def get_internal_user(
    user_id: UUID,
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get internal user details by ID.

    Returns user information with masked sensitive data.
    """
    admin_service = AdminService(db)

    # Get user
    user = await admin_service.get_internal_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify it's an internal user
    internal_roles = [UserRole.ONBOARDING_AGENT, UserRole.SUPPORT_AGENT, UserRole.SYSTEM_ADMIN]
    if user.role not in internal_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not an internal user. Use business user endpoints instead."
        )

    # Build response with masked data
    response = InternalUserResponse(
        id=user.id,
        email_masked=mask_email(user.email_encrypted),
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        phone_masked=mask_phone(user.phone_encrypted) if user.phone_encrypted else None,
        last_login_at=user.last_login_at,
        must_change_password=user.must_change_password,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

    return response


@router.put("/users/{user_id}", response_model=InternalUserResponse)
async def update_internal_user(
    user_id: UUID,
    update_data: InternalUserUpdate,
    request: Request,
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an internal user's information.

    Can update name, phone, and active status.
    Email and role cannot be changed after creation.
    """
    # Get IP address for audit
    ip_address = request.client.host if request.client else None

    admin_service = AdminService(db)

    # Update user
    user = await admin_service.update_internal_user(
        user_id=user_id,
        update_data=update_data,
        updated_by=current_user.id,
        ip_address=ip_address
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Build response with masked data
    response = InternalUserResponse(
        id=user.id,
        email_masked=mask_email(user.email_encrypted),
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        phone_masked=mask_phone(user.phone_encrypted) if user.phone_encrypted else None,
        last_login_at=user.last_login_at,
        must_change_password=user.must_change_password,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

    return response


@router.post("/users/{user_id}/deactivate", response_model=InternalUserResponse)
async def deactivate_internal_user(
    user_id: UUID,
    request: Request,
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate an internal user.

    This prevents the user from logging in but preserves their data and audit trail.
    """
    # Prevent self-deactivation
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )

    # Get IP address for audit
    ip_address = request.client.host if request.client else None

    admin_service = AdminService(db)

    # Deactivate user
    user = await admin_service.deactivate_internal_user(
        user_id=user_id,
        deactivated_by=current_user.id,
        ip_address=ip_address
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Build response with masked data
    response = InternalUserResponse(
        id=user.id,
        email_masked=mask_email(user.email_encrypted),
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        phone_masked=mask_phone(user.phone_encrypted) if user.phone_encrypted else None,
        last_login_at=user.last_login_at,
        must_change_password=user.must_change_password,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

    return response


# ============================================================================
# AUDIT LOG ENDPOINTS
# ============================================================================

@router.get("/audit-logs", response_model=AuditLogListResponse)
async def query_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, max_length=100, description="Filter by action"),
    resource_type: Optional[str] = Query(None, max_length=100, description="Filter by resource type"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    start_date: Optional[str] = Query(None, description="Filter from date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter to date (ISO format)"),
    ip_address: Optional[str] = Query(None, max_length=45, description="Filter by IP address"),
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Query audit logs with advanced filtering.

    Returns paginated list of audit log entries.
    Supports filtering by user, action, resource, status, date range, and IP.
    """
    admin_service = AdminService(db)

    # Parse dates if provided
    from datetime import datetime as dt
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = dt.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            )

    if end_date:
        try:
            end_dt = dt.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            )

    # Build filters
    filters = AuditLogFilters(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        status=status_filter,
        start_date=start_dt,
        end_date=end_dt,
        ip_address=ip_address
    )

    # Get audit logs
    logs, total = await admin_service.get_audit_logs(
        filters=filters,
        page=page,
        page_size=page_size
    )

    # Build response
    log_items = []
    for log in logs:
        item = AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            user_name=log.user.full_name if log.user else None,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            status=log.status,
            details=log.details,
            error_message=log.error_message,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            session_id=log.session_id,
            old_values=log.old_values,
            new_values=log.new_values,
            created_at=log.created_at
        )
        log_items.append(item)

    # Calculate total pages
    total_pages = ceil(total / page_size) if total > 0 else 0

    return AuditLogListResponse(
        logs=log_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/audit-logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log_entry(
    log_id: UUID,
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single audit log entry by ID.

    Returns full details of the audit log entry including
    old/new values for modification tracking.
    """
    admin_service = AdminService(db)

    # Get audit log
    log = await admin_service.get_audit_log(log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log entry not found"
        )

    # Build response
    response = AuditLogResponse(
        id=log.id,
        user_id=log.user_id,
        user_name=log.user.full_name if log.user else None,
        action=log.action,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        status=log.status,
        details=log.details,
        error_message=log.error_message,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        session_id=log.session_id,
        old_values=log.old_values,
        new_values=log.new_values,
        created_at=log.created_at
    )

    return response


# ============================================================================
# ANALYTICS & DASHBOARD ENDPOINTS
# ============================================================================

@router.get("/dashboard", response_model=AdminDashboardStats)
async def get_admin_dashboard(
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get admin dashboard statistics.

    Returns comprehensive system metrics including:
    - Business counts and status
    - User counts by role
    - Invoice and revenue metrics
    - Activity metrics (new registrations, support tickets)
    """
    admin_service = AdminService(db)

    # Get dashboard stats
    stats = await admin_service.get_dashboard_stats()

    return AdminDashboardStats(**stats)


@router.get("/system-health", response_model=SystemHealthMetrics)
async def get_system_health(
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get system health and performance metrics.

    Returns:
    - Database status
    - Audit log metrics
    - Security event counts
    - API activity metrics
    - Active session counts
    """
    admin_service = AdminService(db)

    # Get system health metrics
    health = await admin_service.get_system_health()

    return SystemHealthMetrics(**health)
