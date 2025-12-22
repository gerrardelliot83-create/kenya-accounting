"""
Onboarding Service

Business logic for business onboarding application operations.
Handles application CRUD, submission, review, approval, and rejection.

Security Notes:
- ALL sensitive fields MUST be encrypted before storage
- Decrypt only for authorized agents (onboarding_agent, system_admin)
- Audit logging for ALL status changes
- Row-level security enforced by database policies
- Never log decrypted sensitive data

On Approval Flow:
1. Create business record with encrypted data
2. Create business_admin user with temporary password
3. Link application to created business
4. Send credentials to business owner
"""

from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, date, timedelta
import secrets
import string

from sqlalchemy import select, update, func, and_, or_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.business_application import BusinessApplication, OnboardingStatus
from app.models.business import Business
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog, AuditAction
from app.core.encryption import get_encryption_service
from app.schemas.onboarding import (
    BusinessApplicationCreate,
    BusinessApplicationUpdate,
    ApprovalRequest,
    RejectionRequest,
    InfoRequest,
    ApplicationFilters,
    OnboardingStatsResponse,
    ApprovalResponse
)
from app.services.email_service import get_email_service


class OnboardingService:
    """Service for business onboarding application operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize onboarding service.

        Args:
            db: Database session
        """
        self.db = db
        self.encryption_service = get_encryption_service()

    async def _log_application_audit(
        self,
        application_id: UUID,
        user_id: UUID,
        action: AuditAction,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log application-related action to audit log.

        Args:
            application_id: Application UUID
            user_id: User performing action
            action: Audit action type
            details: Additional details
            ip_address: User's IP address
        """
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type="business_application",
            resource_id=application_id,
            details=details or {},
            ip_address=ip_address
        )
        self.db.add(audit_entry)

    def _generate_temporary_password(self, length: int = 12) -> str:
        """
        Generate a secure temporary password.

        Args:
            length: Password length (minimum 12)

        Returns:
            Generated password
        """
        if length < 12:
            length = 12

        # Use uppercase, lowercase, digits, and special characters
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))

        # Ensure password has at least one of each character type
        if not any(c.isupper() for c in password):
            password = password[:-1] + secrets.choice(string.ascii_uppercase)
        if not any(c.isdigit() for c in password):
            password = password[:-1] + secrets.choice(string.digits)

        return password

    async def create_application(
        self,
        agent_id: UUID,
        application_data: BusinessApplicationCreate,
        ip_address: Optional[str] = None
    ) -> BusinessApplication:
        """
        Create a new business application.

        Args:
            agent_id: Onboarding agent creating the application
            application_data: Application creation data
            ip_address: Agent's IP address for audit

        Returns:
            Created application instance
        """
        # Encrypt sensitive fields
        encrypted_data = {}

        if application_data.kra_pin:
            encrypted_data['kra_pin_encrypted'] = self.encryption_service.encrypt(application_data.kra_pin)

        if application_data.phone:
            encrypted_data['phone_encrypted'] = self.encryption_service.encrypt(application_data.phone)

        if application_data.email:
            encrypted_data['email_encrypted'] = self.encryption_service.encrypt(application_data.email)

        if application_data.owner_national_id:
            encrypted_data['owner_national_id_encrypted'] = self.encryption_service.encrypt(application_data.owner_national_id)

        if application_data.owner_phone:
            encrypted_data['owner_phone_encrypted'] = self.encryption_service.encrypt(application_data.owner_phone)

        if application_data.owner_email:
            encrypted_data['owner_email_encrypted'] = self.encryption_service.encrypt(application_data.owner_email)

        if application_data.bank_account:
            encrypted_data['bank_account_encrypted'] = self.encryption_service.encrypt(application_data.bank_account)

        # Create application
        application = BusinessApplication(
            business_name=application_data.business_name,
            business_type=application_data.business_type,
            county=application_data.county,
            sub_county=application_data.sub_county,
            owner_name=application_data.owner_name,
            vat_registered=application_data.vat_registered,
            tot_registered=application_data.tot_registered,
            notes=application_data.notes,
            created_by=agent_id,
            status=OnboardingStatus.DRAFT,
            **encrypted_data
        )

        self.db.add(application)
        await self.db.flush()

        # Log audit entry
        await self._log_application_audit(
            application_id=application.id,
            user_id=agent_id,
            action=AuditAction.CREATE,
            details={
                "business_name": application_data.business_name,
                "status": "draft"
            },
            ip_address=ip_address
        )

        await self.db.commit()
        await self.db.refresh(application)

        return application

    async def get_application(
        self,
        application_id: UUID,
        agent_id: Optional[UUID] = None
    ) -> Optional[BusinessApplication]:
        """
        Get a business application by ID.

        Args:
            application_id: Application UUID
            agent_id: Optional agent ID for scoping (not used currently, RLS handles it)

        Returns:
            Application instance or None if not found
        """
        query = select(BusinessApplication).where(BusinessApplication.id == application_id)

        # Load relationships
        query = query.options(
            selectinload(BusinessApplication.reviewer),
            selectinload(BusinessApplication.creator),
            selectinload(BusinessApplication.approved_business)
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_applications(
        self,
        filters: Optional[ApplicationFilters] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[BusinessApplication], int]:
        """
        Get business applications with filters and pagination.

        Args:
            filters: Optional filters
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (applications, total_count)
        """
        query = select(BusinessApplication)

        # Apply filters
        if filters:
            if filters.status:
                query = query.where(BusinessApplication.status == filters.status)
            if filters.created_by:
                query = query.where(BusinessApplication.created_by == filters.created_by)
            if filters.reviewed_by:
                query = query.where(BusinessApplication.reviewed_by == filters.reviewed_by)
            if filters.county:
                query = query.where(BusinessApplication.county == filters.county)
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.where(
                    or_(
                        BusinessApplication.business_name.ilike(search_term),
                        BusinessApplication.owner_name.ilike(search_term)
                    )
                )
            if filters.date_from:
                query = query.where(BusinessApplication.created_at >= filters.date_from)
            if filters.date_to:
                query = query.where(BusinessApplication.created_at <= filters.date_to)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination and ordering
        query = query.options(
            selectinload(BusinessApplication.reviewer),
            selectinload(BusinessApplication.creator)
        ).order_by(BusinessApplication.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.db.execute(query)
        applications = result.scalars().all()

        return list(applications), total

    async def update_application(
        self,
        application_id: UUID,
        update_data: BusinessApplicationUpdate,
        agent_id: UUID,
        ip_address: Optional[str] = None
    ) -> Optional[BusinessApplication]:
        """
        Update application details (only for draft or info_requested status).

        Args:
            application_id: Application UUID
            update_data: Update data
            agent_id: Agent performing the update
            ip_address: Agent's IP address for audit

        Returns:
            Updated application or None if not found
        """
        application = await self.get_application(application_id)
        if not application:
            return None

        # Only allow updates for draft or info_requested status
        if not application.can_be_submitted:
            return None

        changes = {}

        # Update non-encrypted fields
        update_fields = update_data.model_dump(exclude_unset=True)

        # Handle encrypted fields
        encrypted_fields_mapping = {
            'kra_pin': 'kra_pin_encrypted',
            'phone': 'phone_encrypted',
            'email': 'email_encrypted',
            'owner_national_id': 'owner_national_id_encrypted',
            'owner_phone': 'owner_phone_encrypted',
            'owner_email': 'owner_email_encrypted',
            'bank_account': 'bank_account_encrypted'
        }

        for field_name, encrypted_field_name in encrypted_fields_mapping.items():
            if field_name in update_fields:
                value = update_fields.pop(field_name)
                if value:
                    setattr(application, encrypted_field_name, self.encryption_service.encrypt(value))
                    changes[field_name] = "updated"
                else:
                    setattr(application, encrypted_field_name, None)
                    changes[field_name] = "cleared"

        # Update remaining fields
        for field, value in update_fields.items():
            if hasattr(application, field):
                setattr(application, field, value)
                changes[field] = value

        # Log audit if there were changes
        if changes:
            await self._log_application_audit(
                application_id=application_id,
                user_id=agent_id,
                action=AuditAction.UPDATE,
                details={"changes": changes},
                ip_address=ip_address
            )

        await self.db.commit()
        await self.db.refresh(application)

        return application

    async def submit_application(
        self,
        application_id: UUID,
        agent_id: UUID,
        ip_address: Optional[str] = None
    ) -> Optional[BusinessApplication]:
        """
        Submit application for review.

        Args:
            application_id: Application UUID
            agent_id: Agent submitting the application
            ip_address: Agent's IP address for audit

        Returns:
            Updated application or None if not found
        """
        application = await self.get_application(application_id)
        if not application:
            return None

        # Can only submit draft or info_requested applications
        if not application.can_be_submitted:
            return None

        # Update status
        application.status = OnboardingStatus.SUBMITTED
        application.submitted_at = datetime.utcnow()

        # Log audit
        await self._log_application_audit(
            application_id=application_id,
            user_id=agent_id,
            action=AuditAction.UPDATE,
            details={
                "action": "submitted",
                "previous_status": "draft" if application.status == OnboardingStatus.DRAFT else "info_requested",
                "new_status": "submitted"
            },
            ip_address=ip_address
        )

        await self.db.commit()
        await self.db.refresh(application)

        return application

    async def approve_application(
        self,
        application_id: UUID,
        agent_id: UUID,
        approval_data: ApprovalRequest,
        ip_address: Optional[str] = None
    ) -> Optional[ApprovalResponse]:
        """
        Approve application and create business + admin user.

        Args:
            application_id: Application UUID
            agent_id: Agent approving the application
            approval_data: Approval data
            ip_address: Agent's IP address for audit

        Returns:
            Approval response with credentials or None if not found
        """
        application = await self.get_application(application_id)
        if not application:
            return None

        # Can only approve submitted or under_review applications
        if not application.can_be_reviewed:
            return None

        # Decrypt sensitive data for business creation
        decrypted_data = {}

        if application.kra_pin_encrypted:
            decrypted_data['kra_pin'] = self.encryption_service.decrypt(application.kra_pin_encrypted)

        if application.phone_encrypted:
            decrypted_data['phone'] = self.encryption_service.decrypt(application.phone_encrypted)

        if application.email_encrypted:
            decrypted_data['email'] = self.encryption_service.decrypt(application.email_encrypted)

        if application.bank_account_encrypted:
            decrypted_data['bank_account'] = self.encryption_service.decrypt(application.bank_account_encrypted)

        owner_email = None
        if application.owner_email_encrypted:
            owner_email = self.encryption_service.decrypt(application.owner_email_encrypted)

        # Create business record
        business = Business(
            name=application.business_name,
            business_type=application.business_type,
            kra_pin_encrypted=application.kra_pin_encrypted,  # Store encrypted
            bank_account_encrypted=application.bank_account_encrypted,  # Store encrypted
            vat_registered=application.vat_registered,
            tot_registered=application.tot_registered,
            phone=decrypted_data.get('phone'),  # Store plain (or encrypt based on Business model)
            email=decrypted_data.get('email'),  # Store plain (or encrypt based on Business model)
            city=application.county,
            onboarding_status='completed',
            is_active=True
        )

        self.db.add(business)
        await self.db.flush()

        # Generate temporary password for business admin
        temp_password = self._generate_temporary_password()

        # Create business admin user
        from app.core.security import hash_password

        admin_user = User(
            email_encrypted=application.owner_email_encrypted if application.owner_email_encrypted else self.encryption_service.encrypt(owner_email or decrypted_data.get('email', f"admin@{application.business_name.lower().replace(' ', '')}.com")),
            phone_encrypted=application.owner_phone_encrypted,
            national_id_encrypted=application.owner_national_id_encrypted,
            first_name=application.owner_name.split()[0] if application.owner_name else "Business",
            last_name=' '.join(application.owner_name.split()[1:]) if application.owner_name and len(application.owner_name.split()) > 1 else "Admin",
            password_hash=hash_password(temp_password),
            role=UserRole.BUSINESS_ADMIN,
            business_id=business.id,
            is_active=True,
            must_change_password=True
        )

        self.db.add(admin_user)
        await self.db.flush()

        # Update application
        application.status = OnboardingStatus.APPROVED
        application.reviewed_by = agent_id
        application.reviewed_at = datetime.utcnow()
        application.approved_business_id = business.id
        if approval_data.notes:
            application.notes = f"{application.notes or ''}\n\nApproval Notes: {approval_data.notes}"

        # Log audit
        await self._log_application_audit(
            application_id=application_id,
            user_id=agent_id,
            action=AuditAction.UPDATE,
            details={
                "action": "approved",
                "business_id": str(business.id),
                "admin_user_id": str(admin_user.id),
                "business_name": application.business_name
            },
            ip_address=ip_address
        )

        await self.db.commit()

        # Send welcome email with credentials
        email_service = get_email_service()
        admin_email_addr = owner_email or decrypted_data.get('email', f"admin@{application.business_name.lower().replace(' ', '')}.com")

        try:
            await email_service.send_application_status_email(
                to_email=admin_email_addr,
                applicant_name=application.owner_name,
                business_name=application.business_name,
                status="approved",
                message=approval_data.notes,
                login_credentials={
                    "email": admin_email_addr,
                    "password": temp_password,
                    "login_url": "https://app.kenyaaccounting.com/login"
                }
            )
        except Exception as e:
            # Log email error but don't fail the approval
            import logging
            logging.error(f"Failed to send approval email to {admin_email_addr}: {str(e)}")

        # Return approval response with credentials
        return ApprovalResponse(
            application_id=application.id,
            business_id=business.id,
            business_name=business.name,
            admin_user_id=admin_user.id,
            admin_email=admin_email_addr,
            temporary_password=temp_password,
            message="Business application approved successfully. Admin account created.",
            password_change_required=True
        )

    async def reject_application(
        self,
        application_id: UUID,
        agent_id: UUID,
        rejection_data: RejectionRequest,
        ip_address: Optional[str] = None
    ) -> Optional[BusinessApplication]:
        """
        Reject application with reason.

        Args:
            application_id: Application UUID
            agent_id: Agent rejecting the application
            rejection_data: Rejection data
            ip_address: Agent's IP address for audit

        Returns:
            Updated application or None if not found
        """
        application = await self.get_application(application_id)
        if not application:
            return None

        # Can only reject submitted or under_review applications
        if not application.can_be_reviewed:
            return None

        # Update application
        application.status = OnboardingStatus.REJECTED
        application.reviewed_by = agent_id
        application.reviewed_at = datetime.utcnow()
        application.rejection_reason = rejection_data.rejection_reason

        # Log audit
        await self._log_application_audit(
            application_id=application_id,
            user_id=agent_id,
            action=AuditAction.UPDATE,
            details={
                "action": "rejected",
                "rejection_reason": rejection_data.rejection_reason
            },
            ip_address=ip_address
        )

        await self.db.commit()
        await self.db.refresh(application)

        # Send rejection email
        email_service = get_email_service()
        owner_email = None
        if application.owner_email_encrypted:
            owner_email = self.encryption_service.decrypt(application.owner_email_encrypted)

        if owner_email:
            try:
                await email_service.send_application_status_email(
                    to_email=owner_email,
                    applicant_name=application.owner_name,
                    business_name=application.business_name,
                    status="rejected",
                    message=rejection_data.rejection_reason
                )
            except Exception as e:
                # Log email error but don't fail the rejection
                import logging
                logging.error(f"Failed to send rejection email to {owner_email}: {str(e)}")

        return application

    async def request_info(
        self,
        application_id: UUID,
        agent_id: UUID,
        info_request_data: InfoRequest,
        ip_address: Optional[str] = None
    ) -> Optional[BusinessApplication]:
        """
        Request more information from applicant.

        Args:
            application_id: Application UUID
            agent_id: Agent requesting information
            info_request_data: Info request data
            ip_address: Agent's IP address for audit

        Returns:
            Updated application or None if not found
        """
        application = await self.get_application(application_id)
        if not application:
            return None

        # Can only request info for submitted or under_review applications
        if not application.can_be_reviewed:
            return None

        # Update application
        application.status = OnboardingStatus.INFO_REQUESTED
        application.reviewed_by = agent_id
        application.reviewed_at = datetime.utcnow()
        application.info_request_note = info_request_data.info_request_note

        # Log audit
        await self._log_application_audit(
            application_id=application_id,
            user_id=agent_id,
            action=AuditAction.UPDATE,
            details={
                "action": "info_requested",
                "info_request_note": info_request_data.info_request_note
            },
            ip_address=ip_address
        )

        await self.db.commit()
        await self.db.refresh(application)

        # Send info requested email
        email_service = get_email_service()
        owner_email = None
        if application.owner_email_encrypted:
            owner_email = self.encryption_service.decrypt(application.owner_email_encrypted)

        if owner_email:
            try:
                await email_service.send_application_status_email(
                    to_email=owner_email,
                    applicant_name=application.owner_name,
                    business_name=application.business_name,
                    status="info_requested",
                    message=info_request_data.info_request_note
                )
            except Exception as e:
                # Log email error but don't fail the request
                import logging
                logging.error(f"Failed to send info request email to {owner_email}: {str(e)}")

        return application

    async def get_onboarding_stats(self) -> OnboardingStatsResponse:
        """
        Get onboarding dashboard statistics.

        Returns:
            Onboarding statistics
        """
        # Get counts by status
        status_counts = await self.db.execute(
            select(
                BusinessApplication.status,
                func.count(BusinessApplication.id)
            ).group_by(BusinessApplication.status)
        )
        status_dict = dict(status_counts.all())

        # Get today's date range
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Get submitted today
        submitted_today = await self.db.execute(
            select(func.count(BusinessApplication.id))
            .where(
                and_(
                    BusinessApplication.submitted_at >= today_start,
                    BusinessApplication.submitted_at.isnot(None)
                )
            )
        )
        submitted_count = submitted_today.scalar_one()

        # Get approved today
        approved_today = await self.db.execute(
            select(func.count(BusinessApplication.id))
            .where(
                and_(
                    BusinessApplication.reviewed_at >= today_start,
                    BusinessApplication.status == OnboardingStatus.APPROVED
                )
            )
        )
        approved_count = approved_today.scalar_one()

        # Get rejected today
        rejected_today = await self.db.execute(
            select(func.count(BusinessApplication.id))
            .where(
                and_(
                    BusinessApplication.reviewed_at >= today_start,
                    BusinessApplication.status == OnboardingStatus.REJECTED
                )
            )
        )
        rejected_count = rejected_today.scalar_one()

        # Calculate average review time (in hours)
        avg_review = await self.db.execute(
            select(
                func.avg(
                    extract('epoch', BusinessApplication.reviewed_at - BusinessApplication.submitted_at) / 3600
                )
            ).where(
                and_(
                    BusinessApplication.reviewed_at.isnot(None),
                    BusinessApplication.submitted_at.isnot(None)
                )
            )
        )
        avg_hours = avg_review.scalar_one()

        # Get pending review count (submitted + info_requested)
        pending_review = await self.db.execute(
            select(func.count(BusinessApplication.id))
            .where(
                BusinessApplication.status.in_([OnboardingStatus.SUBMITTED, OnboardingStatus.INFO_REQUESTED])
            )
        )
        pending_count = pending_review.scalar_one()

        # Get total applications
        total = await self.db.execute(select(func.count(BusinessApplication.id)))
        total_count = total.scalar_one()

        return OnboardingStatsResponse(
            total_applications=total_count,
            draft_count=status_dict.get(OnboardingStatus.DRAFT, 0),
            submitted_count=status_dict.get(OnboardingStatus.SUBMITTED, 0),
            under_review_count=status_dict.get(OnboardingStatus.UNDER_REVIEW, 0),
            info_requested_count=status_dict.get(OnboardingStatus.INFO_REQUESTED, 0),
            approved_count=status_dict.get(OnboardingStatus.APPROVED, 0),
            rejected_count=status_dict.get(OnboardingStatus.REJECTED, 0),
            submitted_today=submitted_count,
            approved_today=approved_count,
            rejected_today=rejected_count,
            avg_review_time_hours=round(avg_hours, 2) if avg_hours else None,
            pending_review_count=pending_count
        )
