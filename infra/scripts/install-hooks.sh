#!/bin/bash
#
# Install Git hooks for the agentic company platform
#

echo "🔧 Installing Git hooks..."

# Check if .git directory exists
if [ ! -d ".git" ]; then
    echo "❌ Error: Not a git repository. Run this from the project root."
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Install pre-commit hook
echo "📝 Installing pre-commit hook (secret detection)..."
cp infra/scripts/pre-commit-hook.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

echo "✅ Git hooks installed successfully!"
echo ""
echo "Hooks installed:"
echo "  - pre-commit: Secret detection (blocks commits with secrets)"
echo ""
echo "To test:"
echo "  echo 'password=\"my-secret-pass\"' > test.txt"
echo "  git add test.txt"
echo "  git commit -m 'test' # Should be blocked"
echo ""
