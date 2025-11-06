import { z } from 'zod'

// Project schemas
export const ProjectTypeEnum = z.enum(['single', 'portfolio'])
export const ProjectStatusEnum = z.enum([
  'idle',
  'research',
  'build',
  'qa',
  'deploy',
  'live',
])

export const ProjectSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1),
  slug: z.string().min(1),
  type: ProjectTypeEnum,
  status: ProjectStatusEnum,
  repoUrl: z.string().url().nullable(),
  createdAt: z.date(),
  updatedAt: z.date(),
})

// Run schemas
export const RunKindEnum = z.enum(['wizard', 'build', 'deploy', 'calc'])
export const RunStatusEnum = z.enum([
  'pending',
  'running',
  'success',
  'failed',
  'cancelled',
])

export const RunSchema = z.object({
  id: z.string().uuid(),
  projectId: z.string().uuid(),
  kind: RunKindEnum,
  step: z.string(),
  status: RunStatusEnum,
  startedAt: z.date().nullable(),
  finishedAt: z.date().nullable(),
  logs: z.string().nullable(),
  artifacts: z.record(z.any()).nullable(),
})

// Agent schemas
export const AgentNameEnum = z.enum([
  'Overseer',
  'Developer',
  'Designer',
  'UX',
  'QA',
  'Security',
  'DevOps',
])

export const AgentStatusEnum = z.enum(['healthy', 'degraded', 'down'])

export const AgentSchema = z.object({
  id: z.string().uuid(),
  name: AgentNameEnum,
  status: AgentStatusEnum,
  lastHeartbeat: z.date().nullable(),
  version: z.string(),
  config: z.record(z.any()),
})

// Approval schemas
export const ApprovalStatusEnum = z.enum([
  'pending',
  'approved',
  'changes_requested',
])

export const ApprovalSchema = z.object({
  id: z.string().uuid(),
  runId: z.string().uuid(),
  step: z.string(),
  status: ApprovalStatusEnum,
  comment: z.string().nullable(),
  createdAt: z.date(),
  decidedAt: z.date().nullable(),
})

// API request schemas
export const FinancialRunRequestSchema = z.object({
  model: z.enum(['formbuilder', 'analytics', 'crm', 'scheduler', 'emailbuilder']),
  args: z.array(z.string()).optional(),
  workdir: z.string().default('/home/doctor/temponest'),
})

export const WizardStepRequestSchema = z.object({
  step: z.string(),
  args: z.array(z.string()).optional(),
  workdir: z.string().default('/home/doctor/temponest'),
})

export type Project = z.infer<typeof ProjectSchema>
export type Run = z.infer<typeof RunSchema>
export type Agent = z.infer<typeof AgentSchema>
export type Approval = z.infer<typeof ApprovalSchema>
export type FinancialRunRequest = z.infer<typeof FinancialRunRequestSchema>
export type WizardStepRequest = z.infer<typeof WizardStepRequestSchema>
