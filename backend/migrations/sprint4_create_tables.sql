-- ============================================================================
-- Sprint 4 Migration: Bank Import and Reconciliation
-- Kenya SMB Accounting MVP
-- Created: 2025-12-07
-- Description: Creates bank_imports and bank_transactions tables for
--              bank statement import and automatic reconciliation
-- ============================================================================

-- ============================================================================
-- PART 1: CREATE ENUMS
-- ============================================================================

-- File type enum
DO $$ BEGIN
    CREATE TYPE file_type_enum AS ENUM ('csv', 'pdf');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Import status enum
DO $$ BEGIN
    CREATE TYPE import_status_enum AS ENUM ('pending', 'parsing', 'mapping', 'importing', 'completed', 'failed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Reconciliation status enum
DO $$ BEGIN
    CREATE TYPE reconciliation_status_enum AS ENUM ('unmatched', 'suggested', 'matched', 'ignored');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- PART 2: CREATE BANK_IMPORTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS bank_imports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Business association
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,

    -- File information
    file_name VARCHAR(255) NOT NULL,
    file_type file_type_enum NOT NULL,
    source_bank VARCHAR(100),

    -- Import status and progress
    status import_status_enum NOT NULL DEFAULT 'pending',
    column_mapping JSONB,
    total_rows INTEGER NOT NULL DEFAULT 0,
    imported_rows INTEGER NOT NULL DEFAULT 0,

    -- Error tracking
    error_message TEXT,

    -- Encrypted audit data
    raw_data_encrypted TEXT,

    -- Constraints
    CONSTRAINT bank_imports_total_rows_positive CHECK (total_rows >= 0),
    CONSTRAINT bank_imports_imported_rows_valid CHECK (imported_rows >= 0 AND imported_rows <= total_rows)
);

COMMENT ON TABLE bank_imports IS 'Bank statement imports for transaction reconciliation';
COMMENT ON COLUMN bank_imports.business_id IS 'Associated business';
COMMENT ON COLUMN bank_imports.file_name IS 'Original uploaded filename';
COMMENT ON COLUMN bank_imports.file_type IS 'File format: csv or pdf';
COMMENT ON COLUMN bank_imports.source_bank IS 'Bank name (e.g., Equity, KCB, M-Pesa)';
COMMENT ON COLUMN bank_imports.status IS 'Current import status';
COMMENT ON COLUMN bank_imports.column_mapping IS 'JSON mapping of file columns to our fields';
COMMENT ON COLUMN bank_imports.total_rows IS 'Total number of rows in file';
COMMENT ON COLUMN bank_imports.imported_rows IS 'Number of rows successfully imported';
COMMENT ON COLUMN bank_imports.error_message IS 'Error message if import failed';
COMMENT ON COLUMN bank_imports.raw_data_encrypted IS 'Encrypted raw parsed content for audit trail';

-- Indexes for bank_imports
CREATE INDEX IF NOT EXISTS ix_bank_imports_id ON bank_imports(id);
CREATE INDEX IF NOT EXISTS ix_bank_imports_created_at ON bank_imports(created_at);
CREATE INDEX IF NOT EXISTS ix_bank_imports_business_id ON bank_imports(business_id);
CREATE INDEX IF NOT EXISTS ix_bank_imports_file_type ON bank_imports(file_type);
CREATE INDEX IF NOT EXISTS ix_bank_imports_source_bank ON bank_imports(source_bank);
CREATE INDEX IF NOT EXISTS ix_bank_imports_status ON bank_imports(status);
CREATE INDEX IF NOT EXISTS ix_bank_imports_business_status ON bank_imports(business_id, status);
CREATE INDEX IF NOT EXISTS ix_bank_imports_business_bank ON bank_imports(business_id, source_bank);

-- ============================================================================
-- PART 3: CREATE BANK_TRANSACTIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS bank_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Business and import association
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    bank_import_id UUID NOT NULL REFERENCES bank_imports(id) ON DELETE CASCADE,

    -- Transaction details
    transaction_date DATE NOT NULL,
    description VARCHAR(1000) NOT NULL,  -- Encrypted
    reference VARCHAR(200),  -- Encrypted

    -- Financial amounts
    debit_amount DECIMAL(15, 2),
    credit_amount DECIMAL(15, 2),
    balance DECIMAL(15, 2),

    -- Audit data
    raw_data JSONB,  -- Encrypted

    -- Reconciliation tracking
    reconciliation_status reconciliation_status_enum NOT NULL DEFAULT 'unmatched',
    matched_expense_id UUID REFERENCES expenses(id) ON DELETE SET NULL,
    matched_invoice_id UUID REFERENCES invoices(id) ON DELETE SET NULL,
    match_confidence DECIMAL(5, 2),

    -- Constraints
    CONSTRAINT bank_transactions_amount_check CHECK (
        (debit_amount IS NOT NULL AND debit_amount >= 0) OR
        (credit_amount IS NOT NULL AND credit_amount >= 0)
    ),
    CONSTRAINT bank_transactions_match_check CHECK (
        matched_expense_id IS NULL OR matched_invoice_id IS NULL
    ),
    CONSTRAINT bank_transactions_confidence_check CHECK (
        match_confidence IS NULL OR (match_confidence >= 0 AND match_confidence <= 100)
    )
);

COMMENT ON TABLE bank_transactions IS 'Individual bank transactions from imported statements';
COMMENT ON COLUMN bank_transactions.business_id IS 'Associated business';
COMMENT ON COLUMN bank_transactions.bank_import_id IS 'Parent bank import';
COMMENT ON COLUMN bank_transactions.transaction_date IS 'Date of the transaction';
COMMENT ON COLUMN bank_transactions.description IS 'Transaction description (encrypted)';
COMMENT ON COLUMN bank_transactions.reference IS 'Transaction reference/code (encrypted)';
COMMENT ON COLUMN bank_transactions.debit_amount IS 'Debit/withdrawal amount (money out)';
COMMENT ON COLUMN bank_transactions.credit_amount IS 'Credit/deposit amount (money in)';
COMMENT ON COLUMN bank_transactions.balance IS 'Account balance after transaction';
COMMENT ON COLUMN bank_transactions.raw_data IS 'Original row data from import (encrypted)';
COMMENT ON COLUMN bank_transactions.reconciliation_status IS 'Reconciliation status';
COMMENT ON COLUMN bank_transactions.matched_expense_id IS 'Matched expense (for debits)';
COMMENT ON COLUMN bank_transactions.matched_invoice_id IS 'Matched invoice payment (for credits)';
COMMENT ON COLUMN bank_transactions.match_confidence IS 'Match confidence score (0-100)';

-- Indexes for bank_transactions
CREATE INDEX IF NOT EXISTS ix_bank_transactions_id ON bank_transactions(id);
CREATE INDEX IF NOT EXISTS ix_bank_transactions_created_at ON bank_transactions(created_at);
CREATE INDEX IF NOT EXISTS ix_bank_transactions_business_id ON bank_transactions(business_id);
CREATE INDEX IF NOT EXISTS ix_bank_transactions_bank_import_id ON bank_transactions(bank_import_id);
CREATE INDEX IF NOT EXISTS ix_bank_transactions_transaction_date ON bank_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS ix_bank_transactions_reconciliation_status ON bank_transactions(reconciliation_status);
CREATE INDEX IF NOT EXISTS ix_bank_transactions_matched_expense_id ON bank_transactions(matched_expense_id);
CREATE INDEX IF NOT EXISTS ix_bank_transactions_matched_invoice_id ON bank_transactions(matched_invoice_id);
CREATE INDEX IF NOT EXISTS ix_bank_transactions_business_date ON bank_transactions(business_id, transaction_date);
CREATE INDEX IF NOT EXISTS ix_bank_transactions_business_status ON bank_transactions(business_id, reconciliation_status);
CREATE INDEX IF NOT EXISTS ix_bank_transactions_import_status ON bank_transactions(bank_import_id, reconciliation_status);
CREATE INDEX IF NOT EXISTS ix_bank_transactions_business_unmatched ON bank_transactions(business_id, reconciliation_status, transaction_date);

-- ============================================================================
-- PART 4: TRIGGERS FOR UPDATED_AT
-- ============================================================================

-- Trigger function for bank_imports
CREATE OR REPLACE FUNCTION update_bank_imports_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_bank_imports_updated_at ON bank_imports;
CREATE TRIGGER trigger_update_bank_imports_updated_at
    BEFORE UPDATE ON bank_imports
    FOR EACH ROW
    EXECUTE FUNCTION update_bank_imports_updated_at();

-- Trigger function for bank_transactions
CREATE OR REPLACE FUNCTION update_bank_transactions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_bank_transactions_updated_at ON bank_transactions;
CREATE TRIGGER trigger_update_bank_transactions_updated_at
    BEFORE UPDATE ON bank_transactions
    FOR EACH ROW
    EXECUTE FUNCTION update_bank_transactions_updated_at();

-- ============================================================================
-- PART 5: ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS for bank_imports
ALTER TABLE bank_imports ENABLE ROW LEVEL SECURITY;

-- Bank imports: Users can only access their business's imports
DROP POLICY IF EXISTS bank_imports_business_isolation ON bank_imports;
CREATE POLICY bank_imports_business_isolation ON bank_imports
    FOR ALL USING (
        business_id IN (
            SELECT business_id
            FROM users
            WHERE id = auth.uid()
        )
    );

-- Enable RLS for bank_transactions
ALTER TABLE bank_transactions ENABLE ROW LEVEL SECURITY;

-- Bank transactions: Users can only access their business's transactions
DROP POLICY IF EXISTS bank_transactions_business_isolation ON bank_transactions;
CREATE POLICY bank_transactions_business_isolation ON bank_transactions
    FOR ALL USING (
        business_id IN (
            SELECT business_id
            FROM users
            WHERE id = auth.uid()
        )
    );

-- ============================================================================
-- PART 6: GRANT PERMISSIONS
-- ============================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON bank_imports TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON bank_transactions TO authenticated;

-- ============================================================================
-- PART 7: VERIFICATION
-- ============================================================================

DO $$
BEGIN
    -- Check tables
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'bank_imports') THEN
        RAISE NOTICE 'Table bank_imports created successfully';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'bank_transactions') THEN
        RAISE NOTICE 'Table bank_transactions created successfully';
    END IF;

    -- Check enums
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'file_type_enum') THEN
        RAISE NOTICE 'Enum file_type_enum created successfully';
    END IF;

    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'import_status_enum') THEN
        RAISE NOTICE 'Enum import_status_enum created successfully';
    END IF;

    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'reconciliation_status_enum') THEN
        RAISE NOTICE 'Enum reconciliation_status_enum created successfully';
    END IF;

    -- Check indexes
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_bank_imports_business_status') THEN
        RAISE NOTICE 'Index ix_bank_imports_business_status created successfully';
    END IF;

    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_bank_transactions_business_unmatched') THEN
        RAISE NOTICE 'Index ix_bank_transactions_business_unmatched created successfully';
    END IF;

    -- Check triggers
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_update_bank_imports_updated_at') THEN
        RAISE NOTICE 'Trigger trigger_update_bank_imports_updated_at created successfully';
    END IF;

    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_update_bank_transactions_updated_at') THEN
        RAISE NOTICE 'Trigger trigger_update_bank_transactions_updated_at created successfully';
    END IF;

    -- Check RLS policies
    IF EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'bank_imports_business_isolation') THEN
        RAISE NOTICE 'RLS policy bank_imports_business_isolation created successfully';
    END IF;

    IF EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'bank_transactions_business_isolation') THEN
        RAISE NOTICE 'RLS policy bank_transactions_business_isolation created successfully';
    END IF;
END $$;

SELECT 'Sprint 4 Migration Complete!' as status;

-- ============================================================================
-- MIGRATION NOTES
-- ============================================================================
--
-- This migration creates:
-- 1. Three new enums: file_type_enum, import_status_enum, reconciliation_status_enum
-- 2. bank_imports table for tracking bank statement uploads
-- 3. bank_transactions table for individual transactions from statements
-- 4. Comprehensive indexes for query performance
-- 5. Updated_at triggers for both tables
-- 6. Row Level Security policies for business isolation
-- 7. Proper foreign key constraints and check constraints
--
-- Security Features:
-- - RLS policies ensure users can only access their business's data
-- - Encrypted fields: description, reference, raw_data
-- - Foreign key cascades protect referential integrity
-- - Check constraints validate data quality
--
-- Reconciliation Features:
-- - Transactions can match to expenses (debits) or invoices (credits)
-- - Match confidence scoring (0-100)
-- - Status tracking: unmatched -> suggested -> matched
-- - Supports manual override and unmatch operations
--
-- ============================================================================
