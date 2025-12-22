"""Core module for security, encryption, and caching services."""

from app.core.security import (
    UserRole,
    Permission,
    PasswordService,
    TokenService,
    AuthorizationService,
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    has_permission,
)
from app.core.encryption import (
    EncryptionService,
    get_encryption_service,
    encrypt,
    decrypt,
    encrypt_optional,
    decrypt_optional,
)
from app.core.cache import (
    CacheService,
    get_cache_service,
    cached,
)

__all__ = [
    # Security
    "UserRole",
    "Permission",
    "PasswordService",
    "TokenService",
    "AuthorizationService",
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_token",
    "has_permission",
    # Encryption
    "EncryptionService",
    "get_encryption_service",
    "encrypt",
    "decrypt",
    "encrypt_optional",
    "decrypt_optional",
    # Cache
    "CacheService",
    "get_cache_service",
    "cached",
]
