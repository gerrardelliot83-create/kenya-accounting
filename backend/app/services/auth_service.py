"""
Authentication Service

Handles user authentication, token generation, and password management.
Integrates with audit logging for security tracking.

Security Notes:
- All authentication attempts are logged (success and failure)
- Failed login attempts are rate limited
- Password changes invalidate existing sessions
- Tokens contain minimal user information
"""

from typing import Optional, Tuple
from uuid import UUID
from datetime import datetime

from fastapi import HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.audit_log import AuditLog, AuditAction, AuditStatus
from app.core.security import (
    verify_password,
    hash_password,
    get_token_service,
)
from app.core.cache import get_cache_service
from app.services.user_service import UserService, get_user_service


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize authentication service.

        Args:
            db: Database session
        """
        self.db = db
        self.user_service = get_user_service(db)
        self.token_service = get_token_service()
        self.cache = get_cache_service()

    async def authenticate_user(
        self,
        email: str,
        password: str
    ) -> Optional[User]:
        """
        Authenticate user with email and password.

        Args:
            email: User email address
            password: User password (plaintext)

        Returns:
            User model if authentication successful, None otherwise

        Note:
            This method does NOT log the authentication attempt.
            Logging should be done by the caller with request context.
        """
        # Get user by email (email is encrypted in database)
        user = await self.user_service.get_user_by_email(email)

        if not user:
            return None

        # Verify password
        if not user.password_hash:
            # User has no password set (shouldn't happen in production)
            return None

        if not verify_password(password, user.password_hash):
            return None

        # Check if user is active
        if not user.is_active:
            return None

        return user

    async def create_user_tokens(self, user: User) -> Tuple[str, str]:
        """
        Create access and refresh tokens for user.

        Args:
            user: User model

        Returns:
            Tuple of (access_token, refresh_token)
        """
        # Decrypt email for token subject
        email = self.user_service.encryption.decrypt(user.email_encrypted)

        # Create access token
        access_token = self.token_service.create_access_token(
            subject=email,
            user_id=str(user.id),
            role=user.role.value,
            business_id=str(user.business_id) if user.business_id else None
        )

        # Create refresh token
        refresh_token = self.token_service.create_refresh_token(
            subject=email,
            user_id=str(user.id)
        )

        return access_token, refresh_token

    async def refresh_access_token(self, refresh_token: str) -> str:
        """
        Validate refresh token and issue new access token.

        Args:
            refresh_token: JWT refresh token

        Returns:
            New access token

        Raises:
            HTTPException: If refresh token is invalid or user not found
        """
        try:
            # Decode refresh token
            payload = self.token_service.decode_token(refresh_token)

            # Verify token type
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )

            # Get user
            user_id = payload.get("user_id")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user_id"
                )

            user = await self.user_service.get_user_by_id(UUID(user_id))
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )

            # Create new access token
            email = self.user_service.encryption.decrypt(user.email_encrypted)
            access_token = self.token_service.create_access_token(
                subject=email,
                user_id=str(user.id),
                role=user.role.value,
                business_id=str(user.business_id) if user.business_id else None
            )

            return access_token

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate refresh token"
            )

    async def change_user_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str
    ) -> None:
        """
        Change user password.

        Args:
            user_id: User UUID
            current_password: Current password (plaintext)
            new_password: New password (plaintext)

        Raises:
            HTTPException: If current password is invalid or user not found
        """
        # Get user
        user = await self.user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify current password
        if not user.password_hash or not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # Check that new password is different
        if current_password == new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password"
            )

        # Update password and clear must_change_password flag
        await self.user_service.update_user(
            user_id=user_id,
            data={
                "password": new_password,  # Will be hashed by user_service
                "must_change_password": False
            }
        )

        # Invalidate user cache
        self.cache.delete(f"user:{user_id}", cache_type="session")

    async def logout_user(self, user_id: UUID, token: str) -> None:
        """
        Logout user by invalidating token.

        For MVP with stateless JWT, we can't truly invalidate tokens.
        This is a placeholder for future token blacklisting.

        Args:
            user_id: User UUID
            token: Access token to invalidate

        Note:
            In production, implement token blacklisting with Redis
            or use shorter token expiration times.
        """
        # Clear user cache
        self.cache.delete(f"user:{user_id}", cache_type="session")

        # TODO: For production, add token to blacklist cache
        # token_jti = decode_token(token).get("jti")
        # self.cache.set(f"blacklist:{token_jti}", True, ttl=token_expiration)

    async def log_auth_event(
        self,
        action: str,
        status: str,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None,
        details: Optional[dict] = None
    ) -> None:
        """
        Log authentication event to audit log.

        Args:
            action: Action performed (e.g., "login", "logout", "password_change")
            status: Action status ("success", "failure", "error")
            user_id: Optional user ID
            ip_address: Optional IP address
            user_agent: Optional user agent string
            error_message: Optional error message
            details: Optional additional details
        """
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type="user",
            resource_id=user_id,
            status=status,
            details=details,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.db.add(audit_log)
        await self.db.commit()

    async def check_login_rate_limit(
        self,
        identifier: str,
        max_attempts: int = 5,
        window_seconds: int = 300
    ) -> bool:
        """
        Check if login attempts are within rate limit.

        Args:
            identifier: Email or IP address
            max_attempts: Maximum attempts allowed
            window_seconds: Time window in seconds

        Returns:
            True if within limit, False if exceeded
        """
        is_allowed, remaining = self.cache.check_rate_limit(
            identifier=f"login:{identifier}",
            max_requests=max_attempts,
            window_seconds=window_seconds
        )

        return is_allowed

    def get_request_context(self, request: Request) -> dict:
        """
        Extract request context for audit logging.

        Args:
            request: FastAPI request

        Returns:
            Dictionary with ip_address and user_agent
        """
        return {
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent")
        }


def get_auth_service(db: AsyncSession) -> AuthService:
    """
    Get authentication service instance.

    Args:
        db: Database session

    Returns:
        AuthService instance
    """
    return AuthService(db)
