/**
 * Commit Lint Configuration
 *
 * Value Proposition: Clear Communication & Automated Changelog
 * - Enforces conventional commits
 * - Enables automated version bumps
 * - Generates clear changelog
 */

module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat',     // New feature
        'fix',      // Bug fix
        'docs',     // Documentation only
        'style',    // Formatting, missing semi-colons, etc
        'refactor', // Code change that neither fixes a bug nor adds a feature
        'perf',     // Performance improvement
        'test',     // Adding tests
        'build',    // Build system changes
        'ci',       // CI configuration changes
        'chore',    // Other changes that don't modify src or test files
        'revert',   // Revert previous commit
      ],
    ],
    'subject-case': [0],
  },
}
