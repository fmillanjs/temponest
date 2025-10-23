import { z } from 'zod'
import { emailSchema, slugSchema } from './common'

/**
 * Organization validation schemas
 */

export const createOrganizationSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters').max(50),
  slug: slugSchema.optional(),
  description: z.string().max(500).optional(),
  website: z.string().url('Invalid URL').optional(),
})

export const updateOrganizationSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters').max(50).optional(),
  description: z.string().max(500).optional(),
  website: z.string().url('Invalid URL').optional(),
  image: z.string().url('Invalid image URL').optional(),
})

export const inviteMemberSchema = z.object({
  email: emailSchema,
  role: z.enum(['owner', 'admin', 'member', 'viewer']).default('member'),
})

export const updateMemberRoleSchema = z.object({
  memberId: z.string().cuid(),
  role: z.enum(['owner', 'admin', 'member', 'viewer']),
})

export type CreateOrganizationInput = z.infer<typeof createOrganizationSchema>
export type UpdateOrganizationInput = z.infer<typeof updateOrganizationSchema>
export type InviteMemberInput = z.infer<typeof inviteMemberSchema>
export type UpdateMemberRoleInput = z.infer<typeof updateMemberRoleSchema>
