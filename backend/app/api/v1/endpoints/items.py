"""
Items/Services API Endpoints

CRUD endpoints for item/service catalog management.
All endpoints require authentication and are scoped to the user's business.
"""

from typing import Optional
from uuid import UUID
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.models.item import ItemType
from app.schemas.item import (
    ItemCreate,
    ItemUpdate,
    ItemResponse,
    ItemListResponse
)
from app.services.item_service import get_item_service


router = APIRouter()


@router.get("/", response_model=ItemListResponse)
async def list_items(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name or SKU"),
    item_type: Optional[ItemType] = Query(None, description="Filter by item type"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List items with pagination and filtering.

    Requires authentication. Returns only items for the user's business.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get item service
    item_service = get_item_service(db)

    # List items
    items, total = await item_service.list_items(
        business_id=current_user.business_id,
        page=page,
        page_size=page_size,
        search=search,
        item_type=item_type,
        is_active=is_active
    )

    # Convert to response schemas
    item_responses = [
        item_service.item_to_response(item)
        for item in items
    ]

    # Calculate total pages
    total_pages = ceil(total / page_size) if total > 0 else 0

    return ItemListResponse(
        items=item_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single item by ID.

    Requires authentication. Item must belong to the user's business.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get item service
    item_service = get_item_service(db)

    # Get item
    item = await item_service.get_item_by_id(
        item_id=item_id,
        business_id=current_user.business_id
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    return item_service.item_to_response(item)


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    item_data: ItemCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new item.

    Requires authentication. Item will be associated with the user's business.
    SKU must be unique within the business.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get item service
    item_service = get_item_service(db)

    # Create item
    try:
        item = await item_service.create_item(
            business_id=current_user.business_id,
            name=item_data.name,
            item_type=item_data.item_type,
            unit_price=item_data.unit_price,
            tax_rate=item_data.tax_rate,
            description=item_data.description,
            sku=item_data.sku
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return item_service.item_to_response(item)


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: UUID,
    item_data: ItemUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an item.

    Requires authentication. Item must belong to the user's business.
    Only provided fields will be updated.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get item service
    item_service = get_item_service(db)

    # Convert Pydantic model to dict, excluding unset fields
    update_data = item_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update"
        )

    # Update item
    try:
        item = await item_service.update_item(
            item_id=item_id,
            business_id=current_user.business_id,
            data=update_data
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    return item_service.item_to_response(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete an item (sets is_active to False).

    Requires authentication. Item must belong to the user's business.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get item service
    item_service = get_item_service(db)

    # Soft delete item
    item = await item_service.soft_delete_item(
        item_id=item_id,
        business_id=current_user.business_id
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    # Return 204 No Content
    return None
