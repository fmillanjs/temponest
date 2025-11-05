#!/bin/bash
# Demo: Build a Contact Form API using the Agentic CLI
# This demonstrates how to use agents to build a real client project

set -e

CLI="/home/doctor/temponest/cli/agentic-cli.sh"

echo "=================================================="
echo "   DEMO: Building Contact Form API with Agents"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

step() {
    echo -e "${BLUE}>>> $1${NC}"
    echo ""
}

result() {
    echo -e "${GREEN}✓ $1${NC}"
    echo ""
}

# Step 1: Initialize project
step "STEP 1: Initializing project 'demo-contact-api'"
$CLI init demo-contact-api
result "Project created at ~/agentic-projects/demo-contact-api"

cd ~/agentic-projects/demo-contact-api

# Step 2: Plan the project
step "STEP 2: Planning with Overseer Agent"
$CLI plan "Build a REST API for contact form submissions with the following features:
- POST /contact endpoint that accepts name, email, phone, message
- Email validation using Pydantic
- Store submissions in PostgreSQL database
- Send email notification using SendGrid
- Rate limiting (5 requests per IP per hour)
- GET /admin/submissions endpoint to list all submissions
- Include FastAPI application structure"

result "Project plan generated - see plan.json"

# Step 3: Develop database models
step "STEP 3: Creating database models with Developer Agent"
$CLI develop "Create SQLAlchemy models for contact form submissions with fields: id (UUID), name (string), email (string), phone (string optional), message (text), submitted_at (timestamp), ip_address (string)" \
    '{"orm":"SQLAlchemy","database":"PostgreSQL"}'

result "Database models generated - see src/"

# Step 4: Develop API endpoints
step "STEP 4: Creating API endpoints with Developer Agent"
$CLI develop "Create FastAPI endpoints:
1. POST /contact - accepts contact form data, validates email, saves to database, sends email via SendGrid
2. GET /admin/submissions - returns paginated list of submissions with filtering
Include rate limiting, Pydantic models, and error handling" \
    '{"framework":"FastAPI","rate_limit":"5 per hour","auth":"API key for admin"}'

result "API endpoints generated - see src/"

# Step 5: Create tests
step "STEP 5: Generating tests with QA Tester Agent"
$CLI test "Write pytest tests for contact form API covering:
- Valid submission
- Invalid email format
- Missing required fields
- Rate limiting
- Admin endpoint with authentication"

result "Tests generated - see tests/"

# Step 6: Security audit
step "STEP 6: Running security audit with Security Auditor Agent"
$CLI audit "Scan for security vulnerabilities including SQL injection, XSS, missing rate limiting, exposed secrets"

result "Security audit complete - see docs/security-audit-*.json"

# Step 7: Deployment configuration
step "STEP 7: Creating deployment configuration with DevOps Agent"
$CLI deploy "Create Docker Compose setup with:
- FastAPI application
- PostgreSQL database
- Nginx reverse proxy with SSL
- Environment variables for SendGrid API key
- Health check endpoints"

result "Deployment files generated - docker-compose.yml, Dockerfile"

# Summary
echo ""
echo "=================================================="
echo "   DEMO COMPLETE!"
echo "=================================================="
echo ""
echo "Generated files:"
echo "  📁 plan.json              - Project breakdown from Overseer"
echo "  📁 src/                   - Database models + API code"
echo "  📁 tests/                 - Automated tests"
echo "  📁 docs/                  - Security audit report"
echo "  📁 docker-compose.yml     - Deployment configuration"
echo "  📁 Dockerfile             - Docker image"
echo ""
echo "Next steps:"
echo "  1. Review generated code in src/"
echo "  2. Customize SendGrid configuration"
echo "  3. Run tests: pytest tests/"
echo "  4. Deploy: docker-compose up -d"
echo ""
echo "Client deliverable value: \$3,000"
echo "Your actual time: ~2 hours"
echo "Effective rate: \$1,500/hr"
echo ""
echo "=================================================="
