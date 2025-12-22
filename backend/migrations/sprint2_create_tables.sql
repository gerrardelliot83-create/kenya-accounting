-- Sprint 2: Contacts, Items, and Invoices Tables
-- Migration for Kenya SMB Accounting MVP
-- Database: PostgreSQL (Supabase)

-- =============================================================================
-- CONTACTS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    contact_type VARCHAR(20) NOT NULL CHECK (contact_type IN ('customer', 'supplier', 'both')),
    name VARCHAR(255) NOT NULL,
    email_encrypted TEXT,
    phone_encrypted TEXT,
    kra_pin_encrypted TEXT,
    address TEXT,
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for contacts
CREATE INDEX IF NOT EXISTS ix_contacts_id ON contacts(id);
CREATE INDEX IF NOT EXISTS ix_contacts_created_at ON contacts(created_at);
CREATE INDEX IF NOT EXISTS ix_contacts_business_id ON contacts(business_id);
CREATE INDEX IF NOT EXISTS ix_contacts_contact_type ON contacts(contact_type);
CREATE INDEX IF NOT EXISTS ix_contacts_is_active ON contacts(is_active);
CREATE INDEX IF NOT EXISTS ix_contacts_business_type ON contacts(business_id, contact_type);
CREATE INDEX IF NOT EXISTS ix_contacts_business_active ON contacts(business_id, is_active);
CREATE INDEX IF NOT EXISTS ix_contacts_name_search ON contacts(name);

-- Comment on contacts table
COMMENT ON TABLE contacts IS 'Customer and supplier contacts with encrypted PII';
COMMENT ON COLUMN contacts.email_encrypted IS 'AES-256-GCM encrypted email';
COMMENT ON COLUMN contacts.phone_encrypted IS 'AES-256-GCM encrypted phone number';
COMMENT ON COLUMN contacts.kra_pin_encrypted IS 'AES-256-GCM encrypted KRA PIN';

-- =============================================================================
-- ITEMS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    item_type VARCHAR(20) NOT NULL CHECK (item_type IN ('product', 'service')),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    sku VARCHAR(100),
    unit_price DECIMAL(15, 2) NOT NULL,
    tax_rate DECIMAL(5, 2) NOT NULL DEFAULT 16.0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_business_sku UNIQUE (business_id, sku)
);

-- Indexes for items
CREATE INDEX IF NOT EXISTS ix_items_id ON items(id);
CREATE INDEX IF NOT EXISTS ix_items_created_at ON items(created_at);
CREATE INDEX IF NOT EXISTS ix_items_business_id ON items(business_id);
CREATE INDEX IF NOT EXISTS ix_items_item_type ON items(item_type);
CREATE INDEX IF NOT EXISTS ix_items_is_active ON items(is_active);
CREATE INDEX IF NOT EXISTS ix_items_business_type ON items(business_id, item_type);
CREATE INDEX IF NOT EXISTS ix_items_business_active ON items(business_id, is_active);
CREATE UNIQUE INDEX IF NOT EXISTS ix_items_business_sku ON items(business_id, sku);
CREATE INDEX IF NOT EXISTS ix_items_name_search ON items(name);

-- Comment on items table
COMMENT ON TABLE items IS 'Product and service catalog';
COMMENT ON COLUMN items.sku IS 'Stock Keeping Unit - unique per business';
COMMENT ON COLUMN items.unit_price IS 'Price per unit before tax';
COMMENT ON COLUMN items.tax_rate IS 'Tax rate percentage (default 16% VAT)';

-- =============================================================================
-- INVOICES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE RESTRICT,
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('draft', 'issued', 'paid', 'partially_paid', 'overdue', 'cancelled')),
    issue_date DATE,
    due_date DATE,
    subtotal DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    tax_amount DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    total_amount DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for invoices
CREATE INDEX IF NOT EXISTS ix_invoices_id ON invoices(id);
CREATE INDEX IF NOT EXISTS ix_invoices_created_at ON invoices(created_at);
CREATE INDEX IF NOT EXISTS ix_invoices_business_id ON invoices(business_id);
CREATE INDEX IF NOT EXISTS ix_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS ix_invoices_issue_date ON invoices(issue_date);
CREATE INDEX IF NOT EXISTS ix_invoices_due_date ON invoices(due_date);
CREATE UNIQUE INDEX IF NOT EXISTS ix_invoices_number_unique ON invoices(invoice_number);
CREATE INDEX IF NOT EXISTS ix_invoices_business_status ON invoices(business_id, status);
CREATE INDEX IF NOT EXISTS ix_invoices_business_dates ON invoices(business_id, issue_date, due_date);
CREATE INDEX IF NOT EXISTS ix_invoices_contact ON invoices(contact_id, status);

-- Comment on invoices table
COMMENT ON TABLE invoices IS 'Customer invoices with status workflow';
COMMENT ON COLUMN invoices.invoice_number IS 'Auto-generated: INV-YYYY-NNNNN';
COMMENT ON COLUMN invoices.status IS 'Workflow: draft -> issued -> paid/cancelled';

-- =============================================================================
-- INVOICE ITEMS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS invoice_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    item_id UUID REFERENCES items(id) ON DELETE SET NULL,
    description VARCHAR(500) NOT NULL,
    quantity DECIMAL(10, 2) NOT NULL DEFAULT 1.0,
    unit_price DECIMAL(15, 2) NOT NULL,
    tax_rate DECIMAL(5, 2) NOT NULL DEFAULT 16.0,
    line_total DECIMAL(15, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for invoice_items
CREATE INDEX IF NOT EXISTS ix_invoice_items_id ON invoice_items(id);
CREATE INDEX IF NOT EXISTS ix_invoice_items_created_at ON invoice_items(created_at);
CREATE INDEX IF NOT EXISTS ix_invoice_items_invoice_id ON invoice_items(invoice_id);
CREATE INDEX IF NOT EXISTS ix_invoice_items_item_id ON invoice_items(item_id);

-- Comment on invoice_items table
COMMENT ON TABLE invoice_items IS 'Line items for invoices';
COMMENT ON COLUMN invoice_items.item_id IS 'Optional reference to catalog item';
COMMENT ON COLUMN invoice_items.line_total IS 'Calculated: quantity * unit_price * (1 + tax_rate/100)';

-- =============================================================================
-- TRIGGERS FOR UPDATED_AT
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for contacts
DROP TRIGGER IF EXISTS update_contacts_updated_at ON contacts;
CREATE TRIGGER update_contacts_updated_at
    BEFORE UPDATE ON contacts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Triggers for items
DROP TRIGGER IF EXISTS update_items_updated_at ON items;
CREATE TRIGGER update_items_updated_at
    BEFORE UPDATE ON items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Triggers for invoices
DROP TRIGGER IF EXISTS update_invoices_updated_at ON invoices;
CREATE TRIGGER update_invoices_updated_at
    BEFORE UPDATE ON invoices
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =============================================================================

-- Enable RLS on all tables
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE items ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoice_items ENABLE ROW LEVEL SECURITY;

-- Contacts RLS Policies
-- Users can only see contacts from their business
CREATE POLICY contacts_select_policy ON contacts
    FOR SELECT
    USING (
        business_id IN (
            SELECT business_id FROM users WHERE id = auth.uid()
        )
    );

CREATE POLICY contacts_insert_policy ON contacts
    FOR INSERT
    WITH CHECK (
        business_id IN (
            SELECT business_id FROM users WHERE id = auth.uid()
        )
    );

CREATE POLICY contacts_update_policy ON contacts
    FOR UPDATE
    USING (
        business_id IN (
            SELECT business_id FROM users WHERE id = auth.uid()
        )
    );

CREATE POLICY contacts_delete_policy ON contacts
    FOR DELETE
    USING (
        business_id IN (
            SELECT business_id FROM users WHERE id = auth.uid()
        )
    );

-- Items RLS Policies
-- Users can only see items from their business
CREATE POLICY items_select_policy ON items
    FOR SELECT
    USING (
        business_id IN (
            SELECT business_id FROM users WHERE id = auth.uid()
        )
    );

CREATE POLICY items_insert_policy ON items
    FOR INSERT
    WITH CHECK (
        business_id IN (
            SELECT business_id FROM users WHERE id = auth.uid()
        )
    );

CREATE POLICY items_update_policy ON items
    FOR UPDATE
    USING (
        business_id IN (
            SELECT business_id FROM users WHERE id = auth.uid()
        )
    );

CREATE POLICY items_delete_policy ON items
    FOR DELETE
    USING (
        business_id IN (
            SELECT business_id FROM users WHERE id = auth.uid()
        )
    );

-- Invoices RLS Policies
-- Users can only see invoices from their business
CREATE POLICY invoices_select_policy ON invoices
    FOR SELECT
    USING (
        business_id IN (
            SELECT business_id FROM users WHERE id = auth.uid()
        )
    );

CREATE POLICY invoices_insert_policy ON invoices
    FOR INSERT
    WITH CHECK (
        business_id IN (
            SELECT business_id FROM users WHERE id = auth.uid()
        )
    );

CREATE POLICY invoices_update_policy ON invoices
    FOR UPDATE
    USING (
        business_id IN (
            SELECT business_id FROM users WHERE id = auth.uid()
        )
    );

CREATE POLICY invoices_delete_policy ON invoices
    FOR DELETE
    USING (
        business_id IN (
            SELECT business_id FROM users WHERE id = auth.uid()
        )
    );

-- Invoice Items RLS Policies
-- Users can only see invoice items from invoices in their business
CREATE POLICY invoice_items_select_policy ON invoice_items
    FOR SELECT
    USING (
        invoice_id IN (
            SELECT id FROM invoices WHERE business_id IN (
                SELECT business_id FROM users WHERE id = auth.uid()
            )
        )
    );

CREATE POLICY invoice_items_insert_policy ON invoice_items
    FOR INSERT
    WITH CHECK (
        invoice_id IN (
            SELECT id FROM invoices WHERE business_id IN (
                SELECT business_id FROM users WHERE id = auth.uid()
            )
        )
    );

CREATE POLICY invoice_items_update_policy ON invoice_items
    FOR UPDATE
    USING (
        invoice_id IN (
            SELECT id FROM invoices WHERE business_id IN (
                SELECT business_id FROM users WHERE id = auth.uid()
            )
        )
    );

CREATE POLICY invoice_items_delete_policy ON invoice_items
    FOR DELETE
    USING (
        invoice_id IN (
            SELECT id FROM invoices WHERE business_id IN (
                SELECT business_id FROM users WHERE id = auth.uid()
            )
        )
    );

-- =============================================================================
-- GRANT PERMISSIONS
-- =============================================================================

-- Grant access to authenticated users
GRANT SELECT, INSERT, UPDATE, DELETE ON contacts TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON items TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON invoices TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON invoice_items TO authenticated;

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Verify tables were created
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'contacts') AND
       EXISTS (SELECT FROM pg_tables WHERE tablename = 'items') AND
       EXISTS (SELECT FROM pg_tables WHERE tablename = 'invoices') AND
       EXISTS (SELECT FROM pg_tables WHERE tablename = 'invoice_items') THEN
        RAISE NOTICE '✓ All Sprint 2 tables created successfully';
    ELSE
        RAISE EXCEPTION '✗ Some tables were not created';
    END IF;
END $$;
