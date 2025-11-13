#!/bin/bash
# Rolling deployment script with zero downtime
# Usage: ./rolling-deploy.sh --service <service> --image <image> --environment <env>

set -e

# Default values
HEALTH_CHECK_TIMEOUT=300
HEALTH_CHECK_INTERVAL=5
MAX_RETRIES=3

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --service)
      SERVICE="$2"
      shift 2
      ;;
    --image)
      IMAGE="$2"
      shift 2
      ;;
    --environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --health-check-timeout)
      HEALTH_CHECK_TIMEOUT="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate required arguments
if [ -z "$SERVICE" ] || [ -z "$IMAGE" ] || [ -z "$ENVIRONMENT" ]; then
  echo "Usage: $0 --service <service> --image <image> --environment <env>"
  exit 1
fi

echo "================================================"
echo "Rolling Deployment - $SERVICE"
echo "================================================"
echo "Environment: $ENVIRONMENT"
echo "Image: $IMAGE"
echo "Health Check Timeout: ${HEALTH_CHECK_TIMEOUT}s"
echo "================================================"

# Load environment-specific configuration
COMPOSE_FILE="docker/docker-compose.${ENVIRONMENT}.yml"
if [ ! -f "$COMPOSE_FILE" ]; then
  echo "Error: Compose file not found: $COMPOSE_FILE"
  exit 1
fi

# Backup current deployment
echo "📦 Backing up current deployment..."
docker compose -f "$COMPOSE_FILE" ps "$SERVICE" > ".deploy-backup-${SERVICE}.txt" 2>&1 || true
docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE" env | grep -v PASSWORD > ".deploy-env-${SERVICE}.txt" 2>&1 || true

# Pull new image
echo "🔄 Pulling new image: $IMAGE"
docker pull "$IMAGE"

# Tag image for deployment
docker tag "$IMAGE" "temponest-${SERVICE}:latest"

# Scale up with new version (blue-green approach)
echo "🚀 Starting new container with updated image..."
export SERVICE_IMAGE="$IMAGE"

# Update the service with new image
docker compose -f "$COMPOSE_FILE" up -d --no-deps --scale "${SERVICE}=2" "$SERVICE"

# Wait for new container to be healthy
echo "🏥 Waiting for new container to pass health checks..."
ELAPSED=0
HEALTHY=false

while [ $ELAPSED -lt $HEALTH_CHECK_TIMEOUT ]; do
  # Get the newest container
  NEW_CONTAINER=$(docker compose -f "$COMPOSE_FILE" ps -q "$SERVICE" | head -n 1)

  if [ -n "$NEW_CONTAINER" ]; then
    # Check if container is running
    STATUS=$(docker inspect --format='{{.State.Status}}' "$NEW_CONTAINER" 2>/dev/null || echo "not_found")

    if [ "$STATUS" = "running" ]; then
      # Check health endpoint if service has one
      HEALTH_URL="http://localhost:$(docker port "$NEW_CONTAINER" | grep -oP '\\d+$' | head -n 1)/health"

      if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
        echo "✅ New container is healthy!"
        HEALTHY=true
        break
      fi
    fi
  fi

  echo "⏳ Waiting... ($ELAPSED/${HEALTH_CHECK_TIMEOUT}s)"
  sleep $HEALTH_CHECK_INTERVAL
  ELAPSED=$((ELAPSED + HEALTH_CHECK_INTERVAL))
done

if [ "$HEALTHY" = false ]; then
  echo "❌ Health check failed after ${HEALTH_CHECK_TIMEOUT}s"
  echo "🔄 Rolling back..."

  # Remove the failed new container
  docker compose -f "$COMPOSE_FILE" up -d --no-deps --scale "${SERVICE}=1" "$SERVICE"

  # Restore from backup
  docker compose -f "$COMPOSE_FILE" up -d --no-deps "$SERVICE"

  echo "❌ Deployment failed and rolled back"
  exit 1
fi

# New container is healthy, remove old container
echo "🔄 Scaling down old container..."
docker compose -f "$COMPOSE_FILE" up -d --no-deps --scale "${SERVICE}=1" "$SERVICE"

# Verify final state
echo "🔍 Verifying deployment..."
sleep 5

FINAL_CONTAINER=$(docker compose -f "$COMPOSE_FILE" ps -q "$SERVICE")
FINAL_IMAGE=$(docker inspect --format='{{.Config.Image}}' "$FINAL_CONTAINER")

if [[ "$FINAL_IMAGE" == *"$IMAGE"* ]] || [[ "$FINAL_IMAGE" == "temponest-${SERVICE}:latest" ]]; then
  echo "✅ Deployment successful!"
  echo "Container: $FINAL_CONTAINER"
  echo "Image: $FINAL_IMAGE"

  # Cleanup backup files
  rm -f ".deploy-backup-${SERVICE}.txt" ".deploy-env-${SERVICE}.txt"

  exit 0
else
  echo "⚠️  Warning: Image mismatch detected"
  echo "Expected: $IMAGE"
  echo "Got: $FINAL_IMAGE"
  exit 1
fi
