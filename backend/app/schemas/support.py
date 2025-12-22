"""
Support Ticket Pydantic Schemas

Request/response schemas for support ticket-related endpoints.
Handles validation and serialization for customer support system.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.support_ticket import TicketCategory, TicketPriority, TicketStatus
from app.models.ticket_message import SenderType
from app.schemas.validators import sanitize_text_input


# Attachment schemas
class AttachmentBase(BaseModel):
    """Base schema for message attachments."""
    name: str = Field(..., description="File name")
    url: str = Field(..., description="File URL")
    type: str = Field(..., description="MIME type")
    size: Optional[int] = Field(None, description="File size in bytes")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate attachment URL is valid HTTPS."""
        if not v.startswith(("https://", "http://")):
            raise ValueError("Attachment URL must be a valid HTTP/HTTPS URL")
        return v


# Ticket Message schemas
class MessageCreate(BaseModel):
    """Schema for creating a ticket message."""
    message: str = Field(..., min_length=1, max_length=5000, description="Message content")
    attachments: Optional[List[AttachmentBase]] = Field(None, description="Optional file attachments")
    is_internal: bool = Field(default=False, description="Internal note (agents only)")

    @field_validator("message")
    @classmethod
    def sanitize_message(cls, v: str) -> str:
        """Sanitize message content to prevent XSS."""
        sanitized = sanitize_text_input(v, allow_html=False)
        if not sanitized or len(sanitized.strip()) == 0:
            raise ValueError("Message cannot be empty after sanitization")
        return sanitized


class MessageResponse(BaseModel):
    """Schema for ticket message responses."""
    id: UUID
    ticket_id: UUID
    sender_id: Optional[UUID]
    sender_type: SenderType
    sender_name: Optional[str] = Field(None, description="Name of message sender")
    message: str
    attachments: Optional[List[AttachmentBase]] = None
    is_internal: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


# Support Ticket schemas
class TicketCreate(BaseModel):
    """Schema for creating a support ticket."""
    subject: str = Field(..., min_length=5, max_length=500, description="Ticket subject/title")
    description: str = Field(..., min_length=10, max_length=5000, description="Detailed issue description")
    category: TicketCategory = Field(..., description="Ticket category")

    @field_validator("subject", "description")
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        """Sanitize text fields to prevent XSS."""
        sanitized = sanitize_text_input(v, allow_html=False)
        if not sanitized or len(sanitized.strip()) == 0:
            raise ValueError("Field cannot be empty after sanitization")
        return sanitized


class TicketUpdate(BaseModel):
    """Schema for updating a ticket (agents only)."""
    status: Optional[TicketStatus] = Field(None, description="Ticket status")
    priority: Optional[TicketPriority] = Field(None, description="Ticket priority")
    assigned_agent_id: Optional[UUID] = Field(None, description="Assigned agent ID")


class TicketResponse(BaseModel):
    """Schema for basic ticket response."""
    id: UUID
    business_id: UUID
    user_id: Optional[UUID]
    ticket_number: str
    subject: str
    description: str
    category: TicketCategory
    priority: TicketPriority
    status: TicketStatus
    assigned_agent_id: Optional[UUID]
    assigned_agent_name: Optional[str] = Field(None, description="Name of assigned agent")
    resolved_at: Optional[datetime]
    satisfaction_rating: Optional[int]
    created_at: datetime
    updated_at: datetime
    message_count: int = Field(default=0, description="Number of messages")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "business_id": "123e4567-e89b-12d3-a456-426614174001",
                "user_id": "123e4567-e89b-12d3-a456-426614174002",
                "ticket_number": "TKT-2025-00001",
                "subject": "Cannot export invoices to PDF",
                "description": "When I try to export an invoice to PDF, I get an error message",
                "category": "technical",
                "priority": "medium",
                "status": "open",
                "assigned_agent_id": None,
                "assigned_agent_name": None,
                "resolved_at": None,
                "satisfaction_rating": None,
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00",
                "message_count": 3
            }
        }
    }


class TicketDetailResponse(TicketResponse):
    """Schema for detailed ticket response with messages."""
    messages: List[MessageResponse] = Field(default_factory=list, description="Ticket conversation thread")


class TicketListResponse(BaseModel):
    """Schema for paginated ticket list response."""
    tickets: List[TicketResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Support Portal schemas (for agents)
class MaskedBusinessInfo(BaseModel):
    """Masked business information for support agents."""
    business_id: UUID
    business_name: str
    business_type: Optional[str] = None
    # Sensitive fields are NOT included (KRA PIN, bank account, etc.)


class TicketWithBusinessContext(TicketDetailResponse):
    """Ticket with business context for support agents."""
    business_info: Optional[MaskedBusinessInfo] = Field(None, description="Masked business information")
    creator_name: Optional[str] = Field(None, description="Name of ticket creator")
    creator_email: Optional[str] = Field(None, description="Email of ticket creator")


class SupportStatsResponse(BaseModel):
    """Support dashboard statistics."""
    open_count: int = Field(..., description="Number of open tickets")
    in_progress_count: int = Field(..., description="Number of tickets in progress")
    waiting_customer_count: int = Field(..., description="Number of tickets waiting for customer")
    resolved_today: int = Field(..., description="Tickets resolved today")
    closed_today: int = Field(..., description="Tickets closed today")
    avg_resolution_time_hours: Optional[float] = Field(None, description="Average resolution time in hours")
    unassigned_count: int = Field(..., description="Number of unassigned tickets")
    high_priority_count: int = Field(..., description="Number of high/urgent priority tickets")
    total_tickets: int = Field(..., description="Total tickets in system")

    model_config = {
        "json_schema_extra": {
            "example": {
                "open_count": 15,
                "in_progress_count": 8,
                "waiting_customer_count": 3,
                "resolved_today": 5,
                "closed_today": 2,
                "avg_resolution_time_hours": 4.5,
                "unassigned_count": 7,
                "high_priority_count": 4,
                "total_tickets": 150
            }
        }
    }


# Canned Response schemas
class CannedResponseResponse(BaseModel):
    """Schema for canned response templates."""
    id: UUID
    title: str
    content: str
    category: str
    is_active: bool
    placeholders: List[str] = Field(default_factory=list, description="List of placeholders in template")
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Invoice Export Issue - Standard Response",
                "content": "Hi {{customer_name}},\n\nThank you for contacting support. I understand you're having trouble exporting invoices to PDF...",
                "category": "technical",
                "is_active": True,
                "placeholders": ["customer_name"],
                "created_at": "2025-01-01T00:00:00"
            }
        }
    }


class CannedResponseListResponse(BaseModel):
    """Schema for canned response list."""
    templates: List[CannedResponseResponse]
    total: int


# Ticket filters for agents
class TicketFilters(BaseModel):
    """Filters for ticket list queries."""
    status: Optional[TicketStatus] = Field(None, description="Filter by status")
    priority: Optional[TicketPriority] = Field(None, description="Filter by priority")
    category: Optional[TicketCategory] = Field(None, description="Filter by category")
    assigned_agent_id: Optional[UUID] = Field(None, description="Filter by assigned agent")
    unassigned: Optional[bool] = Field(None, description="Show only unassigned tickets")
    business_id: Optional[UUID] = Field(None, description="Filter by business (agents only)")
    search: Optional[str] = Field(None, max_length=200, description="Search in subject/description")

    @field_validator("search")
    @classmethod
    def sanitize_search(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize search query."""
        if v is None:
            return None
        return sanitize_text_input(v, allow_html=False)


# Rating schema
class TicketRatingUpdate(BaseModel):
    """Schema for customer satisfaction rating."""
    rating: int = Field(..., ge=1, le=5, description="Satisfaction rating (1-5 stars)")
