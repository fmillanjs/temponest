/**
 * Database Package
 *
 * Value Proposition: Type-Safe Data Access
 * - Single source of truth for database schema
 * - Automatic type generation for all models
 * - Shared across all services (web, admin, workers)
 * - Connection pooling and optimization
 */

import { PrismaClient } from '@prisma/client'

/**
 * Global Prisma Client for Development
 * Prevents multiple instances during hot reload
 */
const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined
}

/**
 * Prisma Client with logging configuration
 */
export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    log:
      process.env.NODE_ENV === 'development'
        ? ['query', 'error', 'warn']
        : ['error'],
  })

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma

/**
 * Export types for use in other packages
 */
export type * from '@prisma/client'

/**
 * Helper function to disconnect Prisma
 * Useful for graceful shutdown in workers
 */
export async function disconnect() {
  await prisma.$disconnect()
}

/**
 * Helper function to check database connection
 */
export async function healthCheck() {
  try {
    await prisma.$queryRaw`SELECT 1`
    return { status: 'ok', message: 'Database connected' }
  } catch (error) {
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error'
    }
  }
}
