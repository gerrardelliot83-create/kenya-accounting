-- ============================================================================
-- Sprint 3 Migration: Expenses, Payments, and Invoice Updates
-- Kenya SMB Accounting MVP
-- Created: 2025-12-07
-- Description: Creates expenses, expense_categories, payments tables
--              and adds amount_paid tracking to invoices
-- ============================================================================

-- ============================================================================
-- PART 1: EXPENSES AND EXPENSE CATEGORIES
-- ============================================================================

-- Table: expense_categories
CREATE TABLE IF NOT EXISTS expense_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT expense_categories_name_business_unique UNIQUE (business_id, name)
);

-- Indexes for expense_categories
CREATE INDEX IF NOT EXISTS ix_expense_categories_id ON expense_categories(id);
CREATE INDEX IF NOT EXISTS ix_expense_categories_business ON expense_categories(business_id, is_active);
CREATE INDEX IF NOT EXISTS ix_expense_categories_system ON expense_categories(is_system, is_active);
CREATE INDEX IF NOT EXISTS ix_expense_categories_name ON expense_categories(name);

-- Table: expenses
CREATE TABLE IF NOT EXISTS expenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    amount DECIMAL(15, 2) NOT NULL CHECK (amount > 0),
    tax_amount DECIMAL(15, 2) NOT NULL DEFAULT 0.00 CHECK (tax_amount >= 0),
    expense_date DATE NOT NULL,
    vendor_name VARCHAR(200),
    receipt_url VARCHAR(500),
    payment_method VARCHAR(50) NOT NULL,
    reference_number VARCHAR(100),
    is_reconciled BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for expenses
CREATE INDEX IF NOT EXISTS ix_expenses_id ON expenses(id);
CREATE INDEX IF NOT EXISTS ix_expenses_business_id ON expenses(business_id);
CREATE INDEX IF NOT EXISTS ix_expenses_category ON expenses(category);
CREATE INDEX IF NOT EXISTS ix_expenses_expense_date ON expenses(expense_date);
CREATE INDEX IF NOT EXISTS ix_expenses_vendor_name ON expenses(vendor_name);
CREATE INDEX IF NOT EXISTS ix_expenses_payment_method ON expenses(payment_method);
CREATE INDEX IF NOT EXISTS ix_expenses_is_reconciled ON expenses(is_reconciled);
CREATE INDEX IF NOT EXISTS ix_expenses_is_active ON expenses(is_active);
CREATE INDEX IF NOT EXISTS ix_expenses_business_date ON expenses(business_id, expense_date);
CREATE INDEX IF NOT EXISTS ix_expenses_business_category ON expenses(business_id, category);
CREATE INDEX IF NOT EXISTS ix_expenses_business_active ON expenses(business_id, is_active);

-- Insert default Kenya-relevant system expense categories
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
-- PART 2: PAYMENTS AND INVOICE UPDATES
-- ============================================================================

-- Add amount_paid column to invoices table
ALTER TABLE invoices
ADD COLUMN IF NOT EXISTS amount_paid DECIMAL(15, 2) NOT NULL DEFAULT 0.00;

COMMENT ON COLUMN invoices.amount_paid IS 'Total amount paid towards this invoice';

-- Table: payments
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    amount DECIMAL(15, 2) NOT NULL CHECK (amount > 0),
    payment_date DATE NOT NULL,
    payment_method VARCHAR(20) NOT NULL,
    reference_number VARCHAR(100),
    notes TEXT
);

-- Indexes for payments
CREATE INDEX IF NOT EXISTS ix_payments_id ON payments(id);
CREATE INDEX IF NOT EXISTS ix_payments_created_at ON payments(created_at);
CREATE INDEX IF NOT EXISTS ix_payments_business_id ON payments(business_id);
CREATE INDEX IF NOT EXISTS ix_payments_invoice_id ON payments(invoice_id);
CREATE INDEX IF NOT EXISTS ix_payments_payment_method ON payments(payment_method);
CREATE INDEX IF NOT EXISTS ix_payments_business_date ON payments(business_id, payment_date);
CREATE INDEX IF NOT EXISTS ix_payments_invoice_date ON payments(invoice_id, payment_date);

-- ============================================================================
-- PART 3: TRIGGERS FOR UPDATED_AT
-- ============================================================================

-- Trigger for expense_categories
CREATE OR REPLACE FUNCTION update_expense_categories_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_expense_categories_updated_at ON expense_categories;
CREATE TRIGGER trigger_update_expense_categories_updated_at
    BEFORE UPDATE ON expense_categories
    FOR EACH ROW
    EXECUTE FUNCTION update_expense_categories_updated_at();

-- Trigger for expenses
CREATE OR REPLACE FUNCTION update_expenses_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_expenses_updated_at ON expenses;
CREATE TRIGGER trigger_update_expenses_updated_at
    BEFORE UPDATE ON expenses
    FOR EACH ROW
    EXECUTE FUNCTION update_expenses_updated_at();

-- ============================================================================
-- PART 4: ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS for expense_categories
ALTER TABLE expense_categories ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS expense_categories_select_policy ON expense_categories;
CREATE POLICY expense_categories_select_policy ON expense_categories
    FOR SELECT USING (is_system = TRUE OR business_id IN (SELECT business_id FROM users WHERE id = auth.uid()));

DROP POLICY IF EXISTS expense_categories_insert_policy ON expense_categories;
CREATE POLICY expense_categories_insert_policy ON expense_categories
    FOR INSERT WITH CHECK (business_id IN (SELECT business_id FROM users WHERE id = auth.uid()) AND is_system = FALSE);

DROP POLICY IF EXISTS expense_categories_update_policy ON expense_categories;
CREATE POLICY expense_categories_update_policy ON expense_categories
    FOR UPDATE USING (business_id IN (SELECT business_id FROM users WHERE id = auth.uid()) AND is_system = FALSE);

DROP POLICY IF EXISTS expense_categories_delete_policy ON expense_categories;
CREATE POLICY expense_categories_delete_policy ON expense_categories
    FOR DELETE USING (business_id IN (SELECT business_id FROM users WHERE id = auth.uid()) AND is_system = FALSE);

-- Enable RLS for expenses
ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS expenses_select_policy ON expenses;
CREATE POLICY expenses_select_policy ON expenses
    FOR SELECT USING (business_id IN (SELECT business_id FROM users WHERE id = auth.uid()));

DROP POLICY IF EXISTS expenses_insert_policy ON expenses;
CREATE POLICY expenses_insert_policy ON expenses
    FOR INSERT WITH CHECK (business_id IN (SELECT business_id FROM users WHERE id = auth.uid()));

DROP POLICY IF EXISTS expenses_update_policy ON expenses;
CREATE POLICY expenses_update_policy ON expenses
    FOR UPDATE USING (business_id IN (SELECT business_id FROM users WHERE id = auth.uid()));

DROP POLICY IF EXISTS expenses_delete_policy ON expenses;
CREATE POLICY expenses_delete_policy ON expenses
    FOR DELETE USING (business_id IN (SELECT business_id FROM users WHERE id = auth.uid()));

-- Enable RLS for payments
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS payments_business_isolation ON payments;
CREATE POLICY payments_business_isolation ON payments
    FOR ALL USING (business_id IN (SELECT business_id FROM users WHERE id = auth.uid()));

-- ============================================================================
-- PART 5: GRANT PERMISSIONS
-- ============================================================================

GRANT ALL ON expense_categories TO authenticated;
GRANT ALL ON expenses TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON payments TO authenticated;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'expense_categories') THEN
        RAISE NOTICE 'Table expense_categories created successfully';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'expenses') THEN
        RAISE NOTICE 'Table expenses created successfully';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'payments') THEN
        RAISE NOTICE 'Table payments created successfully';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'invoices' AND column_name = 'amount_paid') THEN
        RAISE NOTICE 'Column invoices.amount_paid added successfully';
    END IF;
END $$;

SELECT 'Sprint 3 Migration Complete!' as status;
