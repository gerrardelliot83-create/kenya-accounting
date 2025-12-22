-- ============================================================================
-- Sprint 5 Migration: Tax, Reports, Help Centre, and Support Portal
-- Kenya SMB Accounting MVP
-- Created: 2025-12-09
-- Description: Creates tables for tax settings, FAQ system, help articles,
--              support tickets, ticket messages, and canned responses
-- ============================================================================

-- ============================================================================
-- PART 1: CREATE ENUMS
-- ============================================================================

-- Ticket category enum
DO $$ BEGIN
    CREATE TYPE ticket_category_enum AS ENUM ('billing', 'technical', 'feature_request', 'general');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Ticket priority enum
DO $$ BEGIN
    CREATE TYPE ticket_priority_enum AS ENUM ('low', 'medium', 'high', 'urgent');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Ticket status enum
DO $$ BEGIN
    CREATE TYPE ticket_status_enum AS ENUM ('open', 'in_progress', 'waiting_customer', 'resolved', 'closed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Sender type enum
DO $$ BEGIN
    CREATE TYPE sender_type_enum AS ENUM ('customer', 'agent');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- PART 2: CREATE TAX_SETTINGS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS tax_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Business association (one-to-one)
    business_id UUID NOT NULL UNIQUE REFERENCES businesses(id) ON DELETE CASCADE,

    -- VAT (Value Added Tax) settings
    is_vat_registered BOOLEAN NOT NULL DEFAULT FALSE,
    vat_registration_number VARCHAR(50),  -- Encrypted
    vat_registration_date DATE,

    -- TOT (Turnover Tax) settings
    is_tot_eligible BOOLEAN NOT NULL DEFAULT FALSE,

    -- Financial year configuration
    financial_year_start_month INTEGER NOT NULL DEFAULT 1,

    -- Constraints
    CONSTRAINT tax_settings_financial_year_month_check CHECK (
        financial_year_start_month >= 1 AND financial_year_start_month <= 12
    ),
    CONSTRAINT tax_settings_vat_number_check CHECK (
        (is_vat_registered = FALSE) OR (vat_registration_number IS NOT NULL)
    )
);

COMMENT ON TABLE tax_settings IS 'Business tax configuration for Kenya tax compliance';
COMMENT ON COLUMN tax_settings.business_id IS 'Associated business (one-to-one relationship)';
COMMENT ON COLUMN tax_settings.is_vat_registered IS 'Whether business is VAT registered';
COMMENT ON COLUMN tax_settings.vat_registration_number IS 'VAT registration number (encrypted)';
COMMENT ON COLUMN tax_settings.vat_registration_date IS 'Date of VAT registration with KRA';
COMMENT ON COLUMN tax_settings.is_tot_eligible IS 'Whether business is eligible for TOT (1-50M KES)';
COMMENT ON COLUMN tax_settings.financial_year_start_month IS 'Financial year start month (1=Jan, 12=Dec)';

-- Indexes for tax_settings
CREATE INDEX IF NOT EXISTS ix_tax_settings_id ON tax_settings(id);
CREATE INDEX IF NOT EXISTS ix_tax_settings_created_at ON tax_settings(created_at);
CREATE INDEX IF NOT EXISTS ix_tax_settings_business_id ON tax_settings(business_id);
CREATE INDEX IF NOT EXISTS ix_tax_settings_is_vat_registered ON tax_settings(is_vat_registered);
CREATE INDEX IF NOT EXISTS ix_tax_settings_is_tot_eligible ON tax_settings(is_tot_eligible);
CREATE INDEX IF NOT EXISTS ix_tax_settings_business_vat ON tax_settings(business_id, is_vat_registered);
CREATE INDEX IF NOT EXISTS ix_tax_settings_business_tot ON tax_settings(business_id, is_tot_eligible);

-- ============================================================================
-- PART 3: CREATE FAQ_CATEGORIES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS faq_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Category information
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    icon VARCHAR(50),

    -- Display and visibility
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE faq_categories IS 'FAQ categories for organizing help articles';
COMMENT ON COLUMN faq_categories.name IS 'Category name (e.g., Getting Started, Invoicing)';
COMMENT ON COLUMN faq_categories.description IS 'Category description';
COMMENT ON COLUMN faq_categories.icon IS 'Icon name for UI display';
COMMENT ON COLUMN faq_categories.display_order IS 'Display order (lower numbers first)';
COMMENT ON COLUMN faq_categories.is_active IS 'Whether category is visible to users';

-- Indexes for faq_categories
CREATE INDEX IF NOT EXISTS ix_faq_categories_id ON faq_categories(id);
CREATE INDEX IF NOT EXISTS ix_faq_categories_created_at ON faq_categories(created_at);
CREATE INDEX IF NOT EXISTS ix_faq_categories_name ON faq_categories(name);
CREATE INDEX IF NOT EXISTS ix_faq_categories_display_order ON faq_categories(display_order);
CREATE INDEX IF NOT EXISTS ix_faq_categories_is_active ON faq_categories(is_active);
CREATE INDEX IF NOT EXISTS ix_faq_categories_active_order ON faq_categories(is_active, display_order);

-- ============================================================================
-- PART 4: CREATE FAQ_ARTICLES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS faq_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Category association
    category_id UUID NOT NULL REFERENCES faq_categories(id) ON DELETE CASCADE,

    -- Question and answer
    question TEXT NOT NULL,
    answer TEXT NOT NULL,

    -- Search optimization
    keywords TEXT[],

    -- Display and visibility
    display_order INTEGER NOT NULL DEFAULT 0,
    is_published BOOLEAN NOT NULL DEFAULT TRUE,

    -- Analytics
    view_count INTEGER NOT NULL DEFAULT 0
);

COMMENT ON TABLE faq_articles IS 'FAQ articles with questions and answers';
COMMENT ON COLUMN faq_articles.category_id IS 'Parent FAQ category';
COMMENT ON COLUMN faq_articles.question IS 'FAQ question';
COMMENT ON COLUMN faq_articles.answer IS 'FAQ answer (supports markdown)';
COMMENT ON COLUMN faq_articles.keywords IS 'Search keywords for article discovery';
COMMENT ON COLUMN faq_articles.display_order IS 'Display order within category';
COMMENT ON COLUMN faq_articles.is_published IS 'Whether article is visible to users';
COMMENT ON COLUMN faq_articles.view_count IS 'Number of times article has been viewed';

-- Indexes for faq_articles
CREATE INDEX IF NOT EXISTS ix_faq_articles_id ON faq_articles(id);
CREATE INDEX IF NOT EXISTS ix_faq_articles_created_at ON faq_articles(created_at);
CREATE INDEX IF NOT EXISTS ix_faq_articles_category_id ON faq_articles(category_id);
CREATE INDEX IF NOT EXISTS ix_faq_articles_display_order ON faq_articles(display_order);
CREATE INDEX IF NOT EXISTS ix_faq_articles_is_published ON faq_articles(is_published);
CREATE INDEX IF NOT EXISTS ix_faq_articles_category_order ON faq_articles(category_id, display_order);
CREATE INDEX IF NOT EXISTS ix_faq_articles_category_published ON faq_articles(category_id, is_published);
CREATE INDEX IF NOT EXISTS ix_faq_articles_published_views ON faq_articles(is_published, view_count);

-- ============================================================================
-- PART 5: CREATE HELP_ARTICLES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS help_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- URL and identification
    slug VARCHAR(200) NOT NULL UNIQUE,
    title VARCHAR(500) NOT NULL,

    -- Content
    content TEXT NOT NULL,

    -- Organization
    category VARCHAR(100) NOT NULL,
    tags VARCHAR(50)[],

    -- Visibility
    is_published BOOLEAN NOT NULL DEFAULT TRUE,

    -- Analytics
    view_count INTEGER NOT NULL DEFAULT 0
);

COMMENT ON TABLE help_articles IS 'Comprehensive how-to guides and documentation';
COMMENT ON COLUMN help_articles.slug IS 'URL-friendly identifier (e.g., how-to-create-invoice)';
COMMENT ON COLUMN help_articles.title IS 'Article title';
COMMENT ON COLUMN help_articles.content IS 'Article content (markdown format)';
COMMENT ON COLUMN help_articles.category IS 'Article category (e.g., invoicing, expenses, banking)';
COMMENT ON COLUMN help_articles.tags IS 'Tags for search and cross-referencing';
COMMENT ON COLUMN help_articles.is_published IS 'Whether article is visible to users';
COMMENT ON COLUMN help_articles.view_count IS 'Number of times article has been viewed';

-- Indexes for help_articles
CREATE INDEX IF NOT EXISTS ix_help_articles_id ON help_articles(id);
CREATE INDEX IF NOT EXISTS ix_help_articles_created_at ON help_articles(created_at);
CREATE INDEX IF NOT EXISTS ix_help_articles_slug ON help_articles(slug);
CREATE INDEX IF NOT EXISTS ix_help_articles_title ON help_articles(title);
CREATE INDEX IF NOT EXISTS ix_help_articles_category ON help_articles(category);
CREATE INDEX IF NOT EXISTS ix_help_articles_is_published ON help_articles(is_published);
CREATE INDEX IF NOT EXISTS ix_help_articles_category_published ON help_articles(category, is_published);
CREATE INDEX IF NOT EXISTS ix_help_articles_published_views ON help_articles(is_published, view_count);

-- ============================================================================
-- PART 6: CREATE SUPPORT_TICKETS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS support_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Business and user association
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Ticket identification
    ticket_number VARCHAR(20) NOT NULL UNIQUE,

    -- Ticket details
    subject VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,

    -- Classification
    category ticket_category_enum NOT NULL,
    priority ticket_priority_enum NOT NULL DEFAULT 'medium',
    status ticket_status_enum NOT NULL DEFAULT 'open',

    -- Assignment
    assigned_agent_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Resolution tracking
    resolved_at TIMESTAMPTZ,

    -- Customer satisfaction
    satisfaction_rating INTEGER,

    -- Constraints
    CONSTRAINT support_tickets_rating_check CHECK (
        satisfaction_rating IS NULL OR (satisfaction_rating >= 1 AND satisfaction_rating <= 5)
    )
);

COMMENT ON TABLE support_tickets IS 'Customer support tickets';
COMMENT ON COLUMN support_tickets.business_id IS 'Associated business';
COMMENT ON COLUMN support_tickets.user_id IS 'User who created the ticket';
COMMENT ON COLUMN support_tickets.ticket_number IS 'Unique ticket number (TKT-YYYY-NNNNN format)';
COMMENT ON COLUMN support_tickets.subject IS 'Ticket subject/title';
COMMENT ON COLUMN support_tickets.description IS 'Detailed description of the issue';
COMMENT ON COLUMN support_tickets.category IS 'Ticket category: billing, technical, feature_request, general';
COMMENT ON COLUMN support_tickets.priority IS 'Ticket priority: low, medium, high, urgent';
COMMENT ON COLUMN support_tickets.status IS 'Ticket status: open, in_progress, waiting_customer, resolved, closed';
COMMENT ON COLUMN support_tickets.assigned_agent_id IS 'Support agent assigned to ticket';
COMMENT ON COLUMN support_tickets.resolved_at IS 'Timestamp when ticket was resolved';
COMMENT ON COLUMN support_tickets.satisfaction_rating IS 'Customer satisfaction rating (1-5 stars)';

-- Indexes for support_tickets
CREATE INDEX IF NOT EXISTS ix_support_tickets_id ON support_tickets(id);
CREATE INDEX IF NOT EXISTS ix_support_tickets_created_at ON support_tickets(created_at);
CREATE INDEX IF NOT EXISTS ix_support_tickets_business_id ON support_tickets(business_id);
CREATE INDEX IF NOT EXISTS ix_support_tickets_user_id ON support_tickets(user_id);
CREATE INDEX IF NOT EXISTS ix_support_tickets_ticket_number ON support_tickets(ticket_number);
CREATE INDEX IF NOT EXISTS ix_support_tickets_category ON support_tickets(category);
CREATE INDEX IF NOT EXISTS ix_support_tickets_priority ON support_tickets(priority);
CREATE INDEX IF NOT EXISTS ix_support_tickets_status ON support_tickets(status);
CREATE INDEX IF NOT EXISTS ix_support_tickets_assigned_agent_id ON support_tickets(assigned_agent_id);
CREATE INDEX IF NOT EXISTS ix_support_tickets_resolved_at ON support_tickets(resolved_at);
CREATE INDEX IF NOT EXISTS ix_support_tickets_business_status ON support_tickets(business_id, status);
CREATE INDEX IF NOT EXISTS ix_support_tickets_business_priority ON support_tickets(business_id, priority);
CREATE INDEX IF NOT EXISTS ix_support_tickets_agent_status ON support_tickets(assigned_agent_id, status);
CREATE INDEX IF NOT EXISTS ix_support_tickets_status_priority ON support_tickets(status, priority);
CREATE INDEX IF NOT EXISTS ix_support_tickets_business_created ON support_tickets(business_id, created_at);
CREATE INDEX IF NOT EXISTS ix_support_tickets_category_status ON support_tickets(category, status);

-- ============================================================================
-- PART 7: CREATE TICKET_MESSAGES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS ticket_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ticket association
    ticket_id UUID NOT NULL REFERENCES support_tickets(id) ON DELETE CASCADE,

    -- Sender information
    sender_id UUID REFERENCES users(id) ON DELETE SET NULL,
    sender_type sender_type_enum NOT NULL,

    -- Message content
    message TEXT NOT NULL,

    -- Attachments
    attachments JSONB,

    -- Internal notes flag
    is_internal BOOLEAN NOT NULL DEFAULT FALSE
);

COMMENT ON TABLE ticket_messages IS 'Messages and conversation thread for support tickets';
COMMENT ON COLUMN ticket_messages.ticket_id IS 'Associated support ticket';
COMMENT ON COLUMN ticket_messages.sender_id IS 'User who sent the message';
COMMENT ON COLUMN ticket_messages.sender_type IS 'Sender type: customer or agent';
COMMENT ON COLUMN ticket_messages.message IS 'Message content';
COMMENT ON COLUMN ticket_messages.attachments IS 'Attachment metadata array: [{name, url, type, size}]';
COMMENT ON COLUMN ticket_messages.is_internal IS 'Internal note (not visible to customer)';

-- Indexes for ticket_messages
CREATE INDEX IF NOT EXISTS ix_ticket_messages_id ON ticket_messages(id);
CREATE INDEX IF NOT EXISTS ix_ticket_messages_created_at ON ticket_messages(created_at);
CREATE INDEX IF NOT EXISTS ix_ticket_messages_ticket_id ON ticket_messages(ticket_id);
CREATE INDEX IF NOT EXISTS ix_ticket_messages_sender_id ON ticket_messages(sender_id);
CREATE INDEX IF NOT EXISTS ix_ticket_messages_sender_type ON ticket_messages(sender_type);
CREATE INDEX IF NOT EXISTS ix_ticket_messages_is_internal ON ticket_messages(is_internal);
CREATE INDEX IF NOT EXISTS ix_ticket_messages_ticket_created ON ticket_messages(ticket_id, created_at);
CREATE INDEX IF NOT EXISTS ix_ticket_messages_ticket_internal ON ticket_messages(ticket_id, is_internal);
CREATE INDEX IF NOT EXISTS ix_ticket_messages_sender_type_idx ON ticket_messages(sender_id, sender_type);

-- ============================================================================
-- PART 8: CREATE CANNED_RESPONSES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS canned_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Response identification
    title VARCHAR(200) NOT NULL,

    -- Response content
    content TEXT NOT NULL,

    -- Organization
    category VARCHAR(100) NOT NULL,

    -- Visibility
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE canned_responses IS 'Pre-written response templates for support agents';
COMMENT ON COLUMN canned_responses.title IS 'Response title for easy identification';
COMMENT ON COLUMN canned_responses.content IS 'Response content template (supports placeholders)';
COMMENT ON COLUMN canned_responses.category IS 'Response category (e.g., greeting, billing, technical)';
COMMENT ON COLUMN canned_responses.is_active IS 'Whether response is available for use';

-- Indexes for canned_responses
CREATE INDEX IF NOT EXISTS ix_canned_responses_id ON canned_responses(id);
CREATE INDEX IF NOT EXISTS ix_canned_responses_created_at ON canned_responses(created_at);
CREATE INDEX IF NOT EXISTS ix_canned_responses_title ON canned_responses(title);
CREATE INDEX IF NOT EXISTS ix_canned_responses_category ON canned_responses(category);
CREATE INDEX IF NOT EXISTS ix_canned_responses_is_active ON canned_responses(is_active);
CREATE INDEX IF NOT EXISTS ix_canned_responses_category_active ON canned_responses(category, is_active);
CREATE INDEX IF NOT EXISTS ix_canned_responses_active_title ON canned_responses(is_active, title);

-- ============================================================================
-- PART 9: TRIGGERS FOR UPDATED_AT
-- ============================================================================

-- Trigger function for tax_settings
CREATE OR REPLACE FUNCTION update_tax_settings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_tax_settings_updated_at ON tax_settings;
CREATE TRIGGER trigger_update_tax_settings_updated_at
    BEFORE UPDATE ON tax_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_tax_settings_updated_at();

-- Trigger function for faq_categories
CREATE OR REPLACE FUNCTION update_faq_categories_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_faq_categories_updated_at ON faq_categories;
CREATE TRIGGER trigger_update_faq_categories_updated_at
    BEFORE UPDATE ON faq_categories
    FOR EACH ROW
    EXECUTE FUNCTION update_faq_categories_updated_at();

-- Trigger function for faq_articles
CREATE OR REPLACE FUNCTION update_faq_articles_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_faq_articles_updated_at ON faq_articles;
CREATE TRIGGER trigger_update_faq_articles_updated_at
    BEFORE UPDATE ON faq_articles
    FOR EACH ROW
    EXECUTE FUNCTION update_faq_articles_updated_at();

-- Trigger function for help_articles
CREATE OR REPLACE FUNCTION update_help_articles_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_help_articles_updated_at ON help_articles;
CREATE TRIGGER trigger_update_help_articles_updated_at
    BEFORE UPDATE ON help_articles
    FOR EACH ROW
    EXECUTE FUNCTION update_help_articles_updated_at();

-- Trigger function for support_tickets
CREATE OR REPLACE FUNCTION update_support_tickets_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_support_tickets_updated_at ON support_tickets;
CREATE TRIGGER trigger_update_support_tickets_updated_at
    BEFORE UPDATE ON support_tickets
    FOR EACH ROW
    EXECUTE FUNCTION update_support_tickets_updated_at();

-- Trigger function for canned_responses
CREATE OR REPLACE FUNCTION update_canned_responses_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_canned_responses_updated_at ON canned_responses;
CREATE TRIGGER trigger_update_canned_responses_updated_at
    BEFORE UPDATE ON canned_responses
    FOR EACH ROW
    EXECUTE FUNCTION update_canned_responses_updated_at();

-- ============================================================================
-- PART 10: TICKET NUMBER AUTO-GENERATION
-- ============================================================================

-- Create sequence for ticket numbers
CREATE SEQUENCE IF NOT EXISTS ticket_number_seq START WITH 1;

-- Function to generate ticket number
CREATE OR REPLACE FUNCTION generate_ticket_number()
RETURNS TRIGGER AS $$
DECLARE
    year_str VARCHAR(4);
    seq_num VARCHAR(5);
BEGIN
    -- Get current year
    year_str := TO_CHAR(CURRENT_DATE, 'YYYY');

    -- Get next sequence number (padded to 5 digits)
    seq_num := LPAD(nextval('ticket_number_seq')::TEXT, 5, '0');

    -- Generate ticket number in format TKT-YYYY-NNNNN
    NEW.ticket_number := 'TKT-' || year_str || '-' || seq_num;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-generate ticket number on insert
DROP TRIGGER IF EXISTS trigger_generate_ticket_number ON support_tickets;
CREATE TRIGGER trigger_generate_ticket_number
    BEFORE INSERT ON support_tickets
    FOR EACH ROW
    WHEN (NEW.ticket_number IS NULL OR NEW.ticket_number = '')
    EXECUTE FUNCTION generate_ticket_number();

-- ============================================================================
-- PART 11: ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS for tax_settings
ALTER TABLE tax_settings ENABLE ROW LEVEL SECURITY;

-- Tax settings: Users can only access their business's tax settings
DROP POLICY IF EXISTS tax_settings_business_isolation ON tax_settings;
CREATE POLICY tax_settings_business_isolation ON tax_settings
    FOR ALL USING (
        business_id IN (
            SELECT business_id
            FROM users
            WHERE id = auth.uid()
        )
    );

-- FAQ categories and articles are publicly readable (no RLS needed for read)
-- But only admins can modify (handle via application layer)

-- Enable RLS for support_tickets
ALTER TABLE support_tickets ENABLE ROW LEVEL SECURITY;

-- Support tickets: Users can only access their business's tickets
DROP POLICY IF EXISTS support_tickets_business_isolation ON support_tickets;
CREATE POLICY support_tickets_business_isolation ON support_tickets
    FOR ALL USING (
        business_id IN (
            SELECT business_id
            FROM users
            WHERE id = auth.uid()
        )
        OR
        -- Support agents can see assigned tickets
        assigned_agent_id = auth.uid()
    );

-- Enable RLS for ticket_messages
ALTER TABLE ticket_messages ENABLE ROW LEVEL SECURITY;

-- Ticket messages: Users can access messages for tickets they have access to
DROP POLICY IF EXISTS ticket_messages_ticket_access ON ticket_messages;
CREATE POLICY ticket_messages_ticket_access ON ticket_messages
    FOR ALL USING (
        ticket_id IN (
            SELECT id FROM support_tickets
            WHERE business_id IN (
                SELECT business_id
                FROM users
                WHERE id = auth.uid()
            )
            OR assigned_agent_id = auth.uid()
        )
    );

-- ============================================================================
-- PART 12: GRANT PERMISSIONS
-- ============================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON tax_settings TO authenticated;
GRANT SELECT ON faq_categories TO authenticated;
GRANT SELECT ON faq_articles TO authenticated;
GRANT SELECT ON help_articles TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON support_tickets TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON ticket_messages TO authenticated;
GRANT SELECT ON canned_responses TO authenticated;

-- Grant usage on sequences
GRANT USAGE ON SEQUENCE ticket_number_seq TO authenticated;

-- ============================================================================
-- PART 13: VERIFICATION
-- ============================================================================

DO $$
BEGIN
    -- Check tables
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tax_settings') THEN
        RAISE NOTICE 'Table tax_settings created successfully';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'faq_categories') THEN
        RAISE NOTICE 'Table faq_categories created successfully';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'faq_articles') THEN
        RAISE NOTICE 'Table faq_articles created successfully';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'help_articles') THEN
        RAISE NOTICE 'Table help_articles created successfully';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'support_tickets') THEN
        RAISE NOTICE 'Table support_tickets created successfully';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ticket_messages') THEN
        RAISE NOTICE 'Table ticket_messages created successfully';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'canned_responses') THEN
        RAISE NOTICE 'Table canned_responses created successfully';
    END IF;

    -- Check enums
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ticket_category_enum') THEN
        RAISE NOTICE 'Enum ticket_category_enum created successfully';
    END IF;

    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ticket_priority_enum') THEN
        RAISE NOTICE 'Enum ticket_priority_enum created successfully';
    END IF;

    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ticket_status_enum') THEN
        RAISE NOTICE 'Enum ticket_status_enum created successfully';
    END IF;

    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sender_type_enum') THEN
        RAISE NOTICE 'Enum sender_type_enum created successfully';
    END IF;

    -- Check sequences
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'ticket_number_seq') THEN
        RAISE NOTICE 'Sequence ticket_number_seq created successfully';
    END IF;

    -- Check indexes
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_tax_settings_business_vat') THEN
        RAISE NOTICE 'Index ix_tax_settings_business_vat created successfully';
    END IF;

    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_support_tickets_business_status') THEN
        RAISE NOTICE 'Index ix_support_tickets_business_status created successfully';
    END IF;

    -- Check triggers
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_generate_ticket_number') THEN
        RAISE NOTICE 'Trigger trigger_generate_ticket_number created successfully';
    END IF;

    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_update_tax_settings_updated_at') THEN
        RAISE NOTICE 'Trigger trigger_update_tax_settings_updated_at created successfully';
    END IF;

    -- Check RLS policies
    IF EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'tax_settings_business_isolation') THEN
        RAISE NOTICE 'RLS policy tax_settings_business_isolation created successfully';
    END IF;

    IF EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'support_tickets_business_isolation') THEN
        RAISE NOTICE 'RLS policy support_tickets_business_isolation created successfully';
    END IF;

    IF EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'ticket_messages_ticket_access') THEN
        RAISE NOTICE 'RLS policy ticket_messages_ticket_access created successfully';
    END IF;
END $$;

SELECT 'Sprint 5 Migration Complete!' as status;

-- ============================================================================
-- MIGRATION NOTES
-- ============================================================================
--
-- This migration creates:
-- 1. Four new enums: ticket_category_enum, ticket_priority_enum, ticket_status_enum, sender_type_enum
-- 2. tax_settings table for business tax configuration
-- 3. faq_categories and faq_articles tables for FAQ system
-- 4. help_articles table for comprehensive documentation
-- 5. support_tickets table for customer support tickets
-- 6. ticket_messages table for ticket conversation threads
-- 7. canned_responses table for support agent templates
-- 8. Comprehensive indexes for query performance
-- 9. Updated_at triggers for all tables with updated_at column
-- 10. Auto-generation of ticket numbers (TKT-YYYY-NNNNN format)
-- 11. Row Level Security policies for business isolation
-- 12. Proper foreign key constraints and check constraints
--
-- Security Features:
-- - RLS policies ensure users can only access their business's data
-- - Support agents can access assigned tickets
-- - Encrypted field: vat_registration_number
-- - Foreign key cascades protect referential integrity
-- - Check constraints validate data quality
--
-- Tax Configuration:
-- - One-to-one relationship with business
-- - VAT and TOT configuration
-- - Financial year customization
--
-- Support Portal Features:
-- - Automatic ticket numbering with sequence
-- - Priority and category classification
-- - Agent assignment and workload tracking
-- - Customer satisfaction ratings
-- - Internal notes for agent collaboration
-- - File attachment support via JSONB
--
-- Help Centre Features:
-- - FAQ system with categories and articles
-- - Comprehensive help articles with slug-based URLs
-- - View count tracking for analytics
-- - Keyword and tag-based search
-- - Markdown content support
--
-- ============================================================================
