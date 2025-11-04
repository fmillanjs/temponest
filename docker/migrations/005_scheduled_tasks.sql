-- ============================================================================
-- Migration 005: Scheduled Tasks System
-- ============================================================================
-- Description: Creates tables for cron-based workflow scheduling
-- Author: System
-- Date: 2025-11-03
-- ============================================================================

-- Create enum for schedule types
CREATE TYPE schedule_type AS ENUM (
    'cron',      -- Cron expression
    'interval',  -- Fixed interval (e.g., every 5 minutes)
    'once'       -- One-time execution at specific time
);

-- Create enum for execution status
CREATE TYPE execution_status AS ENUM (
    'pending',
    'running',
    'completed',
    'failed',
    'cancelled',
    'timeout'
);

-- ============================================================================
-- Table: scheduled_tasks
-- Purpose: Store scheduled task definitions
-- ============================================================================
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Task identification
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Schedule configuration
    schedule_type schedule_type NOT NULL DEFAULT 'cron',
    cron_expression VARCHAR(100),  -- e.g., "0 */6 * * *" (every 6 hours)
    interval_seconds INTEGER,       -- For interval type (e.g., 300 for 5 minutes)
    scheduled_time TIMESTAMP,       -- For 'once' type
    timezone VARCHAR(50) DEFAULT 'UTC',

    -- Agent configuration
    agent_name VARCHAR(50) NOT NULL,  -- developer, overseer, qa_tester, etc.
    task_payload JSONB NOT NULL,      -- Task description and context

    -- Project/workflow context
    project_id VARCHAR(255),
    workflow_id VARCHAR(255),

    -- Execution settings
    timeout_seconds INTEGER DEFAULT 300,
    max_retries INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 60,

    -- Status
    is_active BOOLEAN DEFAULT true,
    is_paused BOOLEAN DEFAULT false,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),

    -- Statistics
    last_execution_at TIMESTAMP,
    next_execution_at TIMESTAMP,
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,

    -- Validation
    CONSTRAINT valid_schedule CHECK (
        (schedule_type = 'cron' AND cron_expression IS NOT NULL) OR
        (schedule_type = 'interval' AND interval_seconds IS NOT NULL AND interval_seconds > 0) OR
        (schedule_type = 'once' AND scheduled_time IS NOT NULL)
    )
);

-- ============================================================================
-- Table: task_executions
-- Purpose: Track execution history of scheduled tasks
-- ============================================================================
CREATE TABLE IF NOT EXISTS task_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheduled_task_id UUID NOT NULL REFERENCES scheduled_tasks(id) ON DELETE CASCADE,

    -- Execution details
    execution_number INTEGER NOT NULL,  -- Incremental counter per task
    status execution_status DEFAULT 'pending',

    -- Agent execution info
    agent_task_id VARCHAR(255),  -- Links to agent's task_id
    agent_name VARCHAR(50) NOT NULL,

    -- Timing
    scheduled_for TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,

    -- Results
    result JSONB,
    error_message TEXT,

    -- Resource usage
    tokens_used INTEGER DEFAULT 0,
    cost_usd DECIMAL(12, 6) DEFAULT 0,

    -- Retry tracking
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Tenant context (denormalized for querying)
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Scheduled tasks indexes
CREATE INDEX idx_scheduled_tasks_tenant ON scheduled_tasks(tenant_id);
CREATE INDEX idx_scheduled_tasks_active ON scheduled_tasks(is_active) WHERE is_active = true;
CREATE INDEX idx_scheduled_tasks_next_execution ON scheduled_tasks(next_execution_at) WHERE is_active = true AND is_paused = false;
CREATE INDEX idx_scheduled_tasks_agent ON scheduled_tasks(agent_name);
CREATE INDEX idx_scheduled_tasks_project ON scheduled_tasks(project_id) WHERE project_id IS NOT NULL;

-- Task executions indexes
CREATE INDEX idx_task_executions_scheduled_task ON task_executions(scheduled_task_id);
CREATE INDEX idx_task_executions_status ON task_executions(status);
CREATE INDEX idx_task_executions_scheduled_for ON task_executions(scheduled_for DESC);
CREATE INDEX idx_task_executions_tenant ON task_executions(tenant_id);
CREATE INDEX idx_task_executions_created ON task_executions(created_at DESC);

-- ============================================================================
-- Views for Monitoring
-- ============================================================================

-- View: scheduled_tasks_summary
-- Purpose: Summary statistics for scheduled tasks
CREATE OR REPLACE VIEW scheduled_tasks_summary AS
SELECT
    st.id,
    st.tenant_id,
    st.name,
    st.agent_name,
    st.schedule_type,
    st.cron_expression,
    st.is_active,
    st.is_paused,
    st.last_execution_at,
    st.next_execution_at,
    st.total_executions,
    st.successful_executions,
    st.failed_executions,
    CASE
        WHEN st.total_executions = 0 THEN 0
        ELSE ROUND((st.successful_executions::DECIMAL / st.total_executions) * 100, 2)
    END as success_rate_pct,
    COUNT(CASE WHEN te.status = 'running' THEN 1 END) as currently_running,
    COUNT(CASE WHEN te.status = 'pending' THEN 1 END) as pending_executions
FROM scheduled_tasks st
LEFT JOIN task_executions te ON st.id = te.scheduled_task_id
    AND te.created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'
GROUP BY st.id;

-- View: failed_executions_recent
-- Purpose: Recent failed executions for monitoring
CREATE OR REPLACE VIEW failed_executions_recent AS
SELECT
    te.id as execution_id,
    st.id as scheduled_task_id,
    st.tenant_id,
    st.name as task_name,
    st.agent_name,
    te.execution_number,
    te.error_message,
    te.retry_count,
    te.scheduled_for,
    te.started_at,
    te.completed_at,
    te.duration_ms
FROM task_executions te
JOIN scheduled_tasks st ON te.scheduled_task_id = st.id
WHERE te.status = 'failed'
    AND te.completed_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY te.completed_at DESC;

-- View: execution_stats_daily
-- Purpose: Daily execution statistics
CREATE OR REPLACE VIEW execution_stats_daily AS
SELECT
    te.tenant_id,
    te.agent_name,
    DATE(te.completed_at) as execution_date,
    COUNT(*) as total_executions,
    COUNT(CASE WHEN te.status = 'completed' THEN 1 END) as successful_count,
    COUNT(CASE WHEN te.status = 'failed' THEN 1 END) as failed_count,
    COUNT(CASE WHEN te.status = 'timeout' THEN 1 END) as timeout_count,
    AVG(te.duration_ms) as avg_duration_ms,
    SUM(te.cost_usd) as total_cost_usd
FROM task_executions te
WHERE te.completed_at IS NOT NULL
GROUP BY te.tenant_id, te.agent_name, DATE(te.completed_at);

-- ============================================================================
-- Functions
-- ============================================================================

-- Function: update_scheduled_task_updated_at
-- Purpose: Automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_scheduled_task_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER scheduled_tasks_updated_at
    BEFORE UPDATE ON scheduled_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_scheduled_task_updated_at();

CREATE TRIGGER task_executions_updated_at
    BEFORE UPDATE ON task_executions
    FOR EACH ROW
    EXECUTE FUNCTION update_scheduled_task_updated_at();

-- Function: update_task_stats
-- Purpose: Update scheduled task statistics after execution
CREATE OR REPLACE FUNCTION update_task_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status IN ('completed', 'failed') AND OLD.status NOT IN ('completed', 'failed') THEN
        UPDATE scheduled_tasks
        SET
            total_executions = total_executions + 1,
            successful_executions = CASE WHEN NEW.status = 'completed'
                THEN successful_executions + 1
                ELSE successful_executions
            END,
            failed_executions = CASE WHEN NEW.status = 'failed'
                THEN failed_executions + 1
                ELSE failed_executions
            END,
            last_execution_at = NEW.completed_at
        WHERE id = NEW.scheduled_task_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic stats updates
CREATE TRIGGER task_execution_stats_update
    AFTER UPDATE ON task_executions
    FOR EACH ROW
    WHEN (NEW.status IS DISTINCT FROM OLD.status)
    EXECUTE FUNCTION update_task_stats();

-- Function: get_next_scheduled_tasks
-- Purpose: Get tasks that need to be executed
CREATE OR REPLACE FUNCTION get_next_scheduled_tasks(
    p_limit INTEGER DEFAULT 100
)
RETURNS TABLE (
    task_id UUID,
    tenant_id UUID,
    user_id UUID,
    agent_name VARCHAR,
    task_payload JSONB,
    project_id VARCHAR,
    workflow_id VARCHAR,
    timeout_seconds INTEGER,
    max_retries INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        st.id,
        st.tenant_id,
        st.user_id,
        st.agent_name,
        st.task_payload,
        st.project_id,
        st.workflow_id,
        st.timeout_seconds,
        st.max_retries
    FROM scheduled_tasks st
    WHERE st.is_active = true
        AND st.is_paused = false
        AND st.next_execution_at <= CURRENT_TIMESTAMP
    ORDER BY st.next_execution_at
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Row Level Security (RLS)
-- ============================================================================

-- Enable RLS on scheduled_tasks
ALTER TABLE scheduled_tasks ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see tasks from their tenant
CREATE POLICY scheduled_tasks_tenant_isolation ON scheduled_tasks
    FOR ALL
    USING (tenant_id IN (
        SELECT tenant_id FROM users WHERE id = current_setting('app.current_user_id', TRUE)::UUID
    ));

-- Enable RLS on task_executions
ALTER TABLE task_executions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see executions from their tenant
CREATE POLICY task_executions_tenant_isolation ON task_executions
    FOR ALL
    USING (tenant_id IN (
        SELECT tenant_id FROM users WHERE id = current_setting('app.current_user_id', TRUE)::UUID
    ));

-- ============================================================================
-- Grants
-- ============================================================================

-- Grant permissions to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON scheduled_tasks TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON task_executions TO PUBLIC;
GRANT SELECT ON scheduled_tasks_summary TO PUBLIC;
GRANT SELECT ON failed_executions_recent TO PUBLIC;
GRANT SELECT ON execution_stats_daily TO PUBLIC;

-- ============================================================================
-- Migration Complete
-- ============================================================================
COMMENT ON TABLE scheduled_tasks IS 'Scheduled task definitions for cron-based workflows';
COMMENT ON TABLE task_executions IS 'Execution history and results for scheduled tasks';
