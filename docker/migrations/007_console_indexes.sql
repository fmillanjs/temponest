-- ============================================================================
-- Migration 006: Console App Composite Indexes
-- ============================================================================
-- Description: Adds composite indexes for Next.js console app (Prisma schema)
-- Database: saas_console
-- Author: Database Optimization - Phase 4.1
-- Date: 2025-11-12
-- ============================================================================

-- ============================================================================
-- RUNS TABLE COMPOSITE INDEXES
-- ============================================================================
-- Optimize KpiBar queries and run tracking

-- Run queries with date and status filtering (KpiBar optimization)
CREATE INDEX IF NOT EXISTS idx_runs_created_status
ON runs("createdAt" DESC, status);

CREATE INDEX IF NOT EXISTS idx_runs_status_created
ON runs(status, "createdAt" DESC);

-- Project runs with status
CREATE INDEX IF NOT EXISTS idx_runs_project_status_created
ON runs("projectId", status, "createdAt" DESC);

-- ============================================================================
-- APPROVALS TABLE COMPOSITE INDEXES
-- ============================================================================

-- Approval tracking by run and status
CREATE INDEX IF NOT EXISTS idx_approvals_run_status_created
ON approvals("runId", status, "createdAt" DESC);

-- Pending approvals (for approval dashboard)
CREATE INDEX IF NOT EXISTS idx_approvals_pending
ON approvals(status, "createdAt" DESC)
WHERE status = 'pending';

-- ============================================================================
-- AUDIT LOGS TABLE COMPOSITE INDEXES
-- ============================================================================

-- User activity tracking
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_action_created
ON audit_logs("userId", action, "createdAt" DESC)
WHERE "userId" IS NOT NULL;

-- Action-based queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_action_resource
ON audit_logs(action, resource, "createdAt" DESC);

-- ============================================================================
-- PROJECTS TABLE INDEXES
-- ============================================================================

-- Status filtering (for active projects count)
CREATE INDEX IF NOT EXISTS idx_projects_status
ON projects(status);

-- Recent projects
CREATE INDEX IF NOT EXISTS idx_projects_created
ON projects("createdAt" DESC);

-- ============================================================================
-- AGENTS TABLE INDEXES
-- ============================================================================

-- Status filtering (for agent health monitoring)
CREATE INDEX IF NOT EXISTS idx_agents_status
ON agents(status, "lastHeartbeat" DESC);

-- ============================================================================
-- SESSIONS TABLE INDEXES
-- ============================================================================

-- Session expiration cleanup (for session cleanup queries)
CREATE INDEX IF NOT EXISTS idx_sessions_expires
ON sessions("expiresAt");

-- ============================================================================
-- VACUUM AND ANALYZE
-- ============================================================================

ANALYZE runs;
ANALYZE approvals;
ANALYZE audit_logs;
ANALYZE projects;
ANALYZE agents;
ANALYZE sessions;

-- ============================================================================
-- Migration Complete
-- ============================================================================
COMMENT ON INDEX idx_runs_created_status IS 'Optimizes KpiBar dashboard queries for runs by date';
COMMENT ON INDEX idx_runs_project_status_created IS 'Optimizes project detail page run queries';
