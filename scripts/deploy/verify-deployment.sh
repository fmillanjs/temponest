#!/bin/bash
# Verify deployment success
# Usage: ./verify-deployment.sh --service <service> --environment <env>

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
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate required arguments
if [ -z "$SERVICE" ] || [ -z "$ENVIRONMENT" ]; then
  echo "Usage: $0 --service <service> --environment <env>"
  exit 1
fi

echo "================================================"
echo "Verifying Deployment - $SERVICE"
echo "================================================"

COMPOSE_FILE="docker/docker-compose.${ENVIRONMENT}.yml"

# Check if service is running
echo "🔍 Checking if service is running..."
if ! docker compose -f "$COMPOSE_FILE" ps "$SERVICE" | grep -q "Up"; then
  echo "❌ Service is not running"
  exit 1
fi

# Get container ID
CONTAINER_ID=$(docker compose -f "$COMPOSE_FILE" ps -q "$SERVICE")
echo "✅ Service is running (Container: $CONTAINER_ID)"

# Check container health
echo "🏥 Checking container health..."
HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_ID" 2>/dev/null || echo "no_healthcheck")

if [ "$HEALTH_STATUS" = "healthy" ] || [ "$HEALTH_STATUS" = "no_healthcheck" ]; then
  echo "✅ Container health: $HEALTH_STATUS"
else
  echo "❌ Container health: $HEALTH_STATUS"
  exit 1
fi

# Check if service responds to health endpoint
echo "🌐 Checking health endpoint..."
SERVICE_PORT=$(docker port "$CONTAINER_ID" | grep -oP '\d+$' | head -n 1)

if [ -n "$SERVICE_PORT" ]; then
  HEALTH_URL="http://localhost:${SERVICE_PORT}/health"

  if curl -sf "$HEALTH_URL" -o /dev/null; then
    echo "✅ Health endpoint responding: $HEALTH_URL"
  else
    echo "⚠️  Health endpoint not responding: $HEALTH_URL"
  fi
else
  echo "⚠️  Could not determine service port"
fi

# Check container logs for errors
echo "📋 Checking recent logs for errors..."
ERROR_COUNT=$(docker logs "$CONTAINER_ID" --since 5m 2>&1 | grep -iE "error|exception|fatal" | wc -l)

if [ "$ERROR_COUNT" -gt 10 ]; then
  echo "⚠️  Found $ERROR_COUNT errors in recent logs"
  echo "Recent errors:"
  docker logs "$CONTAINER_ID" --since 5m 2>&1 | grep -iE "error|exception|fatal" | tail -5
else
  echo "✅ No significant errors in recent logs ($ERROR_COUNT errors)"
fi

# Check resource usage
echo "📊 Checking resource usage..."
STATS=$(docker stats "$CONTAINER_ID" --no-stream --format "CPU: {{.CPUPerc}} | Memory: {{.MemPerc}}")
echo "✅ Resource usage: $STATS"

echo "================================================"
echo "✅ Deployment verification passed!"
echo "================================================"
exit 0
