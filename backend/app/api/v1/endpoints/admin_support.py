"""
Admin Support API Endpoints (Support Portal)

Internal support portal endpoints for support agents and system admins.
Provides full ticket management, assignment, and analytics capabilities.

Permissions:
- support_agent: Can view/update all tickets, respond, assign
- system_admin: Full access to all support operations
"""

from typing import Optional
from uuid import UUID
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db, require_role
from app.models.user import User
from app.core.security import UserRole
from app.models.support_ticket import TicketStatus, TicketPriority, TicketCategory
from app.schemas.support import (
    TicketUpdate,
    TicketListResponse,
    TicketWithBusinessContext,
    MessageCreate,
    MessageResponse,
    TicketFilters,
    SupportStatsResponse,
    CannedResponseListResponse,
    CannedResponseResponse,
    MaskedBusinessInfo,
    TicketResponse
)
from app.services.support_service import SupportService


router = APIRouter()


# ============================================================================
# TICKET MANAGEMENT ENDPOINTS (AGENTS ONLY)
# ============================================================================

@router.get("/tickets", response_model=TicketListResponse)
async def list_all_tickets(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[TicketStatus] = Query(None, alias="status", description="Filter by status"),
    priority_filter: Optional[TicketPriority] = Query(None, alias="priority", description="Filter by priority"),
    category_filter: Optional[TicketCategory] = Query(None, alias="category", description="Filter by category"),
    assigned_agent_id: Optional[UUID] = Query(None, description="Filter by assigned agent"),
    unassigned: Optional[bool] = Query(None, description="Show only unassigned tickets"),
    business_id: Optional[UUID] = Query(None, description="Filter by business"),
    search: Optional[str] = Query(None, max_length=200, description="Search in subject/description"),
    current_user: User = Depends(require_role([UserRole.SUPPORT_AGENT, UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    List all support tickets (support agents only).

    Returns tickets from all businesses with advanced filtering.
    Supports assignment tracking and workload management.
    """
    # Create support service
    support_service = SupportService(db)

    # Build filters
    filters = TicketFilters(
        status=status_filter,
        priority=priority_filter,
        category=category_filter,
        assigned_agent_id=assigned_agent_id,
        unassigned=unassigned,
        business_id=business_id,
        search=search
    )

    # Get all tickets
    tickets, total = await support_service.get_all_tickets(
        filters=filters,
        page=page,
        page_size=page_size
    )

    # Convert to response schemas
    ticket_responses = []
    for ticket in tickets:
        response = TicketResponse.model_validate(ticket)
        # Add message count
        response.message_count = ticket.message_count
        # Add assigned agent name if available
        if ticket.assigned_agent:
            response.assigned_agent_name = ticket.assigned_agent.full_name
        ticket_responses.append(response)

    # Calculate total pages
    total_pages = ceil(total / page_size) if total > 0 else 0

    return TicketListResponse(
        tickets=ticket_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/tickets/{ticket_id}", response_model=TicketWithBusinessContext)
async def get_ticket_with_context(
    ticket_id: UUID,
    current_user: User = Depends(require_role([UserRole.SUPPORT_AGENT, UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a support ticket with full business context (agents only).

    Returns ticket with masked business information and full conversation.
    Internal notes ARE visible to agents.
    """
    # Create support service
    support_service = SupportService(db)

    # Get ticket with messages (no business scoping for agents)
    ticket = await support_service.get_ticket(
        ticket_id=ticket_id,
        business_id=None,  # Agents can see all tickets
        include_messages=True
    )

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Get messages (including internal notes for agents)
    messages = await support_service.get_ticket_messages(
        ticket_id=ticket_id,
        include_internal=True  # Agents can see internal notes
    )

    # Build response with business context
    response = TicketWithBusinessContext.model_validate(ticket)
    response.message_count = len(messages)

    # Add assigned agent name if available
    if ticket.assigned_agent:
        response.assigned_agent_name = ticket.assigned_agent.full_name

    # Add masked business information
    if ticket.business:
        response.business_info = MaskedBusinessInfo(
            business_id=ticket.business.id,
            business_name=ticket.business.business_name,
            business_type=ticket.business.business_type
            # NOTE: Sensitive fields (KRA PIN, bank account, etc.) are intentionally excluded
        )

    # Add creator information
    if ticket.creator:
        response.creator_name = ticket.creator.full_name
        response.creator_email = ticket.creator.email

    # Convert messages to response schema
    message_responses = []
    for msg in messages:
        msg_response = MessageResponse.model_validate(msg)
        # Add sender name
        if msg.sender:
            msg_response.sender_name = msg.sender.full_name
        message_responses.append(msg_response)

    response.messages = message_responses

    return response


@router.put("/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: UUID,
    update_data: TicketUpdate,
    request: Request,
    current_user: User = Depends(require_role([UserRole.SUPPORT_AGENT, UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Update ticket status, priority, or assignment (agents only).

    Supports changing:
    - Status (open, in_progress, waiting_customer, resolved, closed)
    - Priority (low, medium, high, urgent)
    - Assigned agent
    """
    # Get IP address for audit
    ip_address = request.client.host if request.client else None

    # Create support service
    support_service = SupportService(db)

    # Update ticket
    ticket = await support_service.update_ticket(
        ticket_id=ticket_id,
        update_data=update_data,
        agent_id=current_user.id,
        ip_address=ip_address
    )

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Build response
    response = TicketResponse.model_validate(ticket)
    response.message_count = ticket.message_count
    if ticket.assigned_agent:
        response.assigned_agent_name = ticket.assigned_agent.full_name

    return response


@router.post("/tickets/{ticket_id}/assign", response_model=TicketResponse)
async def assign_ticket_to_agent(
    ticket_id: UUID,
    agent_id: UUID = Query(..., description="Agent ID to assign to"),
    request: Request = None,
    current_user: User = Depends(require_role([UserRole.SUPPORT_AGENT, UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Assign a ticket to a support agent.

    Quick assignment endpoint for workload distribution.
    """
    # Get IP address for audit
    ip_address = request.client.host if request.client else None

    # Create support service
    support_service = SupportService(db)

    # Assign ticket
    ticket = await support_service.assign_ticket(
        ticket_id=ticket_id,
        agent_id=agent_id,
        assigned_by=current_user.id,
        ip_address=ip_address
    )

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Build response
    response = TicketResponse.model_validate(ticket)
    response.message_count = ticket.message_count
    if ticket.assigned_agent:
        response.assigned_agent_name = ticket.assigned_agent.full_name

    return response


@router.post("/tickets/{ticket_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_agent_message(
    ticket_id: UUID,
    message_data: MessageCreate,
    request: Request,
    current_user: User = Depends(require_role([UserRole.SUPPORT_AGENT, UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Add an agent message or internal note to a ticket.

    Agents can create both customer-facing messages and internal notes.
    Internal notes (is_internal=true) are only visible to other agents.
    """
    # Verify ticket exists
    support_service = SupportService(db)
    ticket = await support_service.get_ticket(
        ticket_id=ticket_id,
        business_id=None  # Agents can reply to any ticket
    )

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Get IP address for audit
    ip_address = request.client.host if request.client else None

    # Add message (is_agent=True for agents)
    message = await support_service.add_message(
        ticket_id=ticket_id,
        user_id=current_user.id,
        message_data=message_data,
        is_agent=True,
        ip_address=ip_address
    )

    # Build response
    response = MessageResponse.model_validate(message)
    response.sender_name = current_user.full_name

    return response


# ============================================================================
# SUPPORT DASHBOARD & ANALYTICS
# ============================================================================

@router.get("/stats", response_model=SupportStatsResponse)
async def get_support_stats(
    current_user: User = Depends(require_role([UserRole.SUPPORT_AGENT, UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get support dashboard statistics.

    Returns real-time metrics for support team:
    - Ticket counts by status
    - Today's resolution metrics
    - Average resolution time
    - Unassigned and high-priority counts
    """
    support_service = SupportService(db)
    stats = await support_service.get_support_stats()

    return stats


# ============================================================================
# CANNED RESPONSES
# ============================================================================

@router.get("/templates", response_model=CannedResponseListResponse)
async def get_canned_responses(
    category: Optional[str] = Query(None, max_length=100, description="Filter by category"),
    current_user: User = Depends(require_role([UserRole.SUPPORT_AGENT, UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get canned response templates for agents.

    Returns pre-written response templates for common scenarios.
    Templates can include placeholders (e.g., {{customer_name}}).
    """
    support_service = SupportService(db)
    templates = await support_service.get_canned_responses(category=category)

    # Convert to response schemas
    template_responses = [
        CannedResponseResponse.model_validate(template)
        for template in templates
    ]

    # Add placeholder lists
    for i, template in enumerate(templates):
        template_responses[i].placeholders = template.placeholder_list

    return CannedResponseListResponse(
        templates=template_responses,
        total=len(template_responses)
    )


@router.get("/templates/{template_id}", response_model=CannedResponseResponse)
async def get_canned_response(
    template_id: UUID,
    current_user: User = Depends(require_role([UserRole.SUPPORT_AGENT, UserRole.SYSTEM_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single canned response template by ID.

    Returns template with placeholder information.
    """
    from sqlalchemy import select
    from app.models.canned_response import CannedResponse

    # Get template
    result = await db.execute(
        select(CannedResponse).where(CannedResponse.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template or not template.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Canned response template not found"
        )

    # Build response
    response = CannedResponseResponse.model_validate(template)
    response.placeholders = template.placeholder_list

    return response
