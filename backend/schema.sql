-- ==============================================================================
-- graph8 Self-Healing Outbound Agent — Database Schema (Supabase / PostgreSQL)
-- ==============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. CAMPAIGNS
-- Core campaign configuration, ICP filters, lifecycle status, reference style templates, and batch pacing
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft', -- draft, active, paused, completed
    icp_filters JSONB NOT NULL DEFAULT '{}'::jsonb,
    reference_email_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    daily_limit INTEGER DEFAULT 50,
    sent_today INTEGER DEFAULT 0,
    last_batch_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    org_id TEXT
);

-- 2. CONTACTS
-- Enriched target prospects with real-time intent scores and sequence tracking
CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    graph8_contact_id TEXT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    title TEXT,
    company TEXT,
    intent_score INTEGER DEFAULT 0,
    current_step INTEGER DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'new', -- new, enrolled, replied, bounced, meeting_booked
    enriched_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. VARIANTS
-- Pitch variants (subject + body) for dynamic A/B/n testing and reinforcement learning
CREATE TABLE IF NOT EXISTS variants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    channel TEXT NOT NULL DEFAULT 'email', -- email (extendable later)
    subject TEXT NOT NULL,
    body_template TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active', -- active, killed, draft
    sends_count INTEGER DEFAULT 0,
    opens_count INTEGER DEFAULT 0,
    replies_count INTEGER DEFAULT 0,
    positive_replies_count INTEGER DEFAULT 0,
    meetings_count INTEGER DEFAULT 0,
    score REAL DEFAULT 0.0, -- Confidence-adjusted composite conversion score
    allocation_percentage REAL DEFAULT 50.0, -- Dynamic percentage of un-enrolled contacts routed here
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    killed_at TIMESTAMPTZ
);

-- 4. EVENTS
-- Raw fuel for the feedback loop ingested via graph8 webhooks
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
    variant_id UUID REFERENCES variants(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL, -- sent, opened, replied, bounced, meeting_booked
    raw_payload JSONB DEFAULT '{}'::jsonb,
    sentiment TEXT, -- positive, neutral, negative
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. AGENT_DECISIONS
-- Explainable AI audit trail recording every autonomous action & reinforcement shift
CREATE TABLE IF NOT EXISTS agent_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    decision_type TEXT NOT NULL, -- reallocate, kill_variant, generate_variant, escalate_voice
    reasoning TEXT NOT NULL,
    before_state JSONB DEFAULT '{}'::jsonb,
    after_state JSONB DEFAULT '{}'::jsonb,
    requires_approval BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. APPROVALS
-- Human-in-the-loop governance gates
CREATE TABLE IF NOT EXISTS approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    decision_id UUID REFERENCES agent_decisions(id) ON DELETE SET NULL,
    type TEXT NOT NULL, -- send_new_variant, kill_variant, voice_escalation, reply_draft
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, approved, rejected
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- 7. REFERENCE_EMAILS
-- Saved winning cold outreach copy used as few-shot training examples
CREATE TABLE IF NOT EXISTS reference_emails (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    style_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 8. SETTINGS
-- Non-secret UI-visible application configuration
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- 9. MAILBOX_STATUS
-- Mirrors live connection status from graph8 native mailbox connector
CREATE TABLE IF NOT EXISTS mailbox_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider TEXT NOT NULL DEFAULT 'gmail', -- gmail, outlook, smtp
    graph8_mailbox_id TEXT,
    connected_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'active' -- active, warming_up, error
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_contacts_campaign ON contacts(campaign_id);
CREATE INDEX IF NOT EXISTS idx_variants_campaign ON variants(campaign_id);
CREATE INDEX IF NOT EXISTS idx_events_contact ON events(contact_id);
CREATE INDEX IF NOT EXISTS idx_events_variant ON events(variant_id);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_campaign ON agent_decisions(campaign_id);
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);
