-- ============================================================================
-- Sprint 5 Fix: Add missing updated_at column to ticket_messages
-- Kenya SMB Accounting MVP
-- Created: 2025-12-09
-- Description: Adds the updated_at column to ticket_messages table
-- ============================================================================

-- Add the missing updated_at column to ticket_messages
ALTER TABLE ticket_messages
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

-- Create trigger function for ticket_messages updated_at
CREATE OR REPLACE FUNCTION update_ticket_messages_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for ticket_messages updated_at
DROP TRIGGER IF EXISTS trigger_update_ticket_messages_updated_at ON ticket_messages;
CREATE TRIGGER trigger_update_ticket_messages_updated_at
    BEFORE UPDATE ON ticket_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_ticket_messages_updated_at();

-- Verify the column was added
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'ticket_messages'
        AND column_name = 'updated_at'
    ) THEN
        RAISE NOTICE 'Column updated_at added to ticket_messages successfully';
    ELSE
        RAISE EXCEPTION 'Failed to add updated_at column to ticket_messages';
    END IF;
END $$;

SELECT 'Sprint 5 Fix Complete - ticket_messages.updated_at added!' as status;
