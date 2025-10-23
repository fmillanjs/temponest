/**
 * API Package
 *
 * Value Proposition: Type-Safe API Layer
 * - End-to-end type safety with tRPC
 * - Shared API definitions across web/admin/workers
 * - Auto-generated client types
 * - Composable procedures
 */

import { initTRPC } from '@trpc/server'
import type { Context } from './context'

const t = initTRPC.context<Context>().create()

export const router = t.router
export const publicProcedure = t.procedure
export const protectedProcedure = t.procedure // Add auth middleware later

// Placeholder root router
export const appRouter = router({
  health: publicProcedure.query(() => ({
    status: 'ok',
    timestamp: new Date().toISOString(),
  })),
})

export type AppRouter = typeof appRouter
export { createContext } from './context'
