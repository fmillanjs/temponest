-- Migration: Add Authentication and Authorization System
-- Version: 002
-- Description: Adds users, roles, permissions, API keys, and tenants

-- ============================================================
-- TENANTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    plan VARCHAR(50) DEFAULT 'free',  -- free, developer, enterprise
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create default tenant
INSERT INTO tenants (name, slug, plan) VALUES ('Default Organization', 'default', 'enterprise')
ON CONFLICT (slug) DO NOTHING;

-- ============================================================
-- USERS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for users
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_tenant ON users(tenant_id);

-- ============================================================
-- ROLES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default roles
INSERT INTO roles (name, description) VALUES
    ('admin', 'Full system access including user management'),
    ('manager', 'Department management and workflow approval rights'),
    ('developer', 'Agent execution and code generation rights'),
    ('viewer', 'Read-only access to all resources')
ON CONFLICT (name) DO NOTHING;

-- ============================================================
-- PERMISSIONS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    resource VARCHAR(100) NOT NULL,  -- agents, workflows, departments, etc.
    action VARCHAR(50) NOT NULL,     -- read, write, execute, delete
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default permissions
INSERT INTO permissions (name, description, resource, action) VALUES
    ('agents:read', 'View agent information', 'agents', 'read'),
    ('agents:execute', 'Execute agents', 'agents', 'execute'),
    ('workflows:read', 'View workflows', 'workflows', 'read'),
    ('workflows:create', 'Create new workflows', 'workflows', 'write'),
    ('workflows:delete', 'Delete workflows', 'workflows', 'delete'),
    ('approvals:read', 'View approval requests', 'approvals', 'read'),
    ('approvals:approve', 'Approve or deny requests', 'approvals', 'write'),
    ('departments:read', 'View departments', 'departments', 'read'),
    ('departments:manage', 'Create and modify departments', 'departments', 'write'),
    ('users:read', 'View users', 'users', 'read'),
    ('users:manage', 'Create, update, and delete users', 'users', 'write'),
    ('tenants:manage', 'Manage tenant settings', 'tenants', 'write'),
    ('costs:read', 'View cost information', 'costs', 'read'),
    ('webhooks:manage', 'Create and manage webhooks', 'webhooks', 'write')
ON CONFLICT (name) DO NOTHING;

-- ============================================================
-- ROLE_PERMISSIONS JUNCTION TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- Assign permissions to roles
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p WHERE r.name = 'admin'
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'manager' AND p.name IN (
    'agents:read', 'agents:execute', 'workflows:read', 'workflows:create',
    'approvals:read', 'approvals:approve', 'departments:read', 'departments:manage',
    'costs:read'
)
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'developer' AND p.name IN (
    'agents:read', 'agents:execute', 'workflows:read', 'workflows:create',
    'departments:read', 'costs:read'
)
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'viewer' AND p.name LIKE '%:read'
ON CONFLICT DO NOTHING;

-- ============================================================
-- USER_ROLES JUNCTION TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- ============================================================
-- API_KEYS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    key_prefix VARCHAR(20) NOT NULL,  -- First 8 chars for identification
    name VARCHAR(100) NOT NULL,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    scopes TEXT[],  -- Array of permission names
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for API keys
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_tenant ON api_keys(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(key_prefix);

-- ============================================================
-- ADD TENANT_ID TO EXISTING TABLES
-- ============================================================

-- Add tenant_id to approval_requests (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_name='approval_requests' AND column_name='tenant_id') THEN
        ALTER TABLE approval_requests ADD COLUMN tenant_id UUID REFERENCES tenants(id);

        -- Set default tenant for existing rows
        UPDATE approval_requests SET tenant_id = (SELECT id FROM tenants WHERE slug = 'default');

        -- Make it required
        ALTER TABLE approval_requests ALTER COLUMN tenant_id SET NOT NULL;

        -- Add index
        CREATE INDEX idx_approval_tenant ON approval_requests(tenant_id);
    END IF;
END $$;

-- ============================================================
-- ROW LEVEL SECURITY (RLS) FOR MULTI-TENANCY
-- ============================================================

-- Enable RLS on tables
ALTER TABLE approval_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Policy: Users can only see data from their tenant
CREATE POLICY tenant_isolation_approval_requests ON approval_requests
    FOR ALL
    USING (tenant_id::text = current_setting('app.current_tenant', true));

CREATE POLICY tenant_isolation_users ON users
    FOR ALL
    USING (tenant_id::text = current_setting('app.current_tenant', true));

CREATE POLICY tenant_isolation_api_keys ON api_keys
    FOR ALL
    USING (tenant_id::text = current_setting('app.current_tenant', true));

-- Bypass RLS for superusers
CREATE POLICY bypass_rls_superuser ON users
    FOR ALL
    TO PUBLIC
    USING (is_superuser = true);

-- ============================================================
-- AUDIT LOG
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,  -- login, logout, agent_execute, approval_decision, etc.
    resource_type VARCHAR(100),    -- user, agent, workflow, etc.
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for audit queries
CREATE INDEX IF NOT EXISTS idx_audit_tenant_time ON audit_log(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_user_time ON audit_log(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);

-- ============================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- CREATE DEFAULT ADMIN USER
-- ============================================================
-- Password: admin123 (CHANGE IN PRODUCTION!)
-- Hash generated with bcrypt
INSERT INTO users (email, hashed_password, full_name, tenant_id, is_superuser)
VALUES (
    'admin@agentic.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7WZA7fLWGe',  -- admin123
    'System Administrator',
    (SELECT id FROM tenants WHERE slug = 'default'),
    true
)
ON CONFLICT (email) DO NOTHING;

-- Assign admin role to default admin user
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u, roles r
WHERE u.email = 'admin@agentic.local' AND r.name = 'admin'
ON CONFLICT DO NOTHING;

-- ============================================================
-- VIEWS FOR EASY QUERYING
-- ============================================================

-- View: User permissions (combines roles and permissions)
CREATE OR REPLACE VIEW user_permissions AS
SELECT
    u.id as user_id,
    u.email,
    u.tenant_id,
    r.name as role_name,
    p.name as permission_name,
    p.resource,
    p.action
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id;

-- View: Active API keys with user info
CREATE OR REPLACE VIEW active_api_keys AS
SELECT
    ak.id,
    ak.key_prefix,
    ak.name,
    ak.tenant_id,
    t.name as tenant_name,
    ak.user_id,
    u.email as user_email,
    ak.scopes,
    ak.expires_at,
    ak.last_used_at,
    ak.created_at
FROM api_keys ak
JOIN tenants t ON ak.tenant_id = t.id
LEFT JOIN users u ON ak.user_id = u.id
WHERE ak.is_active = true
  AND (ak.expires_at IS NULL OR ak.expires_at > CURRENT_TIMESTAMP);

COMMENT ON TABLE tenants IS 'Organizations using the platform';
COMMENT ON TABLE users IS 'User accounts with authentication';
COMMENT ON TABLE roles IS 'Roles for role-based access control';
COMMENT ON TABLE permissions IS 'Granular permissions for resources';
COMMENT ON TABLE api_keys IS 'API keys for programmatic access';
COMMENT ON TABLE audit_log IS 'Audit trail of all user actions';
