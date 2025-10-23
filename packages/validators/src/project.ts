import { z } from 'zod'
import { slugSchema } from './common'

/**
 * Project validation schemas
 */

export const createProjectSchema = z.object({
  name: z.string().min(3, 'Name must be at least 3 characters').max(50),
  slug: slugSchema.optional(),
  description: z.string().max(500).optional(),
  templateId: z.string().cuid().optional(),
  config: z.record(z.any()).optional(),
  envVariables: z.record(z.string()).optional(),
})

export const updateProjectSchema = z.object({
  name: z.string().min(3, 'Name must be at least 3 characters').max(50).optional(),
  description: z.string().max(500).optional(),
  config: z.record(z.any()).optional(),
  status: z.enum(['pending', 'creating', 'active', 'failed', 'suspended', 'deleted']).optional(),
})

export const deployProjectSchema = z.object({
  branch: z.string().default('main'),
  environment: z.enum(['development', 'staging', 'production']).default('production'),
  commitSha: z.string().optional(),
})

export const updateEnvVariablesSchema = z.object({
  envVariables: z.record(z.string()),
})

export type CreateProjectInput = z.infer<typeof createProjectSchema>
export type UpdateProjectInput = z.infer<typeof updateProjectSchema>
export type DeployProjectInput = z.infer<typeof deployProjectSchema>
export type UpdateEnvVariablesInput = z.infer<typeof updateEnvVariablesSchema>
