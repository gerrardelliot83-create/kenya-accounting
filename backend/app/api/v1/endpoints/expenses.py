"""
Expenses API Endpoints

CRUD endpoints for expense management with comprehensive filtering and reporting.
All endpoints require authentication and are scoped to the user's business.

Features:
- Expense CRUD operations
- Date range filtering
- Category and vendor filtering
- Expense summary by category
- Category management (system and custom)
- Payment method filtering
- Reconciliation status tracking

Security:
- Rate limiting on create, update, delete operations
- Standard rate limiting on read operations
"""

from typing import Optional
from uuid import UUID
from datetime import date
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseResponse,
    ExpenseListResponse,
    ExpenseSummaryResponse,
    ExpenseCategoryCreate,
    ExpenseCategoryUpdate,
    ExpenseCategoryResponse,
    PaymentMethod
)
from app.services.expense_service import get_expense_service
from app.core.rate_limiter import limiter, RATE_LIMITS


router = APIRouter()


# Expense Endpoints

@router.get("/", response_model=ExpenseListResponse)
@limiter.limit(RATE_LIMITS["read"])
async def list_expenses(
    request: Request,
    response: Response,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    start_date: Optional[date] = Query(None, description="Filter by expense_date >= start_date"),
    end_date: Optional[date] = Query(None, description="Filter by expense_date <= end_date"),
    vendor_name: Optional[str] = Query(None, description="Filter by vendor name (partial match)"),
    payment_method: Optional[PaymentMethod] = Query(None, description="Filter by payment method"),
    is_reconciled: Optional[bool] = Query(None, description="Filter by reconciliation status"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List expenses with pagination and filtering.

    Requires authentication. Returns only expenses for the user's business.

    Filters:
    - category: Filter by expense category
    - start_date: Filter expenses on or after this date
    - end_date: Filter expenses on or before this date
    - vendor_name: Partial match on vendor name (case-insensitive)
    - payment_method: Filter by payment method (cash, bank_transfer, mpesa, card, other)
    - is_reconciled: Filter by reconciliation status
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get expense service
    expense_service = get_expense_service(db)

    # List expenses
    expenses, total = await expense_service.list_expenses(
        business_id=current_user.business_id,
        page=page,
        page_size=page_size,
        category=category,
        start_date=start_date,
        end_date=end_date,
        vendor_name=vendor_name,
        payment_method=payment_method.value if payment_method else None,
        is_reconciled=is_reconciled
    )

    # Convert to response schemas
    expense_responses = [
        expense_service.expense_to_response(expense)
        for expense in expenses
    ]

    # Calculate total pages
    total_pages = ceil(total / page_size) if total > 0 else 0

    return ExpenseListResponse(
        expenses=expense_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/summary", response_model=ExpenseSummaryResponse)
async def get_expense_summary(
    start_date: date = Query(..., description="Start date (inclusive)"),
    end_date: date = Query(..., description="End date (inclusive)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get expense summary by category for a date range.

    Requires authentication. Returns summary for the user's business.

    Returns:
    - Total expenses and tax for the period
    - Breakdown by category with amounts and counts
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Validate date range
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before or equal to end_date"
        )

    # Get expense service
    expense_service = get_expense_service(db)

    # Get summary
    summary = await expense_service.get_expense_summary(
        business_id=current_user.business_id,
        start_date=start_date,
        end_date=end_date
    )

    return summary


# Category Endpoints - MUST be defined BEFORE /{expense_id} to avoid route conflicts

@router.get("/categories", response_model=list[ExpenseCategoryResponse])
async def list_expense_categories(
    include_system: bool = Query(True, description="Include system categories"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List expense categories for the business.

    Requires authentication. Returns system categories and business custom categories.

    System categories are predefined and cannot be modified or deleted.
    Custom categories are created by the business and can be managed.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get expense service
    expense_service = get_expense_service(db)

    # List categories
    categories = await expense_service.list_categories(
        business_id=current_user.business_id,
        include_system=include_system
    )

    return [
        expense_service.category_to_response(category)
        for category in categories
    ]


@router.post("/categories", response_model=ExpenseCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_expense_category(
    category_data: ExpenseCategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a custom expense category.

    Requires authentication. Category will be associated with the user's business.

    Validation:
    - Category name must be unique for this business
    - Name is sanitized to prevent XSS
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get expense service
    expense_service = get_expense_service(db)

    # Create category
    try:
        category = await expense_service.create_category(
            business_id=current_user.business_id,
            name=category_data.name,
            description=category_data.description
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return expense_service.category_to_response(category)


@router.put("/categories/{category_id}", response_model=ExpenseCategoryResponse)
async def update_expense_category(
    category_id: UUID,
    category_data: ExpenseCategoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a custom expense category.

    Requires authentication. Category must belong to the user's business.

    Note: System categories cannot be modified.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get expense service
    expense_service = get_expense_service(db)

    # Convert Pydantic model to dict, excluding unset fields
    update_data = category_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update"
        )

    # Update category
    try:
        category = await expense_service.update_category(
            category_id=category_id,
            business_id=current_user.business_id,
            data=update_data
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    return expense_service.category_to_response(category)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense_category(
    category_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a custom expense category.

    Requires authentication. Category must belong to the user's business.

    Note:
    - System categories cannot be deleted
    - Categories in use by expenses cannot be deleted
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get expense service
    expense_service = get_expense_service(db)

    # Delete category
    try:
        deleted = await expense_service.delete_category(
            category_id=category_id,
            business_id=current_user.business_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    return None


# Expense Item Endpoints - Routes with {expense_id} come AFTER static routes

@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single expense by ID.

    Requires authentication. Expense must belong to the user's business.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get expense service
    expense_service = get_expense_service(db)

    # Get expense
    expense = await expense_service.get_expense_by_id(
        expense_id=expense_id,
        business_id=current_user.business_id
    )

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    return expense_service.expense_to_response(expense)


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMITS["create"])
async def create_expense(
    request: Request,
    response: Response,
    expense_data: ExpenseCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new expense.

    Requires authentication. Expense will be associated with the user's business.

    Validation:
    - Amount must be positive
    - Expense date cannot be in the future
    - All text fields are sanitized
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get expense service
    expense_service = get_expense_service(db)

    # Convert Pydantic model to dict
    expense_dict = expense_data.model_dump()

    # Create expense
    try:
        expense = await expense_service.create_expense(
            business_id=current_user.business_id,
            data=expense_dict
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return expense_service.expense_to_response(expense)


@router.put("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: UUID,
    expense_data: ExpenseUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an expense.

    Requires authentication. Expense must belong to the user's business.

    Note: Reconciled expenses cannot be modified unless you set is_reconciled=false.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get expense service
    expense_service = get_expense_service(db)

    # Convert Pydantic model to dict, excluding unset fields
    update_data = expense_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update"
        )

    # Update expense
    try:
        expense = await expense_service.update_expense(
            expense_id=expense_id,
            business_id=current_user.business_id,
            data=update_data
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    return expense_service.expense_to_response(expense)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete an expense.

    Requires authentication. Expense must belong to the user's business.

    Note: Reconciled expenses cannot be deleted. Unreconcile first.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get expense service
    expense_service = get_expense_service(db)

    # Delete expense
    try:
        deleted = await expense_service.soft_delete_expense(
            expense_id=expense_id,
            business_id=current_user.business_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    return None
