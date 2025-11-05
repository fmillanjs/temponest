# Your First Client Project: Step-by-Step Guide

## Project Example: Build a Contact Form API for Local Business

**Client:** Local marketing agency
**What they need:** API to handle contact form submissions from their website
**Budget:** $3,000
**Timeline:** 3 days
**Your actual work:** 6-8 hours

---

## Day 1: Project Setup & Planning (2 hours)

### Step 1: Client Discovery Call (30 min)

**Questions to ask:**
- What fields do you need? (name, email, phone, message)
- Where are submissions going? (email, database, CRM)
- Any spam protection needed? (yes - reCAPTCHA)
- Hosting preference? (their server or yours)

**Outcome:** Requirements document

---

### Step 2: Break Down the Project with Overseer Agent (10 min)

```bash
# Get auth token (first time only)
export AUTH_TOKEN=$(curl -X POST http://localhost:9002/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

# Ask Overseer to plan the project
curl -X POST http://localhost:9000/overseer/run \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Break down project: Contact form API with email notifications, spam protection, and admin dashboard",
    "context": {
      "tech_stack": "FastAPI + PostgreSQL + SendGrid",
      "timeline": "3 days",
      "features": [
        "POST /contact endpoint",
        "reCAPTCHA validation",
        "Email notification to client",
        "Store submissions in database",
        "Admin dashboard to view submissions"
      ]
    },
    "project_id": "contact-form-agency-001",
    "risk_level": "low"
  }' | jq .
```

**Output:** Task breakdown like:
1. Database schema for submissions
2. FastAPI endpoint for form submission
3. reCAPTCHA validation
4. SendGrid email integration
5. Admin API endpoints
6. Basic frontend dashboard
7. Docker deployment config
8. Tests

---

### Step 3: Review and Adjust Plan (20 min)

**Your job:** Review Overseer output, adjust priorities, group tasks

**Save to project file:**
```bash
# Save task breakdown
echo "$OVERSEER_OUTPUT" > projects/contact-form-001/tasks.json
```

---

### Step 4: Client Approval (30 min)

**Send to client:**
- Task breakdown (simplified, non-technical)
- Timeline (Day 1: Backend, Day 2: Dashboard, Day 3: Deploy)
- Milestones for approval

**Example email:**
> "Here's the plan:
> - Day 1: API that receives form submissions and emails you
> - Day 2: Dashboard to view all submissions
> - Day 3: Deployed and ready to use
>
> Sound good?"

**Get approval** before proceeding

---

## Day 2: Development (3 hours)

### Step 5: Database Schema (15 min)

```bash
# Developer agent creates schema
curl -X POST http://localhost:9000/developer/run \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create PostgreSQL schema for contact form submissions with fields: name, email, phone, message, submitted_at, ip_address",
    "context": {
      "orm": "SQLAlchemy",
      "migration_tool": "Alembic",
      "indexes": ["email", "submitted_at"]
    },
    "project_id": "contact-form-agency-001",
    "idempotency_key": "schema-001"
  }' | jq -r '.result.code' > projects/contact-form-001/models.py
```

**You:** Review the generated code (5 min)

---

### Step 6: API Endpoints (30 min)

```bash
# Create contact form endpoint
curl -X POST http://localhost:9000/developer/run \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create FastAPI POST /contact endpoint that validates form data, checks reCAPTCHA, saves to database, and sends email via SendGrid",
    "context": {
      "validation": "Pydantic models",
      "fields": "name (required), email (required, valid), phone (optional), message (required)",
      "recaptcha": "verify token with Google API",
      "email_to": "client@agency.com",
      "rate_limiting": "5 requests per IP per hour"
    },
    "idempotency_key": "api-endpoint-001"
  }' | jq -r '.result.code' > projects/contact-form-001/api.py
```

```bash
# Create admin endpoints
curl -X POST http://localhost:9000/developer/run \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create FastAPI admin endpoints: GET /admin/submissions (list all with pagination), GET /admin/submissions/:id (get one)",
    "context": {
      "auth": "API key authentication",
      "pagination": "offset/limit, default 50 per page",
      "sorting": "by submitted_at desc"
    },
    "idempotency_key": "admin-api-001"
  }' | jq -r '.result.code' >> projects/contact-form-001/api.py
```

**You:**
- Copy code to project
- Test endpoints manually (Postman/curl): 45 min
- Fix any issues: 30 min

---

### Step 7: Frontend Dashboard (45 min)

```bash
# Simple admin dashboard
curl -X POST http://localhost:9000/developer/run \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create simple HTML/JS admin dashboard that displays contact submissions in a table with search and pagination",
    "context": {
      "framework": "vanilla JavaScript + Tailwind CSS",
      "api": "fetch from /admin/submissions",
      "features": ["search by email", "filter by date", "export to CSV"]
    },
    "idempotency_key": "dashboard-001"
  }' | jq -r '.result.code' > projects/contact-form-001/dashboard.html
```

**You:** Test dashboard (15 min)

---

### Step 8: Tests & Security (30 min)

```bash
# Generate tests
curl -X POST http://localhost:9000/qa-tester/run \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Write pytest tests for contact form API: valid submission, invalid email, missing fields, spam detection, rate limiting",
    "context": {
      "framework": "pytest + pytest-asyncio",
      "coverage_target": "80%"
    },
    "idempotency_key": "tests-001"
  }' | jq -r '.result.tests' > projects/contact-form-001/test_api.py

# Security scan
curl -X POST http://localhost:9000/security-auditor/run \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Scan contact form API for vulnerabilities: SQL injection, XSS, CSRF, rate limiting bypass",
    "context": {
      "files": ["api.py", "models.py"]
    },
    "idempotency_key": "security-001"
  }' | jq .
```

**You:** Review security findings, fix critical issues (30 min)

---

## Day 3: Deployment & Handoff (2 hours)

### Step 9: Deployment Configuration (30 min)

```bash
# Generate Docker setup
curl -X POST http://localhost:9000/devops/run \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create Docker Compose setup with FastAPI app, PostgreSQL, and Nginx reverse proxy",
    "context": {
      "app_port": "8000",
      "postgres_version": "15",
      "nginx_ssl": "Let'\''s Encrypt",
      "env_vars": ["SENDGRID_API_KEY", "RECAPTCHA_SECRET", "DATABASE_URL"]
    },
    "idempotency_key": "deployment-001"
  }' | jq -r '.result.docker_compose' > projects/contact-form-001/docker-compose.yml
```

**You:**
- Deploy to DigitalOcean/AWS (30 min)
- Configure DNS (10 min)
- Test production endpoint (10 min)

---

### Step 10: Documentation (20 min)

```bash
# Generate README
curl -X POST http://localhost:9000/developer/run \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Write README with setup instructions, API documentation, and environment variables",
    "context": {
      "endpoints": ["/contact", "/admin/submissions"],
      "deployment": "Docker Compose",
      "env_vars": "list all required variables with examples"
    },
    "idempotency_key": "readme-001"
  }' | jq -r '.result.documentation' > projects/contact-form-001/README.md
```

---

### Step 11: Client Handoff (1 hour)

**Deliverables:**
1. ✅ Live API endpoint: `https://forms.agency.com/contact`
2. ✅ Admin dashboard: `https://forms.agency.com/admin`
3. ✅ Source code (GitHub repo)
4. ✅ Documentation (README)
5. ✅ API key for admin access
6. ✅ Example HTML form code to embed on their site

**Handoff meeting:**
- Demo the working system (15 min)
- Walk through admin dashboard (15 min)
- Show how to embed form on their website (15 min)
- Answer questions (15 min)

**Invoice:** $3,000 (Net 15 payment terms)

---

## Project Economics

### Time Breakdown:
- **Agent work:** ~3 hours of API calls (you wait while they work)
- **Your work:** 6-8 hours total
  - Planning & review: 2 hours
  - Testing & fixes: 3 hours
  - Deployment: 1 hour
  - Client meetings: 1.5 hours

### Financial:
- **Revenue:** $3,000
- **Costs:**
  - Your time: 8 hours × $150/hr = $1,200 (opportunity cost)
  - Infrastructure: $20 (DigitalOcean server 1 month)
  - **Total cost: $1,220**
- **Profit:** $1,780 (59% margin)

### Comparison to Traditional Development:
- **Traditional:** 40 hours × $100/hr = $4,000 cost to you
- **Would lose money** at $3,000 price point
- **With agents:** Profitable even at low price point

---

## Client Integration

### Add to Their Website:

**HTML form code (give to client):**
```html
<form id="contact-form">
  <input type="text" name="name" required placeholder="Name">
  <input type="email" name="email" required placeholder="Email">
  <input type="tel" name="phone" placeholder="Phone">
  <textarea name="message" required placeholder="Message"></textarea>
  <button type="submit">Submit</button>
</form>

<script src="https://www.google.com/recaptcha/api.js"></script>
<script>
document.getElementById('contact-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const token = await grecaptcha.execute('SITE_KEY');
  const data = new FormData(e.target);
  data.append('recaptcha_token', token);

  const response = await fetch('https://forms.agency.com/contact', {
    method: 'POST',
    body: JSON.stringify(Object.fromEntries(data)),
    headers: {'Content-Type': 'application/json'}
  });

  if (response.ok) {
    alert('Thanks! We\'ll be in touch.');
    e.target.reset();
  }
});
</script>
```

**Client copies this into their WordPress/Webflow/custom site.**

---

## Next Steps After First Project

### Lessons Learned:
- Which agents worked well?
- What needed most human review?
- Where did you save the most time?
- What would you price differently?

### Scale to 5 Projects/Month:
- **Revenue:** $15K/month ($180K/year)
- **Time:** 30-40 hours/month
- **Effective rate:** $375-$500/hour

### Add Complexity:
- Next project: $5K budget
- Then: $10K budget
- Eventually: $25K+ projects

### Build Portfolio:
- Use first 3 projects as case studies
- Post on LinkedIn: "Built contact form API in 3 days"
- Get referrals from happy clients

---

## Troubleshooting

### Agent Output Issues:

**Problem:** Agent code doesn't work
**Solution:**
- Check context was clear enough
- Re-run with more specific requirements
- Fix manually and save pattern for future

**Problem:** Agent made insecure code
**Solution:**
- Run security-auditor agent
- Apply fixes
- Update your review checklist

**Problem:** Output is too generic
**Solution:**
- Add more context: brand, style, specific examples
- Reference similar projects in knowledge base
- Iterate with agent (give feedback, re-run)

---

## Templates for Future Projects

Save your API calls as templates:

```bash
# projects/templates/api-endpoint.sh
#!/bin/bash
curl -X POST http://localhost:9000/developer/run \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"task\": \"$1\",
    \"context\": $2,
    \"project_id\": \"$3\",
    \"idempotency_key\": \"$4\"
  }"
```

**Usage:**
```bash
./templates/api-endpoint.sh \
  "Create REST API for user management" \
  '{"framework":"FastAPI","auth":"JWT"}' \
  "client-xyz-001" \
  "api-users-001"
```

Speeds up future projects significantly!
