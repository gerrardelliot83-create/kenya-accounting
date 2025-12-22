"""
Contact Service

Business logic for contact management operations.
Handles contact CRUD with encryption for sensitive fields.

Security Notes:
- Email, phone, and KRA PIN are encrypted at rest
- All operations are scoped to business_id
- Supports search and filtering
"""

from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID
from datetime import datetime
from math import ceil

from sqlalchemy import select, update, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact, ContactType
from app.core.encryption import get_encryption_service
from app.schemas.contact import ContactResponse
from app.services.audit_service import AuditService


class ContactService:
    """Service for contact database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize contact service.

        Args:
            db: Database session
        """
        self.db = db
        self.encryption = get_encryption_service()
        self.audit = AuditService(db)

    async def get_contact_by_id(
        self,
        contact_id: UUID,
        business_id: UUID
    ) -> Optional[Contact]:
        """
        Get contact by ID with business scoping.

        Args:
            contact_id: Contact UUID
            business_id: Business UUID for security scoping

        Returns:
            Contact model or None if not found
        """
        result = await self.db.execute(
            select(Contact).where(
                Contact.id == contact_id,
                Contact.business_id == business_id
            )
        )
        return result.scalar_one_or_none()

    async def list_contacts(
        self,
        business_id: UUID,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        contact_type: Optional[ContactType] = None,
        is_active: Optional[bool] = True
    ) -> Tuple[List[Contact], int]:
        """
        List contacts with pagination and filtering.

        Args:
            business_id: Business UUID for security scoping
            page: Page number (1-indexed)
            page_size: Number of items per page
            search: Optional search term for name
            contact_type: Optional filter by contact type
            is_active: Optional filter by active status

        Returns:
            Tuple of (contacts list, total count)
        """
        # Build base query
        query = select(Contact).where(Contact.business_id == business_id)

        # Apply filters
        if search:
            query = query.where(Contact.name.ilike(f"%{search}%"))

        if contact_type:
            query = query.where(Contact.contact_type == contact_type)

        if is_active is not None:
            query = query.where(Contact.is_active == is_active)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Order by name
        query = query.order_by(Contact.name)

        # Execute query
        result = await self.db.execute(query)
        contacts = result.scalars().all()

        return list(contacts), total

    async def create_contact(
        self,
        business_id: UUID,
        name: str,
        contact_type: ContactType,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        kra_pin: Optional[str] = None,
        address: Optional[str] = None,
        notes: Optional[str] = None,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> Contact:
        """
        Create a new contact.

        Encrypts sensitive fields before storage.

        Args:
            business_id: Business UUID
            name: Contact name
            contact_type: Contact type
            email: Optional email (will be encrypted)
            phone: Optional phone (will be encrypted)
            kra_pin: Optional KRA PIN (will be encrypted)
            address: Optional address
            notes: Optional notes
            user_id: Optional user ID for audit logging
            ip_address: Optional IP address for audit logging

        Returns:
            Created contact model
        """
        # Encrypt sensitive fields
        email_encrypted = self.encryption.encrypt_optional(email)
        phone_encrypted = self.encryption.encrypt_optional(phone)
        kra_pin_encrypted = self.encryption.encrypt_optional(kra_pin)

        # Create contact
        contact = Contact(
            business_id=business_id,
            name=name,
            contact_type=contact_type,
            email_encrypted=email_encrypted,
            phone_encrypted=phone_encrypted,
            kra_pin_encrypted=kra_pin_encrypted,
            address=address,
            notes=notes,
            is_active=True
        )

        self.db.add(contact)
        await self.db.flush()

        # Log the creation (without sensitive data)
        if user_id:
            await self.audit.log_create(
                user_id=user_id,
                resource_type="contact",
                resource_id=contact.id,
                new_values={
                    "name": name,
                    "contact_type": contact_type.value if hasattr(contact_type, 'value') else contact_type,
                    "has_email": email is not None,
                    "has_phone": phone is not None,
                    "has_kra_pin": kra_pin is not None,
                    "address": address,
                    "notes": notes
                },
                ip_address=ip_address
            )

        await self.db.commit()
        await self.db.refresh(contact)

        return contact

    async def update_contact(
        self,
        contact_id: UUID,
        business_id: UUID,
        data: Dict[str, Any],
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> Optional[Contact]:
        """
        Update contact fields.

        Handles encryption for sensitive fields automatically.

        Args:
            contact_id: Contact UUID
            business_id: Business UUID for security scoping
            data: Dictionary of fields to update
            user_id: Optional user ID for audit logging
            ip_address: Optional IP address for audit logging

        Returns:
            Updated contact or None if not found
        """
        # Get existing contact
        contact = await self.get_contact_by_id(contact_id, business_id)
        if not contact:
            return None

        # Capture old values for audit (without sensitive data)
        old_values = {
            "name": contact.name,
            "contact_type": contact.contact_type.value if hasattr(contact.contact_type, 'value') else contact.contact_type,
            "has_email": contact.email_encrypted is not None,
            "has_phone": contact.phone_encrypted is not None,
            "has_kra_pin": contact.kra_pin_encrypted is not None,
            "address": contact.address,
            "notes": contact.notes,
            "is_active": contact.is_active
        }

        # Prepare new values for audit (without sensitive data)
        new_values = {}
        for key, value in data.items():
            if key in ["email", "phone", "kra_pin"]:
                new_values[f"has_{key}"] = value is not None
            else:
                new_values[key] = value

        # Handle encrypted fields
        if "email" in data:
            data["email_encrypted"] = self.encryption.encrypt_optional(data["email"])
            del data["email"]

        if "phone" in data:
            data["phone_encrypted"] = self.encryption.encrypt_optional(data["phone"])
            del data["phone"]

        if "kra_pin" in data:
            data["kra_pin_encrypted"] = self.encryption.encrypt_optional(data["kra_pin"])
            del data["kra_pin"]

        # Update timestamp
        data["updated_at"] = datetime.utcnow()

        # Update contact
        await self.db.execute(
            update(Contact)
            .where(Contact.id == contact_id, Contact.business_id == business_id)
            .values(**data)
        )

        # Log the update
        if user_id:
            await self.audit.log_update(
                user_id=user_id,
                resource_type="contact",
                resource_id=contact_id,
                old_values=old_values,
                new_values=new_values,
                ip_address=ip_address
            )

        await self.db.commit()

        # Refresh and return
        await self.db.refresh(contact)
        return contact

    async def soft_delete_contact(
        self,
        contact_id: UUID,
        business_id: UUID,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> Optional[Contact]:
        """
        Soft delete a contact by setting is_active to False.

        Args:
            contact_id: Contact UUID
            business_id: Business UUID for security scoping
            user_id: Optional user ID for audit logging
            ip_address: Optional IP address for audit logging

        Returns:
            Updated contact or None if not found
        """
        # Get contact for audit
        contact = await self.get_contact_by_id(contact_id, business_id)
        if not contact:
            return None

        # Log the deletion
        if user_id:
            await self.audit.log_delete(
                user_id=user_id,
                resource_type="contact",
                resource_id=contact_id,
                old_values={
                    "name": contact.name,
                    "contact_type": contact.contact_type.value if hasattr(contact.contact_type, 'value') else contact.contact_type,
                    "is_active": True
                },
                ip_address=ip_address
            )

        return await self.update_contact(contact_id, business_id, {"is_active": False}, user_id, ip_address)

    async def contact_to_response(
        self,
        contact: Contact,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> ContactResponse:
        """
        Convert Contact model to ContactResponse schema.

        Decrypts sensitive fields for response and logs access to sensitive data.

        Args:
            contact: Contact model
            user_id: Optional user ID for audit logging
            ip_address: Optional IP address for audit logging

        Returns:
            ContactResponse schema
        """
        # Decrypt sensitive fields
        email = self.encryption.decrypt_optional(contact.email_encrypted)
        phone = self.encryption.decrypt_optional(contact.phone_encrypted)
        kra_pin = self.encryption.decrypt_optional(contact.kra_pin_encrypted)

        # Log access to sensitive data if any sensitive fields are present
        if user_id and (email or phone or kra_pin):
            fields_accessed = []
            if email:
                fields_accessed.append("email")
            if phone:
                fields_accessed.append("phone")
            if kra_pin:
                fields_accessed.append("kra_pin")

            await self.audit.log_view_sensitive(
                user_id=user_id,
                resource_type="contact",
                resource_id=contact.id,
                fields_accessed=fields_accessed,
                ip_address=ip_address
            )

        return ContactResponse(
            id=contact.id,
            business_id=contact.business_id,
            name=contact.name,
            contact_type=contact.contact_type,
            email=email,
            phone=phone,
            kra_pin=kra_pin,
            address=contact.address,
            notes=contact.notes,
            is_active=contact.is_active,
            created_at=contact.created_at,
            updated_at=contact.updated_at
        )


def get_contact_service(db: AsyncSession) -> ContactService:
    """
    Get contact service instance.

    Args:
        db: Database session

    Returns:
        ContactService instance
    """
    return ContactService(db)
