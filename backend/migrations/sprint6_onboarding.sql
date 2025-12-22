-- ============================================================================
-- Sprint 6 Migration: Onboarding Portal API
-- Kenya SMB Accounting MVP
-- Created: 2025-12-09
-- Description: Creates business_applications table for business onboarding workflow
--              with encrypted sensitive fields and comprehensive status tracking
-- ============================================================================

-- ============================================================================
-- PART 1: CREATE ENUMS
-- ============================================================================

-- Onboarding status enum
DO $$ BEGIN
    CREATE TYPE onboarding_status_enum AS ENUM (
        'draft',           -- Application saved but not submitted
        'submitted',       -- Application submitted for review
        'under_review',    -- Agent reviewing the application
        'approved',        -- Application approved and business created
        'rejected',        -- Application rejected
        'info_requested'   -- More information requested from applicant
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

COMMENT ON TYPE onboarding_status_enum IS 'Status of business onboarding application';

-- ============================================================================
-- PART 2: CREATE BUSINESS_APPLICATIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS business_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Business information
    business_name VARCHAR(255) NOT NULL,
    business_type VARCHAR(50),  -- sole_proprietor, partnership, limited_company

    -- Encrypted sensitive information (MANDATORY ENCRYPTION)
    kra_pin_encrypted TEXT,                  -- Encrypted KRA PIN
    phone_encrypted TEXT,                    -- Encrypted business phone
    email_encrypted TEXT,                    -- Encrypted business email
    owner_national_id_encrypted TEXT,        -- Encrypted owner national ID
    owner_phone_encrypted TEXT,              -- Encrypted owner phone
    owner_email_encrypted TEXT,              -- Encrypted owner email

    -- Location information
    county VARCHAR(100),
    sub_county VARCHAR(100),

    -- Owner information
    owner_name VARCHAR(255),

    -- Bank account (encrypted)
    bank_account_encrypted TEXT,             -- Encrypted bank account number

    -- Tax registration status
    vat_registered BOOLEAN DEFAULT FALSE,
    tot_registered BOOLEAN DEFAULT FALSE,

    -- Application status tracking
    status onboarding_status_enum NOT NULL DEFAULT 'draft',
    submitted_at TIMESTAMPTZ,
    reviewed_at TIMESTAMPTZ,

    -- Review tracking
    reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    rejection_reason TEXT,
    info_request_note TEXT,

    -- Agent tracking
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Approved business tracking (after approval)
    approved_business_id UUID REFERENCES businesses(id) ON DELETE SET NULL,

    -- Additional metadata
    notes TEXT,  -- Internal notes for agents

    -- Constraints
    CONSTRAINT business_applications_email_check CHECK (
        email_encrypted IS NULL OR length(email_encrypted) > 0
    ),
    CONSTRAINT business_applications_status_submitted_check CHECK (
        (status = 'draft') OR (submitted_at IS NOT NULL)
    ),
    CONSTRAINT business_applications_status_reviewed_check CHECK (
        (status NOT IN ('approved', 'rejected')) OR (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL)
    ),
    CONSTRAINT business_applications_rejection_reason_check CHECK (
        (status != 'rejected') OR (rejection_reason IS NOT NULL)
    ),
    CONSTRAINT business_applications_info_request_check CHECK (
        (status != 'info_requested') OR (info_request_note IS NOT NULL)
    ),
    CONSTRAINT business_applications_approved_business_check CHECK (
        (status != 'approved') OR (approved_business_id IS NOT NULL)
    )
);

-- Table and column comments
COMMENT ON TABLE business_applications IS 'Business onboarding applications with encrypted sensitive data';
COMMENT ON COLUMN business_applications.business_name IS 'Name of the business applying for onboarding';
COMMENT ON COLUMN business_applications.business_type IS 'Type: sole_proprietor, partnership, limited_company';
COMMENT ON COLUMN business_applications.kra_pin_encrypted IS 'Encrypted KRA PIN (MANDATORY ENCRYPTION)';
COMMENT ON COLUMN business_applications.phone_encrypted IS 'Encrypted business phone (MANDATORY ENCRYPTION)';
COMMENT ON COLUMN business_applications.email_encrypted IS 'Encrypted business email (MANDATORY ENCRYPTION)';
COMMENT ON COLUMN business_applications.owner_national_id_encrypted IS 'Encrypted owner national ID (MANDATORY ENCRYPTION)';
COMMENT ON COLUMN business_applications.owner_phone_encrypted IS 'Encrypted owner phone (MANDATORY ENCRYPTION)';
COMMENT ON COLUMN business_applications.owner_email_encrypted IS 'Encrypted owner email (MANDATORY ENCRYPTION)';
COMMENT ON COLUMN business_applications.bank_account_encrypted IS 'Encrypted bank account number (MANDATORY ENCRYPTION)';
COMMENT ON COLUMN business_applications.county IS 'County where business is located';
COMMENT ON COLUMN business_applications.sub_county IS 'Sub-county where business is located';
COMMENT ON COLUMN business_applications.owner_name IS 'Name of business owner/director';
COMMENT ON COLUMN business_applications.vat_registered IS 'Whether business is VAT registered';
COMMENT ON COLUMN business_applications.tot_registered IS 'Whether business is TOT registered';
COMMENT ON COLUMN business_applications.status IS 'Application status: draft, submitted, under_review, approved, rejected, info_requested';
COMMENT ON COLUMN business_applications.submitted_at IS 'Timestamp when application was submitted';
COMMENT ON COLUMN business_applications.reviewed_at IS 'Timestamp when application was reviewed';
COMMENT ON COLUMN business_applications.reviewed_by IS 'Agent who reviewed the application';
COMMENT ON COLUMN business_applications.rejection_reason IS 'Reason for rejection (required if rejected)';
COMMENT ON COLUMN business_applications.info_request_note IS 'Note requesting additional information';
COMMENT ON COLUMN business_applications.created_by IS 'Onboarding agent who created the application';
COMMENT ON COLUMN business_applications.approved_business_id IS 'Business ID created after approval';
COMMENT ON COLUMN business_applications.notes IS 'Internal notes for onboarding agents';

-- ============================================================================
-- PART 3: CREATE INDEXES
-- ============================================================================

-- Primary and unique indexes
CREATE INDEX IF NOT EXISTS ix_business_applications_id ON business_applications(id);
CREATE INDEX IF NOT EXISTS ix_business_applications_created_at ON business_applications(created_at);

-- Status tracking indexes
CREATE INDEX IF NOT EXISTS ix_business_applications_status ON business_applications(status);
CREATE INDEX IF NOT EXISTS ix_business_applications_submitted_at ON business_applications(submitted_at);
CREATE INDEX IF NOT EXISTS ix_business_applications_reviewed_at ON business_applications(reviewed_at);

-- Agent tracking indexes
CREATE INDEX IF NOT EXISTS ix_business_applications_created_by ON business_applications(created_by);
CREATE INDEX IF NOT EXISTS ix_business_applications_reviewed_by ON business_applications(reviewed_by);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS ix_business_applications_status_submitted ON business_applications(status, submitted_at DESC);
CREATE INDEX IF NOT EXISTS ix_business_applications_status_created ON business_applications(status, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_business_applications_created_by_status ON business_applications(created_by, status);
CREATE INDEX IF NOT EXISTS ix_business_applications_business_name ON business_applications(business_name);

-- Approved business tracking
CREATE INDEX IF NOT EXISTS ix_business_applications_approved_business ON business_applications(approved_business_id);

-- ============================================================================
-- PART 4: ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on business_applications table
ALTER TABLE business_applications ENABLE ROW LEVEL SECURITY;

-- Policy: System admins can see all applications
CREATE POLICY business_applications_system_admin_all
    ON business_applications
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.id = auth.uid()
            AND users.role = 'system_admin'
            AND users.is_active = TRUE
        )
    );

-- Policy: Onboarding agents can see all applications
CREATE POLICY business_applications_onboarding_agent_all
    ON business_applications
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.id = auth.uid()
            AND users.role = 'onboarding_agent'
            AND users.is_active = TRUE
        )
    );

-- Policy: Business admins can see their approved application (read-only)
CREATE POLICY business_applications_business_admin_select
    ON business_applications
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.id = auth.uid()
            AND users.role = 'business_admin'
            AND users.business_id = business_applications.approved_business_id
            AND users.is_active = TRUE
        )
    );

-- ============================================================================
-- PART 5: CREATE AUDIT TRIGGER
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_business_applications_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
DROP TRIGGER IF EXISTS business_applications_updated_at_trigger ON business_applications;
CREATE TRIGGER business_applications_updated_at_trigger
    BEFORE UPDATE ON business_applications
    FOR EACH ROW
    EXECUTE FUNCTION update_business_applications_updated_at();

-- ============================================================================
-- PART 6: GRANT PERMISSIONS
-- ============================================================================

-- Grant permissions to authenticated users
GRANT SELECT, INSERT, UPDATE ON business_applications TO authenticated;

-- Grant usage on sequences (if any)
-- Note: UUID generation uses gen_random_uuid(), no sequences needed

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================

-- Migration verification
DO $$
BEGIN
    RAISE NOTICE 'Sprint 6 Onboarding Migration completed successfully';
    RAISE NOTICE 'Created: business_applications table';
    RAISE NOTICE 'Created: onboarding_status_enum type';
    RAISE NOTICE 'Created: Indexes for performance optimization';
    RAISE NOTICE 'Created: RLS policies for security';
    RAISE NOTICE 'Created: Update trigger for updated_at';
END $$;
