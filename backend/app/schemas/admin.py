"""
Admin Portal Pydantic Schemas

Request/response schemas for system administrator endpoints.
Handles business directory, internal user management, audit logs, and analytics.

Security Notes:
- All endpoints require system_admin role
- Sensitive business data is masked in responses
- Full audit logging for all admin actions
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, field_validator

from app.models.user import UserRole
from app.schemas.validators import sanitize_text_input


# ============================================================================
# DATA MASKING UTILITIES
# ============================================================================

def mask_kra_pin(kra_pin: Optional[str]) -> Optional[str]:
    """
    Mask KRA PIN showing only last 4 characters.

    Example: A123456789B -> ****6789B
    """
    if not kra_pin or len(kra_pin) < 4:
        return "****"
    return f"****{kra_pin[-4:]}"


def mask_phone(phone: Optional[str]) -> Optional[str]:
    """
    Mask phone number showing only last 4 digits.

    Example: +254712345678 -> ****5678
    """
    if not phone or len(phone) < 4:
        return "****"
    return f"****{phone[-4:]}"


def mask_bank_account(account: Optional[str]) -> Optional[str]:
    """
    Mask bank account showing only last 4 digits.

    Example: 1234567890 -> ****7890
    """
    if not account or len(account) < 4:
        return "****"
    return f"****{account[-4:]}"


def mask_email(email: Optional[str]) -> Optional[str]:
    """
    Mask email showing first 3 chars + domain.

    Example: business@example.com -> bus***@example.com
    """
    if not email or "@" not in email:
        return "***@***"

    local, domain = email.split("@", 1)
    if len(local) <= 3:
        masked_local = f"{local[0]}***"
    else:
        masked_local = f"{local[:3]}***"

    return f"{masked_local}@{domain}"


# ============================================================================
# BUSINESS MANAGEMENT SCHEMAS
# ============================================================================

class BusinessListItem(BaseModel):
    """Business list item with key metrics (for directory view)."""
    id: UUID
    name: str = Field(..., description="Business name")
    business_type: Optional[str] = Field(None, description="Business type (e.g., sole proprietor)")
    onboarding_status: str = Field(..., description="Onboarding status")
    is_active: bool = Field(..., description="Whether business is active")
    created_at: datetime = Field(..., description="Registration date")
    user_count: int = Field(default=0, description="Number of users in business")
    invoice_count: int = Field(default=0, description="Total invoices created")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Acme Corp Ltd",
                "business_type": "limited_company",
                "onboarding_status": "completed",
                "is_active": True,
                "created_at": "2025-01-01T00:00:00",
                "user_count": 3,
                "invoice_count": 45
            }
        }
    }


class BusinessListResponse(BaseModel):
    """Paginated business directory response."""
    businesses: List[BusinessListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class BusinessDetail(BaseModel):
    """Detailed business information with masked sensitive fields."""
    id: UUID
    name: str
    business_type: Optional[str]
    industry: Optional[str]
    onboarding_status: str
    is_active: bool

    # Masked sensitive information
    kra_pin_masked: Optional[str] = Field(None, description="Masked KRA PIN (last 4 chars)")
    phone_masked: Optional[str] = Field(None, description="Masked phone (last 4 digits)")
    email_masked: Optional[str] = Field(None, description="Masked email")
    bank_account_masked: Optional[str] = Field(None, description="Masked bank account")

    # Tax registration
    vat_registered: bool
    tot_registered: bool

    # Address (non-sensitive)
    address: Optional[str]
    city: Optional[str]
    country: str
    postal_code: Optional[str]
    website: Optional[str]

    # Subscription
    subscription_tier: str
    subscription_expires_at: Optional[str]

    # Metadata
    onboarding_completed_at: Optional[str]
    created_at: datetime
    updated_at: datetime

    # Metrics
    user_count: int = Field(default=0, description="Number of users")
    invoice_count: int = Field(default=0, description="Total invoices")
    total_revenue: float = Field(default=0.0, description="Total revenue from paid invoices")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Acme Corp Ltd",
                "business_type": "limited_company",
                "industry": "Technology",
                "onboarding_status": "completed",
                "is_active": True,
                "kra_pin_masked": "****6789B",
                "phone_masked": "****5678",
                "email_masked": "acm***@example.com",
                "bank_account_masked": "****7890",
                "vat_registered": True,
                "tot_registered": False,
                "address": "123 Main St",
                "city": "Nairobi",
                "country": "Kenya",
                "postal_code": "00100",
                "website": "https://acmecorp.co.ke",
                "subscription_tier": "basic",
                "subscription_expires_at": None,
                "onboarding_completed_at": "2025-01-05T00:00:00",
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-05T00:00:00",
                "user_count": 3,
                "invoice_count": 45,
                "total_revenue": 250000.50
            }
        }
    }


class BusinessUserListItem(BaseModel):
    """User list item for business users."""
    id: UUID
    full_name: str
    email_masked: str = Field(..., description="Masked email address")
    role: UserRole
    is_active: bool
    last_login_at: Optional[str]
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class BusinessUserListResponse(BaseModel):
    """List of users for a specific business."""
    users: List[BusinessUserListItem]
    total: int


# ============================================================================
# INTERNAL USER MANAGEMENT SCHEMAS
# ============================================================================

class InternalUserCreate(BaseModel):
    """Schema for creating internal users (agents/admins)."""
    email: EmailStr = Field(..., description="User email address")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    role: UserRole = Field(..., description="User role (onboarding_agent, support_agent, system_admin)")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")

    @field_validator("first_name", "last_name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        """Sanitize name fields."""
        sanitized = sanitize_text_input(v, allow_html=False)
        if not sanitized or len(sanitized.strip()) == 0:
            raise ValueError("Name cannot be empty after sanitization")
        return sanitized

    @field_validator("role")
    @classmethod
    def validate_internal_role(cls, v: UserRole) -> UserRole:
        """Ensure only internal roles can be created."""
        internal_roles = [UserRole.ONBOARDING_AGENT, UserRole.SUPPORT_AGENT, UserRole.SYSTEM_ADMIN]
        if v not in internal_roles:
            raise ValueError(f"Only internal roles can be created: {[r.value for r in internal_roles]}")
        return v


class InternalUserUpdate(BaseModel):
    """Schema for updating internal users."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Last name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    is_active: Optional[bool] = Field(None, description="Whether user is active")

    @field_validator("first_name", "last_name")
    @classmethod
    def sanitize_name(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize name fields."""
        if v is None:
            return None
        sanitized = sanitize_text_input(v, allow_html=False)
        if not sanitized or len(sanitized.strip()) == 0:
            raise ValueError("Name cannot be empty after sanitization")
        return sanitized


class InternalUserResponse(BaseModel):
    """Response schema for internal users with masked sensitive data."""
    id: UUID
    email_masked: str = Field(..., description="Masked email address")
    full_name: str = Field(..., description="User's full name")
    role: UserRole
    is_active: bool
    phone_masked: Optional[str] = Field(None, description="Masked phone number")
    last_login_at: Optional[str]
    must_change_password: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email_masked": "joh***@company.com",
                "full_name": "John Doe",
                "role": "support_agent",
                "is_active": True,
                "phone_masked": "****5678",
                "last_login_at": "2025-01-08T10:30:00",
                "must_change_password": False,
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-05T00:00:00"
            }
        }
    }


class InternalUserListResponse(BaseModel):
    """Paginated list of internal users."""
    users: List[InternalUserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# AUDIT LOG SCHEMAS
# ============================================================================

class AuditLogFilters(BaseModel):
    """Filters for audit log queries."""
    user_id: Optional[UUID] = Field(None, description="Filter by user ID")
    action: Optional[str] = Field(None, max_length=100, description="Filter by action")
    resource_type: Optional[str] = Field(None, max_length=100, description="Filter by resource type")
    status: Optional[str] = Field(None, description="Filter by status (success, failure, error)")
    start_date: Optional[datetime] = Field(None, description="Filter logs from this date")
    end_date: Optional[datetime] = Field(None, description="Filter logs until this date")
    ip_address: Optional[str] = Field(None, max_length=45, description="Filter by IP address")

    @field_validator("action", "resource_type")
    @classmethod
    def sanitize_strings(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize filter strings."""
        if v is None:
            return None
        return sanitize_text_input(v, allow_html=False)


class AuditLogResponse(BaseModel):
    """Single audit log entry response."""
    id: UUID
    user_id: Optional[UUID]
    user_name: Optional[str] = Field(None, description="Name of user who performed action")
    action: str
    resource_type: Optional[str]
    resource_id: Optional[UUID]
    status: str
    details: Optional[dict] = Field(None, description="Additional details (JSON)")
    error_message: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    session_id: Optional[str]
    old_values: Optional[dict] = Field(None, description="Previous values for update operations")
    new_values: Optional[dict] = Field(None, description="New values for create/update operations")
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "user_name": "John Doe",
                "action": "create_business",
                "resource_type": "business",
                "resource_id": "123e4567-e89b-12d3-a456-426614174002",
                "status": "success",
                "details": {"business_name": "Acme Corp"},
                "error_message": None,
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0...",
                "session_id": "sess_abc123",
                "old_values": None,
                "new_values": {"name": "Acme Corp", "status": "pending"},
                "created_at": "2025-01-01T10:00:00"
            }
        }
    }


class AuditLogListResponse(BaseModel):
    """Paginated audit log list response."""
    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# ANALYTICS & DASHBOARD SCHEMAS
# ============================================================================

class AdminDashboardStats(BaseModel):
    """Admin dashboard statistics and metrics."""
    # Business metrics
    total_businesses: int = Field(..., description="Total businesses in system")
    active_businesses: int = Field(..., description="Active businesses")
    pending_onboarding: int = Field(..., description="Businesses pending onboarding")
    completed_onboarding: int = Field(..., description="Businesses with completed onboarding")

    # User metrics
    total_users: int = Field(..., description="Total users in system")
    active_users: int = Field(..., description="Active users")
    business_admins: int = Field(..., description="Number of business admins")
    bookkeepers: int = Field(..., description="Number of bookkeepers")
    support_agents: int = Field(..., description="Number of support agents")
    onboarding_agents: int = Field(..., description="Number of onboarding agents")
    system_admins: int = Field(..., description="Number of system admins")

    # Invoice metrics
    total_invoices: int = Field(..., description="Total invoices created")
    invoices_this_month: int = Field(..., description="Invoices created this month")
    total_revenue: float = Field(..., description="Total revenue from paid invoices")
    revenue_this_month: float = Field(..., description="Revenue this month")

    # Activity metrics
    new_businesses_this_week: int = Field(..., description="Businesses registered this week")
    new_users_this_week: int = Field(..., description="Users registered this week")
    active_support_tickets: int = Field(..., description="Open/in-progress support tickets")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_businesses": 150,
                "active_businesses": 142,
                "pending_onboarding": 5,
                "completed_onboarding": 145,
                "total_users": 450,
                "active_users": 425,
                "business_admins": 150,
                "bookkeepers": 280,
                "support_agents": 8,
                "onboarding_agents": 5,
                "system_admins": 2,
                "total_invoices": 2500,
                "invoices_this_month": 180,
                "total_revenue": 12500000.00,
                "revenue_this_month": 850000.00,
                "new_businesses_this_week": 3,
                "new_users_this_week": 12,
                "active_support_tickets": 15
            }
        }
    }


class SystemHealthMetrics(BaseModel):
    """System health and performance metrics."""
    # Database metrics
    database_status: str = Field(..., description="Database connection status")
    total_records: int = Field(..., description="Total records in database")

    # Audit metrics
    total_audit_logs: int = Field(..., description="Total audit log entries")
    failed_logins_24h: int = Field(..., description="Failed login attempts in last 24 hours")
    security_events_24h: int = Field(..., description="Security events in last 24 hours")

    # Activity metrics
    api_calls_24h: int = Field(..., description="API calls in last 24 hours")
    active_sessions: int = Field(..., description="Currently active user sessions")

    # System info
    uptime_hours: Optional[float] = Field(None, description="System uptime in hours")
    last_backup: Optional[datetime] = Field(None, description="Last database backup timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "database_status": "healthy",
                "total_records": 50000,
                "total_audit_logs": 15000,
                "failed_logins_24h": 12,
                "security_events_24h": 5,
                "api_calls_24h": 8500,
                "active_sessions": 45,
                "uptime_hours": 720.5,
                "last_backup": "2025-01-08T02:00:00"
            }
        }
    }
