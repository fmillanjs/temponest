#!/bin/bash
# Agentic Company CLI - Streamline agent workflows

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AGENT_API="http://localhost:9000"
AUTH_API="http://localhost:9002"
PROJECT_DIR="$HOME/agentic-projects"
TOKEN_FILE="$HOME/.agentic-token"

# Ensure project directory exists
mkdir -p "$PROJECT_DIR"

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Authentication
get_token() {
    if [ -f "$TOKEN_FILE" ]; then
        # Check if token is still valid (simple check, assumes 24hr validity)
        if [ $(($(date +%s) - $(stat -c %Y "$TOKEN_FILE" 2>/dev/null || stat -f %m "$TOKEN_FILE"))) -lt 86400 ]; then
            cat "$TOKEN_FILE"
            return
        fi
    fi

    log_info "Authenticating..."
    local email="${AGENTIC_EMAIL:-admin@example.com}"
    local password="${AGENTIC_PASSWORD:-admin123}"

    TOKEN=$(curl -s -X POST "$AUTH_API/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$email\",\"password\":\"$password\"}" \
        | jq -r '.access_token')

    if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
        log_error "Authentication failed"
        exit 1
    fi

    echo "$TOKEN" > "$TOKEN_FILE"
    log_success "Authenticated"
    echo "$TOKEN"
}

# Call agent
call_agent() {
    local agent=$1
    local task=$2
    local context=$3
    local project_id=$4
    local idem_key=$5

    local token=$(get_token)

    log_info "Running ${agent} agent..."

    local response=$(curl -s -X POST "$AGENT_API/${agent}/run" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d "{
            \"task\": \"$task\",
            \"context\": $context,
            \"project_id\": \"$project_id\",
            \"idempotency_key\": \"$idem_key\",
            \"risk_level\": \"low\"
        }")

    local status=$(echo "$response" | jq -r '.status')

    if [ "$status" == "completed" ]; then
        log_success "${agent} completed"
        echo "$response"
    else
        log_error "${agent} failed"
        echo "$response" | jq -r '.error'
        exit 1
    fi
}

# Commands

cmd_init() {
    local project_name=$1
    if [ -z "$project_name" ]; then
        log_error "Project name required: agentic init <project-name>"
        exit 1
    fi

    local project_path="$PROJECT_DIR/$project_name"

    if [ -d "$project_path" ]; then
        log_error "Project '$project_name' already exists"
        exit 1
    fi

    mkdir -p "$project_path"/{src,tests,docs,deliverables}

    cat > "$project_path/project.json" <<EOF
{
  "name": "$project_name",
  "created_at": "$(date -Iseconds)",
  "client": "",
  "budget": 0,
  "timeline": "",
  "status": "planning",
  "tasks": []
}
EOF

    log_success "Project '$project_name' initialized at $project_path"
    log_info "Next: cd $project_path && agentic plan \"<describe the project>\""
}

cmd_plan() {
    local description=$1
    if [ -z "$description" ]; then
        log_error "Project description required: agentic plan \"<description>\""
        exit 1
    fi

    # Get project name from current directory
    local project_name=$(basename "$PWD")
    local project_id="${project_name}-$(date +%s)"

    log_info "Planning project: $project_name"

    local response=$(call_agent "overseer" \
        "$description" \
        "{}" \
        "$project_id" \
        "plan-001")

    # Save plan
    echo "$response" | jq '.result' > plan.json

    log_success "Project plan saved to plan.json"

    # Display tasks
    echo ""
    log_info "Task breakdown:"
    echo "$response" | jq -r '.result.plan[] | "  - \(.)"'
}

cmd_develop() {
    local task=$1
    local context=${2:-"{}"}

    if [ -z "$task" ]; then
        log_error "Task required: agentic develop \"<task description>\""
        exit 1
    fi

    local project_name=$(basename "$PWD")
    local task_id="dev-$(date +%s)"

    local response=$(call_agent "developer" \
        "$task" \
        "$context" \
        "$project_name" \
        "$task_id")

    # Save code
    local output_file="src/generated-${task_id}.py"
    echo "$response" | jq -r '.result.code // .result' > "$output_file"

    log_success "Code saved to $output_file"
}

cmd_design() {
    local task=$1
    local context=${2:-"{}"}

    if [ -z "$task" ]; then
        log_error "Task required: agentic design \"<design description>\""
        exit 1
    fi

    local project_name=$(basename "$PWD")
    local task_id="design-$(date +%s)"

    local response=$(call_agent "designer" \
        "$task" \
        "$context" \
        "$project_name" \
        "$task_id")

    # Save design
    local output_file="docs/design-${task_id}.json"
    echo "$response" | jq '.result' > "$output_file"

    log_success "Design saved to $output_file"
}

cmd_research() {
    local task=$1
    local context=${2:-"{}"}

    if [ -z "$task" ]; then
        log_error "Task required: agentic research \"<research question>\""
        exit 1
    fi

    local project_name=$(basename "$PWD")
    local task_id="research-$(date +%s)"

    local response=$(call_agent "ux-researcher" \
        "$task" \
        "$context" \
        "$project_name" \
        "$task_id")

    # Save research
    local output_file="docs/research-${task_id}.json"
    echo "$response" | jq '.result' > "$output_file"

    log_success "Research saved to $output_file"
}

cmd_test() {
    local task=$1
    local context=${2:-"{}"}

    if [ -z "$task" ]; then
        log_error "Task required: agentic test \"<what to test>\""
        exit 1
    fi

    local project_name=$(basename "$PWD")
    local task_id="test-$(date +%s)"

    local response=$(call_agent "qa-tester" \
        "$task" \
        "$context" \
        "$project_name" \
        "$task_id")

    # Save tests
    local output_file="tests/test-${task_id}.py"
    echo "$response" | jq -r '.result.tests // .result' > "$output_file"

    log_success "Tests saved to $output_file"
}

cmd_audit() {
    local task=${1:-"Scan for vulnerabilities and security issues"}
    local context=${2:-"{}"}

    local project_name=$(basename "$PWD")
    local task_id="audit-$(date +%s)"

    local response=$(call_agent "security-auditor" \
        "$task" \
        "$context" \
        "$project_name" \
        "$task_id")

    # Save audit report
    local output_file="docs/security-audit-${task_id}.json"
    echo "$response" | jq '.result' > "$output_file"

    log_success "Security audit saved to $output_file"

    # Display critical findings
    echo ""
    log_warning "Security findings:"
    echo "$response" | jq -r '.result.findings[]? | select(.severity == "critical" or .severity == "high") | "  [\(.severity | ascii_upcase)] \(.title)"'
}

cmd_deploy() {
    local task=${1:-"Create Docker deployment configuration"}
    local context=${2:-"{}"}

    local project_name=$(basename "$PWD")
    local task_id="deploy-$(date +%s)"

    local response=$(call_agent "devops" \
        "$task" \
        "$context" \
        "$project_name" \
        "$task_id")

    # Save deployment config
    echo "$response" | jq -r '.result.docker_compose // .result' > "docker-compose.yml"
    echo "$response" | jq -r '.result.dockerfile // ""' > "Dockerfile"

    log_success "Deployment configuration saved"
}

cmd_workflow() {
    local workflow_type=$1

    case $workflow_type in
        "api")
            log_info "Running API development workflow..."
            cmd_plan "Build a REST API"
            sleep 2
            cmd_develop "Create FastAPI application structure"
            sleep 2
            cmd_test "Write tests for API endpoints"
            sleep 2
            cmd_audit "Scan API for security vulnerabilities"
            sleep 2
            cmd_deploy "Create Docker deployment for API"
            log_success "API workflow complete!"
            ;;
        "saas")
            log_info "Running SaaS development workflow..."
            cmd_plan "Build a complete SaaS application"
            sleep 2
            cmd_research "Create user personas and journey maps"
            sleep 2
            cmd_design "Design dashboard UI and components"
            sleep 2
            cmd_develop "Build backend API"
            sleep 2
            cmd_develop "Build frontend React application"
            sleep 2
            cmd_test "Write comprehensive test suite"
            sleep 2
            cmd_audit "Security audit"
            sleep 2
            cmd_deploy "Production deployment setup"
            log_success "SaaS workflow complete!"
            ;;
        *)
            log_error "Unknown workflow type: $workflow_type"
            log_info "Available workflows: api, saas"
            exit 1
            ;;
    esac
}

cmd_status() {
    log_info "Agentic Company Status"
    echo ""

    # Check services
    log_info "Checking services..."

    if curl -s "$AGENT_API/health" > /dev/null 2>&1; then
        log_success "Agent service is running"
    else
        log_error "Agent service is down"
    fi

    if curl -s "$AUTH_API/health" > /dev/null 2>&1; then
        log_success "Auth service is running"
    else
        log_error "Auth service is down"
    fi

    echo ""

    # List projects
    log_info "Recent projects:"
    if [ -d "$PROJECT_DIR" ] && [ "$(ls -A $PROJECT_DIR)" ]; then
        ls -1t "$PROJECT_DIR" | head -5 | while read project; do
            echo "  - $project"
        done
    else
        echo "  (no projects yet)"
    fi
}

cmd_help() {
    cat <<EOF
Agentic Company CLI - Automate your agentic business

USAGE:
    agentic <command> [arguments]

COMMANDS:
    init <name>          Create a new project
    plan "<description>" Plan project with Overseer agent
    develop "<task>"     Generate code with Developer agent
    design "<task>"      Create designs with Designer agent
    research "<task>"    Conduct UX research
    test "<task>"        Generate tests with QA agent
    audit                Run security audit
    deploy               Create deployment config

    workflow <type>      Run complete workflow (api, saas)
    status               Check system status
    help                 Show this help message

EXAMPLES:
    # Start a new project
    agentic init contact-form-api
    cd ~/agentic-projects/contact-form-api

    # Plan the project
    agentic plan "Build a contact form API with email notifications"

    # Develop features
    agentic develop "Create POST /contact endpoint with validation"
    agentic develop "Add email notification with SendGrid"

    # Test and deploy
    agentic test "Write tests for contact endpoint"
    agentic audit
    agentic deploy

    # Run complete workflow
    agentic init my-saas
    cd ~/agentic-projects/my-saas
    agentic workflow saas

ENVIRONMENT VARIABLES:
    AGENTIC_EMAIL        Auth email (default: admin@example.com)
    AGENTIC_PASSWORD     Auth password (default: admin123)

CONFIGURATION:
    Projects:  $PROJECT_DIR
    Token:     $TOKEN_FILE
    Agent API: $AGENT_API
    Auth API:  $AUTH_API

EOF
}

# Main
main() {
    local command=$1
    shift

    case $command in
        init)
            cmd_init "$@"
            ;;
        plan)
            cmd_plan "$@"
            ;;
        develop|dev)
            cmd_develop "$@"
            ;;
        design)
            cmd_design "$@"
            ;;
        research)
            cmd_research "$@"
            ;;
        test)
            cmd_test "$@"
            ;;
        audit)
            cmd_audit "$@"
            ;;
        deploy)
            cmd_deploy "$@"
            ;;
        workflow)
            cmd_workflow "$@"
            ;;
        status)
            cmd_status
            ;;
        help|--help|-h|"")
            cmd_help
            ;;
        *)
            log_error "Unknown command: $command"
            echo ""
            cmd_help
            exit 1
            ;;
    esac
}

main "$@"
