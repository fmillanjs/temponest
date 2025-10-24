/** @type {import('jest').Config} */
module.exports = {
  testEnvironment: 'jsdom', // Required for React component testing
  roots: ['<rootDir>/packages', '<rootDir>/apps'],
  testMatch: ['**/__tests__/**/*.test.ts', '**/__tests__/**/*.test.tsx'],
  testPathIgnorePatterns: [
    '/node_modules/',
    '/packages/api/', // Skip API tests - requires ESM support (nanoid, better-auth, superjson, tRPC)
    // TODO: Configure API tests with proper ESM support (experimental Node ESM or separate config)
  ],
  setupFilesAfterEnv: ['<rootDir>/packages/ui/jest.setup.js'],
  transform: {
    '^.+\\.(t|j)sx?$': [
      '@swc/jest',
      {
        jsc: {
          target: 'es2022',
          parser: {
            syntax: 'typescript',
            tsx: true,
            decorators: true,
          },
        },
      },
    ],
  },
  moduleNameMapper: {
    '^@temponest/utils$': '<rootDir>/packages/ui/__mocks__/@temponest/utils.ts',
    '^@temponest/email/templates/(.*)$': '<rootDir>/packages/email/src/templates/$1',
    '^@temponest/(.*)$': '<rootDir>/packages/$1/src',
  },
  transformIgnorePatterns: [
    'node_modules/(?!(.pnpm|copy-anything|is-what|superjson|msgpackr|bullmq))',
  ],
  collectCoverageFrom: [
    'packages/**/*.{js,jsx,ts,tsx}',
    'apps/**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
    '!**/.next/**',
    '!**/dist/**',
    '!**/coverage/**',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
}
