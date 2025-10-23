import { randomBytes } from 'crypto'

/**
 * Generate utilities
 */

/**
 * Generate random API key
 */
export function generateApiKey(): string {
  const prefix = 'tn_'
  const random = randomBytes(32).toString('base64url')
  return `${prefix}${random}`
}

/**
 * Generate random secret (for webhooks, etc.)
 */
export function generateSecret(length: number = 32): string {
  return randomBytes(length).toString('hex')
}

/**
 * Generate random token
 */
export function generateToken(length: number = 32): string {
  return randomBytes(length).toString('base64url')
}

/**
 * Generate random ID
 */
export function generateId(): string {
  return randomBytes(16).toString('base64url')
}
