#!/bin/bash

###############################################################################
# Docker Container Startup Time Measurement
#
# Measures startup times, resource usage, and health check times for all
# TempoNest Docker containers
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
REPORTS_DIR="${SCRIPT_DIR}/../reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="${REPORTS_DIR}/docker-startup-${TIMESTAMP}.json"

# Create reports directory
mkdir -p "${REPORTS_DIR}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Docker Startup Time Measurement${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Project Root: ${PROJECT_ROOT}"
echo "Results File: ${RESULTS_FILE}"
echo "Timestamp: ${TIMESTAMP}"
echo ""

# Change to project root
cd "${PROJECT_ROOT}"

# Function to measure time
measure_time() {
    local start=$1
    local end=$2
    echo $(awk "BEGIN {print $end - $start}")
}

# Function to wait for container health
wait_for_health() {
    local container=$1
    local timeout=${2:-120}  # Default 120 seconds
    local start_time=$(date +%s)
    local health_start=$(date +%s.%N)

    echo -e "${YELLOW}Waiting for ${container} to be healthy...${NC}"

    while true; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))

        if [ $elapsed -gt $timeout ]; then
            echo -e "${RED}✗ Timeout waiting for ${container}${NC}"
            return 1
        fi

        local health=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "none")

        if [ "$health" == "healthy" ]; then
            local health_end=$(date +%s.%N)
            local health_time=$(measure_time $health_start $health_end)
            echo -e "${GREEN}✓ ${container} is healthy (${health_time}s)${NC}"
            echo "$health_time"
            return 0
        elif [ "$health" == "none" ]; then
            # No health check defined, check if running
            local status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "")
            if [ "$status" == "running" ]; then
                local health_end=$(date +%s.%N)
                local health_time=$(measure_time $health_start $health_end)
                echo -e "${GREEN}✓ ${container} is running (${health_time}s)${NC}"
                echo "$health_time"
                return 0
            fi
        fi

        sleep 2
    done
}

# Function to get container stats
get_container_stats() {
    local container=$1

    local cpu=$(docker stats --no-stream --format "{{.CPUPerc}}" "$container" | sed 's/%//')
    local mem=$(docker stats --no-stream --format "{{.MemUsage}}" "$container" | awk '{print $1}')
    local net=$(docker stats --no-stream --format "{{.NetIO}}" "$container")

    echo "{\"cpu\":\"$cpu\",\"memory\":\"$mem\",\"network\":\"$net\"}"
}

# Function to get container size
get_container_size() {
    local container=$1
    docker inspect --format='{{.SizeRw}}' "$container" 2>/dev/null || echo "0"
}

# Function to get image size
get_image_size() {
    local image=$1
    docker images --format "{{.Size}}" "$image" | head -1 || echo "0"
}

echo -e "${YELLOW}Stopping all containers...${NC}"
docker-compose down
sleep 5

echo -e "${YELLOW}Removing volumes (optional, for clean start)...${NC}"
# Uncomment to remove volumes for truly clean start
# docker-compose down -v

echo ""
echo -e "${BLUE}Starting containers and measuring startup times...${NC}"
echo ""

# Start time
GLOBAL_START=$(date +%s.%N)

# Start containers
echo -e "${YELLOW}Running docker-compose up -d...${NC}"
COMPOSE_START=$(date +%s.%N)
docker-compose up -d
COMPOSE_END=$(date +%s.%N)
COMPOSE_TIME=$(measure_time $COMPOSE_START $COMPOSE_END)

echo -e "${GREEN}✓ docker-compose up completed in ${COMPOSE_TIME}s${NC}"
echo ""

# Wait a moment for containers to start
sleep 3

# Get list of containers
CONTAINERS=$(docker-compose ps --services)

echo -e "${BLUE}Measuring individual container startup times...${NC}"
echo ""

# Initialize JSON results
echo "{" > "$RESULTS_FILE"
echo "  \"timestamp\": \"$(date -Iseconds)\"," >> "$RESULTS_FILE"
echo "  \"compose_time\": $COMPOSE_TIME," >> "$RESULTS_FILE"
echo "  \"containers\": {" >> "$RESULTS_FILE"

FIRST=true
TOTAL_HEALTH_TIME=0
HEALTHY_COUNT=0

for container in $CONTAINERS; do
    # Get full container name
    FULL_NAME=$(docker-compose ps -q "$container" | xargs docker inspect --format='{{.Name}}' | sed 's/\///')

    if [ -z "$FULL_NAME" ]; then
        echo -e "${RED}✗ Container $container not found${NC}"
        continue
    fi

    echo -e "${BLUE}=== $container ($FULL_NAME) ===${NC}"

    # Add comma if not first entry
    if [ "$FIRST" = false ]; then
        echo "," >> "$RESULTS_FILE"
    fi
    FIRST=false

    # Get container start time
    CONTAINER_START=$(docker inspect --format='{{.State.StartedAt}}' "$FULL_NAME")
    CONTAINER_START_EPOCH=$(date -d "$CONTAINER_START" +%s 2>/dev/null || echo "0")

    # Wait for health
    HEALTH_TIME=$(wait_for_health "$FULL_NAME" 120) || HEALTH_TIME="timeout"

    if [ "$HEALTH_TIME" != "timeout" ]; then
        TOTAL_HEALTH_TIME=$(awk "BEGIN {print $TOTAL_HEALTH_TIME + $HEALTH_TIME}")
        HEALTHY_COUNT=$((HEALTHY_COUNT + 1))
    fi

    # Get resource stats
    STATS=$(get_container_stats "$FULL_NAME")

    # Get size info
    IMAGE=$(docker inspect --format='{{.Config.Image}}' "$FULL_NAME")
    IMAGE_SIZE=$(get_image_size "$IMAGE")

    # Write to JSON
    echo -n "    \"$container\": {" >> "$RESULTS_FILE"
    echo -n "\"name\":\"$FULL_NAME\"," >> "$RESULTS_FILE"
    echo -n "\"image\":\"$IMAGE\"," >> "$RESULTS_FILE"
    echo -n "\"image_size\":\"$IMAGE_SIZE\"," >> "$RESULTS_FILE"
    echo -n "\"health_time\":\"$HEALTH_TIME\"," >> "$RESULTS_FILE"
    echo -n "\"stats\":$STATS" >> "$RESULTS_FILE"
    echo -n "}" >> "$RESULTS_FILE"

    echo ""
done

# Close JSON
echo "" >> "$RESULTS_FILE"
echo "  }," >> "$RESULTS_FILE"

# Calculate total time
GLOBAL_END=$(date +%s.%N)
TOTAL_TIME=$(measure_time $GLOBAL_START $GLOBAL_END)

# Calculate average health time
if [ $HEALTHY_COUNT -gt 0 ]; then
    AVG_HEALTH_TIME=$(awk "BEGIN {print $TOTAL_HEALTH_TIME / $HEALTHY_COUNT}")
else
    AVG_HEALTH_TIME=0
fi

echo "  \"summary\": {" >> "$RESULTS_FILE"
echo "    \"total_time\": $TOTAL_TIME," >> "$RESULTS_FILE"
echo "    \"compose_time\": $COMPOSE_TIME," >> "$RESULTS_FILE"
echo "    \"total_health_time\": $TOTAL_HEALTH_TIME," >> "$RESULTS_FILE"
echo "    \"average_health_time\": $AVG_HEALTH_TIME," >> "$RESULTS_FILE"
echo "    \"healthy_containers\": $HEALTHY_COUNT," >> "$RESULTS_FILE"
echo "    \"total_containers\": $(echo "$CONTAINERS" | wc -l)" >> "$RESULTS_FILE"
echo "  }" >> "$RESULTS_FILE"
echo "}" >> "$RESULTS_FILE"

# Print summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Total Startup Time:     ${GREEN}${TOTAL_TIME}s${NC}"
echo -e "Docker Compose Time:    ${GREEN}${COMPOSE_TIME}s${NC}"
echo -e "Total Health Time:      ${GREEN}${TOTAL_HEALTH_TIME}s${NC}"
echo -e "Average Health Time:    ${GREEN}${AVG_HEALTH_TIME}s${NC}"
echo -e "Healthy Containers:     ${GREEN}${HEALTHY_COUNT}${NC}"
echo -e "Total Containers:       $(echo "$CONTAINERS" | wc -l)"
echo ""
echo -e "${GREEN}✓ Results saved to: ${RESULTS_FILE}${NC}"
echo ""

# Generate human-readable report
READABLE_REPORT="${REPORTS_DIR}/docker-startup-${TIMESTAMP}.txt"
{
    echo "========================================="
    echo "Docker Startup Performance Report"
    echo "========================================="
    echo ""
    echo "Timestamp: $(date)"
    echo ""
    echo "Summary"
    echo "-------"
    echo "Total Startup Time:     ${TOTAL_TIME}s"
    echo "Docker Compose Time:    ${COMPOSE_TIME}s"
    echo "Total Health Time:      ${TOTAL_HEALTH_TIME}s"
    echo "Average Health Time:    ${AVG_HEALTH_TIME}s"
    echo "Healthy Containers:     ${HEALTHY_COUNT}"
    echo "Total Containers:       $(echo "$CONTAINERS" | wc -l)"
    echo ""
    echo "Container Details"
    echo "-----------------"
    echo ""

    # Parse JSON and print details
    for container in $CONTAINERS; do
        FULL_NAME=$(docker-compose ps -q "$container" 2>/dev/null | xargs docker inspect --format='{{.Name}}' 2>/dev/null | sed 's/\///' || echo "")
        if [ -n "$FULL_NAME" ]; then
            IMAGE=$(docker inspect --format='{{.Config.Image}}' "$FULL_NAME" 2>/dev/null || echo "unknown")
            IMAGE_SIZE=$(get_image_size "$IMAGE")
            HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "$FULL_NAME" 2>/dev/null || echo "none")

            echo "$container ($FULL_NAME)"
            echo "  Image: $IMAGE"
            echo "  Image Size: $IMAGE_SIZE"
            echo "  Health: $HEALTH"
            echo ""
        fi
    done

    echo "Full JSON results: ${RESULTS_FILE}"
} > "$READABLE_REPORT"

echo -e "${GREEN}✓ Readable report: ${READABLE_REPORT}${NC}"
echo ""

# Optionally show docker stats
echo -e "${YELLOW}Current container resource usage:${NC}"
docker stats --no-stream

echo ""
echo -e "${GREEN}✓ Measurement complete!${NC}"
