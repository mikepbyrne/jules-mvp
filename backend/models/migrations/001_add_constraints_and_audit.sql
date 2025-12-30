-- Migration: Add database constraints and opt-in audit trail
-- Generated: 2025-12-29
-- Description: Critical security and compliance improvements

-- 1. Add unique constraint on phone numbers
ALTER TABLE members
ADD CONSTRAINT unique_phone_number UNIQUE (phone_number);

-- 2. Add soft delete columns
ALTER TABLE members
ADD COLUMN deleted_at TIMESTAMP;

ALTER TABLE households
ADD COLUMN deleted_at TIMESTAMP;

-- Create indexes for soft delete queries
CREATE INDEX idx_members_active ON members(id) WHERE deleted_at IS NULL;
CREATE INDEX idx_households_active ON households(id) WHERE deleted_at IS NULL;

-- 3. Create opt-in audit log table
CREATE TABLE opt_in_audit_log (
    id VARCHAR(36) PRIMARY KEY,
    member_id VARCHAR(36) REFERENCES members(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL, -- 'invited', 'consented', 'declined', 'opted_out', 'rejoined'
    ip_address VARCHAR(45),
    user_agent TEXT,
    metadata JSONB, -- Additional context (e.g., invitation method, consent text shown)
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Index for audit queries
CREATE INDEX idx_opt_in_audit_member ON opt_in_audit_log(member_id, created_at DESC);
CREATE INDEX idx_opt_in_audit_action ON opt_in_audit_log(action, created_at DESC);

-- Make audit log immutable (prevent updates/deletes)
CREATE RULE opt_in_audit_no_update AS ON UPDATE TO opt_in_audit_log DO INSTEAD NOTHING;
CREATE RULE opt_in_audit_no_delete AS ON DELETE TO opt_in_audit_log DO INSTEAD NOTHING;

-- 4. Add indexes for phone number lookups
CREATE INDEX idx_members_phone ON members(phone_number) WHERE deleted_at IS NULL;

-- 5. Add conversation state indexes
CREATE INDEX idx_conversation_household ON conversation_states(household_id, member_id);
CREATE INDEX idx_conversation_activity ON conversation_states(last_activity_at DESC);

-- 6. Add message indexes
CREATE INDEX idx_messages_household_created ON messages(household_id, created_at DESC);
CREATE INDEX idx_messages_member_created ON messages(member_id, created_at DESC);

-- 7. Add recipe indexes
CREATE INDEX idx_recipes_household ON family_recipes(household_id, created_at DESC);
CREATE INDEX idx_recipes_submitted_by ON family_recipes(submitted_by_id);

-- 8. Add pantry indexes
CREATE INDEX idx_pantry_household ON pantry_items(household_id, category);
CREATE INDEX idx_pantry_status ON pantry_items(household_id, quantity_status);

-- 9. Add function to log opt-in changes automatically
CREATE OR REPLACE FUNCTION log_opt_in_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Log when opt_in_status changes
    IF (TG_OP = 'UPDATE' AND OLD.opt_in_status IS DISTINCT FROM NEW.opt_in_status) THEN
        INSERT INTO opt_in_audit_log (id, member_id, action, created_at)
        VALUES (
            gen_random_uuid()::text,
            NEW.id,
            CASE NEW.opt_in_status
                WHEN 'active' THEN 'consented'
                WHEN 'declined' THEN 'declined'
                WHEN 'opted_out' THEN 'opted_out'
                ELSE 'status_changed'
            END,
            NOW()
        );
    END IF;

    -- Log when member is first invited
    IF (TG_OP = 'INSERT' AND NEW.opt_in_status = 'pending') THEN
        INSERT INTO opt_in_audit_log (id, member_id, action, created_at)
        VALUES (
            gen_random_uuid()::text,
            NEW.id,
            'invited',
            NOW()
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic opt-in logging
CREATE TRIGGER trg_log_opt_in_changes
    AFTER INSERT OR UPDATE ON members
    FOR EACH ROW
    EXECUTE FUNCTION log_opt_in_change();

-- 10. Add check constraints for data validation
ALTER TABLE members
ADD CONSTRAINT check_opt_in_status
    CHECK (opt_in_status IN ('pending', 'active', 'declined', 'opted_out', 'expired'));

ALTER TABLE members
ADD CONSTRAINT check_role
    CHECK (role IN ('adult', 'teen', 'child'));

ALTER TABLE messages
ADD CONSTRAINT check_direction
    CHECK (direction IN ('inbound', 'outbound'));

ALTER TABLE messages
ADD CONSTRAINT check_channel
    CHECK (channel IN ('group', 'individual'));

-- 11. Add comments for documentation
COMMENT ON TABLE opt_in_audit_log IS 'Immutable audit trail for TCPA compliance. Tracks all opt-in/opt-out actions.';
COMMENT ON COLUMN members.deleted_at IS 'Soft delete timestamp for GDPR compliance. NULL = active.';
COMMENT ON CONSTRAINT unique_phone_number ON members IS 'Prevents duplicate accounts. Critical for SMS compliance.';

-- 12. Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT ON opt_in_audit_log TO app_user;
-- GRANT SELECT, INSERT, UPDATE ON members TO app_user;
