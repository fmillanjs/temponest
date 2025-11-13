#!/bin/bash

###############################################################################
# K6 Load Test Runner for TempoNest
#
# Runs all K6 performance tests and generates comprehensive reports
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORTS_DIR="${SCRIPT_DIR}/../reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Test configuration
AUTH_URL="${AUTH_URL:-http://localhost:9002}"
AGENTS_URL="${AGENTS_URL:-http://localhost:9000}"
VUS="${VUS:-50}"
DURATION="${DURATION:-3m}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TempoNest K6 Load Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Timestamp: ${TIMESTAMP}"
echo -e "Auth URL: ${AUTH_URL}"
echo -e "Agents URL: ${AGENTS_URL}"
echo -e "VUs: ${VUS}"
echo -e "Duration: ${DURATION}"
echo ""

# Create reports directory
mkdir -p "${REPORTS_DIR}"

# Check if k6 is installed
if ! command -v k6 &> /dev/null; then
    echo -e "${RED}Error: k6 is not installed${NC}"
    echo "Please install k6: https://k6.io/docs/getting-started/installation/"
    exit 1
fi

# Check if services are running
echo -e "${YELLOW}Checking if services are running...${NC}"
if ! curl -f -s "${AUTH_URL}/health" > /dev/null 2>&1; then
    echo -e "${RED}Error: Auth service is not responding at ${AUTH_URL}${NC}"
    echo "Please start Docker containers: docker-compose up -d"
    exit 1
fi

if ! curl -f -s "${AGENTS_URL}/health" > /dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Agents service is not responding at ${AGENTS_URL}${NC}"
    echo "Some tests may fail. Continuing anyway..."
fi

echo -e "${GREEN}Services are running${NC}"
echo ""

# Function to run a test
run_test() {
    local test_name=$1
    local test_file=$2
    local report_prefix=$3

    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Running: ${test_name}${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    local json_report="${REPORTS_DIR}/${report_prefix}_${TIMESTAMP}.json"
    local summary_report="${REPORTS_DIR}/${report_prefix}_${TIMESTAMP}_summary.txt"

    # Run k6 test
    if k6 run "${test_file}" \
        -e BASE_URL="${AUTH_URL}" \
        -e AUTH_URL="${AUTH_URL}" \
        -e AGENTS_URL="${AGENTS_URL}" \
        --out "json=${json_report}" \
        2>&1 | tee "${summary_report}"; then
        echo -e "${GREEN}✓ ${test_name} completed successfully${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}✗ ${test_name} failed${NC}"
        echo ""
        return 1
    fi
}

# Track results
total_tests=0
passed_tests=0
failed_tests=0

# Test 1: Auth API
total_tests=$((total_tests + 1))
if run_test "Auth API Load Test" "${SCRIPT_DIR}/auth-api.js" "k6-auth"; then
    passed_tests=$((passed_tests + 1))
else
    failed_tests=$((failed_tests + 1))
fi

sleep 5  # Brief pause between tests

# Test 2: Agents API
total_tests=$((total_tests + 1))
if run_test "Agents API Load Test" "${SCRIPT_DIR}/agents-api.js" "k6-agents"; then
    passed_tests=$((passed_tests + 1))
else
    failed_tests=$((failed_tests + 1))
fi

# Generate summary report
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Total Tests: ${total_tests}"
echo -e "${GREEN}Passed: ${passed_tests}${NC}"
if [ ${failed_tests} -gt 0 ]; then
    echo -e "${RED}Failed: ${failed_tests}${NC}"
else
    echo -e "Failed: ${failed_tests}"
fi
echo ""
echo -e "Reports saved to: ${REPORTS_DIR}"
echo -e "Timestamp: ${TIMESTAMP}"
echo ""

# Create consolidated report
CONSOLIDATED_REPORT="${REPORTS_DIR}/k6-consolidated-${TIMESTAMP}.txt"
{
    echo "========================================="
    echo "TempoNest K6 Load Test Results"
    echo "========================================="
    echo ""
    echo "Timestamp: ${TIMESTAMP}"
    echo "Auth URL: ${AUTH_URL}"
    echo "Agents URL: ${AGENTS_URL}"
    echo ""
    echo "Test Results:"
    echo "  Total: ${total_tests}"
    echo "  Passed: ${passed_tests}"
    echo "  Failed: ${failed_tests}"
    echo ""
    echo "Individual Test Reports:"
    echo ""

    for report in "${REPORTS_DIR}"/*_${TIMESTAMP}_summary.txt; do
        if [ -f "$report" ]; then
            echo "----------------------------------------"
            echo "Report: $(basename "$report")"
            echo "----------------------------------------"
            cat "$report"
            echo ""
        fi
    done
} > "${CONSOLIDATED_REPORT}"

echo -e "${GREEN}Consolidated report: ${CONSOLIDATED_REPORT}${NC}"
echo ""

# Exit with appropriate code
if [ ${failed_tests} -gt 0 ]; then
    echo -e "${RED}Some tests failed. Please review the reports.${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed successfully!${NC}"
    exit 0
fi
