#!/bin/bash
# Update Knowledge Base
# Re-downloads external docs and triggers re-ingestion

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================="
echo "Update Knowledge Base"
echo "========================================="
echo ""

# Download latest external docs
echo "1. Downloading latest external documentation..."
"$SCRIPT_DIR/download-external-docs.sh"
echo ""

# Trigger re-ingestion by restarting ingestion service
echo "2. Restarting ingestion service..."
docker-compose restart ingestion
echo "   ✅ Ingestion service restarted"
echo ""

# Wait for processing
echo "3. Waiting for ingestion to process new files..."
sleep 30

# Verify
echo "4. Verifying collection size..."
SIZE=$(curl -s http://localhost:6333/collections/agentic_knowledge | jq -r '.result.points_count')
echo "   📊 Current vectors: $SIZE"
echo ""

echo "========================================="
echo "Update Complete"
echo "========================================="
echo "Knowledge base has been updated with latest documentation"
echo ""
