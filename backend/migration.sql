-- Kenya SMB Accounting MVP - Initial Database Schema
-- Run this SQL in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create user_role enum type
CREATE TYPE user_role AS ENUM (
    'system_admin',
    'business_admin',
    'bookkeeper',
    'onboarding_agent',
    'support_agent'
);

-- Create businesses table
CREATE TABLE businesses (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    name VARCHAR(255) NOT NULL,
    kra_pin_encrypted TEXT,
    bank_account_encrypted TEXT,
    tax_certificate_encrypted TEXT,
    vat_registered BOOLEAN DEFAULT false NOT NULL,
    tot_registered BOOLEAN DEFAULT false NOT NULL,
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100) DEFAULT 'Kenya' NOT NULL,
    postal_code VARCHAR(20),
    phone VARCHAR(20),
    email VARCHAR(255),
    website VARCHAR(255),
    industry VARCHAR(100),
    business_type VARCHAR(50),
    onboarding_status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    onboarding_completed_at VARCHAR,
    is_active BOOLEAN DEFAULT true NOT NULL,
    subscription_tier VARCHAR(50) DEFAULT 'basic' NOT NULL,
    subscription_expires_at VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_businesses_kra_pin UNIQUE (kra_pin_encrypted)
);

-- Indexes for businesses
CREATE INDEX ix_businesses_id ON businesses (id);
CREATE INDEX ix_businesses_name ON businesses (name);
CREATE INDEX ix_businesses_kra_pin_encrypted ON businesses (kra_pin_encrypted);
CREATE INDEX ix_businesses_is_active ON businesses (is_active);
CREATE INDEX ix_businesses_onboarding_status ON businesses (onboarding_status);
CREATE INDEX ix_businesses_created_at ON businesses (created_at);
CREATE INDEX ix_businesses_onboarding_status_active ON businesses (onboarding_status, is_active);
CREATE INDEX ix_businesses_subscription ON businesses (subscription_tier, is_active);

-- Create users table
CREATE TABLE users (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    email_encrypted VARCHAR NOT NULL,
    phone_encrypted VARCHAR,
    national_id_encrypted VARCHAR,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role user_role DEFAULT 'business_admin' NOT NULL,
    business_id UUID,
    is_active BOOLEAN DEFAULT true NOT NULL,
    must_change_password BOOLEAN DEFAULT true NOT NULL,
    last_login_at VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_users_business_id FOREIGN KEY(business_id) REFERENCES businesses (id) ON DELETE SET NULL,
    CONSTRAINT uq_users_email UNIQUE (email_encrypted)
);

-- Indexes for users
CREATE INDEX ix_users_id ON users (id);
CREATE INDEX ix_users_email_encrypted ON users (email_encrypted);
CREATE INDEX ix_users_role ON users (role);
CREATE INDEX ix_users_business_id ON users (business_id);
CREATE INDEX ix_users_is_active ON users (is_active);
CREATE INDEX ix_users_created_at ON users (created_at);
CREATE INDEX ix_users_business_role ON users (business_id, role);
CREATE INDEX ix_users_active_role ON users (is_active, role);

-- Create audit_logs table
CREATE TABLE audit_logs (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    status VARCHAR(20) DEFAULT 'success' NOT NULL,
    details JSON,
    error_message TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    session_id VARCHAR(255),
    old_values JSON,
    new_values JSON,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_audit_logs_user_id FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
);

-- Indexes for audit_logs
CREATE INDEX ix_audit_logs_id ON audit_logs (id);
CREATE INDEX ix_audit_logs_user_id ON audit_logs (user_id);
CREATE INDEX ix_audit_logs_action ON audit_logs (action);
CREATE INDEX ix_audit_logs_resource_type ON audit_logs (resource_type);
CREATE INDEX ix_audit_logs_resource_id ON audit_logs (resource_id);
CREATE INDEX ix_audit_logs_status ON audit_logs (status);
CREATE INDEX ix_audit_logs_ip_address ON audit_logs (ip_address);
CREATE INDEX ix_audit_logs_session_id ON audit_logs (session_id);
CREATE INDEX ix_audit_logs_created_at ON audit_logs (created_at);
CREATE INDEX ix_audit_logs_user_action ON audit_logs (user_id, action);
CREATE INDEX ix_audit_logs_resource ON audit_logs (resource_type, resource_id);
CREATE INDEX ix_audit_logs_status_action ON audit_logs (status, action);
CREATE INDEX ix_audit_logs_ip_created ON audit_logs (ip_address, created_at);

-- Enable Row Level Security on all tables
ALTER TABLE businesses ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policy for businesses
CREATE POLICY businesses_select_policy ON businesses
FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM users
        WHERE users.id = current_setting('app.current_user_id', true)::uuid
        AND users.role = 'system_admin'
        AND users.is_active = true
    )
    OR
    EXISTS (
        SELECT 1 FROM users
        WHERE users.id = current_setting('app.current_user_id', true)::uuid
        AND users.business_id = businesses.id
        AND users.role IN ('business_admin', 'bookkeeper')
        AND users.is_active = true
    )
    OR
    EXISTS (
        SELECT 1 FROM users
        WHERE users.id = current_setting('app.current_user_id', true)::uuid
        AND users.role IN ('onboarding_agent', 'support_agent')
        AND users.is_active = true
    )
);

-- RLS Policy for users
CREATE POLICY users_select_policy ON users
FOR SELECT
USING (
    id = current_setting('app.current_user_id', true)::uuid
    OR
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.id = current_setting('app.current_user_id', true)::uuid
        AND u.role = 'system_admin'
        AND u.is_active = true
    )
    OR
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.id = current_setting('app.current_user_id', true)::uuid
        AND u.role = 'business_admin'
        AND u.business_id = users.business_id
        AND u.is_active = true
    )
    OR
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.id = current_setting('app.current_user_id', true)::uuid
        AND u.role = 'support_agent'
        AND u.is_active = true
    )
);

-- RLS Policy for audit_logs
CREATE POLICY audit_logs_select_policy ON audit_logs
FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM users
        WHERE users.id = current_setting('app.current_user_id', true)::uuid
        AND users.role = 'system_admin'
        AND users.is_active = true
    )
    OR
    EXISTS (
        SELECT 1 FROM users
        WHERE users.id = current_setting('app.current_user_id', true)::uuid
        AND users.role = 'support_agent'
        AND users.is_active = true
    )
);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
CREATE TRIGGER update_businesses_updated_at
BEFORE UPDATE ON businesses
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_audit_logs_updated_at
BEFORE UPDATE ON audit_logs
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Alembic version tracking (optional, for future migrations)
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
INSERT INTO alembic_version (version_num) VALUES ('001_initial');
