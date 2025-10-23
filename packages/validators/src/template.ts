import { z } from 'zod'
import { slugSchema, urlSchema } from './common'

/**
 * Template validation schemas
 */

export const createTemplateSchema = z.object({
  name: z.string().min(3, 'Name must be at least 3 characters').max(50),
  slug: slugSchema,
  description: z.string().min(10, 'Description must be at least 10 characters').max(500),
  category: z.enum(['saas', 'ecommerce', 'blog', 'api', 'landing']).default('saas'),
  repositoryUrl: urlSchema,
  repositoryRef: z.string().default('main'),
  image: urlSchema.optional(),
  tags: z.array(z.string()).default([]),
  isPublic: z.boolean().default(false),
  defaultConfig: z.record(z.any()).optional(),
  requiredEnvVars: z.array(z.string()).default([]),
})

export const updateTemplateSchema = z.object({
  name: z.string().min(3, 'Name must be at least 3 characters').max(50).optional(),
  description: z.string().min(10, 'Description must be at least 10 characters').max(500).optional(),
  category: z.enum(['saas', 'ecommerce', 'blog', 'api', 'landing']).optional(),
  image: urlSchema.optional(),
  tags: z.array(z.string()).optional(),
  isPublic: z.boolean().optional(),
  isFeatured: z.boolean().optional(),
  defaultConfig: z.record(z.any()).optional(),
  requiredEnvVars: z.array(z.string()).optional(),
})

export const templateFilterSchema = z.object({
  category: z.enum(['saas', 'ecommerce', 'blog', 'api', 'landing']).optional(),
  tags: z.array(z.string()).optional(),
  isPublic: z.boolean().optional(),
  isFeatured: z.boolean().optional(),
})

export type CreateTemplateInput = z.infer<typeof createTemplateSchema>
export type UpdateTemplateInput = z.infer<typeof updateTemplateSchema>
export type TemplateFilter = z.infer<typeof templateFilterSchema>
