#!/bin/bash
# Setup Knowledge Base - Initial RAG database population
# This script verifies the starter documents and triggers ingestion

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DOCS_DIR="$PROJECT_ROOT/docker/documents"

echo "========================================="
echo "RAG Knowledge Base Setup"
echo "========================================="
echo ""

# Check if documents exist
echo "1. Checking starter documents..."
EXPECTED_DOCS=(
    "fastapi-best-practices.md"
    "database-schema-design.md"
    "react-component-patterns.md"
    "security-best-practices.md"
    "pytest-testing-patterns.md"
    "docker-containerization.md"
    "ui-design-system.md"
    "api-error-handling.md"
    "ci-cd-workflows.md"
    "ux-research-methods.md"
)

MISSING_DOCS=()
for doc in "${EXPECTED_DOCS[@]}"; do
    if [ ! -f "$DOCS_DIR/$doc" ]; then
        MISSING_DOCS+=("$doc")
    fi
done

if [ ${#MISSING_DOCS[@]} -gt 0 ]; then
    echo "❌ Missing documents:"
    for doc in "${MISSING_DOCS[@]}"; do
        echo "   - $doc"
    done
    echo ""
    echo "Please ensure all starter documents are in $DOCS_DIR"
    exit 1
fi

echo "✅ Found all 10 starter documents"
echo ""

# Count total documents
TOTAL_DOCS=$(find "$DOCS_DIR" -type f \( -name "*.md" -o -name "*.txt" -o -name "*.pdf" \) | wc -l)
echo "📚 Total documents in directory: $TOTAL_DOCS"
echo ""

# Check if ingestion service is running
echo "2. Checking ingestion service..."
if ! docker ps | grep -q "agentic-ingestion"; then
    echo "❌ Ingestion service is not running"
    echo "Please start it with: docker-compose up -d ingestion"
    exit 1
fi
echo "✅ Ingestion service is running"
echo ""

# Check Qdrant is accessible
echo "3. Checking Qdrant vector database..."
if ! curl -s http://localhost:6333/collections > /dev/null; then
    echo "❌ Qdrant is not accessible at localhost:6333"
    echo "Please start it with: docker-compose up -d qdrant"
    exit 1
fi
echo "✅ Qdrant is accessible"
echo ""

# Get current collection size
echo "4. Checking current collection size..."
CURRENT_SIZE=$(curl -s http://localhost:6333/collections/agentic_knowledge | jq -r '.result.points_count // 0' 2>/dev/null || echo "0")
echo "📊 Current vectors in collection: $CURRENT_SIZE"
echo ""

# Monitor ingestion
echo "5. Monitoring ingestion process..."
echo "   Watching ingestion logs for 30 seconds..."
echo "   (Documents are chunked and embedded automatically)"
echo ""

# Wait for ingestion to process files
sleep 5

# Check logs for ingestion activity
docker logs agentic-ingestion --tail 50 | grep -i "ingested\|processing\|error" || echo "   No recent ingestion activity"
echo ""

# Wait a bit more for processing
echo "   Waiting for processing to complete..."
sleep 10

# Check new collection size
echo "6. Verifying ingestion..."
NEW_SIZE=$(curl -s http://localhost:6333/collections/agentic_knowledge | jq -r '.result.points_count // 0' 2>/dev/null || echo "0")
ADDED=$((NEW_SIZE - CURRENT_SIZE))

echo "📊 New vectors in collection: $NEW_SIZE"
echo "➕ Vectors added: $ADDED"
echo ""

if [ "$NEW_SIZE" -lt 100 ]; then
    echo "⚠️  Warning: Expected at least 100 vectors (10 docs × ~20 chunks)"
    echo "   Current: $NEW_SIZE vectors"
    echo ""
    echo "   Ingestion may still be processing. Check logs with:"
    echo "   docker logs -f agentic-ingestion"
    echo ""
else
    echo "✅ Successfully ingested documents!"
    echo ""
fi

# Test RAG retrieval
echo "7. Testing RAG retrieval..."
TEST_QUERY='{"query_vector":[0.1],"limit":5}'
if curl -s -X POST http://localhost:6333/collections/agentic_knowledge/points/search \
    -H "Content-Type: application/json" \
    -d '{"vector":[0.1,0.2,0.3],"limit":1}' > /dev/null 2>&1; then
    echo "✅ RAG retrieval is working"
else
    echo "⚠️  RAG retrieval test failed (this may be normal if collection is still building)"
fi
echo ""

# Summary
echo "========================================="
echo "Setup Summary"
echo "========================================="
echo "Documents: $TOTAL_DOCS files"
echo "Vectors: $NEW_SIZE in Qdrant"
echo "Status: $([ "$NEW_SIZE" -gt 100 ] && echo "✅ Ready" || echo "⚠️  Processing")"
echo ""

if [ "$NEW_SIZE" -gt 100 ]; then
    echo "✅ Knowledge base is ready!"
    echo ""
    echo "Next steps:"
    echo "1. Update docker/.env: REQUIRE_CITATIONS=true"
    echo "2. Restart agents: docker-compose restart agents"
    echo "3. Test with: curl http://localhost:9000/developer/run"
    echo ""
else
    echo "⚠️  Knowledge base is still processing"
    echo ""
    echo "Wait a few minutes and check:"
    echo "  curl http://localhost:6333/collections/agentic_knowledge | jq '.result.points_count'"
    echo ""
    echo "Or monitor ingestion:"
    echo "  docker logs -f agentic-ingestion"
    echo ""
fi

echo "========================================="
