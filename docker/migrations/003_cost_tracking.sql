-- Migration: Add Cost Tracking and Budget Management
-- Version: 003
-- Description: Adds cost tracking per execution, budgets, and alerts

-- ============================================================
-- COST_TRACKING TABLE
-- Records every agent execution with associated costs
-- ============================================================
CREATE TABLE IF NOT EXISTS cost_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Execution details
    task_id VARCHAR(255) NOT NULL,
    agent_name VARCHAR(100) NOT NULL,

    -- User/tenant context
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Project/workflow grouping
    project_id VARCHAR(255),  -- Optional project identifier
    workflow_id VARCHAR(255),  -- Optional workflow identifier

    -- Model details
    model_provider VARCHAR(50) NOT NULL,  -- claude, openai, ollama
    model_name VARCHAR(100) NOT NULL,

    -- Token usage
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,

    -- Cost calculation (in USD)
    input_cost_usd DECIMAL(12, 6) DEFAULT 0,
    output_cost_usd DECIMAL(12, 6) DEFAULT 0,
    total_cost_usd DECIMAL(12, 6) DEFAULT 0,

    -- Performance metrics
    latency_ms INTEGER,
    status VARCHAR(20) DEFAULT 'completed',  -- completed, failed, timeout

    -- Metadata
    context JSONB,  -- Additional context (citations count, tool calls, etc.)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX idx_cost_tenant ON cost_tracking(tenant_id, created_at DESC);
CREATE INDEX idx_cost_user ON cost_tracking(user_id, created_at DESC);
CREATE INDEX idx_cost_agent ON cost_tracking(agent_name, created_at DESC);
CREATE INDEX idx_cost_project ON cost_tracking(project_id, created_at DESC);
CREATE INDEX idx_cost_workflow ON cost_tracking(workflow_id, created_at DESC);
CREATE INDEX idx_cost_date ON cost_tracking(created_at DESC);
CREATE INDEX idx_cost_model ON cost_tracking(model_provider, model_name, created_at DESC);

-- ============================================================
-- COST_BUDGETS TABLE
-- Budget limits per tenant/user/project
-- ============================================================
CREATE TABLE IF NOT EXISTS cost_budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Scope (one of these will be set)
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    project_id VARCHAR(255),

    -- Budget constraints
    budget_type VARCHAR(20) NOT NULL,  -- daily, weekly, monthly, total
    budget_amount_usd DECIMAL(12, 2) NOT NULL,
    current_spend_usd DECIMAL(12, 2) DEFAULT 0,

    -- Time window
    period_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    period_end TIMESTAMP,

    -- Alert thresholds (percentage of budget)
    alert_threshold_pct INTEGER DEFAULT 80,  -- Alert at 80% of budget
    critical_threshold_pct INTEGER DEFAULT 95,  -- Critical alert at 95%

    -- Status
    is_active BOOLEAN DEFAULT true,
    last_reset_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Metadata
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraint: Must have at least one scope
    CHECK (
        (tenant_id IS NOT NULL)::INTEGER +
        (user_id IS NOT NULL)::INTEGER +
        (project_id IS NOT NULL)::INTEGER = 1
    )
);

-- Indexes
CREATE INDEX idx_budget_tenant ON cost_budgets(tenant_id, is_active);
CREATE INDEX idx_budget_user ON cost_budgets(user_id, is_active);
CREATE INDEX idx_budget_project ON cost_budgets(project_id, is_active);
CREATE INDEX idx_budget_period ON cost_budgets(period_start, period_end);

-- ============================================================
-- COST_ALERTS TABLE
-- Budget alert notifications
-- ============================================================
CREATE TABLE IF NOT EXISTS cost_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Alert context
    budget_id UUID NOT NULL REFERENCES cost_budgets(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Alert details
    alert_type VARCHAR(20) NOT NULL,  -- warning, critical, exceeded
    threshold_pct INTEGER NOT NULL,
    current_spend_usd DECIMAL(12, 2) NOT NULL,
    budget_amount_usd DECIMAL(12, 2) NOT NULL,

    -- Notification
    is_acknowledged BOOLEAN DEFAULT false,
    acknowledged_by UUID REFERENCES users(id) ON DELETE SET NULL,
    acknowledged_at TIMESTAMP,

    -- Message
    message TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_alert_budget ON cost_alerts(budget_id, created_at DESC);
CREATE INDEX idx_alert_tenant ON cost_alerts(tenant_id, is_acknowledged, created_at DESC);
CREATE INDEX idx_alert_date ON cost_alerts(created_at DESC);

-- ============================================================
-- MODEL_PRICING TABLE
-- Pricing per model (configurable)
-- ============================================================
CREATE TABLE IF NOT EXISTS model_pricing (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,

    -- Pricing in USD per 1M tokens
    input_price_per_1m DECIMAL(12, 6) NOT NULL,
    output_price_per_1m DECIMAL(12, 6) NOT NULL,

    -- Metadata
    is_active BOOLEAN DEFAULT true,
    effective_date DATE DEFAULT CURRENT_DATE,
    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(provider, model_name, effective_date)
);

-- Default pricing (as of 2025)
INSERT INTO model_pricing (provider, model_name, input_price_per_1m, output_price_per_1m, notes) VALUES
    -- Claude pricing
    ('claude', 'claude-sonnet-4-20250514', 3.00, 15.00, 'Claude Sonnet 4 (May 2025)'),
    ('claude', 'claude-opus-4-20250514', 15.00, 75.00, 'Claude Opus 4 (May 2025)'),
    ('claude', 'claude-haiku-4-20250514', 0.25, 1.25, 'Claude Haiku 4 (May 2025)'),

    -- OpenAI pricing
    ('openai', 'gpt-4o', 2.50, 10.00, 'GPT-4 Optimized'),
    ('openai', 'gpt-4-turbo', 10.00, 30.00, 'GPT-4 Turbo'),
    ('openai', 'gpt-3.5-turbo', 0.50, 1.50, 'GPT-3.5 Turbo'),

    -- Ollama (free but track usage)
    ('ollama', 'mistral:7b-instruct', 0.00, 0.00, 'Ollama Mistral 7B (self-hosted, free)'),
    ('ollama', 'codellama:13b', 0.00, 0.00, 'Ollama Code Llama 13B (self-hosted, free)'),
    ('ollama', 'llama2:70b', 0.00, 0.00, 'Ollama Llama 2 70B (self-hosted, free)')
ON CONFLICT (provider, model_name, effective_date) DO NOTHING;

-- ============================================================
-- VIEWS FOR COST REPORTING
-- ============================================================

-- Cost summary by tenant
CREATE OR REPLACE VIEW v_cost_by_tenant AS
SELECT
    t.id as tenant_id,
    t.name as tenant_name,
    t.plan,
    COUNT(*) as total_executions,
    SUM(ct.total_tokens) as total_tokens,
    SUM(ct.total_cost_usd) as total_cost_usd,
    AVG(ct.total_cost_usd) as avg_cost_per_execution,
    MIN(ct.created_at) as first_execution,
    MAX(ct.created_at) as last_execution
FROM cost_tracking ct
JOIN tenants t ON ct.tenant_id = t.id
GROUP BY t.id, t.name, t.plan;

-- Cost summary by agent
CREATE OR REPLACE VIEW v_cost_by_agent AS
SELECT
    agent_name,
    COUNT(*) as total_executions,
    SUM(total_tokens) as total_tokens,
    SUM(total_cost_usd) as total_cost_usd,
    AVG(total_cost_usd) as avg_cost_per_execution,
    AVG(latency_ms) as avg_latency_ms,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count,
    MIN(created_at) as first_execution,
    MAX(created_at) as last_execution
FROM cost_tracking
GROUP BY agent_name;

-- Cost summary by project
CREATE OR REPLACE VIEW v_cost_by_project AS
SELECT
    project_id,
    tenant_id,
    COUNT(*) as total_executions,
    SUM(total_tokens) as total_tokens,
    SUM(total_cost_usd) as total_cost_usd,
    AVG(total_cost_usd) as avg_cost_per_execution,
    MIN(created_at) as first_execution,
    MAX(created_at) as last_execution
FROM cost_tracking
WHERE project_id IS NOT NULL
GROUP BY project_id, tenant_id;

-- Daily cost summary
CREATE OR REPLACE VIEW v_cost_daily AS
SELECT
    DATE(created_at) as date,
    tenant_id,
    agent_name,
    COUNT(*) as executions,
    SUM(total_tokens) as total_tokens,
    SUM(total_cost_usd) as total_cost_usd
FROM cost_tracking
GROUP BY DATE(created_at), tenant_id, agent_name;

-- ============================================================
-- FUNCTIONS FOR BUDGET MANAGEMENT
-- ============================================================

-- Function to check and update budget
CREATE OR REPLACE FUNCTION check_and_update_budget(
    p_tenant_id UUID,
    p_user_id UUID,
    p_project_id VARCHAR,
    p_cost_usd DECIMAL
) RETURNS TABLE (
    exceeded BOOLEAN,
    budget_id UUID,
    alert_type VARCHAR
) AS $$
DECLARE
    v_budget RECORD;
    v_new_spend DECIMAL;
    v_utilization_pct DECIMAL;
    v_alert_type VARCHAR;
BEGIN
    -- Find active budgets that apply
    FOR v_budget IN
        SELECT * FROM cost_budgets
        WHERE is_active = true
        AND (
            (tenant_id = p_tenant_id AND user_id IS NULL AND project_id IS NULL) OR
            (user_id = p_user_id) OR
            (project_id = p_project_id)
        )
        AND (period_end IS NULL OR period_end > CURRENT_TIMESTAMP)
        ORDER BY
            CASE
                WHEN project_id IS NOT NULL THEN 1  -- Project budgets most specific
                WHEN user_id IS NOT NULL THEN 2      -- User budgets second
                ELSE 3                                -- Tenant budgets least specific
            END
    LOOP
        -- Calculate new spend
        v_new_spend := v_budget.current_spend_usd + p_cost_usd;
        v_utilization_pct := (v_new_spend / v_budget.budget_amount_usd) * 100;

        -- Update budget
        UPDATE cost_budgets
        SET current_spend_usd = v_new_spend,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = v_budget.id;

        -- Determine alert type
        v_alert_type := NULL;
        IF v_utilization_pct >= 100 THEN
            v_alert_type := 'exceeded';
        ELSIF v_utilization_pct >= v_budget.critical_threshold_pct THEN
            v_alert_type := 'critical';
        ELSIF v_utilization_pct >= v_budget.alert_threshold_pct THEN
            v_alert_type := 'warning';
        END IF;

        -- Create alert if needed
        IF v_alert_type IS NOT NULL THEN
            INSERT INTO cost_alerts (
                budget_id,
                tenant_id,
                alert_type,
                threshold_pct,
                current_spend_usd,
                budget_amount_usd,
                message
            ) VALUES (
                v_budget.id,
                COALESCE(v_budget.tenant_id, (SELECT tenant_id FROM users WHERE id = v_budget.user_id)),
                v_alert_type,
                v_utilization_pct::INTEGER,
                v_new_spend,
                v_budget.budget_amount_usd,
                format('Budget %s: %.1f%% utilized ($%.2f of $%.2f)',
                    v_alert_type, v_utilization_pct, v_new_spend, v_budget.budget_amount_usd)
            );
        END IF;

        -- Return result
        RETURN QUERY SELECT
            v_utilization_pct >= 100,
            v_budget.id,
            v_alert_type;
    END LOOP;

    -- If no budgets found, return false
    IF NOT FOUND THEN
        RETURN QUERY SELECT false, NULL::UUID, NULL::VARCHAR;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to reset periodic budgets
CREATE OR REPLACE FUNCTION reset_periodic_budgets() RETURNS void AS $$
BEGIN
    UPDATE cost_budgets
    SET current_spend_usd = 0,
        last_reset_at = CURRENT_TIMESTAMP,
        period_start = CURRENT_TIMESTAMP,
        period_end = CASE budget_type
            WHEN 'daily' THEN CURRENT_TIMESTAMP + INTERVAL '1 day'
            WHEN 'weekly' THEN CURRENT_TIMESTAMP + INTERVAL '7 days'
            WHEN 'monthly' THEN CURRENT_TIMESTAMP + INTERVAL '30 days'
            ELSE period_end
        END
    WHERE is_active = true
    AND budget_type IN ('daily', 'weekly', 'monthly')
    AND period_end < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- GRANTS
-- ============================================================
GRANT SELECT ON cost_tracking TO postgres;
GRANT INSERT ON cost_tracking TO postgres;
GRANT SELECT ON cost_budgets TO postgres;
GRANT UPDATE ON cost_budgets TO postgres;
GRANT SELECT ON cost_alerts TO postgres;
GRANT INSERT ON cost_alerts TO postgres;
GRANT SELECT ON model_pricing TO postgres;
GRANT SELECT ON v_cost_by_tenant TO postgres;
GRANT SELECT ON v_cost_by_agent TO postgres;
GRANT SELECT ON v_cost_by_project TO postgres;
GRANT SELECT ON v_cost_daily TO postgres;
