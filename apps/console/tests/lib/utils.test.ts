import { describe, it, expect, beforeEach, vi } from 'vitest'
import { cn, formatDate, formatDateTime, formatRelativeTime } from '@/lib/utils'

describe('Utils', () => {
  describe('cn (className merger)', () => {
    it('merges multiple class names', () => {
      const result = cn('class1', 'class2', 'class3')
      expect(result).toBe('class1 class2 class3')
    })

    it('handles conditional classes', () => {
      const result = cn('base', true && 'active', false && 'inactive')
      expect(result).toBe('base active')
    })

    it('merges tailwind classes correctly', () => {
      const result = cn('px-2 py-1', 'px-4')
      // twMerge should keep only the last px class
      expect(result).toBe('py-1 px-4')
    })

    it('handles arrays of classes', () => {
      const result = cn(['class1', 'class2'], 'class3')
      expect(result).toBe('class1 class2 class3')
    })

    it('handles undefined and null values', () => {
      const result = cn('base', undefined, null, 'other')
      expect(result).toBe('base other')
    })

    it('handles empty input', () => {
      const result = cn()
      expect(result).toBe('')
    })
  })

  describe('formatDate', () => {
    it('formats Date object correctly', () => {
      const date = new Date('2024-01-15T12:00:00Z')
      const result = formatDate(date)
      expect(result).toMatch(/Jan 15, 2024/)
    })

    it('formats date string correctly', () => {
      const result = formatDate('2024-01-15T12:00:00Z')
      expect(result).toMatch(/Jan 15, 2024/)
    })

    it('handles different months', () => {
      const date = new Date('2024-12-25T12:00:00Z')
      const result = formatDate(date)
      expect(result).toMatch(/Dec 25, 2024/)
    })
  })

  describe('formatDateTime', () => {
    it('formats Date object with time', () => {
      const date = new Date('2024-01-15T14:30:00Z')
      const result = formatDateTime(date)
      // Should include both date and time
      expect(result).toMatch(/Jan 15, 2024/)
      expect(result).toMatch(/\d+:\d+/)
    })

    it('formats date string with time', () => {
      const result = formatDateTime('2024-01-15T14:30:00Z')
      expect(result).toMatch(/Jan 15, 2024/)
      expect(result).toMatch(/\d+:\d+/)
    })
  })

  describe('formatRelativeTime', () => {
    beforeEach(() => {
      // Fix the current time for consistent tests
      vi.useFakeTimers()
      vi.setSystemTime(new Date('2024-01-15T12:00:00Z'))
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('formats seconds ago', () => {
      const date = new Date('2024-01-15T11:59:30Z') // 30 seconds ago
      const result = formatRelativeTime(date)
      expect(result).toBe('30s ago')
    })

    it('formats minutes ago', () => {
      const date = new Date('2024-01-15T11:55:00Z') // 5 minutes ago
      const result = formatRelativeTime(date)
      expect(result).toBe('5m ago')
    })

    it('formats hours ago', () => {
      const date = new Date('2024-01-15T10:00:00Z') // 2 hours ago
      const result = formatRelativeTime(date)
      expect(result).toBe('2h ago')
    })

    it('formats days ago', () => {
      const date = new Date('2024-01-13T12:00:00Z') // 2 days ago
      const result = formatRelativeTime(date)
      expect(result).toBe('2d ago')
    })

    it('handles date strings', () => {
      const result = formatRelativeTime('2024-01-15T11:59:00Z') // 1 minute ago
      expect(result).toBe('1m ago')
    })

    it('handles very recent times (< 1 second)', () => {
      const date = new Date('2024-01-15T11:59:59.5Z') // < 1 second ago
      const result = formatRelativeTime(date)
      expect(result).toMatch(/0s ago/)
    })

    it('rounds down minutes correctly', () => {
      const date = new Date('2024-01-15T11:50:30Z') // 9.5 minutes ago
      const result = formatRelativeTime(date)
      expect(result).toBe('9m ago')
    })
  })
})
