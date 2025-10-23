/**
 * Types Package
 *
 * Value Proposition: Type Safety & Code Clarity
 * - Shared types across all packages
 * - Single source of truth for data structures
 * - Better IDE autocomplete
 * - Prevents type mismatches
 */

// Re-export database types
export type * from '@temponest/database'

// API Response types
export interface ApiResponse<T = unknown> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface PaginatedResponse<T> {
  data: T[]
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
}

// Error types
export interface ApiError {
  code: string
  message: string
  details?: unknown
}

// Session types
export interface SessionUser {
  id: string
  email: string
  name: string | null
  image: string | null
  emailVerified: boolean
}

// Organization context
export interface OrganizationContext {
  id: string
  name: string
  slug: string
  role: 'owner' | 'admin' | 'member' | 'viewer'
  plan: string
  limits: Record<string, number>
}

// Feature flags
export interface FeatureFlags {
  enableSignup: boolean
  enableOAuth: boolean
  enable2FA: boolean
  enableWebhooks: boolean
  enableAnalytics: boolean
}

// Environment config
export interface Config {
  app: {
    name: string
    url: string
    env: 'development' | 'staging' | 'production'
  }
  features: FeatureFlags
  limits: {
    maxProjectsPerOrg: Record<string, number>
    maxMembersPerOrg: Record<string, number>
    maxDeploymentsPerMonth: Record<string, number>
  }
}

// Webhook event types
export type WebhookEvent =
  | 'project.created'
  | 'project.updated'
  | 'project.deleted'
  | 'deployment.started'
  | 'deployment.success'
  | 'deployment.failed'
  | 'member.invited'
  | 'member.joined'
  | 'member.removed'

export interface WebhookPayload<T = unknown> {
  event: WebhookEvent
  data: T
  organizationId: string
  timestamp: string
}

// Job types for background workers
export type JobType =
  | 'deploy-project'
  | 'send-email'
  | 'process-webhook'
  | 'cleanup-old-data'
  | 'generate-report'

export interface JobData {
  type: JobType
  payload: unknown
  organizationId?: string
  userId?: string
}

// Coolify integration types
export interface CoolifyDeployment {
  projectId: string
  appId: string
  deploymentId: string
  status: 'pending' | 'building' | 'deploying' | 'success' | 'failed'
  url?: string
  logs?: string
}

// Analytics event types
export type AnalyticsEvent =
  | 'page_view'
  | 'project_created'
  | 'deployment_triggered'
  | 'template_used'
  | 'subscription_upgraded'
  | 'api_key_created'

export interface AnalyticsEventData {
  event: AnalyticsEvent
  properties?: Record<string, unknown>
  userId?: string
  organizationId?: string
  timestamp: Date
}
