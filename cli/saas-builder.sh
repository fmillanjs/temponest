#!/bin/bash
# SaaS Builder - Automated SaaS product development workflow

set -e

CLI="/home/doctor/temponest/cli/agentic-cli.sh"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=================================================="
echo "   🚀 SaaS Product Builder"
echo "   Build production-ready SaaS in 8 weeks"
echo "=================================================="
echo ""

# Gather product details
echo -e "${BLUE}Let's build your SaaS product!${NC}"
echo ""

read -p "Product name (e.g., 'TinyAnalytics'): " PRODUCT_NAME
read -p "One-line description: " DESCRIPTION
read -p "Target customer (e.g., 'small businesses'): " TARGET_CUSTOMER
read -p "Core problem it solves: " PROBLEM
read -p "Pricing (Starter/Pro/Business in $): " PRICING

SLUG=$(echo "$PRODUCT_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')

echo ""
echo -e "${GREEN}Building: $PRODUCT_NAME${NC}"
echo "Description: $DESCRIPTION"
echo "Target: $TARGET_CUSTOMER"
echo "Problem: $PROBLEM"
echo "Pricing: $PRICING"
echo ""

read -p "Continue? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo "Cancelled."
    exit 0
fi

# Initialize project
echo ""
echo -e "${BLUE}=== Week 1: Validation & Research ===${NC}"
echo ""

$CLI init "saas-$SLUG"
cd ~/agentic-projects/saas-$SLUG

# Create project metadata
cat > product.json <<EOF
{
  "name": "$PRODUCT_NAME",
  "slug": "$SLUG",
  "description": "$DESCRIPTION",
  "target_customer": "$TARGET_CUSTOMER",
  "problem": "$PROBLEM",
  "pricing": "$PRICING",
  "created_at": "$(date -Iseconds)",
  "status": "building",
  "launch_date": null,
  "mrr": 0,
  "customers": 0
}
EOF

echo -e "${GREEN}✓${NC} Project initialized: ~/agentic-projects/saas-$SLUG"

# Market research
echo ""
echo "🔍 Conducting market research..."
$CLI research "Analyze the market for $PRODUCT_NAME ($DESCRIPTION). Research:
1. Target customer demographics and behaviors ($TARGET_CUSTOMER)
2. Main pain point: $PROBLEM
3. Competitors and their pricing
4. Market gaps and opportunities
5. Willingness to pay ($PRICING range)" \
  "{\"industry\":\"SaaS\",\"product\":\"$PRODUCT_NAME\"}" > research/market-analysis.json

echo -e "${GREEN}✓${NC} Market research completed"

# User personas
echo ""
echo "👤 Creating user personas..."
$CLI research "Create 3 detailed user personas for $PRODUCT_NAME targeting $TARGET_CUSTOMER:
1. Early adopter (tech-savvy, willing to try new tools)
2. Mainstream user (needs reliability, proven solution)
3. Enterprise buyer (procurement process, compliance needs)
Include demographics, goals, pain points, and buying triggers" \
  "{\"product\":\"$PRODUCT_NAME\",\"problem\":\"$PROBLEM\"}" > research/personas.json

echo -e "${GREEN}✓${NC} User personas created"

# User journey
echo ""
echo "🗺️  Mapping user journey..."
$CLI research "Map the ideal user journey for $PRODUCT_NAME from discovery to paying customer:
Stages: Awareness → Trial → Conversion → Retention → Advocacy
For each stage include: user actions, emotions, pain points, opportunities to delight" \
  "{\"conversion_goal\":\"free trial to paid\"}" > research/user-journey.json

echo -e "${GREEN}✓${NC} User journey mapped"

echo ""
echo -e "${YELLOW}Week 1 Complete! Review:${NC}"
echo "  - research/market-analysis.json"
echo "  - research/personas.json"
echo "  - research/user-journey.json"
echo ""
echo "Next: Week 2 - Design & Planning"
echo ""

# Week 2: Design
echo -e "${BLUE}=== Week 2: Design & Planning ===${NC}"
echo ""
read -p "Continue to design phase? (y/n): " CONTINUE
if [ "$CONTINUE" != "y" ]; then
    echo "Paused. Run this script again to continue."
    exit 0
fi

# Project planning
echo ""
echo "📋 Planning MVP features..."
$CLI plan "Build SaaS product: $PRODUCT_NAME

Description: $DESCRIPTION
Target: $TARGET_CUSTOMER
Problem: $PROBLEM

CORE FEATURES:
- User authentication (email/password, social login)
- Subscription billing with Stripe (pricing: $PRICING)
- [CORE FEATURE 1 - based on $PROBLEM]
- [CORE FEATURE 2 - supporting feature]
- [CORE FEATURE 3 - differentiator]
- User dashboard
- Admin panel

TECH STACK:
- Backend: FastAPI + PostgreSQL
- Frontend: React + Tailwind CSS
- Payment: Stripe
- Email: SendGrid
- Deployment: Docker + AWS

Break down into detailed tasks for 8-week timeline."

echo -e "${GREEN}✓${NC} MVP plan created"

# Landing page design
echo ""
echo "🎨 Designing landing page..."
$CLI design "Design a high-converting landing page for $PRODUCT_NAME

Product: $DESCRIPTION
Target: $TARGET_CUSTOMER
Value Prop: Solve $PROBLEM

Sections:
1. Hero with headline, subheadline, CTA button 'Start Free Trial'
2. Social proof (logos or testimonials)
3. Features (3 key features with icons)
4. How it works (3-step process)
5. Pricing table ($PRICING)
6. Final CTA
7. Footer

Style: Modern SaaS, clean, trustworthy
Colors: Professional (suggest palette)
CTA: Clear, action-oriented" \
  "{\"conversion_goal\":\"trial signups\",\"mobile_responsive\":true}" > docs/landing-page-design.json

echo -e "${GREEN}✓${NC} Landing page designed"

# App UI design
echo ""
echo "🎨 Designing application UI..."
$CLI design "Design the main dashboard UI for $PRODUCT_NAME

User goal: Solve $PROBLEM efficiently

Layout:
- Left sidebar: Navigation menu
- Top header: Search, notifications, user menu
- Main area: Key metrics/data display
- Action buttons: Primary actions users take

Components needed:
- Stats cards (showing key metrics)
- Data table (for main content)
- Modal for create/edit
- Settings panel

Style: Clean, data-focused, modern
Framework: React components
Accessibility: WCAG 2.1 AA compliant" \
  "{\"framework\":\"React\",\"ui_library\":\"shadcn/ui\"}" > docs/app-ui-design.json

echo -e "${GREEN}✓${NC} Application UI designed"

# Pricing page design
echo ""
echo "💰 Designing pricing page..."
PRICING_ARRAY=(${PRICING//\// })
$CLI design "Design pricing page for $PRODUCT_NAME with 3 tiers:

Starter: \$${PRICING_ARRAY[0]}/month
  - Basic features
  - Limited usage
  - Email support

Professional: \$${PRICING_ARRAY[1]}/month (RECOMMENDED)
  - All features
  - Higher limits
  - Priority support
  - Most popular

Business: \$${PRICING_ARRAY[2]}/month
  - Unlimited usage
  - Advanced features
  - Dedicated support
  - SLA

Design elements:
- Highlight Professional tier
- Clear feature comparison
- Monthly/Annual toggle (20% discount annual)
- Trust signals (money-back guarantee, cancel anytime)
- FAQ section" \
  "{\"style\":\"clean value prop\",\"highlight\":\"Professional\"}" > docs/pricing-design.json

echo -e "${GREEN}✓${NC} Pricing page designed"

echo ""
echo -e "${YELLOW}Week 2 Complete! Review:${NC}"
echo "  - plan.json (complete MVP plan)"
echo "  - docs/landing-page-design.json"
echo "  - docs/app-ui-design.json"
echo "  - docs/pricing-design.json"
echo ""
echo "Next: Week 3-4 - Backend Development"
echo ""

# Week 3: Backend Development
echo -e "${BLUE}=== Week 3-4: Backend Development ===${NC}"
echo ""
read -p "Continue to backend development? (y/n): " CONTINUE
if [ "$CONTINUE" != "y" ]; then
    echo "Paused. Run this script again to continue."
    exit 0
fi

echo ""
echo "💾 Creating database schema..."
$CLI develop "Create PostgreSQL database schema for $PRODUCT_NAME:

Tables:
1. users
   - id (UUID, primary key)
   - email (unique, indexed)
   - password_hash
   - full_name
   - stripe_customer_id
   - subscription_tier (starter/pro/business)
   - subscription_status (active/cancelled/past_due)
   - trial_ends_at
   - created_at, updated_at

2. subscriptions
   - id (UUID)
   - user_id (foreign key)
   - stripe_subscription_id
   - plan (starter/pro/business)
   - status
   - current_period_end
   - cancel_at_period_end

3. [Add your core domain tables based on $PROBLEM]

Use SQLAlchemy ORM with proper relationships and indexes.
Include Alembic migration files." \
  "{\"database\":\"PostgreSQL\",\"orm\":\"SQLAlchemy\"}" > src/models.py

echo -e "${GREEN}✓${NC} Database schema created"

echo ""
echo "🔐 Building authentication system..."
$CLI develop "Build FastAPI authentication system for $PRODUCT_NAME:

Endpoints:
- POST /auth/register (email, password, returns JWT)
- POST /auth/login (email, password, returns JWT + refresh token)
- POST /auth/refresh (refresh token, returns new JWT)
- POST /auth/forgot-password (sends reset email via SendGrid)
- POST /auth/reset-password (token, new password)
- GET /auth/me (returns current user, requires JWT)
- POST /auth/logout (invalidates refresh token)

Features:
- Password hashing with bcrypt
- JWT tokens (15min expiry) + refresh tokens (30 day)
- Email verification for new signups
- Rate limiting on auth endpoints
- Middleware for protected routes

Security:
- OWASP best practices
- Input validation with Pydantic
- CORS configuration" \
  "{\"framework\":\"FastAPI\",\"auth\":\"JWT\",\"email\":\"SendGrid\"}" > src/auth.py

echo -e "${GREEN}✓${NC} Authentication system built"

echo ""
echo "💳 Integrating Stripe billing..."
$CLI develop "Implement Stripe subscription billing for $PRODUCT_NAME:

Plans:
- Starter: \$${PRICING_ARRAY[0]}/month (price_starter)
- Professional: \$${PRICING_ARRAY[1]}/month (price_pro)
- Business: \$${PRICING_ARRAY[2]}/month (price_business)

Endpoints:
- POST /billing/create-checkout-session (create Stripe checkout for plan)
- POST /billing/webhook (handle Stripe events)
- GET /billing/portal (redirect to Stripe customer portal)
- GET /billing/subscription (get current subscription details)
- POST /billing/upgrade (upgrade/downgrade plan)
- POST /billing/cancel (cancel subscription at period end)

Webhook Events to Handle:
- checkout.session.completed (activate subscription)
- customer.subscription.updated (handle plan changes)
- customer.subscription.deleted (handle cancellation)
- invoice.payment_failed (handle failed payments)

Features:
- 14-day free trial
- Proration for upgrades/downgrades
- Cancel at end of billing period
- Webhook signature verification" \
  "{\"payment\":\"Stripe\",\"pricing\":\"$PRICING\",\"trial_days\":14}" > src/billing.py

echo -e "${GREEN}✓${NC} Stripe integration complete"

echo ""
echo "⚙️  Building core feature API..."
# This is product-specific, so we'll create a template
cat > src/api_template.py <<'EOF'
# TODO: Customize this for your specific product features
# Example structure for a SaaS API

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

router = APIRouter()

# GET /resources - List user's resources
@router.get("/resources")
async def list_resources(
    skip: int = 0,
    limit: int = 50,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check subscription limits
    plan_limits = {
        "starter": 10,
        "pro": 100,
        "business": -1  # unlimited
    }

    resources = db.query(Resource).filter(
        Resource.user_id == current_user.id
    ).offset(skip).limit(limit).all()

    return {"resources": resources, "total": len(resources)}

# POST /resources - Create new resource
@router.post("/resources")
async def create_resource(
    resource_data: ResourceCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check plan limits
    count = db.query(Resource).filter(
        Resource.user_id == current_user.id
    ).count()

    limit = plan_limits.get(current_user.subscription_tier, 10)
    if limit != -1 and count >= limit:
        raise HTTPException(
            status_code=403,
            detail=f"Plan limit reached. Upgrade to create more."
        )

    resource = Resource(**resource_data.dict(), user_id=current_user.id)
    db.add(resource)
    db.commit()

    return resource

# Add more CRUD endpoints...
EOF

echo -e "${GREEN}✓${NC} API template created (customize for your product)"

echo ""
echo "👨‍💼 Building admin panel API..."
$CLI develop "Create admin API endpoints for $PRODUCT_NAME:

Endpoints:
- GET /admin/dashboard (key metrics: MRR, customers, churn)
- GET /admin/users (list all users with filters, pagination)
- GET /admin/users/:id (detailed user view)
- POST /admin/users/:id/upgrade (manually upgrade user)
- POST /admin/users/:id/refund (issue refund)
- GET /admin/revenue (revenue charts and breakdown)
- GET /admin/analytics (usage analytics, feature adoption)
- GET /admin/health (system health metrics)

Authorization:
- Require admin role in JWT
- Audit log all admin actions

Features:
- Export data to CSV
- Real-time metrics
- Search and filtering" \
  "{\"auth\":\"admin role required\",\"logging\":\"audit trail\"}" > src/admin.py

echo -e "${GREEN}✓${NC} Admin panel API built"

echo ""
echo -e "${YELLOW}Week 3-4 Complete! Backend is ready:${NC}"
echo "  - src/models.py (database schema)"
echo "  - src/auth.py (authentication)"
echo "  - src/billing.py (Stripe integration)"
echo "  - src/api_template.py (customize for your features)"
echo "  - src/admin.py (admin panel)"
echo ""
echo "Next: Week 5 - Frontend Development"
echo ""

# Save progress
cat > build-progress.json <<EOF
{
  "product": "$PRODUCT_NAME",
  "week_completed": 4,
  "phases_complete": [
    "validation",
    "design",
    "backend"
  ],
  "next_phase": "frontend",
  "estimated_completion": "4 weeks"
}
EOF

echo "Progress saved to build-progress.json"
echo ""
echo "To continue, run: cd ~/agentic-projects/saas-$SLUG && bash ../../cli/saas-builder.sh"
