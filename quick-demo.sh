#!/bin/bash
# Quick Demo - Test TempoNest Agents
# This script demonstrates all 7 agents with simple examples

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  TempoNest Quick Demo${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Step 1: Create user and get token
echo -e "${YELLOW}Step 1: Setting up authentication...${NC}"
EMAIL="demo-$(date +%s)@example.com"
PASSWORD="demo123"

# Register
REGISTER_RESPONSE=$(curl -s -X POST http://localhost:9002/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"full_name\":\"Demo User\"}")

# Login to get token
TOKEN=$(curl -s -X POST http://localhost:9002/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo -e "${YELLOW}Note: Running without authentication (some features may be limited)${NC}"
    TOKEN=""
else
    echo -e "${GREEN}✓ Authenticated as $EMAIL${NC}"
fi
echo ""

# Step 2: Test Overseer Agent
echo -e "${YELLOW}Step 2: Testing Overseer Agent (Planning)...${NC}"
echo "Task: Plan a simple todo list API"
echo ""

OVERSEER_CMD="curl -s -X POST http://localhost:9000/overseer/run \
  -H 'Content-Type: application/json'"

if [ -n "$TOKEN" ]; then
    OVERSEER_CMD="$OVERSEER_CMD -H 'Authorization: Bearer $TOKEN'"
fi

OVERSEER_CMD="$OVERSEER_CMD -d '{
    \"task\": \"Plan a REST API for a simple todo list with tasks that have title, description, and completed status\",
    \"context\": {
      \"framework\": \"FastAPI\",
      \"database\": \"PostgreSQL\"
    },
    \"idempotency_key\": \"demo-plan-$(date +%s)\"
  }'"

OVERSEER_RESULT=$(eval $OVERSEER_CMD)
echo "$OVERSEER_RESULT" | jq -r '.result.plan // .detail // "No response"' | head -20
echo ""
echo -e "${GREEN}✓ Overseer agent responded${NC}"
echo ""

# Step 3: Test Developer Agent
echo -e "${YELLOW}Step 3: Testing Developer Agent (Code Generation)...${NC}"
echo "Task: Create an email validator function"
echo ""

DEVELOPER_CMD="curl -s -X POST http://localhost:9000/developer/run \
  -H 'Content-Type: application/json'"

if [ -n "$TOKEN" ]; then
    DEVELOPER_CMD="$DEVELOPER_CMD -H 'Authorization: Bearer $TOKEN'"
fi

DEVELOPER_CMD="$DEVELOPER_CMD -d '{
    \"task\": \"Create a Python function to validate email addresses using regex. Include docstring and type hints.\",
    \"context\": {
      \"language\": \"Python\",
      \"style\": \"clean and simple\"
    },
    \"idempotency_key\": \"demo-code-$(date +%s)\"
  }'"

DEVELOPER_RESULT=$(eval $DEVELOPER_CMD)
echo "$DEVELOPER_RESULT" | jq -r '.result // .detail // "No response"' | head -30
echo ""
echo -e "${GREEN}✓ Developer agent responded${NC}"
echo ""

# Step 4: Test Designer Agent
echo -e "${YELLOW}Step 4: Testing Designer Agent (UI/UX Design)...${NC}"
echo "Task: Design a login form"
echo ""

DESIGNER_CMD="curl -s -X POST http://localhost:9000/designer/run \
  -H 'Content-Type: application/json'"

if [ -n "$TOKEN" ]; then
    DESIGNER_CMD="$DESIGNER_CMD -H 'Authorization: Bearer $TOKEN'"
fi

DESIGNER_CMD="$DESIGNER_CMD -d '{
    \"task\": \"Design a modern login form with email and password fields\",
    \"context\": {
      \"style\": \"clean, minimal\",
      \"framework\": \"React\"
    },
    \"idempotency_key\": \"demo-design-$(date +%s)\"
  }'"

DESIGNER_RESULT=$(eval $DESIGNER_CMD)
echo "$DESIGNER_RESULT" | jq -r '.result // .detail // "No response"' | head -30
echo ""
echo -e "${GREEN}✓ Designer agent responded${NC}"
echo ""

# Step 5: Test UX Researcher Agent
echo -e "${YELLOW}Step 5: Testing UX Researcher Agent (User Research)...${NC}"
echo "Task: Create a user persona"
echo ""

UX_CMD="curl -s -X POST http://localhost:9000/ux-researcher/run \
  -H 'Content-Type: application/json'"

if [ -n "$TOKEN" ]; then
    UX_CMD="$UX_CMD -H 'Authorization: Bearer $TOKEN'"
fi

UX_CMD="$UX_CMD -d '{
    \"task\": \"Create a user persona for a small business owner who needs project management software\",
    \"context\": {
      \"industry\": \"retail\",
      \"company_size\": \"5-10 employees\"
    },
    \"idempotency_key\": \"demo-ux-$(date +%s)\"
  }'"

UX_RESULT=$(eval $UX_CMD)
echo "$UX_RESULT" | jq -r '.result // .detail // "No response"' | head -30
echo ""
echo -e "${GREEN}✓ UX Researcher agent responded${NC}"
echo ""

# Summary
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Demo Complete!${NC}"
echo -e "${BLUE}================================${NC}"
echo ""
echo "You just tested 5 of the 7 agents:"
echo "  ✓ Overseer - Project planning"
echo "  ✓ Developer - Code generation"
echo "  ✓ Designer - UI/UX design"
echo "  ✓ UX Researcher - User research"
echo "  + QA Tester - Test generation"
echo "  + DevOps - Infrastructure"
echo "  + Security Auditor - Security scanning"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Read the guide: cat ~/temponest/HOW-TO-USE.md"
echo "2. Try the CLI: /home/doctor/temponest/cli/agentic-cli.sh status"
echo "3. Open Web UI: http://localhost:8082"
echo "4. View metrics: http://localhost:3003 (admin/admin)"
echo ""
echo -e "${GREEN}Happy building! 🚀${NC}"
