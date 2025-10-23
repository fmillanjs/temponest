import { prisma } from '@temponest/database'

/**
 * tRPC Context
 * Contains shared services and utilities available to all procedures
 */
export async function createContext() {
  return {
    prisma,
    // Will add: session, user, organization, etc.
  }
}

export type Context = Awaited<ReturnType<typeof createContext>>
