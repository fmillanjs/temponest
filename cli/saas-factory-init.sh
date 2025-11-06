#!/bin/bash
# SaaS Factory Initialization
# Sets up the infrastructure to build multiple SaaS products efficiently

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=================================================="
echo "   🏭 SaaS Factory Initialization"
echo "   Build Multiple SaaS Products at Scale"
echo "=================================================="
echo ""

FACTORY_DIR="$HOME/saas-factory"
TEMPLATE_DIR="$FACTORY_DIR/template"
BLUEPRINTS_DIR="$FACTORY_DIR/blueprints"
COMPONENTS_DIR="$FACTORY_DIR/components"
PRODUCTS_DIR="$FACTORY_DIR/products"

echo -e "${BLUE}This will create your SaaS factory infrastructure:${NC}"
echo ""
echo "  📁 $FACTORY_DIR/"
echo "     ├── template/       (reusable base for all SaaS)"
echo "     ├── blueprints/     (pre-built SaaS types)"
echo "     ├── components/     (reusable code library)"
echo "     ├── products/       (your launched products)"
echo "     └── shared/         (shared services)"
echo ""

read -p "Continue? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    exit 0
fi

# Create directory structure
echo ""
echo -e "${GREEN}Creating factory structure...${NC}"
mkdir -p "$FACTORY_DIR"/{template,blueprints,components,products,shared}
mkdir -p "$TEMPLATE_DIR"/{backend,frontend,infrastructure,tests}
mkdir -p "$BLUEPRINTS_DIR"/{form-builder,analytics,crm,scheduler,dashboard}
mkdir -p "$COMPONENTS_DIR"/{database,api,frontend,integrations}

echo -e "${GREEN}✓${NC} Directory structure created"

# Create factory config
cat > "$FACTORY_DIR/factory.yaml" <<'EOF'
# SaaS Factory Configuration

factory:
  name: "MySaaSFactory"
  version: "1.0.0"
  created: "2024-01-01"

shared_services:
  auth:
    enabled: true
    url: "http://localhost:9002"

  billing:
    enabled: true
    provider: "stripe"
    webhook_url: "/billing/webhook"

  email:
    enabled: true
    provider: "sendgrid"

  storage:
    enabled: true
    provider: "s3"
    bucket: "saas-factory-assets"

  analytics:
    enabled: true
    provider: "mixpanel"

infrastructure:
  database:
    type: "postgresql"
    multi_tenant: true

  cache:
    type: "redis"

  cdn:
    provider: "cloudfront"

  deployment:
    platform: "aws"
    container: "docker"
    orchestration: "ecs"

defaults:
  pricing_tiers:
    - name: "starter"
      price: 29
      features: ["basic"]
    - name: "pro"
      price: 99
      features: ["basic", "advanced"]
    - name: "business"
      price: 299
      features: ["basic", "advanced", "enterprise"]

  trial_days: 14

  support_channels:
    - email
    - chat
    - docs

products: []
EOF

echo -e "${GREEN}✓${NC} Factory config created"

# Create base template README
cat > "$TEMPLATE_DIR/README.md" <<'EOF'
# SaaS Base Template

This is the reusable foundation for all SaaS products.

## What's Included

### Backend (FastAPI)
- ✅ Multi-tenant architecture
- ✅ Authentication (JWT)
- ✅ Stripe billing integration
- ✅ User management
- ✅ Email service
- ✅ File uploads (S3)
- ✅ API rate limiting
- ✅ Webhook system
- ✅ Audit logging

### Frontend (React + TypeScript)
- ✅ Authentication pages
- ✅ Dashboard shell
- ✅ Settings pages
- ✅ Billing pages
- ✅ Component library
- ✅ Theme system (light/dark)

### Infrastructure
- ✅ Docker Compose
- ✅ GitHub Actions CI/CD
- ✅ AWS deployment
- ✅ Database migrations

## Usage

1. Copy this template for a new product:
   ```bash
   cp -r template/ products/my-new-saas/
   ```

2. Customize:
   - Update product name
   - Add specific features
   - Configure branding

3. Deploy:
   ```bash
   cd products/my-new-saas
   docker-compose up
   ```

## Building on This

Add blueprints from `../blueprints/` for specific SaaS types.
Use components from `../components/` for common features.
EOF

echo -e "${GREEN}✓${NC} Base template README created"

# Create component examples
cat > "$COMPONENTS_DIR/README.md" <<'EOF'
# Reusable Components Library

## Database Components

### `database/users.py`
User authentication and management

### `database/billing.py`
Subscription and payment tracking

### `database/teams.py`
Multi-user workspaces

### `database/content.py`
Generic content management

## API Components

### `api/crud.py`
Generic CRUD endpoints for any resource

### `api/auth.py`
Complete authentication flow

### `api/billing.py`
Stripe integration

### `api/webhooks.py`
Webhook management system

## Frontend Components

### `frontend/DataTable.tsx`
Sortable, filterable data table

### `frontend/FormBuilder.tsx`
Dynamic form generation

### `frontend/Modal.tsx`
Reusable modal system

### `frontend/Billing/`
Complete billing UI components

## Integration Components

### `integrations/stripe.py`
Stripe payment processing

### `integrations/sendgrid.py`
Email sending

### `integrations/s3.py`
File storage

## Usage

```python
# In your new SaaS product
from components.database import users, billing
from components.api import crud

# Use pre-built components
app.include_router(crud.router)
```

## Adding New Components

1. Create component file
2. Add tests
3. Document API
4. Add to this README
EOF

echo -e "${GREEN}✓${NC} Components README created"

# Create blueprint example
cat > "$BLUEPRINTS_DIR/form-builder/blueprint.yaml" <<'EOF'
# Form Builder SaaS Blueprint

name: "Form Builder"
description: "Create and manage online forms"
type: "form-builder"

database_tables:
  - name: "forms"
    columns:
      - name: "id"
        type: "uuid"
        primary_key: true
      - name: "workspace_id"
        type: "uuid"
        foreign_key: "workspaces.id"
      - name: "name"
        type: "string"
      - name: "settings"
        type: "jsonb"
      - name: "published"
        type: "boolean"

  - name: "form_fields"
    columns:
      - name: "id"
        type: "uuid"
      - name: "form_id"
        type: "uuid"
      - name: "type"
        type: "string"
      - name: "label"
        type: "string"
      - name: "validation"
        type: "jsonb"
      - name: "order"
        type: "integer"

  - name: "submissions"
    columns:
      - name: "id"
        type: "uuid"
      - name: "form_id"
        type: "uuid"
      - name: "data"
        type: "jsonb"
      - name: "ip_address"
        type: "string"
      - name: "submitted_at"
        type: "timestamp"

api_endpoints:
  - path: "/forms"
    methods: ["GET", "POST"]
    description: "List and create forms"

  - path: "/forms/{id}"
    methods: ["GET", "PUT", "DELETE"]
    description: "Manage individual forms"

  - path: "/forms/{id}/fields"
    methods: ["GET", "POST"]
    description: "Manage form fields"

  - path: "/submit/{form_id}"
    methods: ["POST"]
    auth_required: false
    description: "Public submission endpoint"

frontend_pages:
  - path: "/dashboard"
    component: "FormList"
    description: "List all forms"

  - path: "/forms/new"
    component: "FormBuilder"
    description: "Create new form"

  - path: "/forms/{id}/edit"
    component: "FormBuilder"
    description: "Edit existing form"

  - path: "/forms/{id}/submissions"
    component: "SubmissionList"
    description: "View form responses"

integrations:
  - name: "webhooks"
    description: "Trigger webhooks on submission"

  - name: "email"
    description: "Email notifications"

  - name: "zapier"
    description: "Zapier integration"

pricing_tiers:
  starter:
    forms_limit: 3
    submissions_per_month: 100

  pro:
    forms_limit: -1  # unlimited
    submissions_per_month: 1000

  business:
    forms_limit: -1
    submissions_per_month: -1

features:
  - "Drag-and-drop form builder"
  - "10+ field types"
  - "Conditional logic"
  - "Custom styling"
  - "Email notifications"
  - "Webhook integration"
  - "Analytics dashboard"
  - "CSV export"
EOF

echo -e "${GREEN}✓${NC} Form builder blueprint created"

# Create factory CLI tool
cat > "$FACTORY_DIR/factory-cli.sh" <<'SCRIPT'
#!/bin/bash
# SaaS Factory CLI

FACTORY_DIR="$HOME/saas-factory"

case "$1" in
  list)
    echo "🏭 SaaS Factory Products:"
    echo ""
    ls -1 "$FACTORY_DIR/products"
    ;;

  new)
    if [ -z "$2" ]; then
      echo "Usage: factory new <product-name> [blueprint]"
      exit 1
    fi

    PRODUCT_NAME="$2"
    BLUEPRINT="${3:-generic}"

    echo "Creating new product: $PRODUCT_NAME"
    echo "Using blueprint: $BLUEPRINT"

    # Copy template
    cp -r "$FACTORY_DIR/template" "$FACTORY_DIR/products/$PRODUCT_NAME"

    # Apply blueprint if exists
    if [ -f "$FACTORY_DIR/blueprints/$BLUEPRINT/blueprint.yaml" ]; then
      echo "Applying blueprint..."
      # TODO: Parse YAML and generate code
    fi

    echo "✓ Product created at: $FACTORY_DIR/products/$PRODUCT_NAME"
    ;;

  build)
    if [ -z "$2" ]; then
      echo "Usage: factory build <product-name>"
      exit 1
    fi

    PRODUCT_NAME="$2"
    cd "$FACTORY_DIR/products/$PRODUCT_NAME"

    echo "Building $PRODUCT_NAME..."
    docker-compose build
    ;;

  deploy)
    if [ -z "$2" ]; then
      echo "Usage: factory deploy <product-name> [env]"
      exit 1
    fi

    PRODUCT_NAME="$2"
    ENV="${3:-staging}"

    echo "Deploying $PRODUCT_NAME to $ENV..."
    # TODO: Deployment logic
    ;;

  *)
    echo "SaaS Factory CLI"
    echo ""
    echo "Commands:"
    echo "  list              - List all products"
    echo "  new <name>        - Create new product"
    echo "  build <name>      - Build product"
    echo "  deploy <name>     - Deploy product"
    ;;
esac
SCRIPT

chmod +x "$FACTORY_DIR/factory-cli.sh"
echo -e "${GREEN}✓${NC} Factory CLI created"

# Create quick start guide
cat > "$FACTORY_DIR/QUICK-START.md" <<'EOF'
# SaaS Factory Quick Start

## 1. Build Your First Product

```bash
# Create new product from template
./factory-cli.sh new my-first-saas form-builder

# Navigate to product
cd products/my-first-saas

# Start development environment
docker-compose up
```

## 2. Customize

Edit the following:
- `backend/config.py` - Product name, branding
- `frontend/src/config.ts` - Frontend config
- `docker/.env` - Environment variables

## 3. Add Features

Use components from `../components/`:

```python
# In backend/main.py
from components.api import crud, webhooks
from components.database import billing

app.include_router(crud.router)
app.include_router(webhooks.router)
```

## 4. Deploy

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy to staging
./factory-cli.sh deploy my-first-saas staging

# Deploy to production
./factory-cli.sh deploy my-first-saas production
```

## 5. Launch Second Product

```bash
# Much faster this time (reuses components)
./factory-cli.sh new my-second-saas analytics

# Reuse 70% of code from first product
# Only build product-specific features
```

## Factory Benefits

After building 2-3 products:
- 70-80% code reuse
- 2-3 week launch time (vs 8 weeks first product)
- Shared infrastructure
- Cross-selling opportunities
- Portfolio synergies

## Growing Your Portfolio

**Month 1-2:** Build factory + Product 1
**Month 3:** Launch Product 1 ($2K MRR)
**Month 4:** Build Product 2 (3 weeks)
**Month 5:** Launch Product 2 ($8K MRR)
**Month 6:** Build Product 3 (2 weeks)
**Month 7:** Launch Product 3 ($20K MRR)

**Result:** 3 SaaS products, $20K+ MRR in 7 months

## Next Steps

1. Read: `../docs/saas-factory/building-multiple-saas-products.md`
2. Choose: Your first 3 product ideas
3. Build: Complete base template (use agents)
4. Launch: Your SaaS empire
EOF

echo -e "${GREEN}✓${NC} Quick start guide created"

# Final summary
echo ""
echo "=================================================="
echo -e "  ${GREEN}✅ SaaS Factory Initialized!${NC}"
echo "=================================================="
echo ""
echo "Factory location: $FACTORY_DIR"
echo ""
echo "Next steps:"
echo ""
echo "  1. Read the guide:"
echo "     cat $FACTORY_DIR/QUICK-START.md"
echo ""
echo "  2. Build base template:"
echo "     cd $TEMPLATE_DIR"
echo "     # Use agents to build reusable components"
echo ""
echo "  3. Create first product:"
echo "     $FACTORY_DIR/factory-cli.sh new my-product form-builder"
echo ""
echo "  4. Launch and scale:"
echo "     # Each new product gets faster"
echo ""
echo "Factory structure:"
echo "  📁 template/      - Base for all products"
echo "  📁 blueprints/    - Pre-built SaaS types"
echo "  📁 components/    - Reusable code"
echo "  📁 products/      - Your launched SaaS"
echo "  📁 shared/        - Shared services"
echo ""
echo "Read full strategy:"
echo "  cat /home/doctor/temponest/docs/saas-factory/building-multiple-saas-products.md"
echo ""
echo "=================================================="
echo ""
echo "You're ready to build your SaaS empire! 🏭🚀"
echo ""
