"""
Support API Endpoints (Client-Facing)

Customer support ticket and help centre endpoints for business users.
All ticket operations are scoped to the user's business.

Permissions:
- business_admin, bookkeeper: Can create and view their business tickets
- All authenticated users: Can access help centre content
"""

from typing import Optional
from uuid import UUID
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.models.support_ticket import TicketStatus, TicketPriority, TicketCategory
from app.schemas.support import (
    TicketCreate,
    TicketResponse,
    TicketDetailResponse,
    TicketListResponse,
    MessageCreate,
    MessageResponse,
    TicketFilters,
    TicketRatingUpdate
)
from app.schemas.help import (
    FaqCategoryListResponse,
    FaqArticleListResponse,
    FaqArticleResponse,
    FaqSearchRequest,
    HelpArticleListResponse,
    HelpArticleSummaryResponse,
    HelpArticleResponse,
    HelpArticleFilters
)
from app.services.support_service import SupportService
from app.services.help_service import HelpService


router = APIRouter()


# ============================================================================
# SUPPORT TICKET ENDPOINTS
# ============================================================================

@router.get("/tickets", response_model=TicketListResponse)
async def list_my_tickets(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[TicketStatus] = Query(None, alias="status", description="Filter by status"),
    priority_filter: Optional[TicketPriority] = Query(None, alias="priority", description="Filter by priority"),
    category_filter: Optional[TicketCategory] = Query(None, alias="category", description="Filter by category"),
    search: Optional[str] = Query(None, max_length=200, description="Search in subject/description"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List support tickets for my business.

    Returns tickets created by anyone in the user's business.
    Supports filtering by status, priority, and category.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Create support service
    support_service = SupportService(db)

    # Build filters
    filters = TicketFilters(
        status=status_filter,
        priority=priority_filter,
        category=category_filter,
        search=search
    )

    # Get tickets for business
    tickets, total = await support_service.get_business_tickets(
        business_id=current_user.business_id,
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


@router.post("/tickets", response_model=TicketDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_data: TicketCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new support ticket.

    Ticket is created in 'open' status with 'medium' priority.
    Ticket number is auto-generated in format TKT-YYYY-NNNNN.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get IP address for audit
    ip_address = request.client.host if request.client else None

    # Create support service
    support_service = SupportService(db)

    # Create ticket
    ticket = await support_service.create_ticket(
        business_id=current_user.business_id,
        user_id=current_user.id,
        ticket_data=ticket_data,
        ip_address=ip_address
    )

    # Return detail response (with empty messages list)
    response = TicketDetailResponse.model_validate(ticket)
    response.messages = []
    response.message_count = 0

    if ticket.creator:
        response.assigned_agent_name = None

    return response


@router.get("/tickets/{ticket_id}", response_model=TicketDetailResponse)
async def get_ticket(
    ticket_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a support ticket by ID with full conversation history.

    Ticket must belong to the user's business.
    Internal notes are NOT visible to customers.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Create support service
    support_service = SupportService(db)

    # Get ticket with messages (scoped to business)
    ticket = await support_service.get_ticket(
        ticket_id=ticket_id,
        business_id=current_user.business_id,
        include_messages=True
    )

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Get messages (excluding internal notes)
    messages = await support_service.get_ticket_messages(
        ticket_id=ticket_id,
        include_internal=False  # Customers cannot see internal notes
    )

    # Build response
    response = TicketDetailResponse.model_validate(ticket)
    response.message_count = len(messages)

    # Add assigned agent name if available
    if ticket.assigned_agent:
        response.assigned_agent_name = ticket.assigned_agent.full_name

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


@router.post("/tickets/{ticket_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_ticket_message(
    ticket_id: UUID,
    message_data: MessageCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a message to a support ticket.

    Ticket must belong to the user's business.
    Customers cannot create internal notes (is_internal is forced to False).
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Verify ticket exists and belongs to user's business
    support_service = SupportService(db)
    ticket = await support_service.get_ticket(
        ticket_id=ticket_id,
        business_id=current_user.business_id
    )

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Get IP address for audit
    ip_address = request.client.host if request.client else None

    # Add message (is_agent=False for customers)
    message = await support_service.add_message(
        ticket_id=ticket_id,
        user_id=current_user.id,
        message_data=message_data,
        is_agent=False,
        ip_address=ip_address
    )

    # Build response
    response = MessageResponse.model_validate(message)
    response.sender_name = current_user.full_name

    return response


@router.put("/tickets/{ticket_id}/rating", response_model=TicketResponse)
async def rate_ticket(
    ticket_id: UUID,
    rating_data: TicketRatingUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Rate a resolved or closed ticket (customer satisfaction).

    Ticket must belong to the user's business and be in resolved/closed status.
    Rating is 1-5 stars.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Update rating
    support_service = SupportService(db)
    ticket = await support_service.update_satisfaction_rating(
        ticket_id=ticket_id,
        business_id=current_user.business_id,
        rating=rating_data.rating
    )

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found or cannot be rated (must be resolved/closed)"
        )

    # Build response
    response = TicketResponse.model_validate(ticket)
    response.message_count = ticket.message_count
    if ticket.assigned_agent:
        response.assigned_agent_name = ticket.assigned_agent.full_name

    return response


# ============================================================================
# HELP CENTRE ENDPOINTS (FAQ)
# ============================================================================

@router.get("/faq/categories", response_model=FaqCategoryListResponse)
async def list_faq_categories(
    db: AsyncSession = Depends(get_db)
):
    """
    List all active FAQ categories.

    Public endpoint (authentication optional).
    Returns categories with article counts, ordered by display_order.
    """
    help_service = HelpService(db)
    categories = await help_service.get_faq_categories(active_only=True)

    from app.schemas.help import FaqCategoryResponse

    category_responses = [
        FaqCategoryResponse.model_validate(cat)
        for cat in categories
    ]

    return FaqCategoryListResponse(
        categories=category_responses,
        total=len(category_responses)
    )


@router.get("/faq", response_model=FaqArticleListResponse)
async def list_faq_articles(
    category_id: Optional[UUID] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    List FAQ articles with optional category filter.

    Public endpoint (authentication optional).
    Returns published articles only, ordered by display_order.
    """
    help_service = HelpService(db)

    articles, total = await help_service.get_faq_articles(
        category_id=category_id,
        published_only=True,
        page=page,
        page_size=page_size
    )

    # Convert to response schemas
    article_responses = []
    for article in articles:
        response = FaqArticleResponse.model_validate(article)
        # Add category name
        if article.category:
            response.category_name = article.category.name
        article_responses.append(response)

    # Calculate total pages
    total_pages = ceil(total / page_size) if total > 0 else 0

    return FaqArticleListResponse(
        articles=article_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/faq/search", response_model=FaqArticleListResponse)
async def search_faq(
    search_request: FaqSearchRequest,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search FAQ articles by keywords.

    Public endpoint (authentication optional).
    Searches in question, answer, and keyword fields.
    Results ordered by relevance (view count and display order).
    """
    help_service = HelpService(db)

    articles, total = await help_service.search_faq(
        query_text=search_request.query,
        category_id=search_request.category_id,
        page=page,
        page_size=page_size
    )

    # Convert to response schemas
    article_responses = []
    for article in articles:
        response = FaqArticleResponse.model_validate(article)
        # Add category name
        if article.category:
            response.category_name = article.category.name
        article_responses.append(response)

    # Calculate total pages
    total_pages = ceil(total / page_size) if total > 0 else 0

    return FaqArticleListResponse(
        articles=article_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/faq/{article_id}", response_model=FaqArticleResponse)
async def get_faq_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single FAQ article by ID.

    Public endpoint (authentication optional).
    Increments view count for analytics.
    """
    help_service = HelpService(db)

    article = await help_service.get_faq_article(article_id)

    if not article or not article.is_published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FAQ article not found"
        )

    # Increment view count (fire and forget)
    await help_service.increment_faq_view_count(article_id)

    # Build response
    response = FaqArticleResponse.model_validate(article)
    if article.category:
        response.category_name = article.category.name

    return response


# ============================================================================
# HELP CENTRE ENDPOINTS (ARTICLES)
# ============================================================================

@router.get("/articles", response_model=HelpArticleListResponse)
async def list_help_articles(
    category: Optional[str] = Query(None, max_length=100, description="Filter by category"),
    tag: Optional[str] = Query(None, max_length=50, description="Filter by tag"),
    search: Optional[str] = Query(None, max_length=200, description="Search in title/content"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    List help articles with filtering and search.

    Public endpoint (authentication optional).
    Returns published articles only, ordered by view count and date.
    """
    help_service = HelpService(db)

    # Build filters
    filters = HelpArticleFilters(
        category=category,
        tag=tag,
        search=search,
        published_only=True
    )

    articles, total = await help_service.get_help_articles(
        filters=filters,
        page=page,
        page_size=page_size
    )

    # Convert to summary response schemas
    article_responses = [
        HelpArticleSummaryResponse.model_validate(article)
        for article in articles
    ]

    # Calculate total pages
    total_pages = ceil(total / page_size) if total > 0 else 0

    return HelpArticleListResponse(
        articles=article_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/articles/{slug}", response_model=HelpArticleResponse)
async def get_help_article(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a help article by its slug.

    Public endpoint (authentication optional).
    Increments view count for analytics.
    """
    help_service = HelpService(db)

    article = await help_service.get_help_article_by_slug(
        slug=slug,
        published_only=True
    )

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help article not found"
        )

    # Increment view count (fire and forget)
    await help_service.increment_help_article_view_count(article.id)

    return HelpArticleResponse.model_validate(article)
