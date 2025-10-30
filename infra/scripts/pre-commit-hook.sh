#!/bin/bash
#
# Pre-commit hook to prevent committing secrets
#
# Install: ./infra/scripts/install-hooks.sh
# Or manually: cp infra/scripts/pre-commit-hook.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Secret patterns to detect
declare -A PATTERNS=(
    ["AWS_KEY"]="AKIA[0-9A-Z]{16}"
    ["PRIVATE_KEY"]="-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"
    ["PASSWORD"]="password\s*=\s*['\"][^'\"]{8,}['\"]"
    ["API_KEY"]="api[_-]?key\s*[:=]\s*['\"][^'\"]{20,}['\"]"
    ["SECRET"]="secret[_-]?key\s*[:=]\s*['\"][^'\"]{20,}['\"]"
    ["TOKEN"]="[a-zA-Z0-9]{32,}"
    ["PEM_FILE"]="\.pem$"
)

# Allowed patterns (won't trigger alerts)
ALLOWED_PATTERNS=(
    "\.env\.example"
    "\.env\.template"
    "example\.env"
)

# Files to check
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)

# If no files staged, exit
if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

echo -e "${GREEN}🔒 Running secret detection...${NC}"

# Track if we found any secrets
FOUND_SECRETS=0

# Check each staged file
for FILE in $STAGED_FILES; do
    # Skip allowed patterns
    SKIP=0
    for ALLOWED in "${ALLOWED_PATTERNS[@]}"; do
        if echo "$FILE" | grep -qE "$ALLOWED"; then
            SKIP=1
            break
        fi
    done

    if [ $SKIP -eq 1 ]; then
        continue
    fi

    # Skip binary files
    if file "$FILE" | grep -q "binary"; then
        continue
    fi

    # Skip if file doesn't exist (deleted)
    if [ ! -f "$FILE" ]; then
        continue
    fi

    # Check for .env files (except allowed ones)
    if echo "$FILE" | grep -qE "\.env$"; then
        echo -e "${RED}❌ Blocked: .env file detected${NC}"
        echo "   File: $FILE"
        echo "   Reason: .env files should not be committed"
        echo "   Fix: Add to .gitignore or rename to .env.example"
        echo ""
        FOUND_SECRETS=1
        continue
    fi

    # Check content for secret patterns
    CONTENT=$(git show ":$FILE")

    for PATTERN_NAME in "${!PATTERNS[@]}"; do
        PATTERN="${PATTERNS[$PATTERN_NAME]}"

        if echo "$CONTENT" | grep -qiE "$PATTERN"; then
            # Extract matching lines
            MATCHES=$(echo "$CONTENT" | grep -niE "$PATTERN" | head -3)

            echo -e "${RED}❌ Potential secret detected: $PATTERN_NAME${NC}"
            echo "   File: $FILE"
            echo "   Pattern: $PATTERN"
            echo "   Matches:"
            echo "$MATCHES" | while IFS= read -r line; do
                echo "      $line"
            done
            echo ""

            FOUND_SECRETS=1
        fi
    done
done

# If secrets found, block commit
if [ $FOUND_SECRETS -eq 1 ]; then
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}🚫 COMMIT BLOCKED - Secrets detected${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "To fix:"
    echo "  1. Remove sensitive data from the files"
    echo "  2. Use environment variables or .env files (gitignored)"
    echo "  3. If false positive, add pattern to ALLOWED_PATTERNS in this script"
    echo ""
    echo "To bypass this check (NOT RECOMMENDED):"
    echo "  git commit --no-verify"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ No secrets detected${NC}"
exit 0
