-- Initialize databases for Temporal, Langfuse, Approvals, and Agentic
-- This script runs on first PostgreSQL startup

-- Create Langfuse database
CREATE DATABASE langfuse;

-- Create Approvals database
CREATE DATABASE approvals;

-- Note: Temporal database is created by the temporal auto-setup container
-- Note: Agentic database is the default database (created by POSTGRES_DB env var)

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE langfuse TO postgres;
GRANT ALL PRIVILEGES ON DATABASE approvals TO postgres;
GRANT ALL PRIVILEGES ON DATABASE agentic TO postgres;

\c approvals;

-- Create approvals table
CREATE TABLE IF NOT EXISTS approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id VARCHAR(255) NOT NULL,
    run_id VARCHAR(255) NOT NULL,
    task_description TEXT NOT NULL,
    risk_level VARCHAR(20) NOT NULL CHECK (risk_level IN ('low', 'medium', 'high')),
    requested_by VARCHAR(255),
    context JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'denied')),
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_approval_workflow ON approval_requests(workflow_id, run_id);
CREATE INDEX idx_approval_status ON approval_requests(status);
CREATE INDEX idx_approval_created ON approval_requests(created_at DESC);

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    approval_id UUID REFERENCES approval_requests(id),
    action VARCHAR(50) NOT NULL,
    actor VARCHAR(255),
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_approval ON audit_log(approval_id);
CREATE INDEX idx_audit_created ON audit_log(created_at DESC);

-- Switch to agentic database for auth system tables
\c agentic;

-- Run auth system migration
\i /docker-entrypoint-initdb.d/migrations/002_auth_system.sql
