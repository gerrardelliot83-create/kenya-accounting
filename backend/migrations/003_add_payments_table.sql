-- Migration: Add Payments Table and Update Invoices
-- Sprint 3: Payment Recording API
-- Description: Creates payments table and adds payment tracking to invoices

-- ============================================================================
-- 1. Add amount_paid column to invoices table
-- ============================================================================

ALTER TABLE invoices
ADD COLUMN IF NOT EXISTS amount_paid DECIMAL(15, 2) NOT NULL DEFAULT 0.00;

COMMENT ON COLUMN invoices.amount_paid IS 'Total amount paid towards this invoice';


-- ============================================================================
-- 2. Create payments table
-- ============================================================================

CREATE TABLE IF NOT EXISTS payments (
    -- Primary key (inherited from base model pattern)
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Timestamps (inherited from base model pattern)
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Business association
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,

    -- Invoice reference
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,

    -- Payment details
    amount DECIMAL(15, 2) NOT NULL CHECK (amount > 0),
    payment_date DATE NOT NULL,
    payment_method VARCHAR(20) NOT NULL,

    -- Optional reference information
    reference_number VARCHAR(100),
    notes TEXT
);

-- Add comments
COMMENT ON TABLE payments IS 'Records payments received against invoices';
COMMENT ON COLUMN payments.business_id IS 'Associated business';
COMMENT ON COLUMN payments.invoice_id IS 'Invoice this payment applies to';
COMMENT ON COLUMN payments.amount IS 'Payment amount (must be positive)';
COMMENT ON COLUMN payments.payment_date IS 'Date payment was received';
COMMENT ON COLUMN payments.payment_method IS 'Payment method (cash, bank_transfer, mpesa, card, cheque, other)';
COMMENT ON COLUMN payments.reference_number IS 'Payment reference (M-Pesa code, cheque number, transaction ID, etc.)';
COMMENT ON COLUMN payments.notes IS 'Additional payment notes';


-- ============================================================================
-- 3. Create indexes for payments table
-- ============================================================================

-- Primary indexes
CREATE INDEX IF NOT EXISTS ix_payments_id ON payments(id);
CREATE INDEX IF NOT EXISTS ix_payments_created_at ON payments(created_at);

-- Business scoping
CREATE INDEX IF NOT EXISTS ix_payments_business_id ON payments(business_id);

-- Invoice reference
CREATE INDEX IF NOT EXISTS ix_payments_invoice_id ON payments(invoice_id);

-- Payment method filter
CREATE INDEX IF NOT EXISTS ix_payments_payment_method ON payments(payment_method);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS ix_payments_business_date ON payments(business_id, payment_date);
CREATE INDEX IF NOT EXISTS ix_payments_invoice_date ON payments(invoice_id, payment_date);


-- ============================================================================
-- 4. Enable Row Level Security (RLS) for payments
-- ============================================================================

ALTER TABLE payments ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access payments for their business
CREATE POLICY payments_business_isolation ON payments
    FOR ALL
    USING (
        business_id IN (
            SELECT business_id
            FROM users
            WHERE id = auth.uid()
        )
    );

COMMENT ON POLICY payments_business_isolation ON payments IS
    'Users can only access payments for their business';


-- ============================================================================
-- 5. Grant permissions
-- ============================================================================

-- Grant permissions to authenticated users
GRANT SELECT, INSERT, UPDATE, DELETE ON payments TO authenticated;

-- Grant usage on sequences (if any)
-- Note: UUID generation doesn't use sequences, but included for completeness


-- ============================================================================
-- 6. Verification queries (for testing - comment out in production)
-- ============================================================================

-- Verify table was created
-- SELECT table_name, table_type
-- FROM information_schema.tables
-- WHERE table_name = 'payments';

-- Verify columns
-- SELECT column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'payments'
-- ORDER BY ordinal_position;

-- Verify indexes
-- SELECT indexname, indexdef
-- FROM pg_indexes
-- WHERE tablename = 'payments'
-- ORDER BY indexname;

-- Verify RLS is enabled
-- SELECT tablename, rowsecurity
-- FROM pg_tables
-- WHERE tablename = 'payments';

-- Verify invoice amount_paid column
-- SELECT column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'invoices' AND column_name = 'amount_paid';


-- ============================================================================
-- Rollback Script (for reference - run manually if needed)
-- ============================================================================

/*
-- Drop payments table
DROP TABLE IF EXISTS payments CASCADE;

-- Remove amount_paid column from invoices
ALTER TABLE invoices DROP COLUMN IF EXISTS amount_paid;
*/
