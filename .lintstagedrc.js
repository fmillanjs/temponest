/**
 * Lint Staged Configuration
 *
 * Value Proposition: Code Quality Automation
 * - Runs checks only on staged files (fast)
 * - Auto-fixes formatting issues
 * - Prevents bad code from being committed
 */

module.exports = {
  '*.{js,jsx,ts,tsx}': [
    'eslint --fix',
    'prettier --write',
  ],
  '*.{json,md,mdx,css,html,yml,yaml,scss}': [
    'prettier --write',
  ],
  '*.ts?(x)': () => 'pnpm type-check',
}
