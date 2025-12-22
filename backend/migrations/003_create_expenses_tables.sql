-- Migration: Create expenses and expense_categories tables
-- Sprint 3: Expenses API
-- Created: 2025-12-07
-- Description: Creates tables for expense tracking and categorization

-- ============================================================================
-- Table: expense_categories
-- Description: Stores expense categories (system and custom)
-- ============================================================================

CREATE TABLE IF NOT EXISTS expense_categories (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Business association (NULL for system categories)
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,

    -- Category details
    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- Category type
    is_system BOOLEAN NOT NULL DEFAULT FALSE,

    -- Soft delete
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Audit timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT expense_categories_name_business_unique UNIQUE (business_id, name)
);

-- Indexes for expense_categories
CREATE INDEX IF NOT EXISTS ix_expense_categories_id ON expense_categories(id);
CREATE INDEX IF NOT EXISTS ix_expense_categories_business ON expense_categories(business_id, is_active);
CREATE INDEX IF NOT EXISTS ix_expense_categories_system ON expense_categories(is_system, is_active);
CREATE INDEX IF NOT EXISTS ix_expense_categories_name ON expense_categories(name);
CREATE INDEX IF NOT EXISTS ix_expense_categories_created_at ON expense_categories(created_at);

-- Comments for expense_categories
COMMENT ON TABLE expense_categories IS 'Expense categories for business expense tracking (system and custom)';
COMMENT ON COLUMN expense_categories.id IS 'Unique identifier';
COMMENT ON COLUMN expense_categories.business_id IS 'Associated business (NULL for system categories)';
COMMENT ON COLUMN expense_categories.name IS 'Category name';
COMMENT ON COLUMN expense_categories.description IS 'Category description';
COMMENT ON COLUMN expense_categories.is_system IS 'Whether this is a system-defined category (cannot be deleted)';
COMMENT ON COLUMN expense_categories.is_active IS 'Soft delete flag';


-- ============================================================================
-- Table: expenses
-- Description: Stores business expenses with comprehensive tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS expenses (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Business association
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,

    -- Categorization
    category VARCHAR(100) NOT NULL,

    -- Description
    description TEXT NOT NULL,

    -- Financial amounts
    amount DECIMAL(15, 2) NOT NULL CHECK (amount > 0),
    tax_amount DECIMAL(15, 2) NOT NULL DEFAULT 0.00 CHECK (tax_amount >= 0),

    -- Date tracking
    expense_date DATE NOT NULL,

    -- Vendor information
    vendor_name VARCHAR(200),

    -- Receipt/document tracking
    receipt_url VARCHAR(500),

    -- Payment details
    payment_method VARCHAR(50) NOT NULL,
    reference_number VARCHAR(100),

    -- Reconciliation tracking
    is_reconciled BOOLEAN NOT NULL DEFAULT FALSE,

    -- Additional notes
    notes TEXT,

    -- Soft delete
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Audit timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for expenses (optimized for common queries)
CREATE INDEX IF NOT EXISTS ix_expenses_id ON expenses(id);
CREATE INDEX IF NOT EXISTS ix_expenses_business_id ON expenses(business_id);
CREATE INDEX IF NOT EXISTS ix_expenses_category ON expenses(category);
CREATE INDEX IF NOT EXISTS ix_expenses_expense_date ON expenses(expense_date);
CREATE INDEX IF NOT EXISTS ix_expenses_vendor_name ON expenses(vendor_name);
CREATE INDEX IF NOT EXISTS ix_expenses_payment_method ON expenses(payment_method);
CREATE INDEX IF NOT EXISTS ix_expenses_is_reconciled ON expenses(is_reconciled);
CREATE INDEX IF NOT EXISTS ix_expenses_is_active ON expenses(is_active);
CREATE INDEX IF NOT EXISTS ix_expenses_created_at ON expenses(created_at);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS ix_expenses_business_date ON expenses(business_id, expense_date);
CREATE INDEX IF NOT EXISTS ix_expenses_business_category ON expenses(business_id, category);
CREATE INDEX IF NOT EXISTS ix_expenses_business_vendor ON expenses(business_id, vendor_name);
CREATE INDEX IF NOT EXISTS ix_expenses_business_reconciled ON expenses(business_id, is_reconciled);
CREATE INDEX IF NOT EXISTS ix_expenses_business_active ON expenses(business_id, is_active);
CREATE INDEX IF NOT EXISTS ix_expenses_date_range ON expenses(business_id, expense_date, category);

-- Comments for expenses
COMMENT ON TABLE expenses IS 'Business expenses with comprehensive tracking for Kenya SMB accounting';
COMMENT ON COLUMN expenses.id IS 'Unique identifier';
COMMENT ON COLUMN expenses.business_id IS 'Associated business';
COMMENT ON COLUMN expenses.category IS 'Expense category (e.g., office_supplies, travel, utilities)';
COMMENT ON COLUMN expenses.description IS 'Expense description';
COMMENT ON COLUMN expenses.amount IS 'Expense amount (must be positive)';
COMMENT ON COLUMN expenses.tax_amount IS 'Tax amount (VAT/TOT)';
COMMENT ON COLUMN expenses.expense_date IS 'Date expense was incurred';
COMMENT ON COLUMN expenses.vendor_name IS 'Vendor/supplier name';
COMMENT ON COLUMN expenses.receipt_url IS 'URL to receipt or invoice document';
COMMENT ON COLUMN expenses.payment_method IS 'Payment method: cash, bank_transfer, mpesa, card, other';
COMMENT ON COLUMN expenses.reference_number IS 'Transaction reference (e.g., M-Pesa code, bank reference)';
COMMENT ON COLUMN expenses.is_reconciled IS 'Whether expense has been reconciled with bank statement';
COMMENT ON COLUMN expenses.notes IS 'Additional notes or comments';
COMMENT ON COLUMN expenses.is_active IS 'Soft delete flag';


-- ============================================================================
-- Insert default Kenya-relevant system expense categories
-- ============================================================================

INSERT INTO expense_categories (business_id, name, description, is_system, is_active) VALUES
    (NULL, 'Office Supplies', 'Stationery, printer supplies, and office materials', TRUE, TRUE),
    (NULL, 'Travel & Transport', 'Business travel, fuel, vehicle maintenance, and transport costs', TRUE, TRUE),
    (NULL, 'Utilities', 'Electricity, water, internet, and phone bills', TRUE, TRUE),
    (NULL, 'Rent', 'Office or shop rent payments', TRUE, TRUE),
    (NULL, 'Salaries & Wages', 'Employee salaries, wages, and contractor payments', TRUE, TRUE),
    (NULL, 'Professional Services', 'Accounting, legal, consulting, and other professional services', TRUE, TRUE),
    (NULL, 'Marketing & Advertising', 'Marketing campaigns, advertising, and promotional materials', TRUE, TRUE),
    (NULL, 'Bank Charges', 'Bank fees, transaction charges, and loan interest', TRUE, TRUE),
    (NULL, 'M-Pesa Charges', 'M-Pesa transaction fees and mobile money charges', TRUE, TRUE),
    (NULL, 'Insurance', 'Business insurance premiums', TRUE, TRUE),
    (NULL, 'Maintenance & Repairs', 'Equipment and facility maintenance and repairs', TRUE, TRUE),
    (NULL, 'Licenses & Permits', 'Business licenses, permits, and regulatory fees', TRUE, TRUE),
    (NULL, 'Training & Development', 'Employee training and professional development', TRUE, TRUE),
    (NULL, 'Other', 'Miscellaneous expenses not covered by other categories', TRUE, TRUE)
ON CONFLICT (business_id, name) DO NOTHING;


-- ============================================================================
-- Trigger: Update updated_at timestamp on expense_categories
-- ============================================================================

CREATE OR REPLACE FUNCTION update_expense_categories_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_expense_categories_updated_at
    BEFORE UPDATE ON expense_categories
    FOR EACH ROW
    EXECUTE FUNCTION update_expense_categories_updated_at();


-- ============================================================================
-- Trigger: Update updated_at timestamp on expenses
-- ============================================================================

CREATE OR REPLACE FUNCTION update_expenses_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_expenses_updated_at
    BEFORE UPDATE ON expenses
    FOR EACH ROW
    EXECUTE FUNCTION update_expenses_updated_at();


-- ============================================================================
-- Row Level Security (RLS) for expense_categories
-- ============================================================================

-- Enable RLS
ALTER TABLE expense_categories ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view system categories and their business categories
CREATE POLICY expense_categories_select_policy ON expense_categories
    FOR SELECT
    USING (
        is_system = TRUE OR
        business_id IN (
            SELECT business_id FROM users WHERE id = auth.uid()
        )
    );

-- Policy: Users can insert custom categories for their business
CREATE POLICY expense_categories_insert_policy ON expense_categories
    FOR INSERT
    WITH CHECK (
        business_id IN (
            SELECT business_id FROM users WHERE id = auth.uid()
        ) AND
        is_system = FALSE
    );

-- Policy: Users can update their business categories (not system categories)
CREATE POLICY expense_categories_update_policy ON expense_categories
    FOR UPDATE
    USING (
        business_id IN (
            SELECT business_id FROM users WHERE id = auth.uid()
        ) AND
        is_system = FALSE
    );

-- Policy: Users can delete their business categories (not system categories)
CREATE POLICY expense_categories_delete_policy ON expense_categories
    FOR DELETE
    USING (
        business_id IN (
            SELECT business_id FROM users WHERE id = auth.uid()
        ) AND
        is_system = FALSE
    );


-- ============================================================================
-- Row Level Security (RLS) for expenses
-- ============================================================================

-- Enable RLS
ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only view expenses for their business
CREATE POLICY expenses_select_policy ON expenses
    FOR SELECT
    USING (
        business_id IN (
            SELECT business_id FROM users WHERE id = auth.uid()
        )
    );

-- Policy: Users can only insert expenses for their business
CREATE POLICY expenses_insert_policy ON expenses
    FOR INSERT
    WITH CHECK (
        business_id IN (
            SELECT business_id FROM users WHERE id = auth.uid()
        )
    );

-- Policy: Users can only update expenses for their business
CREATE POLICY expenses_update_policy ON expenses
    FOR UPDATE
    USING (
        business_id IN (
            SELECT business_id FROM users WHERE id = auth.uid()
        )
    );

-- Policy: Users can only delete expenses for their business
CREATE POLICY expenses_delete_policy ON expenses
    FOR DELETE
    USING (
        business_id IN (
            SELECT business_id FROM users WHERE id = auth.uid()
        )
    );


-- ============================================================================
-- Grant permissions (if needed for service role)
-- ============================================================================

GRANT ALL ON expense_categories TO authenticated;
GRANT ALL ON expenses TO authenticated;


-- ============================================================================
-- Verification queries
-- ============================================================================

-- Verify expense_categories table was created
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'expense_categories') THEN
        RAISE NOTICE 'Table expense_categories created successfully';
    ELSE
        RAISE EXCEPTION 'Failed to create table expense_categories';
    END IF;
END $$;

-- Verify expenses table was created
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'expenses') THEN
        RAISE NOTICE 'Table expenses created successfully';
    ELSE
        RAISE EXCEPTION 'Failed to create table expenses';
    END IF;
END $$;

-- Verify system categories were inserted
DO $$
DECLARE
    category_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO category_count FROM expense_categories WHERE is_system = TRUE;
    IF category_count >= 14 THEN
        RAISE NOTICE 'System expense categories inserted successfully (count: %)', category_count;
    ELSE
        RAISE WARNING 'Expected at least 14 system categories, found %', category_count;
    END IF;
END $$;
