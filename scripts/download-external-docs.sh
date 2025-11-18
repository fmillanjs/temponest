#!/bin/bash
# Download External Documentation
# Fetches documentation from public sources (FastAPI, React, etc.)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMP_DIR="/tmp/temponest-docs-download"
DOCS_DIR="$(cd "$SCRIPT_DIR/../docker/documents/external" && pwd)"

echo "========================================="
echo "Download External Documentation"
echo "========================================="
echo ""

# Create temp directory
mkdir -p "$TEMP_DIR"
mkdir -p "$DOCS_DIR"

echo "📥 Downloading documentation sources..."
echo ""

# 1. FastAPI Documentation (markdown files from repo)
echo "1. FastAPI Documentation..."
if [ -d "$TEMP_DIR/fastapi" ]; then
    cd "$TEMP_DIR/fastapi" && git pull
else
    git clone --depth 1 https://github.com/tiangolo/fastapi.git "$TEMP_DIR/fastapi"
fi
# Copy markdown docs
find "$TEMP_DIR/fastapi/docs" -name "*.md" -exec cp {} "$DOCS_DIR/" \; 2>/dev/null || true
echo "   ✅ FastAPI docs copied"

# 2. React Documentation
echo "2. React Documentation..."
if [ -d "$TEMP_DIR/react" ]; then
    cd "$TEMP_DIR/react" && git pull
else
    git clone --depth 1 https://github.com/reactjs/react.dev.git "$TEMP_DIR/react"
fi
find "$TEMP_DIR/react/src/content" -name "*.md" -exec cp {} "$DOCS_DIR/" \; 2>/dev/null || true
echo "   ✅ React docs copied"

# 3. OWASP Top 10 (download markdown version)
echo "3. OWASP Top 10..."
curl -sL https://raw.githubusercontent.com/OWASP/Top10/master/2021/docs/index.md -o "$DOCS_DIR/owasp-top-10.md"
echo "   ✅ OWASP Top 10 downloaded"

# 4. pytest Documentation
echo "4. pytest Documentation..."
if [ -d "$TEMP_DIR/pytest" ]; then
    cd "$TEMP_DIR/pytest" && git pull
else
    git clone --depth 1 https://github.com/pytest-dev/pytest.git "$TEMP_DIR/pytest"
fi
find "$TEMP_DIR/pytest/doc" -name "*.rst" -o -name "*.md" | head -20 | xargs -I {} cp {} "$DOCS_DIR/" 2>/dev/null || true
echo "   ✅ pytest docs copied"

echo ""
echo "========================================="
echo "Download Complete"
echo "========================================="

DOC_COUNT=$(find "$DOCS_DIR" -type f | wc -l)
echo "📚 Total external documents: $DOC_COUNT"
echo "📁 Location: $DOCS_DIR"
echo ""
echo "Next: Run ./setup-knowledge-base.sh to ingest these documents"
echo "========================================="
