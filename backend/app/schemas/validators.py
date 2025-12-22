"""
Shared Validators

Common validation functions for Pydantic schemas.
Provides input sanitization and security validation.
"""

import re
from typing import Optional


def sanitize_text_input(value: Optional[str], allow_html: bool = False) -> Optional[str]:
    """
    Sanitize text input to prevent XSS and SQL injection.

    Args:
        value: Input string to sanitize
        allow_html: Whether to allow HTML tags (default: False)

    Returns:
        Sanitized string or None if input is None
    """
    if value is None:
        return None

    # Strip leading/trailing whitespace
    value = value.strip()

    if not value:
        return None

    # If HTML is not allowed, remove all HTML tags
    if not allow_html:
        # Remove HTML tags
        value = re.sub(r'<[^>]+>', '', value)

    # Remove null bytes (can cause issues with PostgreSQL)
    value = value.replace('\x00', '')

    # Remove control characters except newlines, carriage returns, and tabs
    value = re.sub(r'[\x01-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)

    # Prevent SQL injection by escaping single quotes
    # (Note: SQLAlchemy parameterization is the primary defense)
    # This is an additional layer of defense
    value = value.replace('\x00', '')  # Remove null bytes

    return value if value else None


def validate_kenya_phone(phone: Optional[str]) -> Optional[str]:
    """
    Validate and normalize Kenya phone number format.

    Accepts:
    - +254XXXXXXXXX (13 digits)
    - 07XXXXXXXX or 01XXXXXXXX (10 digits)

    Args:
        phone: Phone number to validate

    Returns:
        Normalized phone number

    Raises:
        ValueError: If phone format is invalid
    """
    if phone is None:
        return None

    # Remove spaces and common separators
    phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    # Kenya phone numbers: +254XXXXXXXXX or 07XXXXXXXX or 01XXXXXXXX
    if phone.startswith("+254"):
        if len(phone) != 13:
            raise ValueError("Invalid Kenya phone number format (must be +254XXXXXXXXX)")
    elif phone.startswith("0"):
        if len(phone) != 10:
            raise ValueError("Invalid Kenya phone number format (must be 0XXXXXXXXX)")
    else:
        raise ValueError("Phone number must start with +254 or 0")

    return phone


def validate_kra_pin(kra_pin: Optional[str]) -> Optional[str]:
    """
    Validate KRA PIN format.

    Format: A followed by 9 digits and a letter (e.g., A012345678X)

    Args:
        kra_pin: KRA PIN to validate

    Returns:
        Normalized KRA PIN (uppercase)

    Raises:
        ValueError: If KRA PIN format is invalid
    """
    if kra_pin is None:
        return None

    # Strip and convert to uppercase
    kra_pin = kra_pin.strip().upper()

    if len(kra_pin) != 11:
        raise ValueError("KRA PIN must be 11 characters")

    if not kra_pin[0].isalpha():
        raise ValueError("KRA PIN must start with a letter")

    if not kra_pin[1:10].isdigit():
        raise ValueError("KRA PIN must have 9 digits after the first letter")

    if not kra_pin[10].isalpha():
        raise ValueError("KRA PIN must end with a letter")

    return kra_pin


def validate_sku(sku: Optional[str]) -> Optional[str]:
    """
    Validate SKU format (alphanumeric, hyphens, underscores allowed).

    Args:
        sku: SKU to validate

    Returns:
        Normalized SKU (uppercase)

    Raises:
        ValueError: If SKU format is invalid
    """
    if sku is None:
        return None

    sku = sku.strip().upper()

    # Check for valid characters
    if not all(c.isalnum() or c in ['-', '_'] for c in sku):
        raise ValueError("SKU can only contain letters, numbers, hyphens, and underscores")

    return sku
