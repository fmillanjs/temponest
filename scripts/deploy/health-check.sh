#!/bin/bash
# Health check script for deployed services
# Usage: ./health-check.sh --service <service> --environment <env> [--timeout <seconds>]

set -e

TIMEOUT=60
INTERVAL=5

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
    --timeout)
      TIMEOUT="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# If no service specified, check all services
if [ -z "$SERVICE" ]; then
  echo "================================================"
  echo "Health Check - All Services"
  echo "================================================"

  SERVICES=("agents" "auth" "scheduler" "approval_ui" "ingestion" "temporal_workers" "web_ui" "console")

  for svc in "${SERVICES[@]}"; do
    echo ""
    echo "Checking $svc..."
    $0 --service "$svc" --environment "$ENVIRONMENT" --timeout "$TIMEOUT" || true
  done

  exit 0
fi

# Validate required arguments
if [ -z "$ENVIRONMENT" ]; then
  echo "Usage: $0 --service <service> --environment <env> [--timeout <seconds>]"
  exit 1
fi

echo "================================================"
echo "Health Check - $SERVICE"
echo "================================================"

COMPOSE_FILE="docker/docker-compose.${ENVIRONMENT}.yml"

# Check if service exists
if ! docker compose -f "$COMPOSE_FILE" ps "$SERVICE" &>/dev/null; then
  echo "❌ Service not found: $SERVICE"
  exit 1
fi

# Get container ID
CONTAINER_ID=$(docker compose -f "$COMPOSE_FILE" ps -q "$SERVICE" 2>/dev/null)

if [ -z "$CONTAINER_ID" ]; then
  echo "❌ Service is not running"
  exit 1
fi

# Check if container is running
STATUS=$(docker inspect --format='{{.State.Status}}' "$CONTAINER_ID")
echo "📊 Container Status: $STATUS"

if [ "$STATUS" != "running" ]; then
  echo "❌ Container is not running"
  exit 1
fi

# Get service port
SERVICE_PORT=$(docker port "$CONTAINER_ID" 2>/dev/null | grep -oP '\d+$' | head -n 1)

if [ -z "$SERVICE_PORT" ]; then
  echo "⚠️  Could not determine service port"
  echo "✅ Container is running (no health endpoint available)"
  exit 0
fi

# Health check with retry
HEALTH_URL="http://localhost:${SERVICE_PORT}/health"
echo "🌐 Health URL: $HEALTH_URL"

ELAPSED=0
HEALTHY=false

while [ $ELAPSED -lt $TIMEOUT ]; do
  if HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null); then
    if [ "$HTTP_CODE" -eq 200 ]; then
      echo "✅ Service is healthy! (HTTP $HTTP_CODE)"
      HEALTHY=true
      break
    else
      echo "⏳ Waiting... HTTP $HTTP_CODE ($ELAPSED/${TIMEOUT}s)"
    fi
  else
    echo "⏳ Waiting... Connection failed ($ELAPSED/${TIMEOUT}s)"
  fi

  sleep $INTERVAL
  ELAPSED=$((ELAPSED + INTERVAL))
done

if [ "$HEALTHY" = false ]; then
  echo "❌ Health check failed after ${TIMEOUT}s"
  echo "Recent logs:"
  docker logs "$CONTAINER_ID" --tail 20
  exit 1
fi

# Additional checks
echo ""
echo "📊 Additional Health Metrics:"

# Check uptime
STARTED_AT=$(docker inspect --format='{{.State.StartedAt}}' "$CONTAINER_ID")
echo "  Started: $STARTED_AT"

# Check restart count
RESTART_COUNT=$(docker inspect --format='{{.RestartCount}}' "$CONTAINER_ID")
echo "  Restart Count: $RESTART_COUNT"

if [ "$RESTART_COUNT" -gt 3 ]; then
  echo "  ⚠️  Warning: High restart count!"
fi

# Check memory usage
MEM_USAGE=$(docker stats "$CONTAINER_ID" --no-stream --format "{{.MemPerc}}" | grep -oP '[\d.]+')
echo "  Memory Usage: ${MEM_USAGE}%"

if (( $(echo "$MEM_USAGE > 90" | bc -l) )); then
  echo "  ⚠️  Warning: High memory usage!"
fi

# Check CPU usage
CPU_USAGE=$(docker stats "$CONTAINER_ID" --no-stream --format "{{.CPUPerc}}" | grep -oP '[\d.]+')
echo "  CPU Usage: ${CPU_USAGE}%"

echo ""
echo "================================================"
echo "✅ Health check passed for $SERVICE"
echo "================================================"

exit 0
