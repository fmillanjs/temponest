#!/bin/bash
# TempoNest - Quick Start Script
# Run this to get started with the platform

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

clear
echo -e "${BLUE}"
cat << "EOF"
 _____ _____ __  __ ____   ___  _   _ _____ ____ _____
|_   _| ____|  \/  |  _ \ / _ \| \ | | ____/ ___|_   _|
  | | |  _| | |\/| | |_) | | | |  \| |  _| \___ \ | |
  | | | |___| |  | |  __/| |_| | |\  | |___ ___) || |
  |_| |_____|_|  |_|_|    \___/|_| \_|_____|____/ |_|

        AI Agent Platform for Rapid Development
EOF
echo -e "${NC}"

echo ""
echo -e "${YELLOW}Checking system status...${NC}"
echo ""

# Check Docker containers
CONTAINER_COUNT=$(docker ps --filter "name=agentic" --format "{{.Names}}" 2>/dev/null | wc -l)

if [ "$CONTAINER_COUNT" -lt 10 ]; then
    echo -e "${RED}⚠ Warning: Only $CONTAINER_COUNT containers running (expected 17+)${NC}"
    echo ""
    echo "Would you like to start the services? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Starting services..."
        cd /home/doctor/temponest/docker
        docker-compose up -d
        echo "Waiting for services to be healthy (30 seconds)..."
        sleep 30
    fi
else
    echo -e "${GREEN}✓ Services running: $CONTAINER_COUNT containers${NC}"
fi

# Check agent service health
AGENT_HEALTH=$(curl -s http://localhost:9000/health 2>/dev/null | jq -r '.status // "unknown"')

if [ "$AGENT_HEALTH" == "healthy" ]; then
    echo -e "${GREEN}✓ Agent service: healthy${NC}"

    # Count ready agents
    READY_AGENTS=$(curl -s http://localhost:9000/health 2>/dev/null | jq -r '.services | to_entries[] | select(.value=="ready") | .key' | wc -l)
    echo -e "${GREEN}✓ Agents ready: $READY_AGENTS/7${NC}"
else
    echo -e "${YELLOW}⚠ Agent service: $AGENT_HEALTH${NC}"
fi

echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  What would you like to do?${NC}"
echo -e "${BLUE}================================${NC}"
echo ""
echo "1) Run quick demo (test all agents)"
echo "2) Read the user guide"
echo "3) Open web dashboards"
echo "4) Check detailed system status"
echo "5) Exit"
echo ""
echo -n "Enter choice [1-5]: "
read -r choice

case $choice in
    1)
        echo ""
        echo -e "${YELLOW}Running quick demo...${NC}"
        echo ""
        /home/doctor/temponest/quick-demo.sh
        ;;
    2)
        echo ""
        echo -e "${YELLOW}Opening user guide...${NC}"
        echo ""
        less /home/doctor/temponest/HOW-TO-USE.md
        ;;
    3)
        echo ""
        echo -e "${YELLOW}Available dashboards:${NC}"
        echo ""
        echo "Web UI:        http://localhost:8082"
        echo "Grafana:       http://localhost:3003 (admin/admin)"
        echo "Langfuse:      http://localhost:3001"
        echo "Temporal:      http://localhost:8080"
        echo "Qdrant:        http://localhost:6333/dashboard"
        echo "Prometheus:    http://localhost:9091"
        echo ""
        ;;
    4)
        echo ""
        echo -e "${YELLOW}Detailed system status:${NC}"
        echo ""
        curl -s http://localhost:9000/health | jq '.'
        echo ""
        echo -e "${YELLOW}Docker containers:${NC}"
        docker ps --filter "name=agentic" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -20
        ;;
    5)
        echo ""
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo ""
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${GREEN}Quick Reference:${NC}"
echo -e "${BLUE}================================${NC}"
echo ""
echo "Full guide:        cat ~/temponest/HOW-TO-USE.md"
echo "Run demo:          ~/temponest/quick-demo.sh"
echo "CLI tool:          ~/temponest/cli/agentic-cli.sh status"
echo "Web UI:            http://localhost:8082"
echo "Grafana:           http://localhost:3003"
echo ""
echo -e "${YELLOW}Pro tip: Create an alias for easy access:${NC}"
echo "  alias agentic='/home/doctor/temponest/cli/agentic-cli.sh'"
echo ""
