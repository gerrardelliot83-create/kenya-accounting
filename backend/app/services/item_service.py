"""
Item/Service Service

Business logic for item/service catalog management.
Handles CRUD operations with business scoping.

Security Notes:
- All operations are scoped to business_id
- SKU uniqueness is enforced per business
- Supports search and filtering
"""

from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.item import Item, ItemType
from app.schemas.item import ItemResponse
from app.services.audit_service import AuditService


class ItemService:
    """Service for item/service database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize item service.

        Args:
            db: Database session
        """
        self.db = db
        self.audit = AuditService(db)

    async def get_item_by_id(
        self,
        item_id: UUID,
        business_id: UUID
    ) -> Optional[Item]:
        """
        Get item by ID with business scoping.

        Args:
            item_id: Item UUID
            business_id: Business UUID for security scoping

        Returns:
            Item model or None if not found
        """
        result = await self.db.execute(
            select(Item).where(
                Item.id == item_id,
                Item.business_id == business_id
            )
        )
        return result.scalar_one_or_none()

    async def get_item_by_sku(
        self,
        sku: str,
        business_id: UUID
    ) -> Optional[Item]:
        """
        Get item by SKU with business scoping.

        Args:
            sku: Item SKU
            business_id: Business UUID for security scoping

        Returns:
            Item model or None if not found
        """
        result = await self.db.execute(
            select(Item).where(
                Item.sku == sku,
                Item.business_id == business_id
            )
        )
        return result.scalar_one_or_none()

    async def list_items(
        self,
        business_id: UUID,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        item_type: Optional[ItemType] = None,
        is_active: Optional[bool] = True
    ) -> Tuple[List[Item], int]:
        """
        List items with pagination and filtering.

        Args:
            business_id: Business UUID for security scoping
            page: Page number (1-indexed)
            page_size: Number of items per page
            search: Optional search term for name or SKU
            item_type: Optional filter by item type
            is_active: Optional filter by active status

        Returns:
            Tuple of (items list, total count)
        """
        # Build base query
        query = select(Item).where(Item.business_id == business_id)

        # Apply filters
        if search:
            query = query.where(
                (Item.name.ilike(f"%{search}%")) |
                (Item.sku.ilike(f"%{search}%"))
            )

        if item_type:
            query = query.where(Item.item_type == item_type)

        if is_active is not None:
            query = query.where(Item.is_active == is_active)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Order by name
        query = query.order_by(Item.name)

        # Execute query
        result = await self.db.execute(query)
        items = result.scalars().all()

        return list(items), total

    async def create_item(
        self,
        business_id: UUID,
        name: str,
        item_type: ItemType,
        unit_price: Decimal,
        tax_rate: Decimal = Decimal("16.0"),
        description: Optional[str] = None,
        sku: Optional[str] = None,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> Item:
        """
        Create a new item.

        Args:
            business_id: Business UUID
            name: Item name
            item_type: Item type (product or service)
            unit_price: Unit price before tax
            tax_rate: Tax rate percentage (default 16%)
            description: Optional description
            sku: Optional SKU (must be unique per business)
            user_id: Optional user ID for audit logging
            ip_address: Optional IP address for audit logging

        Returns:
            Created item model

        Raises:
            ValueError: If SKU already exists for this business
        """
        # Check if SKU already exists (if provided)
        if sku:
            existing_item = await self.get_item_by_sku(sku, business_id)
            if existing_item:
                raise ValueError(f"Item with SKU '{sku}' already exists")

        # Create item
        item = Item(
            business_id=business_id,
            name=name,
            item_type=item_type,
            description=description,
            sku=sku,
            unit_price=unit_price,
            tax_rate=tax_rate,
            is_active=True
        )

        try:
            self.db.add(item)
            await self.db.flush()

            # Log the creation
            if user_id:
                await self.audit.log_create(
                    user_id=user_id,
                    resource_type="item",
                    resource_id=item.id,
                    new_values={
                        "name": name,
                        "item_type": item_type.value if hasattr(item_type, 'value') else item_type,
                        "sku": sku,
                        "unit_price": float(unit_price),
                        "tax_rate": float(tax_rate),
                        "description": description
                    },
                    ip_address=ip_address
                )

            await self.db.commit()
            await self.db.refresh(item)
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"SKU must be unique: {str(e)}")

        return item

    async def update_item(
        self,
        item_id: UUID,
        business_id: UUID,
        data: Dict[str, Any],
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> Optional[Item]:
        """
        Update item fields.

        Args:
            item_id: Item UUID
            business_id: Business UUID for security scoping
            data: Dictionary of fields to update
            user_id: Optional user ID for audit logging
            ip_address: Optional IP address for audit logging

        Returns:
            Updated item or None if not found

        Raises:
            ValueError: If SKU update conflicts with existing SKU
        """
        # Get existing item
        item = await self.get_item_by_id(item_id, business_id)
        if not item:
            return None

        # Capture old values for audit
        old_values = {
            "name": item.name,
            "item_type": item.item_type.value if hasattr(item.item_type, 'value') else item.item_type,
            "sku": item.sku,
            "unit_price": float(item.unit_price),
            "tax_rate": float(item.tax_rate),
            "description": item.description,
            "is_active": item.is_active
        }

        # Check for SKU conflicts if updating SKU
        if "sku" in data and data["sku"] != item.sku:
            existing_item = await self.get_item_by_sku(data["sku"], business_id)
            if existing_item and existing_item.id != item_id:
                raise ValueError(f"Item with SKU '{data['sku']}' already exists")

        # Update timestamp
        data["updated_at"] = datetime.utcnow()

        # Update item
        try:
            await self.db.execute(
                update(Item)
                .where(Item.id == item_id, Item.business_id == business_id)
                .values(**data)
            )

            # Log the update
            if user_id:
                await self.audit.log_update(
                    user_id=user_id,
                    resource_type="item",
                    resource_id=item_id,
                    old_values=old_values,
                    new_values={k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                               for k, v in data.items() if k != "updated_at"},
                    ip_address=ip_address
                )

            await self.db.commit()
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Update failed: {str(e)}")

        # Refresh and return
        await self.db.refresh(item)
        return item

    async def soft_delete_item(
        self,
        item_id: UUID,
        business_id: UUID,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> Optional[Item]:
        """
        Soft delete an item by setting is_active to False.

        Args:
            item_id: Item UUID
            business_id: Business UUID for security scoping
            user_id: Optional user ID for audit logging
            ip_address: Optional IP address for audit logging

        Returns:
            Updated item or None if not found
        """
        # Get item for audit
        item = await self.get_item_by_id(item_id, business_id)
        if not item:
            return None

        # Log the deletion
        if user_id:
            await self.audit.log_delete(
                user_id=user_id,
                resource_type="item",
                resource_id=item_id,
                old_values={
                    "name": item.name,
                    "sku": item.sku,
                    "is_active": True
                },
                ip_address=ip_address
            )

        return await self.update_item(item_id, business_id, {"is_active": False}, user_id, ip_address)

    def item_to_response(self, item: Item) -> ItemResponse:
        """
        Convert Item model to ItemResponse schema.

        Args:
            item: Item model

        Returns:
            ItemResponse schema
        """
        return ItemResponse(
            id=item.id,
            business_id=item.business_id,
            name=item.name,
            item_type=item.item_type,
            description=item.description,
            sku=item.sku,
            unit_price=item.unit_price,
            tax_rate=item.tax_rate,
            is_active=item.is_active,
            created_at=item.created_at,
            updated_at=item.updated_at
        )


def get_item_service(db: AsyncSession) -> ItemService:
    """
    Get item service instance.

    Args:
        db: Database session

    Returns:
        ItemService instance
    """
    return ItemService(db)
