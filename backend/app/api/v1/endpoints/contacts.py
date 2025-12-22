"""
Contacts API Endpoints

CRUD endpoints for contact management with encryption.
All endpoints require authentication and are scoped to the user's business.

Security:
- Rate limiting on create, update operations
- Sensitive data (phone, national_id, bank_account) encrypted at rest
"""

from typing import Optional
from uuid import UUID
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.models.contact import ContactType
from app.schemas.contact import (
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ContactListResponse
)
from app.services.contact_service import get_contact_service
from app.core.rate_limiter import limiter, RATE_LIMITS


router = APIRouter()


@router.get("/", response_model=ContactListResponse)
@limiter.limit(RATE_LIMITS["read"])
async def list_contacts(
    request: Request,
    response: Response,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name"),
    contact_type: Optional[ContactType] = Query(None, description="Filter by contact type"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List contacts with pagination and filtering.

    Requires authentication. Returns only contacts for the user's business.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get contact service
    contact_service = get_contact_service(db)

    # List contacts
    contacts, total = await contact_service.list_contacts(
        business_id=current_user.business_id,
        page=page,
        page_size=page_size,
        search=search,
        contact_type=contact_type,
        is_active=is_active
    )

    # Convert to response schemas (async)
    contact_responses = []
    for contact in contacts:
        contact_responses.append(await contact_service.contact_to_response(contact))

    # Calculate total pages
    total_pages = ceil(total / page_size) if total > 0 else 0

    return ContactListResponse(
        contacts=contact_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single contact by ID.

    Requires authentication. Contact must belong to the user's business.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get contact service
    contact_service = get_contact_service(db)

    # Get contact
    contact = await contact_service.get_contact_by_id(
        contact_id=contact_id,
        business_id=current_user.business_id
    )

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )

    return await contact_service.contact_to_response(contact)


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMITS["create"])
async def create_contact(
    request: Request,
    response: Response,
    contact_data: ContactCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new contact.

    Requires authentication. Contact will be associated with the user's business.
    Sensitive fields (email, phone, KRA PIN) are encrypted.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get contact service
    contact_service = get_contact_service(db)

    # Create contact
    try:
        contact = await contact_service.create_contact(
            business_id=current_user.business_id,
            name=contact_data.name,
            contact_type=contact_data.contact_type,
            email=contact_data.email,
            phone=contact_data.phone,
            kra_pin=contact_data.kra_pin,
            address=contact_data.address,
            notes=contact_data.notes
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return await contact_service.contact_to_response(contact)


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: UUID,
    contact_data: ContactUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a contact.

    Requires authentication. Contact must belong to the user's business.
    Only provided fields will be updated.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get contact service
    contact_service = get_contact_service(db)

    # Convert Pydantic model to dict, excluding unset fields
    update_data = contact_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update"
        )

    # Update contact
    try:
        contact = await contact_service.update_contact(
            contact_id=contact_id,
            business_id=current_user.business_id,
            data=update_data
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )

    return await contact_service.contact_to_response(contact)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a contact (sets is_active to False).

    Requires authentication. Contact must belong to the user's business.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get contact service
    contact_service = get_contact_service(db)

    # Soft delete contact
    contact = await contact_service.soft_delete_contact(
        contact_id=contact_id,
        business_id=current_user.business_id
    )

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )

    # Return 204 No Content
    return None
