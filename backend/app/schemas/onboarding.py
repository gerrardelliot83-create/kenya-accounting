"""
Onboarding Schemas

Pydantic schemas for business onboarding application API.
Handles validation, serialization, and deserialization of onboarding data.

Security Notes:
- Sensitive fields are handled encrypted in database
- Response schemas never expose encrypted field values directly
- Decrypted values are only shown to authorized agents
- Validation ensures data integrity before storage
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, validator

from app.models.business_application import OnboardingStatus, BusinessType


# ============================================================================
# BASE SCHEMAS
# ============================================================================

class BusinessApplicationBase(BaseModel):
    """Base schema for business application data."""
    business_name: str = Field(..., min_length=1, max_length=255, description="Name of the business")
    business_type: Optional[str] = Field(None, description="Type: sole_proprietor, partnership, limited_company")

    # Sensitive fields (will be encrypted in database)
    kra_pin: Optional[str] = Field(None, max_length=20, description="KRA PIN")
    phone: Optional[str] = Field(None, max_length=20, description="Business phone number")
    email: Optional[EmailStr] = Field(None, description="Business email address")

    # Location
    county: Optional[str] = Field(None, max_length=100, description="County")
    sub_county: Optional[str] = Field(None, max_length=100, description="Sub-county")

    # Owner information
    owner_name: Optional[str] = Field(None, max_length=255, description="Owner/director name")
    owner_national_id: Optional[str] = Field(None, max_length=50, description="Owner national ID")
    owner_phone: Optional[str] = Field(None, max_length=20, description="Owner phone number")
    owner_email: Optional[EmailStr] = Field(None, description="Owner email address")

    # Bank information
    bank_account: Optional[str] = Field(None, max_length=50, description="Bank account number")

    # Tax registration
    vat_registered: bool = Field(default=False, description="VAT registered")
    tot_registered: bool = Field(default=False, description="TOT registered")

    # Notes
    notes: Optional[str] = Field(None, description="Internal notes")

    @validator('business_type')
    def validate_business_type(cls, v):
        """Validate business type is one of allowed values."""
        if v is not None:
            allowed = ['sole_proprietor', 'partnership', 'limited_company']
            if v not in allowed:
                raise ValueError(f"business_type must be one of {allowed}")
        return v

    @validator('kra_pin')
    def validate_kra_pin(cls, v):
        """Validate KRA PIN format (basic validation)."""
        if v is not None and v.strip():
            v = v.strip().upper()
            # KRA PIN format: A000000000X (letter + 9 digits + letter)
            if len(v) < 11:
                raise ValueError("KRA PIN must be at least 11 characters")
        return v

    @validator('phone', 'owner_phone')
    def validate_phone(cls, v):
        """Validate phone number format (Kenya)."""
        if v is not None and v.strip():
            v = v.strip()
            # Remove common prefixes and formatting
            v = v.replace('+254', '0').replace(' ', '').replace('-', '')
            if not v.startswith('0') or len(v) != 10:
                raise ValueError("Phone number must be in format: 0XXXXXXXXX (10 digits)")
        return v


# ============================================================================
# CREATE SCHEMAS
# ============================================================================

class BusinessApplicationCreate(BusinessApplicationBase):
    """Schema for creating a new business application."""
    pass


# ============================================================================
# UPDATE SCHEMAS
# ============================================================================

class BusinessApplicationUpdate(BaseModel):
    """Schema for updating business application details."""
    business_name: Optional[str] = Field(None, min_length=1, max_length=255)
    business_type: Optional[str] = None
    kra_pin: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    county: Optional[str] = None
    sub_county: Optional[str] = None
    owner_name: Optional[str] = None
    owner_national_id: Optional[str] = None
    owner_phone: Optional[str] = None
    owner_email: Optional[EmailStr] = None
    bank_account: Optional[str] = None
    vat_registered: Optional[bool] = None
    tot_registered: Optional[bool] = None
    notes: Optional[str] = None

    @validator('business_type')
    def validate_business_type(cls, v):
        """Validate business type is one of allowed values."""
        if v is not None:
            allowed = ['sole_proprietor', 'partnership', 'limited_company']
            if v not in allowed:
                raise ValueError(f"business_type must be one of {allowed}")
        return v


# ============================================================================
# APPROVAL/REJECTION SCHEMAS
# ============================================================================

class ApprovalRequest(BaseModel):
    """Schema for approving a business application."""
    notes: Optional[str] = Field(None, description="Optional approval notes")


class RejectionRequest(BaseModel):
    """Schema for rejecting a business application."""
    rejection_reason: str = Field(..., min_length=10, max_length=1000, description="Reason for rejection")


class InfoRequest(BaseModel):
    """Schema for requesting more information."""
    info_request_note: str = Field(..., min_length=10, max_length=1000, description="Information needed from applicant")


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class BusinessApplicationResponse(BaseModel):
    """Schema for business application response."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    # Business information
    business_name: str
    business_type: Optional[str]

    # Decrypted sensitive fields (only for authorized users)
    kra_pin: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

    # Location
    county: Optional[str]
    sub_county: Optional[str]

    # Owner information
    owner_name: Optional[str]
    owner_national_id: Optional[str] = None
    owner_phone: Optional[str] = None
    owner_email: Optional[str] = None

    # Bank information
    bank_account: Optional[str] = None

    # Tax registration
    vat_registered: bool
    tot_registered: bool

    # Status tracking
    status: OnboardingStatus
    submitted_at: Optional[datetime]
    reviewed_at: Optional[datetime]

    # Review information
    reviewed_by: Optional[UUID]
    reviewer_name: Optional[str] = None
    rejection_reason: Optional[str]
    info_request_note: Optional[str]

    # Agent tracking
    created_by: Optional[UUID]
    creator_name: Optional[str] = None

    # Approved business
    approved_business_id: Optional[UUID]

    # Notes
    notes: Optional[str]

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v) if v else None
        }


class BusinessApplicationListItem(BaseModel):
    """Simplified schema for application list view."""
    id: UUID
    created_at: datetime
    business_name: str
    business_type: Optional[str]
    status: OnboardingStatus
    submitted_at: Optional[datetime]
    county: Optional[str]
    created_by: Optional[UUID]
    creator_name: Optional[str] = None
    reviewed_by: Optional[UUID]
    reviewer_name: Optional[str] = None

    class Config:
        from_attributes = True


class BusinessApplicationListResponse(BaseModel):
    """Paginated list of business applications."""
    applications: List[BusinessApplicationListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# APPROVAL RESPONSE SCHEMA (includes generated credentials)
# ============================================================================

class ApprovalResponse(BaseModel):
    """Schema for approval response with generated credentials."""
    application_id: UUID
    business_id: UUID
    business_name: str

    # Generated business admin credentials
    admin_user_id: UUID
    admin_email: str
    temporary_password: str

    # Instructions
    message: str = "Business application approved successfully. Admin account created."
    password_change_required: bool = True

    class Config:
        json_encoders = {
            UUID: lambda v: str(v) if v else None
        }


# ============================================================================
# STATISTICS SCHEMA
# ============================================================================

class OnboardingStatsResponse(BaseModel):
    """Statistics for onboarding dashboard."""
    total_applications: int
    draft_count: int
    submitted_count: int
    under_review_count: int
    info_requested_count: int
    approved_count: int
    rejected_count: int

    # Today's stats
    submitted_today: int
    approved_today: int
    rejected_today: int

    # Agent stats
    avg_review_time_hours: Optional[float] = None
    pending_review_count: int  # submitted + info_requested


# ============================================================================
# FILTER SCHEMA
# ============================================================================

class ApplicationFilters(BaseModel):
    """Filters for application list queries."""
    status: Optional[OnboardingStatus] = None
    created_by: Optional[UUID] = None
    reviewed_by: Optional[UUID] = None
    county: Optional[str] = None
    search: Optional[str] = None  # Search in business_name, owner_name
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
