import { slugify, createUniqueSlug, createUniqueSlugDb } from '../slug'

describe('slugify', () => {
  it('should convert text to lowercase', () => {
    expect(slugify('Hello World')).toBe('hello-world')
  })

  it('should replace spaces with hyphens', () => {
    expect(slugify('my awesome project')).toBe('my-awesome-project')
  })

  it('should remove special characters', () => {
    expect(slugify('Hello@World!')).toBe('helloworld')
  })

  it('should handle multiple spaces', () => {
    expect(slugify('hello    world')).toBe('hello-world')
  })

  it('should trim leading and trailing hyphens', () => {
    expect(slugify('  hello world  ')).toBe('hello-world')
  })

  it('should handle unicode characters', () => {
    expect(slugify('Café Münchën')).toBe('caf-mnchn')
  })

  it('should handle empty string', () => {
    expect(slugify('')).toBe('')
  })

  it('should handle numbers', () => {
    expect(slugify('Project 2024')).toBe('project-2024')
  })

  it('should handle multiple consecutive hyphens', () => {
    expect(slugify('hello---world')).toBe('hello-world')
  })

  it('should remove leading hyphens', () => {
    expect(slugify('---hello')).toBe('hello')
  })

  it('should remove trailing hyphens', () => {
    expect(slugify('hello---')).toBe('hello')
  })
})

describe('createUniqueSlug', () => {
  it('should return original slug if not in existing list', () => {
    const slug = 'my-project'
    const existing = ['other-project', 'another-project']
    expect(createUniqueSlug(slug, existing)).toBe('my-project')
  })

  it('should append -1 if slug already exists', () => {
    const slug = 'my-project'
    const existing = ['my-project']
    expect(createUniqueSlug(slug, existing)).toBe('my-project-1')
  })

  it('should append -2 if slug and slug-1 already exist', () => {
    const slug = 'my-project'
    const existing = ['my-project', 'my-project-1']
    expect(createUniqueSlug(slug, existing)).toBe('my-project-2')
  })

  it('should find the next available number', () => {
    const slug = 'my-project'
    const existing = ['my-project', 'my-project-1', 'my-project-2', 'my-project-3']
    expect(createUniqueSlug(slug, existing)).toBe('my-project-4')
  })

  it('should handle empty existing list', () => {
    const slug = 'my-project'
    expect(createUniqueSlug(slug, [])).toBe('my-project')
  })

  it('should work with complex slugs', () => {
    const slug = 'complex-slug-name-2024'
    const existing = ['complex-slug-name-2024']
    expect(createUniqueSlug(slug, existing)).toBe('complex-slug-name-2024-1')
  })
})

describe('createUniqueSlugDb', () => {
  it('should return original slug if not in database', async () => {
    const mockPrisma = {
      project: {
        findUnique: jest.fn().mockResolvedValue(null),
      },
    }

    const result = await createUniqueSlugDb(
      mockPrisma as any,
      'project',
      'my-project'
    )

    expect(result).toBe('my-project')
    expect(mockPrisma.project.findUnique).toHaveBeenCalledWith({
      where: { slug: 'my-project' },
      select: { id: true },
    })
  })

  it('should append -1 if slug exists in database', async () => {
    const mockPrisma = {
      project: {
        findUnique: jest
          .fn()
          .mockResolvedValueOnce({ id: 'existing-id' }) // First slug exists
          .mockResolvedValueOnce(null), // Second slug doesn't exist
      },
    }

    const result = await createUniqueSlugDb(
      mockPrisma as any,
      'project',
      'my-project'
    )

    expect(result).toBe('my-project-1')
    expect(mockPrisma.project.findUnique).toHaveBeenCalledTimes(2)
  })

  it('should find next available slug with multiple conflicts', async () => {
    const mockPrisma = {
      organization: {
        findUnique: jest
          .fn()
          .mockResolvedValueOnce({ id: 'id-1' }) // my-org exists
          .mockResolvedValueOnce({ id: 'id-2' }) // my-org-1 exists
          .mockResolvedValueOnce({ id: 'id-3' }) // my-org-2 exists
          .mockResolvedValueOnce(null), // my-org-3 doesn't exist
      },
    }

    const result = await createUniqueSlugDb(
      mockPrisma as any,
      'organization',
      'my-org'
    )

    expect(result).toBe('my-org-3')
    expect(mockPrisma.organization.findUnique).toHaveBeenCalledTimes(4)
  })

  it('should work with template model', async () => {
    const mockPrisma = {
      template: {
        findUnique: jest.fn().mockResolvedValue(null),
      },
    }

    const result = await createUniqueSlugDb(
      mockPrisma as any,
      'template',
      'my-template'
    )

    expect(result).toBe('my-template')
    expect(mockPrisma.template.findUnique).toHaveBeenCalledWith({
      where: { slug: 'my-template' },
      select: { id: true },
    })
  })

  it('should fallback to timestamp if max attempts reached', async () => {
    const mockPrisma = {
      project: {
        findUnique: jest.fn().mockResolvedValue({ id: 'existing-id' }), // Always exists
      },
    }

    const beforeTimestamp = Date.now()
    const result = await createUniqueSlugDb(
      mockPrisma as any,
      'project',
      'my-project',
      5 // maxAttempts
    )
    const afterTimestamp = Date.now()

    // Should have format: my-project-{timestamp}
    expect(result).toMatch(/^my-project-\d+$/)

    // Extract timestamp from result
    const timestamp = parseInt(result.split('-').pop()!)
    expect(timestamp).toBeGreaterThanOrEqual(beforeTimestamp)
    expect(timestamp).toBeLessThanOrEqual(afterTimestamp)

    // Should have tried: my-project, my-project-1, my-project-2, my-project-3, my-project-4
    expect(mockPrisma.project.findUnique).toHaveBeenCalledTimes(5)
  })

  it('should respect custom maxAttempts parameter', async () => {
    const mockPrisma = {
      project: {
        findUnique: jest.fn().mockResolvedValue({ id: 'existing-id' }),
      },
    }

    await createUniqueSlugDb(mockPrisma as any, 'project', 'my-project', 3)

    // Should try: my-project, my-project-1, my-project-2
    expect(mockPrisma.project.findUnique).toHaveBeenCalledTimes(3)
  })

  it('should use default maxAttempts of 100 if not specified', async () => {
    const mockPrisma = {
      organization: {
        findUnique: jest.fn().mockResolvedValue({ id: 'existing-id' }),
      },
    }

    await createUniqueSlugDb(mockPrisma as any, 'organization', 'my-org')

    // Should try 100 times
    expect(mockPrisma.organization.findUnique).toHaveBeenCalledTimes(100)
  })

  it('should handle empty base slug', async () => {
    const mockPrisma = {
      project: {
        findUnique: jest.fn().mockResolvedValue(null),
      },
    }

    const result = await createUniqueSlugDb(mockPrisma as any, 'project', '')

    expect(result).toBe('')
    expect(mockPrisma.project.findUnique).toHaveBeenCalledWith({
      where: { slug: '' },
      select: { id: true },
    })
  })
})
