"""
Onboarding Portal API Endpoints

Business onboarding application endpoints for onboarding agents and system admins.
Provides complete CRUD operations, submission, review, approval, and rejection.

Permissions:
- onboarding_agent: Can create, view, update, submit, review all applications
- system_admin: Full access to all onboarding operations

Security:
- All sensitive fields are encrypted in database
- Decrypted values only shown to authorized agents
- RLS policies enforce access control
- All status changes are audit logged
"""

from typing import Optional
from uuid import UUID
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db, require_role
from app.models.user import User
from app.core.security import UserRole
from app.models.business_application import OnboardingStatus
from app.core.encryption import get_encryption_service
from app.schemas.onboarding import (
    BusinessApplicationCreate,
    BusinessApplicationUpdate,
    BusinessApplicationResponse,
    BusinessApplicationListResponse,
    BusinessApplicationListItem,
    ApprovalRequest,
    RejectionRequest,
    InfoRequest,
    ApprovalResponse,
    ApplicationFilters,
    OnboardingStatsResponse
)
from app.services.onboarding_service import OnboardingService


router = APIRouter()


def _decrypt_application_fields(application, encryption_service) -> BusinessApplicationResponse:
    """
    Helper to decrypt application fields and build response.

    Args:
        application: BusinessApplication model instance
        encryption_service: EncryptionService instance

    Returns:
        BusinessApplicationResponse with decrypted fields
    """
    response = BusinessApplicationResponse.model_validate(application)

    # Decrypt sensitive fields for authorized agents
    if application.kra_pin_encrypted:
        response.kra_pin = encryption_service.decrypt_optional(application.kra_pin_encrypted)

    if application.phone_encrypted:
        response.phone = encryption_service.decrypt_optional(application.phone_encrypted)

    if application.email_encrypted:
        response.email = encryption_service.decrypt_optional(application.email_encrypted)

    if application.owner_national_id_encrypted:
        response.owner_national_id = encryption_service.decrypt_optional(application.owner_national_id_encrypted)

    if application.owner_phone_encrypted:
        response.owner_phone = encryption_service.decrypt_optional(application.owner_phone_encrypted)

    if application.owner_email_encrypted:
        response.owner_email = encryption_service.decrypt_optional(application.owner_email_encrypted)

    if application.bank_account_encrypted:
        response.bank_account = encryption_service.decrypt_optional(application.bank_account_encrypted)

    # Add agent names if available
    if application.reviewer:
        response.reviewer_name = application.reviewer.full_name

    if application.creator:
        response.creator_name = application.creator.full_name

    return response


# ============================================================================
# APPLICATION CRUD ENDPOINTS
# ============================================================================

@router.post("/applications", response_model=BusinessApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    application_data: BusinessApplicationCreate,
    request: Request,
    current_user: User = Depends(require_role([UserRole.ONBOARDING_AGENT, UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new business application (agents only).

    Creates application in 'draft' status with encrypted sensitive fields.
    All mandatory encrypted fields (kra_pin, phone, email, national_id, bank_account)
    are automatically encrypted before storage.

    Returns the created application with decrypted fields for agent review.
    """
    # Get IP address for audit
    ip_address = request.client.host if request.client else None

    # Create onboarding service
    onboarding_service = OnboardingService(db)

    # Create application
    application = await onboarding_service.create_application(
        agent_id=current_user.id,
        application_data=application_data,
        ip_address=ip_address
    )

    # Build response with decrypted fields
    encryption_service = get_encryption_service()
    return _decrypt_application_fields(application, encryption_service)


@router.get("/applications", response_model=BusinessApplicationListResponse)
async def list_applications(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[OnboardingStatus] = Query(None, alias="status", description="Filter by status"),
    created_by: Optional[UUID] = Query(None, description="Filter by creating agent"),
    reviewed_by: Optional[UUID] = Query(None, description="Filter by reviewing agent"),
    county: Optional[str] = Query(None, description="Filter by county"),
    search: Optional[str] = Query(None, max_length=200, description="Search in business/owner name"),
    current_user: User = Depends(require_role([UserRole.ONBOARDING_AGENT, UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    List all business applications (agents only).

    Returns applications with pagination and filtering.
    Supports filtering by status, agent, county, and search term.

    Note: Sensitive fields are NOT included in list view for performance.
    Use GET /applications/{id} to view full details with decrypted fields.
    """
    # Create onboarding service
    onboarding_service = OnboardingService(db)

    # Build filters
    filters = ApplicationFilters(
        status=status_filter,
        created_by=created_by,
        reviewed_by=reviewed_by,
        county=county,
        search=search
    )

    # Get applications
    applications, total = await onboarding_service.get_applications(
        filters=filters,
        page=page,
        page_size=page_size
    )

    # Convert to list response (no decryption for list view)
    application_items = []
    for app in applications:
        item = BusinessApplicationListItem.model_validate(app)

        # Add agent names if available
        if app.creator:
            item.creator_name = app.creator.full_name
        if app.reviewer:
            item.reviewer_name = app.reviewer.full_name

        application_items.append(item)

    # Calculate total pages
    total_pages = ceil(total / page_size) if total > 0 else 0

    return BusinessApplicationListResponse(
        applications=application_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/applications/{application_id}", response_model=BusinessApplicationResponse)
async def get_application(
    application_id: UUID,
    current_user: User = Depends(require_role([UserRole.ONBOARDING_AGENT, UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a business application by ID with full details (agents only).

    Returns application with ALL decrypted sensitive fields.
    Use this endpoint to view complete application details for review.
    """
    # Create onboarding service
    onboarding_service = OnboardingService(db)

    # Get application
    application = await onboarding_service.get_application(
        application_id=application_id,
        agent_id=current_user.id
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    # Build response with decrypted fields
    encryption_service = get_encryption_service()
    return _decrypt_application_fields(application, encryption_service)


@router.put("/applications/{application_id}", response_model=BusinessApplicationResponse)
async def update_application(
    application_id: UUID,
    update_data: BusinessApplicationUpdate,
    request: Request,
    current_user: User = Depends(require_role([UserRole.ONBOARDING_AGENT, UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Update business application details (agents only).

    Only applications in 'draft' or 'info_requested' status can be updated.
    Approved, rejected, and submitted applications cannot be edited.

    All sensitive fields are automatically encrypted before storage.
    """
    # Get IP address for audit
    ip_address = request.client.host if request.client else None

    # Create onboarding service
    onboarding_service = OnboardingService(db)

    # Update application
    application = await onboarding_service.update_application(
        application_id=application_id,
        update_data=update_data,
        agent_id=current_user.id,
        ip_address=ip_address
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found or cannot be updated (check status)"
        )

    # Build response with decrypted fields
    encryption_service = get_encryption_service()
    return _decrypt_application_fields(application, encryption_service)


# ============================================================================
# APPLICATION WORKFLOW ENDPOINTS
# ============================================================================

@router.post("/applications/{application_id}/submit", response_model=BusinessApplicationResponse)
async def submit_application(
    application_id: UUID,
    request: Request,
    current_user: User = Depends(require_role([UserRole.ONBOARDING_AGENT, UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit application for review (agents only).

    Changes application status from 'draft' or 'info_requested' to 'submitted'.
    Sets submitted_at timestamp.

    Only applications in 'draft' or 'info_requested' status can be submitted.
    """
    # Get IP address for audit
    ip_address = request.client.host if request.client else None

    # Create onboarding service
    onboarding_service = OnboardingService(db)

    # Submit application
    application = await onboarding_service.submit_application(
        application_id=application_id,
        agent_id=current_user.id,
        ip_address=ip_address
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found or cannot be submitted (check status)"
        )

    # Build response with decrypted fields
    encryption_service = get_encryption_service()
    return _decrypt_application_fields(application, encryption_service)


@router.post("/applications/{application_id}/approve", response_model=ApprovalResponse)
async def approve_application(
    application_id: UUID,
    approval_data: ApprovalRequest,
    request: Request,
    current_user: User = Depends(require_role([UserRole.ONBOARDING_AGENT, UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Approve business application (agents only).

    On approval, this endpoint will:
    1. Create a new business record with encrypted sensitive data
    2. Create a business_admin user account with temporary password
    3. Update application status to 'approved'
    4. Link application to created business
    5. Return generated credentials for the business admin

    IMPORTANT: Save the returned credentials securely!
    The temporary password is only shown once and must be provided to the business owner.
    The business admin will be required to change the password on first login.

    Only applications in 'submitted' or 'under_review' status can be approved.
    """
    # Get IP address for audit
    ip_address = request.client.host if request.client else None

    # Create onboarding service
    onboarding_service = OnboardingService(db)

    # Approve application
    approval_response = await onboarding_service.approve_application(
        application_id=application_id,
        agent_id=current_user.id,
        approval_data=approval_data,
        ip_address=ip_address
    )

    if not approval_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found or cannot be approved (check status)"
        )

    return approval_response


@router.post("/applications/{application_id}/reject", response_model=BusinessApplicationResponse)
async def reject_application(
    application_id: UUID,
    rejection_data: RejectionRequest,
    request: Request,
    current_user: User = Depends(require_role([UserRole.ONBOARDING_AGENT, UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Reject business application with reason (agents only).

    Changes application status to 'rejected' and records rejection reason.
    Rejection reason is REQUIRED and must be at least 10 characters.

    Only applications in 'submitted' or 'under_review' status can be rejected.
    """
    # Get IP address for audit
    ip_address = request.client.host if request.client else None

    # Create onboarding service
    onboarding_service = OnboardingService(db)

    # Reject application
    application = await onboarding_service.reject_application(
        application_id=application_id,
        agent_id=current_user.id,
        rejection_data=rejection_data,
        ip_address=ip_address
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found or cannot be rejected (check status)"
        )

    # Build response with decrypted fields
    encryption_service = get_encryption_service()
    return _decrypt_application_fields(application, encryption_service)


@router.post("/applications/{application_id}/request-info", response_model=BusinessApplicationResponse)
async def request_more_info(
    application_id: UUID,
    info_request_data: InfoRequest,
    request: Request,
    current_user: User = Depends(require_role([UserRole.ONBOARDING_AGENT, UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Request more information from applicant (agents only).

    Changes application status to 'info_requested' and records the information needed.
    Info request note is REQUIRED and must be at least 10 characters.

    The applicant can then update the application and re-submit.
    Only applications in 'submitted' or 'under_review' status can have info requested.
    """
    # Get IP address for audit
    ip_address = request.client.host if request.client else None

    # Create onboarding service
    onboarding_service = OnboardingService(db)

    # Request info
    application = await onboarding_service.request_info(
        application_id=application_id,
        agent_id=current_user.id,
        info_request_data=info_request_data,
        ip_address=ip_address
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found or cannot request info (check status)"
        )

    # Build response with decrypted fields
    encryption_service = get_encryption_service()
    return _decrypt_application_fields(application, encryption_service)


# ============================================================================
# STATISTICS & DASHBOARD
# ============================================================================

@router.get("/stats", response_model=OnboardingStatsResponse)
async def get_onboarding_stats(
    current_user: User = Depends(require_role([UserRole.ONBOARDING_AGENT, UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get onboarding dashboard statistics (agents only).

    Returns real-time metrics for onboarding team:
    - Application counts by status
    - Today's submission and approval metrics
    - Average review time
    - Pending review count

    Use this endpoint to build agent dashboard.
    """
    onboarding_service = OnboardingService(db)
    stats = await onboarding_service.get_onboarding_stats()

    return stats
