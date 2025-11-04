-- ============================================================================
-- Migration 004: Webhook and Event System
-- ============================================================================
-- Description: Creates tables for webhook management and event notifications
-- Author: System
-- Date: 2025-11-03
-- ============================================================================

-- Create enum for event types
CREATE TYPE event_type AS ENUM (
    'task.started',
    'task.completed',
    'task.failed',
    'budget.warning',
    'budget.exceeded',
    'budget.critical',
    'approval.requested',
    'approval.approved',
    'approval.rejected',
    'agent.error',
    'workflow.started',
    'workflow.completed',
    'workflow.failed'
);

-- Create enum for webhook delivery status
CREATE TYPE delivery_status AS ENUM (
    'pending',
    'delivered',
    'failed',
    'retrying'
);

-- ============================================================================
-- Table: webhooks
-- Purpose: Store webhook configurations for event notifications
-- ============================================================================
CREATE TABLE IF NOT EXISTS webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Webhook configuration
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    description TEXT,

    -- Event subscriptions (array of event types)
    events event_type[] NOT NULL DEFAULT '{}',

    -- Authentication
    secret_key VARCHAR(255) NOT NULL,  -- For HMAC signature

    -- Filtering
    project_filter VARCHAR(255),  -- Optional: only events for specific project
    workflow_filter VARCHAR(255), -- Optional: only events for specific workflow

    -- Retry configuration
    max_retries INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 60,  -- Initial delay, doubles each retry
    timeout_seconds INTEGER DEFAULT 30,

    -- Status
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,  -- Set to true after first successful delivery

    -- Headers (JSON for custom headers)
    custom_headers JSONB DEFAULT '{}',

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_triggered_at TIMESTAMP,
    total_deliveries INTEGER DEFAULT 0,
    successful_deliveries INTEGER DEFAULT 0,
    failed_deliveries INTEGER DEFAULT 0
);

-- ============================================================================
-- Table: webhook_deliveries
-- Purpose: Track webhook delivery attempts and results
-- ============================================================================
CREATE TABLE IF NOT EXISTS webhook_deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    webhook_id UUID NOT NULL REFERENCES webhooks(id) ON DELETE CASCADE,

    -- Event details
    event_type event_type NOT NULL,
    event_id VARCHAR(255) NOT NULL,  -- task_id, budget_id, etc.
    payload JSONB NOT NULL,

    -- Delivery tracking
    status delivery_status DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,

    -- Timing
    scheduled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    next_retry_at TIMESTAMP,
    delivered_at TIMESTAMP,

    -- Response tracking
    http_status_code INTEGER,
    response_body TEXT,
    response_headers JSONB,
    error_message TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Table: event_log
-- Purpose: Audit log of all events published in the system
-- ============================================================================
CREATE TABLE IF NOT EXISTS event_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Event details
    event_type event_type NOT NULL,
    event_id VARCHAR(255) NOT NULL,  -- task_id, budget_id, etc.
    source VARCHAR(100) NOT NULL,  -- 'agents', 'cost_tracker', 'approval_ui', etc.

    -- Event data
    payload JSONB NOT NULL,

    -- Context
    project_id VARCHAR(255),
    workflow_id VARCHAR(255),

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    webhook_count INTEGER DEFAULT 0  -- How many webhooks were triggered
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Webhooks table indexes
CREATE INDEX idx_webhooks_tenant ON webhooks(tenant_id);
CREATE INDEX idx_webhooks_active ON webhooks(is_active) WHERE is_active = true;
CREATE INDEX idx_webhooks_events ON webhooks USING GIN(events);
CREATE INDEX idx_webhooks_project_filter ON webhooks(project_filter) WHERE project_filter IS NOT NULL;

-- Webhook deliveries indexes
CREATE INDEX idx_webhook_deliveries_webhook ON webhook_deliveries(webhook_id);
CREATE INDEX idx_webhook_deliveries_status ON webhook_deliveries(status);
CREATE INDEX idx_webhook_deliveries_event_type ON webhook_deliveries(event_type);
CREATE INDEX idx_webhook_deliveries_next_retry ON webhook_deliveries(next_retry_at) WHERE status = 'retrying';
CREATE INDEX idx_webhook_deliveries_created ON webhook_deliveries(created_at DESC);

-- Event log indexes
CREATE INDEX idx_event_log_tenant ON event_log(tenant_id);
CREATE INDEX idx_event_log_event_type ON event_log(event_type);
CREATE INDEX idx_event_log_event_id ON event_log(event_id);
CREATE INDEX idx_event_log_created ON event_log(created_at DESC);
CREATE INDEX idx_event_log_project ON event_log(project_id) WHERE project_id IS NOT NULL;

-- ============================================================================
-- Views for Monitoring
-- ============================================================================

-- View: webhook_health
-- Purpose: Monitor webhook health and delivery success rates
CREATE OR REPLACE VIEW webhook_health AS
SELECT
    w.id,
    w.tenant_id,
    w.name,
    w.url,
    w.is_active,
    w.total_deliveries,
    w.successful_deliveries,
    w.failed_deliveries,
    CASE
        WHEN w.total_deliveries = 0 THEN 0
        ELSE ROUND((w.successful_deliveries::DECIMAL / w.total_deliveries) * 100, 2)
    END as success_rate_pct,
    w.last_triggered_at,
    COUNT(CASE WHEN wd.status = 'pending' THEN 1 END) as pending_count,
    COUNT(CASE WHEN wd.status = 'retrying' THEN 1 END) as retrying_count,
    COUNT(CASE WHEN wd.status = 'failed' THEN 1 END) as recent_failed_count
FROM webhooks w
LEFT JOIN webhook_deliveries wd ON w.id = wd.webhook_id
    AND wd.created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'
GROUP BY w.id;

-- View: event_summary
-- Purpose: Summary of events by type and tenant
CREATE OR REPLACE VIEW event_summary AS
SELECT
    tenant_id,
    event_type,
    DATE(created_at) as event_date,
    COUNT(*) as event_count,
    COUNT(CASE WHEN webhook_count > 0 THEN 1 END) as events_with_webhooks,
    AVG(webhook_count) as avg_webhooks_per_event
FROM event_log
GROUP BY tenant_id, event_type, DATE(created_at);

-- View: failed_deliveries_recent
-- Purpose: Recent failed webhook deliveries for alerting
CREATE OR REPLACE VIEW failed_deliveries_recent AS
SELECT
    wd.id as delivery_id,
    w.id as webhook_id,
    w.tenant_id,
    w.name as webhook_name,
    w.url,
    wd.event_type,
    wd.event_id,
    wd.attempts,
    wd.error_message,
    wd.http_status_code,
    wd.created_at,
    wd.updated_at
FROM webhook_deliveries wd
JOIN webhooks w ON wd.webhook_id = w.id
WHERE wd.status = 'failed'
    AND wd.updated_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY wd.updated_at DESC;

-- ============================================================================
-- Functions
-- ============================================================================

-- Function: update_webhook_updated_at
-- Purpose: Automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_webhook_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER webhooks_updated_at
    BEFORE UPDATE ON webhooks
    FOR EACH ROW
    EXECUTE FUNCTION update_webhook_updated_at();

CREATE TRIGGER webhook_deliveries_updated_at
    BEFORE UPDATE ON webhook_deliveries
    FOR EACH ROW
    EXECUTE FUNCTION update_webhook_updated_at();

-- Function: increment_webhook_stats
-- Purpose: Update webhook statistics after delivery attempt
CREATE OR REPLACE FUNCTION increment_webhook_stats(
    p_webhook_id UUID,
    p_success BOOLEAN
)
RETURNS VOID AS $$
BEGIN
    UPDATE webhooks
    SET
        total_deliveries = total_deliveries + 1,
        successful_deliveries = CASE WHEN p_success THEN successful_deliveries + 1 ELSE successful_deliveries END,
        failed_deliveries = CASE WHEN NOT p_success THEN failed_deliveries + 1 ELSE failed_deliveries END,
        last_triggered_at = CURRENT_TIMESTAMP
    WHERE id = p_webhook_id;
END;
$$ LANGUAGE plpgsql;

-- Function: get_webhooks_for_event
-- Purpose: Get all active webhooks that should receive an event
CREATE OR REPLACE FUNCTION get_webhooks_for_event(
    p_tenant_id UUID,
    p_event_type event_type,
    p_project_id VARCHAR DEFAULT NULL,
    p_workflow_id VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    webhook_id UUID,
    webhook_url TEXT,
    secret_key VARCHAR,
    custom_headers JSONB,
    timeout_seconds INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        w.id,
        w.url,
        w.secret_key,
        w.custom_headers,
        w.timeout_seconds
    FROM webhooks w
    WHERE w.tenant_id = p_tenant_id
        AND w.is_active = true
        AND p_event_type = ANY(w.events)
        AND (w.project_filter IS NULL OR w.project_filter = p_project_id)
        AND (w.workflow_filter IS NULL OR w.workflow_filter = p_workflow_id);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Row Level Security (RLS)
-- ============================================================================

-- Enable RLS on webhooks
ALTER TABLE webhooks ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see webhooks from their tenant
CREATE POLICY webhooks_tenant_isolation ON webhooks
    FOR ALL
    USING (tenant_id IN (
        SELECT tenant_id FROM users WHERE id = current_setting('app.current_user_id', TRUE)::UUID
    ));

-- Enable RLS on webhook_deliveries
ALTER TABLE webhook_deliveries ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see deliveries for their tenant's webhooks
CREATE POLICY webhook_deliveries_tenant_isolation ON webhook_deliveries
    FOR ALL
    USING (webhook_id IN (
        SELECT id FROM webhooks WHERE tenant_id IN (
            SELECT tenant_id FROM users WHERE id = current_setting('app.current_user_id', TRUE)::UUID
        )
    ));

-- Enable RLS on event_log
ALTER TABLE event_log ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see events from their tenant
CREATE POLICY event_log_tenant_isolation ON event_log
    FOR ALL
    USING (tenant_id IN (
        SELECT tenant_id FROM users WHERE id = current_setting('app.current_user_id', TRUE)::UUID
    ));

-- ============================================================================
-- Grants
-- ============================================================================

-- Grant permissions to application user (assumes 'agentic_app' role exists)
GRANT SELECT, INSERT, UPDATE, DELETE ON webhooks TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON webhook_deliveries TO PUBLIC;
GRANT SELECT, INSERT ON event_log TO PUBLIC;
GRANT SELECT ON webhook_health TO PUBLIC;
GRANT SELECT ON event_summary TO PUBLIC;
GRANT SELECT ON failed_deliveries_recent TO PUBLIC;

-- ============================================================================
-- Sample Data (for testing)
-- ============================================================================

-- Insert a test webhook (disabled by default)
INSERT INTO webhooks (tenant_id, name, url, events, secret_key, is_active, description)
SELECT
    t.id,
    'Test Webhook - Task Completion',
    'https://webhook.site/test-endpoint',
    ARRAY['task.completed', 'task.failed']::event_type[],
    encode(gen_random_bytes(32), 'hex'),
    false,  -- Disabled by default
    'Test webhook for task completion events'
FROM tenants t
WHERE t.slug = 'acme'
LIMIT 1;

-- ============================================================================
-- Migration Complete
-- ============================================================================
COMMENT ON TABLE webhooks IS 'Webhook configurations for event notifications';
COMMENT ON TABLE webhook_deliveries IS 'Delivery attempts and results for webhooks';
COMMENT ON TABLE event_log IS 'Audit log of all events published in the system';
