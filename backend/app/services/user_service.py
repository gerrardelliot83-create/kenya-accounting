"""
User Service

Business logic for user management operations.
Handles user CRUD operations with encryption for sensitive fields.

Security Notes:
- Email, phone, and national_id are encrypted at rest
- Password hashes are never returned in queries
- All operations are auditable
"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.encryption import get_encryption_service
from app.core.security import hash_password
from app.schemas.user import UserResponse


class UserService:
    """Service for user database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize user service.

        Args:
            db: Database session
        """
        self.db = db
        self.encryption = get_encryption_service()

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            User model or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Note: Since AES-GCM uses random nonces, we can't directly query
        encrypted emails. Instead, we fetch all users and compare decrypted.
        For production with many users, add an email_hash column for lookups.

        Args:
            email: User email address (plaintext)

        Returns:
            User model or None if not found
        """
        # Normalize email
        email_lower = email.lower().strip()

        # Fetch all users and compare decrypted emails
        # TODO: Add email_hash column for efficient lookups in production
        result = await self.db.execute(select(User))
        users = result.scalars().all()

        for user in users:
            try:
                decrypted_email = self.encryption.decrypt(user.email_encrypted)
                if decrypted_email.lower().strip() == email_lower:
                    return user
            except Exception:
                # Skip users with invalid encrypted data
                continue

        return None

    async def create_user(
        self,
        email: str,
        password: str,
        role: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        national_id: Optional[str] = None,
        business_id: Optional[UUID] = None,
        must_change_password: bool = True
    ) -> User:
        """
        Create a new user.

        Encrypts sensitive fields before storage.

        Args:
            email: User email (plaintext)
            password: User password (plaintext)
            role: User role
            first_name: Optional first name
            last_name: Optional last name
            phone: Optional phone number (plaintext)
            national_id: Optional national ID (plaintext)
            business_id: Optional associated business ID
            must_change_password: Force password change on first login

        Returns:
            Created user model

        Raises:
            ValueError: If user with email already exists
        """
        # Check if user exists
        existing_user = await self.get_user_by_email(email)
        if existing_user:
            raise ValueError(f"User with email {email} already exists")

        # Encrypt sensitive fields
        email_encrypted = self.encryption.encrypt(email.lower())
        phone_encrypted = self.encryption.encrypt_optional(phone)
        national_id_encrypted = self.encryption.encrypt_optional(national_id)

        # Hash password
        password_hash = hash_password(password)

        # Create user
        user = User(
            email_encrypted=email_encrypted,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            phone_encrypted=phone_encrypted,
            national_id_encrypted=national_id_encrypted,
            role=role,
            business_id=business_id,
            must_change_password=must_change_password,
            is_active=True
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def update_user(
        self,
        user_id: UUID,
        data: Dict[str, Any]
    ) -> Optional[User]:
        """
        Update user fields.

        Handles encryption for sensitive fields automatically.

        Args:
            user_id: User UUID
            data: Dictionary of fields to update

        Returns:
            Updated user or None if not found
        """
        # Get existing user
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        # Handle encrypted fields
        if "email" in data:
            data["email_encrypted"] = self.encryption.encrypt(data["email"].lower())
            del data["email"]

        if "phone" in data:
            data["phone_encrypted"] = self.encryption.encrypt_optional(data["phone"])
            del data["phone"]

        if "national_id" in data:
            data["national_id_encrypted"] = self.encryption.encrypt_optional(
                data["national_id"]
            )
            del data["national_id"]

        # Handle password hashing
        if "password" in data:
            data["password_hash"] = hash_password(data["password"])
            del data["password"]

        # Update timestamp
        data["updated_at"] = datetime.utcnow()

        # Update user
        await self.db.execute(
            update(User).where(User.id == user_id).values(**data)
        )
        await self.db.commit()

        # Refresh and return
        await self.db.refresh(user)
        return user

    async def update_last_login(self, user_id: UUID) -> None:
        """
        Update user's last login timestamp.

        Args:
            user_id: User UUID
        """
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                last_login_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow()
            )
        )
        await self.db.commit()

    async def deactivate_user(self, user_id: UUID) -> Optional[User]:
        """
        Deactivate a user account.

        Args:
            user_id: User UUID

        Returns:
            Updated user or None if not found
        """
        return await self.update_user(user_id, {"is_active": False})

    async def activate_user(self, user_id: UUID) -> Optional[User]:
        """
        Activate a user account.

        Args:
            user_id: User UUID

        Returns:
            Updated user or None if not found
        """
        return await self.update_user(user_id, {"is_active": True})

    def user_to_response(self, user: User) -> UserResponse:
        """
        Convert User model to UserResponse schema.

        Decrypts sensitive fields for response.

        Args:
            user: User model

        Returns:
            UserResponse schema
        """
        # Decrypt sensitive fields
        email = self.encryption.decrypt(user.email_encrypted)
        phone = self.encryption.decrypt_optional(user.phone_encrypted)

        return UserResponse(
            id=user.id,
            email=email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=phone,
            role=user.role,
            business_id=user.business_id,
            is_active=user.is_active,
            must_change_password=user.must_change_password,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at
        )


def get_user_service(db: AsyncSession) -> UserService:
    """
    Get user service instance.

    Args:
        db: Database session

    Returns:
        UserService instance
    """
    return UserService(db)
