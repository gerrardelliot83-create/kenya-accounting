"""Initial schema with users, businesses, and audit_logs

Revision ID: 001_initial
Revises:
Create Date: 2025-12-06 00:00:00.000000

SECURITY NOTES:
- All tables have RLS (Row Level Security) enabled
- Encrypted fields use TEXT type to store base64-encoded data
- UUID extension must be enabled
- Proper indexes for query performance
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade database schema.

    Creates:
    1. PostgreSQL extensions (uuid-ossp)
    2. Custom enum types
    3. Core tables (businesses, users, audit_logs)
    4. Indexes for performance
    5. Row Level Security policies
    """

    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    # Create enum types
    op.execute("""
        CREATE TYPE user_role AS ENUM (
            'system_admin',
            'business_admin',
            'bookkeeper',
            'onboarding_agent',
            'support_agent'
        );
    """)

    # ========================================
    # Create businesses table
    # ========================================
    op.create_table(
        'businesses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),

        # Encrypted sensitive fields
        sa.Column('kra_pin_encrypted', sa.Text(), nullable=True),
        sa.Column('bank_account_encrypted', sa.Text(), nullable=True),
        sa.Column('tax_certificate_encrypted', sa.Text(), nullable=True),

        # Tax registration
        sa.Column('vat_registered', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('tot_registered', sa.Boolean(), nullable=False, server_default='false'),

        # Address
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=False, server_default='Kenya'),
        sa.Column('postal_code', sa.String(length=20), nullable=True),

        # Contact
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),

        # Business details
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('business_type', sa.String(length=50), nullable=True),

        # Onboarding
        sa.Column('onboarding_status', sa.String(length=50), nullable=False,
                  server_default='pending'),
        sa.Column('onboarding_completed_at', sa.String(), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        # Subscription
        sa.Column('subscription_tier', sa.String(length=50), nullable=False,
                  server_default='basic'),
        sa.Column('subscription_expires_at', sa.String(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),

        # Constraints
        sa.UniqueConstraint('kra_pin_encrypted', name='uq_businesses_kra_pin'),
    )

    # Indexes for businesses
    op.create_index('ix_businesses_id', 'businesses', ['id'])
    op.create_index('ix_businesses_name', 'businesses', ['name'])
    op.create_index('ix_businesses_kra_pin_encrypted', 'businesses', ['kra_pin_encrypted'])
    op.create_index('ix_businesses_is_active', 'businesses', ['is_active'])
    op.create_index('ix_businesses_onboarding_status', 'businesses', ['onboarding_status'])
    op.create_index('ix_businesses_created_at', 'businesses', ['created_at'])
    op.create_index('ix_businesses_onboarding_status_active', 'businesses',
                    ['onboarding_status', 'is_active'])
    op.create_index('ix_businesses_subscription', 'businesses',
                    ['subscription_tier', 'is_active'])

    # ========================================
    # Create users table
    # ========================================
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()'), nullable=False),

        # Encrypted personal information
        sa.Column('email_encrypted', sa.String(), nullable=False),
        sa.Column('phone_encrypted', sa.String(), nullable=True),
        sa.Column('national_id_encrypted', sa.String(), nullable=True),

        # User profile
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),

        # Role
        sa.Column('role', postgresql.ENUM('system_admin', 'business_admin', 'bookkeeper',
                  'onboarding_agent', 'support_agent', name='user_role'),
                  nullable=False, server_default='business_admin'),

        # Business association
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('must_change_password', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_login_at', sa.String(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),

        # Foreign keys
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'],
                                name='fk_users_business_id', ondelete='SET NULL'),

        # Constraints
        sa.UniqueConstraint('email_encrypted', name='uq_users_email'),
    )

    # Indexes for users
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email_encrypted', 'users', ['email_encrypted'])
    op.create_index('ix_users_role', 'users', ['role'])
    op.create_index('ix_users_business_id', 'users', ['business_id'])
    op.create_index('ix_users_is_active', 'users', ['is_active'])
    op.create_index('ix_users_created_at', 'users', ['created_at'])
    op.create_index('ix_users_business_role', 'users', ['business_id', 'role'])
    op.create_index('ix_users_active_role', 'users', ['is_active', 'role'])

    # ========================================
    # Create audit_logs table
    # ========================================
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()'), nullable=False),

        # User and action
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),

        # Resource
        sa.Column('resource_type', sa.String(length=100), nullable=True),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Outcome
        sa.Column('status', sa.String(length=20), nullable=False, server_default='success'),

        # Details
        sa.Column('details', postgresql.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),

        # Request context
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),

        # Data changes
        sa.Column('old_values', postgresql.JSON(), nullable=True),
        sa.Column('new_values', postgresql.JSON(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),

        # Foreign keys
        sa.ForeignKeyConstraint(['user_id'], ['users.id'],
                                name='fk_audit_logs_user_id', ondelete='SET NULL'),
    )

    # Indexes for audit_logs
    op.create_index('ix_audit_logs_id', 'audit_logs', ['id'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'])
    op.create_index('ix_audit_logs_resource_id', 'audit_logs', ['resource_id'])
    op.create_index('ix_audit_logs_status', 'audit_logs', ['status'])
    op.create_index('ix_audit_logs_ip_address', 'audit_logs', ['ip_address'])
    op.create_index('ix_audit_logs_session_id', 'audit_logs', ['session_id'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('ix_audit_logs_user_action', 'audit_logs', ['user_id', 'action'])
    op.create_index('ix_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('ix_audit_logs_status_action', 'audit_logs', ['status', 'action'])
    op.create_index('ix_audit_logs_ip_created', 'audit_logs', ['ip_address', 'created_at'])

    # ========================================
    # Enable Row Level Security
    # ========================================

    # Enable RLS on all tables
    op.execute('ALTER TABLE businesses ENABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE users ENABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;')

    # RLS Policies for businesses table
    op.execute("""
        CREATE POLICY businesses_select_policy ON businesses
        FOR SELECT
        USING (
            -- System admins can see all businesses
            EXISTS (
                SELECT 1 FROM users
                WHERE users.id = current_setting('app.current_user_id', true)::uuid
                AND users.role = 'system_admin'
                AND users.is_active = true
            )
            OR
            -- Business admins and bookkeepers can see their own business
            EXISTS (
                SELECT 1 FROM users
                WHERE users.id = current_setting('app.current_user_id', true)::uuid
                AND users.business_id = businesses.id
                AND users.role IN ('business_admin', 'bookkeeper')
                AND users.is_active = true
            )
            OR
            -- Onboarding and support agents can see all businesses
            EXISTS (
                SELECT 1 FROM users
                WHERE users.id = current_setting('app.current_user_id', true)::uuid
                AND users.role IN ('onboarding_agent', 'support_agent')
                AND users.is_active = true
            )
        );
    """)

    # RLS Policies for users table
    op.execute("""
        CREATE POLICY users_select_policy ON users
        FOR SELECT
        USING (
            -- Users can see their own data
            id = current_setting('app.current_user_id', true)::uuid
            OR
            -- System admins can see all users
            EXISTS (
                SELECT 1 FROM users u
                WHERE u.id = current_setting('app.current_user_id', true)::uuid
                AND u.role = 'system_admin'
                AND u.is_active = true
            )
            OR
            -- Business admins can see users in their business
            EXISTS (
                SELECT 1 FROM users u
                WHERE u.id = current_setting('app.current_user_id', true)::uuid
                AND u.role = 'business_admin'
                AND u.business_id = users.business_id
                AND u.is_active = true
            )
            OR
            -- Support agents can see all users
            EXISTS (
                SELECT 1 FROM users u
                WHERE u.id = current_setting('app.current_user_id', true)::uuid
                AND u.role = 'support_agent'
                AND u.is_active = true
            )
        );
    """)

    # RLS Policies for audit_logs table (read-only for admins)
    op.execute("""
        CREATE POLICY audit_logs_select_policy ON audit_logs
        FOR SELECT
        USING (
            -- System admins can see all audit logs
            EXISTS (
                SELECT 1 FROM users
                WHERE users.id = current_setting('app.current_user_id', true)::uuid
                AND users.role = 'system_admin'
                AND users.is_active = true
            )
            OR
            -- Support agents can see all audit logs
            EXISTS (
                SELECT 1 FROM users
                WHERE users.id = current_setting('app.current_user_id', true)::uuid
                AND users.role = 'support_agent'
                AND users.is_active = true
            )
        );
    """)

    # Create updated_at trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    # Add updated_at triggers to all tables
    op.execute("""
        CREATE TRIGGER update_businesses_updated_at
        BEFORE UPDATE ON businesses
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)

    op.execute("""
        CREATE TRIGGER update_users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)

    op.execute("""
        CREATE TRIGGER update_audit_logs_updated_at
        BEFORE UPDATE ON audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Downgrade database schema."""

    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS update_audit_logs_updated_at ON audit_logs;')
    op.execute('DROP TRIGGER IF EXISTS update_users_updated_at ON users;')
    op.execute('DROP TRIGGER IF EXISTS update_businesses_updated_at ON businesses;')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column();')

    # Drop RLS policies
    op.execute('DROP POLICY IF EXISTS audit_logs_select_policy ON audit_logs;')
    op.execute('DROP POLICY IF EXISTS users_select_policy ON users;')
    op.execute('DROP POLICY IF EXISTS businesses_select_policy ON businesses;')

    # Drop tables
    op.drop_table('audit_logs')
    op.drop_table('users')
    op.drop_table('businesses')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS user_role;')
