#!/bin/bash
# Verify RAG Health
# Checks Qdrant collection status and tests retrieval

set -e

echo "========================================="
echo "RAG Health Check"
echo "========================================="
echo ""

# 1. Check Qdrant connectivity
echo "1. Checking Qdrant connection..."
if curl -s http://localhost:6333/health > /dev/null; then
    echo "   ✅ Qdrant is healthy"
else
    echo "   ❌ Qdrant is not accessible"
    exit 1
fi
echo ""

# 2. Check collection existence
echo "2. Checking collection 'agentic_knowledge'..."
COLLECTION_INFO=$(curl -s http://localhost:6333/collections/agentic_knowledge)
if echo "$COLLECTION_INFO" | jq -e '.result' > /dev/null 2>&1; then
    echo "   ✅ Collection exists"

    POINTS_COUNT=$(echo "$COLLECTION_INFO" | jq -r '.result.points_count')
    VECTORS_COUNT=$(echo "$COLLECTION_INFO" | jq -r '.result.vectors_count')

    echo "   📊 Vectors: $POINTS_COUNT"
    echo "   📊 Total vectors: $VECTORS_COUNT"
else
    echo "   ❌ Collection not found"
    exit 1
fi
echo ""

# 3. Check minimum vector count
echo "3. Checking minimum vector requirement..."
if [ "$POINTS_COUNT" -lt 100 ]; then
    echo "   ⚠️  Warning: Only $POINTS_COUNT vectors (expected 100+)"
    echo "      Run: ./setup-knowledge-base.sh to ingest documents"
else
    echo "   ✅ Sufficient vectors ($POINTS_COUNT >= 100)"
fi
echo ""

# 4. Check ingestion service
echo "4. Checking ingestion service..."
if docker ps | grep -q "agentic-ingestion"; then
    echo "   ✅ Ingestion service is running"

    # Check recent logs
    RECENT_ERRORS=$(docker logs agentic-ingestion --tail 50 | grep -i "error" | wc -l)
    if [ "$RECENT_ERRORS" -gt 0 ]; then
        echo "   ⚠️  Warning: $RECENT_ERRORS errors in recent logs"
        echo "      Check with: docker logs agentic-ingestion --tail 50"
    else
        echo "   ✅ No recent errors in ingestion logs"
    fi
else
    echo "   ❌ Ingestion service is not running"
    echo "      Start with: docker-compose up -d ingestion"
fi
echo ""

# 5. Test agent citation requirement
echo "5. Testing agent citation requirements..."
if curl -s http://localhost:9000/health > /dev/null 2>&1; then
    echo "   ✅ Agents service is running"

    # Check if REQUIRE_CITATIONS is enabled
    REQUIRE_CITATIONS=$(grep "REQUIRE_CITATIONS" docker/.env | cut -d'=' -f2)
    if [ "$REQUIRE_CITATIONS" = "true" ]; then
        if [ "$POINTS_COUNT" -lt 100 ]; then
            echo "   ⚠️  Warning: REQUIRE_CITATIONS=true but only $POINTS_COUNT vectors"
            echo "      Agents may fail! Add more documents or set REQUIRE_CITATIONS=false"
        else
            echo "   ✅ Citations enabled with sufficient vectors"
        fi
    else
        echo "   ℹ️  Citations are disabled (REQUIRE_CITATIONS=false)"
    fi
else
    echo "   ❌ Agents service is not accessible"
fi
echo ""

# Summary
echo "========================================="
echo "Health Check Summary"
echo "========================================="
echo "Qdrant: $(curl -s http://localhost:6333/health > /dev/null && echo "✅ Healthy" || echo "❌ Down")"
echo "Collection: $([ "$POINTS_COUNT" -gt 0 ] && echo "✅ $POINTS_COUNT vectors" || echo "❌ Empty")"
echo "Ingestion: $(docker ps | grep -q "agentic-ingestion" && echo "✅ Running" || echo "❌ Stopped")"
echo "Agents: $(curl -s http://localhost:9000/health > /dev/null && echo "✅ Running" || echo "❌ Stopped")"
echo ""

if [ "$POINTS_COUNT" -ge 100 ] && docker ps | grep -q "agentic-ingestion"; then
    echo "✅ RAG system is healthy and ready!"
else
    echo "⚠️  RAG system needs attention (see warnings above)"
fi
echo "========================================="
