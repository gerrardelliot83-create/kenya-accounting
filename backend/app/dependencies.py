"""
Dependency Injection

FastAPI dependencies for authentication, authorization, and common operations.
"""

from typing import Optional, Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import (
    UserRole,
    Permission,
    decode_token,
    has_permission as check_permission,
)
from app.core.cache import get_cache_service, CacheService
from app.db.session import get_db
from app.models.user import User
from app.config import get_settings


# Security scheme
security_scheme = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> str:
    """
    Extract and validate user ID from JWT token.

    Args:
        credentials: HTTP Bearer token credentials

    Returns:
        User ID from token

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        token = credentials.credentials
        payload = decode_token(token)

        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id",
            )

        return user_id

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user from database.

    Args:
        user_id: User ID from token
        db: Database session

    Returns:
        User model instance

    Raises:
        HTTPException: If user not found or inactive
    """
    # Query database - always fetch fresh to ensure proper session binding
    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Ensure current user is active.

    Args:
        current_user: Current user from get_current_user

    Returns:
        Active user

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    return current_user


def require_role(allowed_roles: list[UserRole]):
    """
    Dependency factory to require specific roles.

    Usage:
        @router.get("/admin")
        async def admin_endpoint(
            user: User = Depends(require_role([UserRole.SYSTEM_ADMIN]))
        ):
            ...

    Args:
        allowed_roles: List of allowed user roles

    Returns:
        Dependency function
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return role_checker


def require_permission(required_permission: Permission):
    """
    Dependency factory to require specific permission.

    Usage:
        @router.post("/business")
        async def create_business(
            user: User = Depends(require_permission(Permission.BUSINESS_CREATE))
        ):
            ...

    Args:
        required_permission: Required permission

    Returns:
        Dependency function
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if not check_permission(current_user.role, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_permission.value}",
            )
        return current_user

    return permission_checker


async def check_rate_limit(
    request: Request,
    cache: CacheService = Depends(get_cache_service),
) -> None:
    """
    Check rate limit for API requests.

    Uses IP address as identifier for unauthenticated requests.

    Args:
        request: FastAPI request
        cache: Cache service

    Raises:
        HTTPException: If rate limit exceeded
    """
    settings = get_settings()

    # Get identifier (IP address for now)
    identifier = request.client.host if request.client else "unknown"

    # Check rate limit
    is_allowed, remaining = cache.check_rate_limit(
        identifier=identifier,
        max_requests=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window,
    )

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={
                "X-RateLimit-Limit": str(settings.rate_limit_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(settings.rate_limit_window),
            },
        )


# Type aliases for common dependencies
CurrentUser = Annotated[User, Depends(get_current_active_user)]
SystemAdmin = Annotated[User, Depends(require_role([UserRole.SYSTEM_ADMIN]))]
BusinessAdmin = Annotated[User, Depends(require_role([UserRole.SYSTEM_ADMIN, UserRole.BUSINESS_ADMIN]))]
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]
