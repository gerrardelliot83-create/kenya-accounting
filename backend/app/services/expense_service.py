"""
Expense Service

Business logic for expense management operations.
Handles expense CRUD, categorization, filtering, and summary reporting.

Features:
- Business-scoped expense operations
- Category management (system and custom)
- Date range filtering
- Expense summaries by category
- Soft delete support
- Vendor tracking

Security Notes:
- All operations are scoped to business_id
- Input validation at schema level
- Proper error handling with ValueError
"""

from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID
from datetime import date
from decimal import Decimal

from sqlalchemy import select, update, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense import Expense
from app.models.expense_category import ExpenseCategory
from app.schemas.expense import (
    ExpenseResponse,
    ExpenseSummaryByCategoryResponse,
    ExpenseSummaryResponse,
    ExpenseCategoryResponse
)
from app.services.audit_service import AuditService


class ExpenseService:
    """Service for expense database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize expense service.

        Args:
            db: Database session
        """
        self.db = db
        self.audit = AuditService(db)

    async def get_expense_by_id(
        self,
        expense_id: UUID,
        business_id: UUID
    ) -> Optional[Expense]:
        """
        Get expense by ID with business scoping.

        Args:
            expense_id: Expense UUID
            business_id: Business UUID for security scoping

        Returns:
            Expense model or None if not found
        """
        result = await self.db.execute(
            select(Expense).where(
                Expense.id == expense_id,
                Expense.business_id == business_id,
                Expense.is_active == True
            )
        )
        return result.scalar_one_or_none()

    async def list_expenses(
        self,
        business_id: UUID,
        page: int = 1,
        page_size: int = 50,
        category: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        vendor_name: Optional[str] = None,
        payment_method: Optional[str] = None,
        is_reconciled: Optional[bool] = None
    ) -> Tuple[List[Expense], int]:
        """
        List expenses with pagination and filtering.

        Args:
            business_id: Business UUID for security scoping
            page: Page number (1-indexed)
            page_size: Number of items per page
            category: Optional filter by category
            start_date: Optional filter by expense_date >= start_date
            end_date: Optional filter by expense_date <= end_date
            vendor_name: Optional filter by vendor name (partial match)
            payment_method: Optional filter by payment method
            is_reconciled: Optional filter by reconciliation status

        Returns:
            Tuple of (expenses list, total count)
        """
        # Build base query
        query = select(Expense).where(
            Expense.business_id == business_id,
            Expense.is_active == True
        )

        # Apply filters
        if category:
            query = query.where(Expense.category == category)

        if start_date:
            query = query.where(Expense.expense_date >= start_date)

        if end_date:
            query = query.where(Expense.expense_date <= end_date)

        if vendor_name:
            # Partial match, case-insensitive
            query = query.where(Expense.vendor_name.ilike(f"%{vendor_name}%"))

        if payment_method:
            query = query.where(Expense.payment_method == payment_method)

        if is_reconciled is not None:
            query = query.where(Expense.is_reconciled == is_reconciled)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Order by expense_date descending (newest first)
        query = query.order_by(Expense.expense_date.desc(), Expense.created_at.desc())

        # Execute query
        result = await self.db.execute(query)
        expenses = result.scalars().all()

        return list(expenses), total

    async def create_expense(
        self,
        business_id: UUID,
        data: Dict[str, Any],
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> Expense:
        """
        Create a new expense.

        Args:
            business_id: Business UUID
            data: Expense data dictionary
            user_id: Optional user ID for audit logging
            ip_address: Optional IP address for audit logging

        Returns:
            Created expense model

        Raises:
            ValueError: If data is invalid
        """
        # Validate amount is positive
        if data.get("amount", 0) <= 0:
            raise ValueError("Expense amount must be positive")

        # Create expense
        expense = Expense(
            business_id=business_id,
            category=data["category"],
            description=data["description"],
            amount=Decimal(str(data["amount"])),
            tax_amount=Decimal(str(data.get("tax_amount", "0.00"))),
            expense_date=data["expense_date"],
            vendor_name=data.get("vendor_name"),
            receipt_url=data.get("receipt_url"),
            payment_method=data["payment_method"],
            reference_number=data.get("reference_number"),
            notes=data.get("notes"),
            is_reconciled=False,  # New expenses start as unreconciled
            is_active=True
        )

        self.db.add(expense)
        await self.db.flush()

        # Log the creation
        if user_id:
            await self.audit.log_create(
                user_id=user_id,
                resource_type="expense",
                resource_id=expense.id,
                new_values={
                    "category": data["category"],
                    "description": data["description"],
                    "amount": float(data["amount"]),
                    "expense_date": str(data["expense_date"]),
                    "vendor_name": data.get("vendor_name"),
                    "payment_method": data["payment_method"]
                },
                ip_address=ip_address
            )

        await self.db.commit()
        await self.db.refresh(expense)

        return expense

    async def update_expense(
        self,
        expense_id: UUID,
        business_id: UUID,
        data: Dict[str, Any],
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> Optional[Expense]:
        """
        Update expense fields.

        Args:
            expense_id: Expense UUID
            business_id: Business UUID for security scoping
            data: Dictionary of fields to update
            user_id: Optional user ID for audit logging
            ip_address: Optional IP address for audit logging

        Returns:
            Updated expense or None if not found

        Raises:
            ValueError: If data is invalid or expense is reconciled
        """
        # Get existing expense
        expense = await self.get_expense_by_id(expense_id, business_id)
        if not expense:
            return None

        # Capture old values for audit
        old_values = {
            "category": expense.category,
            "description": expense.description,
            "amount": float(expense.amount),
            "is_reconciled": expense.is_reconciled
        }

        # Prevent updating reconciled expenses (business rule)
        if expense.is_reconciled and "is_reconciled" not in data:
            raise ValueError("Cannot modify reconciled expense. Unreconcile first.")

        # Validate amount if provided
        if "amount" in data and data["amount"] <= 0:
            raise ValueError("Expense amount must be positive")

        # Convert decimal fields
        if "amount" in data:
            data["amount"] = Decimal(str(data["amount"]))
        if "tax_amount" in data:
            data["tax_amount"] = Decimal(str(data["tax_amount"]))

        # Update expense
        await self.db.execute(
            update(Expense)
            .where(
                Expense.id == expense_id,
                Expense.business_id == business_id,
                Expense.is_active == True
            )
            .values(**data)
        )

        # Log the update
        if user_id:
            await self.audit.log_update(
                user_id=user_id,
                resource_type="expense",
                resource_id=expense_id,
                old_values=old_values,
                new_values={k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                           for k, v in data.items()},
                ip_address=ip_address
            )

        await self.db.commit()

        # Refresh and return
        await self.db.refresh(expense)
        return expense

    async def soft_delete_expense(
        self,
        expense_id: UUID,
        business_id: UUID,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Soft delete an expense.

        Args:
            expense_id: Expense UUID
            business_id: Business UUID for security scoping
            user_id: Optional user ID for audit logging
            ip_address: Optional IP address for audit logging

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If expense is reconciled
        """
        # Get existing expense
        expense = await self.get_expense_by_id(expense_id, business_id)
        if not expense:
            return False

        # Prevent deleting reconciled expenses (business rule)
        if expense.is_reconciled:
            raise ValueError("Cannot delete reconciled expense. Unreconcile first.")

        # Log the deletion
        if user_id:
            await self.audit.log_delete(
                user_id=user_id,
                resource_type="expense",
                resource_id=expense_id,
                old_values={
                    "description": expense.description,
                    "amount": float(expense.amount),
                    "is_active": True
                },
                ip_address=ip_address
            )

        # Soft delete
        await self.db.execute(
            update(Expense)
            .where(
                Expense.id == expense_id,
                Expense.business_id == business_id
            )
            .values(is_active=False)
        )
        await self.db.commit()

        return True

    async def get_expense_summary(
        self,
        business_id: UUID,
        start_date: date,
        end_date: date
    ) -> ExpenseSummaryResponse:
        """
        Get expense summary by category for a date range.

        Args:
            business_id: Business UUID
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Expense summary with category breakdown
        """
        # Query for summary by category
        result = await self.db.execute(
            select(
                Expense.category,
                func.sum(Expense.amount).label("total_amount"),
                func.sum(Expense.tax_amount).label("total_tax"),
                func.count(Expense.id).label("expense_count")
            )
            .where(
                Expense.business_id == business_id,
                Expense.is_active == True,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date
            )
            .group_by(Expense.category)
            .order_by(func.sum(Expense.amount).desc())
        )

        category_summaries = []
        total_expenses = Decimal("0.00")
        total_tax = Decimal("0.00")
        total_count = 0

        for row in result:
            category_summary = ExpenseSummaryByCategoryResponse(
                category=row.category,
                total_amount=round(Decimal(str(row.total_amount or 0)), 2),
                total_tax=round(Decimal(str(row.total_tax or 0)), 2),
                expense_count=row.expense_count
            )
            category_summaries.append(category_summary)
            total_expenses += category_summary.total_amount
            total_tax += category_summary.total_tax
            total_count += category_summary.expense_count

        return ExpenseSummaryResponse(
            start_date=start_date,
            end_date=end_date,
            total_expenses=round(total_expenses, 2),
            total_tax=round(total_tax, 2),
            expense_count=total_count,
            by_category=category_summaries
        )

    # Category Management Methods

    async def get_category_by_id(
        self,
        category_id: UUID,
        business_id: Optional[UUID] = None
    ) -> Optional[ExpenseCategory]:
        """
        Get expense category by ID.

        Args:
            category_id: Category UUID
            business_id: Optional business UUID (for custom categories)

        Returns:
            ExpenseCategory or None
        """
        query = select(ExpenseCategory).where(
            ExpenseCategory.id == category_id,
            ExpenseCategory.is_active == True
        )

        # If business_id provided, filter by it (for custom categories)
        if business_id:
            query = query.where(
                or_(
                    ExpenseCategory.business_id == business_id,
                    ExpenseCategory.is_system == True
                )
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_categories(
        self,
        business_id: UUID,
        include_system: bool = True
    ) -> List[ExpenseCategory]:
        """
        List expense categories for a business.

        Args:
            business_id: Business UUID
            include_system: Whether to include system categories

        Returns:
            List of expense categories
        """
        query = select(ExpenseCategory).where(
            ExpenseCategory.is_active == True
        )

        if include_system:
            # Include both system categories and business custom categories
            query = query.where(
                or_(
                    ExpenseCategory.business_id == business_id,
                    ExpenseCategory.is_system == True
                )
            )
        else:
            # Only custom categories for this business
            query = query.where(ExpenseCategory.business_id == business_id)

        query = query.order_by(
            ExpenseCategory.is_system.desc(),  # System categories first
            ExpenseCategory.name.asc()
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_category(
        self,
        business_id: UUID,
        name: str,
        description: Optional[str] = None
    ) -> ExpenseCategory:
        """
        Create a custom expense category.

        Args:
            business_id: Business UUID
            name: Category name
            description: Optional description

        Returns:
            Created category

        Raises:
            ValueError: If category name already exists for this business
        """
        # Check if category name already exists for this business
        existing = await self.db.execute(
            select(ExpenseCategory).where(
                ExpenseCategory.business_id == business_id,
                ExpenseCategory.name == name,
                ExpenseCategory.is_active == True
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Category '{name}' already exists for this business")

        # Create category
        category = ExpenseCategory(
            business_id=business_id,
            name=name,
            description=description,
            is_system=False,
            is_active=True
        )

        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)

        return category

    async def update_category(
        self,
        category_id: UUID,
        business_id: UUID,
        data: Dict[str, Any]
    ) -> Optional[ExpenseCategory]:
        """
        Update a custom expense category.

        Args:
            category_id: Category UUID
            business_id: Business UUID
            data: Update data

        Returns:
            Updated category or None

        Raises:
            ValueError: If category is system category or name already exists
        """
        # Get category
        category = await self.get_category_by_id(category_id, business_id)
        if not category:
            return None

        # Check if it's a system category
        if category.is_system:
            raise ValueError("Cannot modify system category")

        # Check if it belongs to this business
        if category.business_id != business_id:
            raise ValueError("Category does not belong to this business")

        # Check name uniqueness if name is being updated
        if "name" in data:
            existing = await self.db.execute(
                select(ExpenseCategory).where(
                    ExpenseCategory.business_id == business_id,
                    ExpenseCategory.name == data["name"],
                    ExpenseCategory.id != category_id,
                    ExpenseCategory.is_active == True
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"Category '{data['name']}' already exists for this business")

        # Update category
        await self.db.execute(
            update(ExpenseCategory)
            .where(
                ExpenseCategory.id == category_id,
                ExpenseCategory.business_id == business_id
            )
            .values(**data)
        )
        await self.db.commit()

        await self.db.refresh(category)
        return category

    async def delete_category(
        self,
        category_id: UUID,
        business_id: UUID
    ) -> bool:
        """
        Soft delete a custom expense category.

        Args:
            category_id: Category UUID
            business_id: Business UUID

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If category is system category or in use
        """
        # Get category
        category = await self.get_category_by_id(category_id, business_id)
        if not category:
            return False

        # Check if it's a system category
        if category.is_system:
            raise ValueError("Cannot delete system category")

        # Check if it belongs to this business
        if category.business_id != business_id:
            raise ValueError("Category does not belong to this business")

        # Check if category is in use
        expenses_using_category = await self.db.execute(
            select(func.count(Expense.id))
            .where(
                Expense.business_id == business_id,
                Expense.category == category.name,
                Expense.is_active == True
            )
        )
        count = expenses_using_category.scalar()
        if count > 0:
            raise ValueError(
                f"Cannot delete category '{category.name}' as it is used by {count} expense(s)"
            )

        # Soft delete
        await self.db.execute(
            update(ExpenseCategory)
            .where(
                ExpenseCategory.id == category_id,
                ExpenseCategory.business_id == business_id
            )
            .values(is_active=False)
        )
        await self.db.commit()

        return True

    def expense_to_response(self, expense: Expense) -> ExpenseResponse:
        """
        Convert Expense model to ExpenseResponse schema.

        Args:
            expense: Expense model

        Returns:
            ExpenseResponse schema
        """
        return ExpenseResponse(
            id=expense.id,
            business_id=expense.business_id,
            category=expense.category,
            description=expense.description,
            amount=expense.amount,
            tax_amount=expense.tax_amount,
            expense_date=expense.expense_date,
            vendor_name=expense.vendor_name,
            receipt_url=expense.receipt_url,
            payment_method=expense.payment_method,
            reference_number=expense.reference_number,
            is_reconciled=expense.is_reconciled,
            notes=expense.notes,
            is_active=expense.is_active,
            created_at=expense.created_at,
            updated_at=expense.updated_at
        )

    def category_to_response(self, category: ExpenseCategory) -> ExpenseCategoryResponse:
        """
        Convert ExpenseCategory model to ExpenseCategoryResponse schema.

        Args:
            category: ExpenseCategory model

        Returns:
            ExpenseCategoryResponse schema
        """
        return ExpenseCategoryResponse(
            id=category.id,
            business_id=category.business_id,
            name=category.name,
            description=category.description,
            is_system=category.is_system,
            is_active=category.is_active,
            created_at=category.created_at,
            updated_at=category.updated_at
        )


def get_expense_service(db: AsyncSession) -> ExpenseService:
    """
    Get expense service instance.

    Args:
        db: Database session

    Returns:
        ExpenseService instance
    """
    return ExpenseService(db)
