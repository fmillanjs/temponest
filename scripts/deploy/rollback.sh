#!/bin/bash
# Rollback to previous deployment
# Usage: ./rollback.sh --service <service> --environment <env>

set -e

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --service)
      SERVICE="$2"
      shift 2
      ;;
    --environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --to-version)
      VERSION="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate required arguments
if [ -z "$SERVICE" ] || [ -z "$ENVIRONMENT" ]; then
  echo "Usage: $0 --service <service> --environment <env> [--to-version <version>]"
  exit 1
fi

echo "================================================"
echo "Rolling Back - $SERVICE"
echo "================================================"
echo "Environment: $ENVIRONMENT"
echo "================================================"

COMPOSE_FILE="docker/docker-compose.${ENVIRONMENT}.yml"

# Get current image
CURRENT_CONTAINER=$(docker compose -f "$COMPOSE_FILE" ps -q "$SERVICE")
CURRENT_IMAGE=$(docker inspect --format='{{.Config.Image}}' "$CURRENT_CONTAINER" 2>/dev/null || echo "unknown")

echo "📦 Current image: $CURRENT_IMAGE"

# Find previous version
if [ -z "$VERSION" ]; then
  echo "🔍 Finding previous version..."

  # Get image history
  REGISTRY="ghcr.io"
  IMAGE_NAME="${REGISTRY}/${GITHUB_REPOSITORY_OWNER:-temponest}/temponest-${SERVICE}"

  # Get previous tag (assuming we tag with commit SHAs)
  PREVIOUS_TAG=$(git log --pretty=format:"%H" -n 2 | tail -1)
  PREVIOUS_IMAGE="${IMAGE_NAME}:${PREVIOUS_TAG}"

  echo "📦 Previous version: $PREVIOUS_IMAGE"
else
  PREVIOUS_IMAGE="${IMAGE_NAME}:${VERSION}"
  echo "📦 Rolling back to: $PREVIOUS_IMAGE"
fi

# Check if backup files exist
if [ -f ".deploy-backup-${SERVICE}.txt" ]; then
  echo "📋 Found backup deployment state"
  cat ".deploy-backup-${SERVICE}.txt"
fi

# Stop current container
echo "🛑 Stopping current container..."
docker compose -f "$COMPOSE_FILE" stop "$SERVICE"

# Pull previous image
echo "🔄 Pulling previous image..."
if docker pull "$PREVIOUS_IMAGE" 2>/dev/null; then
  echo "✅ Previous image pulled successfully"

  # Update compose to use previous image
  export SERVICE_IMAGE="$PREVIOUS_IMAGE"
else
  echo "⚠️  Could not pull previous image, using latest tagged version"

  # Use latest image instead
  docker compose -f "$COMPOSE_FILE" pull "$SERVICE"
fi

# Start service with previous version
echo "🚀 Starting service with previous version..."
docker compose -f "$COMPOSE_FILE" up -d "$SERVICE"

# Wait for service to be healthy
echo "⏳ Waiting for service to be healthy..."
sleep 10

# Verify rollback
ROLLBACK_CONTAINER=$(docker compose -f "$COMPOSE_FILE" ps -q "$SERVICE")
ROLLBACK_IMAGE=$(docker inspect --format='{{.Config.Image}}' "$ROLLBACK_CONTAINER")

echo "================================================"
echo "✅ Rollback completed!"
echo "Container: $ROLLBACK_CONTAINER"
echo "Image: $ROLLBACK_IMAGE"
echo "================================================"

# Check health
./scripts/deploy/health-check.sh --service "$SERVICE" --environment "$ENVIRONMENT" || true

exit 0
