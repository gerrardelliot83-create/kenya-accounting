"""Add password_hash to users table

Revision ID: 002_add_password_hash
Revises: 001_initial
Create Date: 2025-12-06 12:00:00.000000

SECURITY NOTE:
- Password hashes are stored using bcrypt
- Never log or expose password hashes
- Ensure password complexity requirements on creation
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_password_hash'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add password_hash column to users table."""

    # Add password_hash column
    op.add_column(
        'users',
        sa.Column('password_hash', sa.String(length=255), nullable=True)
    )

    # Note: For existing users, password_hash will be null
    # This should be populated during user creation or password reset


def downgrade() -> None:
    """Remove password_hash column from users table."""

    op.drop_column('users', 'password_hash')
