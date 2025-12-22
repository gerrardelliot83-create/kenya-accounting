"""
Security Module

Handles authentication, authorization, and security utilities.
Integrates with Supabase Auth for user authentication.

Components:
- JWT token creation and validation
- Password hashing and verification
- Role-based access control (RBAC)
- Permission checking decorators
"""

from datetime import datetime, timedelta
from typing import Optional, List, Union
from enum import Enum

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings
from app.core.cache import get_cache_service


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token security
security_scheme = HTTPBearer()


class UserRole(str, Enum):
    """
    User roles for RBAC.

    Hierarchy (highest to lowest):
    1. SYSTEM_ADMIN - Full system access
    2. BUSINESS_ADMIN - Business owner/administrator
    3. BOOKKEEPER - Accounting staff
    4. ONBOARDING_AGENT - Onboarding portal staff
    5. SUPPORT_AGENT - Support portal staff
    """
    SYSTEM_ADMIN = "system_admin"
    BUSINESS_ADMIN = "business_admin"
    BOOKKEEPER = "bookkeeper"
    ONBOARDING_AGENT = "onboarding_agent"
    SUPPORT_AGENT = "support_agent"


class Permission(str, Enum):
    """
    System permissions for fine-grained access control.
    """
    # Business Management
    BUSINESS_CREATE = "business:create"
    BUSINESS_READ = "business:read"
    BUSINESS_UPDATE = "business:update"
    BUSINESS_DELETE = "business:delete"

    # User Management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Transaction Management
    TRANSACTION_CREATE = "transaction:create"
    TRANSACTION_READ = "transaction:read"
    TRANSACTION_UPDATE = "transaction:update"
    TRANSACTION_DELETE = "transaction:delete"

    # Report Access
    REPORT_VIEW = "report:view"
    REPORT_EXPORT = "report:export"

    # Audit Logs
    AUDIT_VIEW = "audit:view"

    # System Administration
    SYSTEM_CONFIG = "system:config"


# Role-Permission Mapping
ROLE_PERMISSIONS: dict[UserRole, List[Permission]] = {
    UserRole.SYSTEM_ADMIN: [p for p in Permission],  # All permissions
    UserRole.BUSINESS_ADMIN: [
        Permission.BUSINESS_READ,
        Permission.BUSINESS_UPDATE,
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.TRANSACTION_CREATE,
        Permission.TRANSACTION_READ,
        Permission.TRANSACTION_UPDATE,
        Permission.TRANSACTION_DELETE,
        Permission.REPORT_VIEW,
        Permission.REPORT_EXPORT,
    ],
    UserRole.BOOKKEEPER: [
        Permission.BUSINESS_READ,
        Permission.TRANSACTION_CREATE,
        Permission.TRANSACTION_READ,
        Permission.TRANSACTION_UPDATE,
        Permission.REPORT_VIEW,
    ],
    UserRole.ONBOARDING_AGENT: [
        Permission.BUSINESS_CREATE,
        Permission.BUSINESS_READ,
        Permission.BUSINESS_UPDATE,
        Permission.USER_CREATE,
        Permission.USER_READ,
    ],
    UserRole.SUPPORT_AGENT: [
        Permission.BUSINESS_READ,
        Permission.USER_READ,
        Permission.TRANSACTION_READ,
        Permission.AUDIT_VIEW,
    ],
}


class PasswordService:
    """Service for password hashing and verification."""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password

        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)


class TokenService:
    """Service for JWT token creation and validation."""

    def __init__(self):
        """Initialize token service with settings."""
        self.settings = get_settings()

    def create_access_token(
        self,
        subject: str,
        user_id: str,
        role: str,
        business_id: Optional[str] = None,
        additional_claims: Optional[dict] = None
    ) -> str:
        """
        Create a JWT access token.

        Args:
            subject: Token subject (usually user email)
            user_id: User ID
            role: User role
            business_id: Optional business ID for tenant isolation
            additional_claims: Optional additional claims to include

        Returns:
            Encoded JWT token
        """
        expire = datetime.utcnow() + timedelta(
            minutes=self.settings.jwt_access_token_expire_minutes
        )

        claims = {
            "sub": subject,
            "user_id": user_id,
            "role": role,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }

        if business_id:
            claims["business_id"] = business_id

        if additional_claims:
            claims.update(additional_claims)

        return jwt.encode(
            claims,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm
        )

    def create_refresh_token(self, subject: str, user_id: str) -> str:
        """
        Create a JWT refresh token.

        Args:
            subject: Token subject (usually user email)
            user_id: User ID

        Returns:
            Encoded JWT refresh token
        """
        expire = datetime.utcnow() + timedelta(
            days=self.settings.jwt_refresh_token_expire_days
        )

        claims = {
            "sub": subject,
            "user_id": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }

        return jwt.encode(
            claims,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm
        )

    def decode_token(self, token: str) -> dict:
        """
        Decode and validate a JWT token.

        Args:
            token: JWT token to decode

        Returns:
            Token payload

        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm]
            )
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )


class AuthorizationService:
    """Service for role and permission checking."""

    @staticmethod
    def has_permission(user_role: UserRole, permission: Permission) -> bool:
        """
        Check if a role has a specific permission.

        Args:
            user_role: User's role
            permission: Permission to check

        Returns:
            True if role has permission, False otherwise
        """
        role_perms = ROLE_PERMISSIONS.get(user_role, [])
        return permission in role_perms

    @staticmethod
    def has_any_permission(
        user_role: UserRole,
        permissions: List[Permission]
    ) -> bool:
        """
        Check if a role has any of the specified permissions.

        Args:
            user_role: User's role
            permissions: List of permissions to check

        Returns:
            True if role has any permission, False otherwise
        """
        return any(
            AuthorizationService.has_permission(user_role, perm)
            for perm in permissions
        )

    @staticmethod
    def has_all_permissions(
        user_role: UserRole,
        permissions: List[Permission]
    ) -> bool:
        """
        Check if a role has all of the specified permissions.

        Args:
            user_role: User's role
            permissions: List of permissions to check

        Returns:
            True if role has all permissions, False otherwise
        """
        return all(
            AuthorizationService.has_permission(user_role, perm)
            for perm in permissions
        )

    @staticmethod
    def get_user_permissions(user_role: UserRole) -> List[Permission]:
        """
        Get all permissions for a role.

        Args:
            user_role: User's role

        Returns:
            List of permissions
        """
        return ROLE_PERMISSIONS.get(user_role, [])


# Global service instances
def get_password_service() -> PasswordService:
    """Get password service instance."""
    return PasswordService()


def get_token_service() -> TokenService:
    """Get token service instance."""
    return TokenService()


def get_authorization_service() -> AuthorizationService:
    """Get authorization service instance."""
    return AuthorizationService()


# Utility functions
def hash_password(password: str) -> str:
    """Hash a password."""
    return get_password_service().hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password."""
    return get_password_service().verify_password(plain_password, hashed_password)


def create_access_token(
    subject: str,
    user_id: str,
    role: str,
    business_id: Optional[str] = None,
    additional_claims: Optional[dict] = None
) -> str:
    """Create an access token."""
    return get_token_service().create_access_token(
        subject=subject,
        user_id=user_id,
        role=role,
        business_id=business_id,
        additional_claims=additional_claims
    )


def decode_token(token: str) -> dict:
    """Decode a JWT token."""
    return get_token_service().decode_token(token)


def has_permission(user_role: UserRole, permission: Permission) -> bool:
    """Check if role has permission."""
    return get_authorization_service().has_permission(user_role, permission)
