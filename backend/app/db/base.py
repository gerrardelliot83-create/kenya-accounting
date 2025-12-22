"""
SQLAlchemy Base Model

Provides base model class with common fields and utilities.
All database models should inherit from Base.
"""

from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import DeclarativeBase


class BaseModel(DeclarativeBase):
    """
    Base model class with common fields.

    All models inherit:
    - id: UUID primary key
    - created_at: Timestamp of creation
    - updated_at: Timestamp of last update

    Also provides:
    - Automatic table name generation from class name
    - Dictionary conversion method
    """

    # Don't create a table for the base model
    __abstract__ = True

    # Common columns for all models
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    @declared_attr
    def __tablename__(cls) -> str:
        """
        Generate table name from class name.

        Converts CamelCase to snake_case and pluralizes.
        Examples:
            User -> users
            Business -> businesses
            AuditLog -> audit_logs
        """
        import re

        # Convert CamelCase to snake_case
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

        # Simple pluralization (add 's' or 'es')
        if name.endswith('s') or name.endswith('sh') or name.endswith('ch'):
            return f"{name}es"
        elif name.endswith('y') and len(name) > 1 and name[-2] not in 'aeiou':
            return f"{name[:-1]}ies"
        else:
            return f"{name}s"

    def to_dict(self, exclude: list = None) -> dict:
        """
        Convert model instance to dictionary.

        Args:
            exclude: List of field names to exclude

        Returns:
            Dictionary representation of model
        """
        exclude = exclude or []
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
            if c.name not in exclude
        }

    def __repr__(self) -> str:
        """String representation of model."""
        return f"<{self.__class__.__name__}(id={self.id})>"


# Export Base for use in models
Base = BaseModel
