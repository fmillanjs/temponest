#!/bin/bash
# Smoke tests after deployment
# Usage: ./smoke-tests.sh --environment <env>

set -e

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
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
if [ -z "$ENVIRONMENT" ]; then
  echo "Usage: $0 --environment <env>"
  exit 1
fi

echo "================================================"
echo "Smoke Tests - $ENVIRONMENT"
echo "================================================"

FAILED_TESTS=0
PASSED_TESTS=0

# Test helper functions
test_endpoint() {
  local name="$1"
  local url="$2"
  local expected_code="${3:-200}"

  echo -n "Testing $name... "

  if HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null); then
    if [ "$HTTP_CODE" -eq "$expected_code" ]; then
      echo "✅ PASS (HTTP $HTTP_CODE)"
      ((PASSED_TESTS++))
      return 0
    else
      echo "❌ FAIL (Expected HTTP $expected_code, got $HTTP_CODE)"
      ((FAILED_TESTS++))
      return 1
    fi
  else
    echo "❌ FAIL (Connection failed)"
    ((FAILED_TESTS++))
    return 1
  fi
}

test_service_health() {
  local service="$1"
  local port="$2"

  test_endpoint "$service health" "http://localhost:${port}/health"
}

echo ""
echo "🔍 Running smoke tests..."
echo ""

# Test core services
test_service_health "Auth Service" "8001"
test_service_health "Agents Service" "8000"
test_service_health "Scheduler Service" "8002"

# Test auth endpoints
test_endpoint "Auth Login (unauthenticated)" "http://localhost:8001/api/v1/auth/login" "401,405,422"

# Test agents endpoints
test_endpoint "Agents List" "http://localhost:8000/api/v1/agents" "401,200"

# Test web UI
test_endpoint "Web UI" "http://localhost:5001" "200"

# Test console
test_endpoint "Console" "http://localhost:3000" "200,307,308"

# Test database connectivity
echo ""
echo "🗄️  Testing database connectivity..."

if docker compose -f "docker/docker-compose.${ENVIRONMENT}.yml" exec -T postgres pg_isready -U postgres &>/dev/null; then
  echo "✅ PostgreSQL is ready"
  ((PASSED_TESTS++))
else
  echo "❌ PostgreSQL connection failed"
  ((FAILED_TESTS++))
fi

# Test Redis connectivity
echo ""
echo "💾 Testing Redis connectivity..."

if docker compose -f "docker/docker-compose.${ENVIRONMENT}.yml" exec -T redis redis-cli ping &>/dev/null; then
  echo "✅ Redis is ready"
  ((PASSED_TESTS++))
else
  echo "❌ Redis connection failed"
  ((FAILED_TESTS++))
fi

# Test Qdrant connectivity
echo ""
echo "🔍 Testing Qdrant connectivity..."

if curl -sf "http://localhost:6333/healthz" &>/dev/null; then
  echo "✅ Qdrant is ready"
  ((PASSED_TESTS++))
else
  echo "❌ Qdrant connection failed"
  ((FAILED_TESTS++))
fi

# Summary
echo ""
echo "================================================"
echo "Smoke Test Results"
echo "================================================"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "================================================"

if [ $FAILED_TESTS -gt 0 ]; then
  echo "❌ Some smoke tests failed"
  exit 1
else
  echo "✅ All smoke tests passed!"
  exit 0
fi
