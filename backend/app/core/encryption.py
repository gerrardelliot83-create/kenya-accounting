"""
AES-256-GCM Encryption Service

Provides encryption and decryption for sensitive data fields.
Uses AES-256 in GCM (Galois/Counter Mode) for authenticated encryption.

MANDATORY ENCRYPTED FIELDS:
- kra_pin
- bank_account_number
- tax_certificate_number
- phone
- email
- national_id
- transaction_reference
- account_details

Security Notes:
- GCM mode provides both confidentiality and authenticity
- Each encryption uses a unique nonce to prevent replay attacks
- The encryption key must be kept secure and rotated periodically
- Never log decrypted sensitive data
"""

import base64
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

from app.config import get_settings


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data using AES-256-GCM.

    Attributes:
        _key: The encryption key derived from settings
        _aesgcm: AESGCM cipher instance
    """

    def __init__(self):
        """
        Initialize the encryption service with the configured key.

        Raises:
            ValueError: If encryption key is not properly configured
        """
        settings = get_settings()

        # Decode the base64url-encoded key from settings
        try:
            key_bytes = base64.urlsafe_b64decode(
                settings.encryption_key + "=" * (4 - len(settings.encryption_key) % 4)
            )
        except Exception as e:
            raise ValueError(f"Invalid encryption key format: {e}")

        # Ensure we have a 32-byte key for AES-256
        if len(key_bytes) < 32:
            # Pad the key if necessary (not recommended for production)
            key_bytes = key_bytes.ljust(32, b'\0')
        else:
            key_bytes = key_bytes[:32]

        self._key = key_bytes
        self._aesgcm = AESGCM(self._key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext using AES-256-GCM.

        The output format is: base64(nonce + ciphertext + tag)
        - Nonce: 12 bytes (96 bits) - randomly generated for each encryption
        - Ciphertext: variable length
        - Tag: 16 bytes (128 bits) - authentication tag

        Args:
            plaintext: The string to encrypt

        Returns:
            Base64-encoded encrypted data (nonce + ciphertext + tag)

        Raises:
            ValueError: If plaintext is None or empty
            Exception: If encryption fails
        """
        if not plaintext:
            raise ValueError("Cannot encrypt empty or None value")

        try:
            # Convert plaintext to bytes
            plaintext_bytes = plaintext.encode('utf-8')

            # Generate a random 12-byte nonce (96 bits)
            # Each encryption MUST use a unique nonce
            nonce = os.urandom(12)

            # Encrypt and authenticate
            # GCM mode returns ciphertext with authentication tag appended
            ciphertext_with_tag = self._aesgcm.encrypt(
                nonce,
                plaintext_bytes,
                None  # No associated data
            )

            # Combine nonce + ciphertext_with_tag for storage
            encrypted_data = nonce + ciphertext_with_tag

            # Encode as base64 for safe storage in database
            return base64.b64encode(encrypted_data).decode('utf-8')

        except Exception as e:
            # Log error without exposing sensitive data
            raise Exception(f"Encryption failed: {type(e).__name__}")

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext encrypted with AES-256-GCM.

        Args:
            ciphertext: Base64-encoded encrypted data (nonce + ciphertext + tag)

        Returns:
            Decrypted plaintext string

        Raises:
            ValueError: If ciphertext is None, empty, or invalid format
            InvalidTag: If authentication fails (data tampered or corrupted)
            Exception: If decryption fails
        """
        if not ciphertext:
            raise ValueError("Cannot decrypt empty or None value")

        try:
            # Decode from base64
            encrypted_data = base64.b64decode(ciphertext)

            # Validate minimum length (12 bytes nonce + 16 bytes tag + at least 1 byte data)
            if len(encrypted_data) < 29:
                raise ValueError("Invalid ciphertext: too short")

            # Extract nonce (first 12 bytes)
            nonce = encrypted_data[:12]

            # Extract ciphertext with tag (remaining bytes)
            ciphertext_with_tag = encrypted_data[12:]

            # Decrypt and verify authentication tag
            plaintext_bytes = self._aesgcm.decrypt(
                nonce,
                ciphertext_with_tag,
                None  # No associated data
            )

            # Convert bytes to string
            return plaintext_bytes.decode('utf-8')

        except InvalidTag:
            # Authentication failed - data was tampered with or corrupted
            raise ValueError("Decryption failed: data integrity check failed")
        except Exception as e:
            # Log error without exposing sensitive data
            raise Exception(f"Decryption failed: {type(e).__name__}")

    def encrypt_optional(self, plaintext: Optional[str]) -> Optional[str]:
        """
        Encrypt plaintext, returning None if input is None.

        Convenience method for encrypting optional fields.

        Args:
            plaintext: The string to encrypt, or None

        Returns:
            Base64-encoded encrypted data, or None if input was None
        """
        if plaintext is None:
            return None
        return self.encrypt(plaintext)

    def decrypt_optional(self, ciphertext: Optional[str]) -> Optional[str]:
        """
        Decrypt ciphertext, returning None if input is None.

        Convenience method for decrypting optional fields.

        Args:
            ciphertext: Base64-encoded encrypted data, or None

        Returns:
            Decrypted plaintext string, or None if input was None
        """
        if ciphertext is None:
            return None
        return self.decrypt(ciphertext)


# Global encryption service instance
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """
    Get the global encryption service instance.

    Uses singleton pattern to ensure only one instance exists.

    Returns:
        EncryptionService: The global encryption service instance
    """
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


# Convenience functions for direct use
def encrypt(plaintext: str) -> str:
    """Encrypt plaintext using the global encryption service."""
    return get_encryption_service().encrypt(plaintext)


def decrypt(ciphertext: str) -> str:
    """Decrypt ciphertext using the global encryption service."""
    return get_encryption_service().decrypt(ciphertext)


def encrypt_optional(plaintext: Optional[str]) -> Optional[str]:
    """Encrypt optional plaintext using the global encryption service."""
    return get_encryption_service().encrypt_optional(plaintext)


def decrypt_optional(ciphertext: Optional[str]) -> Optional[str]:
    """Decrypt optional ciphertext using the global encryption service."""
    return get_encryption_service().decrypt_optional(ciphertext)
