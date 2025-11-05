# Project Templates - Quick Reference

## Template 1: REST API ($3K-$8K, 3-5 days)

### Client Request:
"We need an API to handle [X functionality] with database storage"

### Workflow:
```bash
# 1. Initialize
agentic init api-project-name
cd ~/agentic-projects/api-project-name

# 2. Plan
agentic plan "Build REST API for [describe functionality] with [tech stack]"

# 3. Database
agentic develop "Create database schema for [entities]" \
    '{"orm":"SQLAlchemy","database":"PostgreSQL"}'

# 4. API Endpoints
agentic develop "Create FastAPI endpoints: [list endpoints]" \
    '{"framework":"FastAPI","auth":"JWT"}'

# 5. Tests
agentic test "Write pytest tests for [main functionality]"

# 6. Security
agentic audit

# 7. Deploy
agentic deploy "Docker Compose with FastAPI, PostgreSQL, Redis"
```

### Deliverables:
- Source code (GitHub repo)
- API documentation (OpenAPI/Swagger)
- Tests (pytest)
- Docker deployment
- README

### Economics:
- Bill: $3K-$8K
- Time: 6-10 hours
- Rate: $300-$1,333/hr

---

## Template 2: SaaS Dashboard ($10K-$25K, 2-4 weeks)

### Client Request:
"We need a dashboard to visualize [data] with user management"

### Workflow:
```bash
# 1. Initialize
agentic init saas-dashboard
cd ~/agentic-projects/saas-dashboard

# 2. Research
agentic research "Create user personas for [target audience]" \
    '{"industry":"SaaS","use_case":"[describe]"}'

# 3. Design
agentic design "Design dashboard UI with [features]" \
    '{"style":"modern","framework":"React"}'

# 4. Backend
agentic develop "Build FastAPI backend with auth, data APIs" \
    '{"database":"PostgreSQL","auth":"JWT","features":["user mgmt","data endpoints"]}'

# 5. Frontend
agentic develop "Build React dashboard with [components]" \
    '{"ui_library":"shadcn/ui","state":"Zustand","charts":"Recharts"}'

# 6. Tests
agentic test "Write comprehensive test suite for API and components"

# 7. Security
agentic audit

# 8. Deploy
agentic deploy "Production Docker setup with SSL, backups"
```

### Deliverables:
- User research (personas, journey maps)
- Design system
- Backend API
- Frontend application
- Tests
- Deployment

### Economics:
- Bill: $10K-$25K
- Time: 20-40 hours
- Rate: $250-$1,250/hr

---

## Template 3: Security Audit ($8K-$20K, 1-2 weeks)

### Client Request:
"We need a security audit for investor due diligence"

### Workflow:
```bash
# 1. Initialize
agentic init security-audit-clientname
cd ~/agentic-projects/security-audit-clientname

# 2. Code Scan
agentic audit "Scan codebase for OWASP Top 10 vulnerabilities: SQL injection, XSS, CSRF, authentication issues" \
    '{"repo_path":"/path/to/client/code","framework":"FastAPI"}'

# 3. Infrastructure Review
agentic audit "Review Docker and deployment configuration for security issues" \
    '{"files":["docker-compose.yml","Dockerfile","nginx.conf"]}'

# 4. Compliance Check
agentic audit "Assess SOC 2 Type II readiness" \
    '{"requirements":["access controls","encryption","logging","backups"]}'

# 5. Remediation Code (if client wants fixes)
agentic develop "Fix SQL injection vulnerabilities using parameterized queries"
agentic develop "Add rate limiting to API endpoints"
agentic develop "Implement security headers (CSP, HSTS, X-Frame-Options)"

# 6. Infrastructure Hardening
agentic deploy "Set up AWS Secrets Manager for sensitive data"
agentic deploy "Configure WAF rules for common attacks"

# 7. Re-scan
agentic audit "Validate fixes resolved vulnerabilities"
```

### Deliverables:
- Security audit report
- Vulnerability findings (by severity)
- Compliance gap analysis
- Remediation code (if requested)
- Re-scan validation

### Economics:
- Bill: $8K-$20K
- Time: 12-25 hours
- Rate: $667-$1,667/hr

---

## Template 4: UI/UX Design Package ($5K-$15K, 1-2 weeks)

### Client Request:
"We need to redesign [feature/product] to improve UX"

### Workflow:
```bash
# 1. Initialize
agentic init ux-redesign-clientname
cd ~/agentic-projects/ux-redesign-clientname

# 2. Research
agentic research "Analyze [product] for usability issues and pain points" \
    '{"current_state":"[describe]","user_feedback":"[summarize]"}'

agentic research "Create user personas for [target users]" \
    '{"demographics":"[describe]","behaviors":"[describe]"}'

agentic research "Map user journey for [key workflow]" \
    '{"stages":["awareness","consideration","decision","retention"]}'

# 3. Design
agentic design "Create wireframes for [screens/features]" \
    '{"platform":"mobile","style":"minimal"}'

agentic design "Design high-fidelity mockups with brand colors" \
    '{"brand":"[colors]","components":"[list]"}'

agentic design "Create design system documentation" \
    '{"components":["Button","Input","Card"],"tokens":"JSON + CSS"}'

# 4. Prototype (optional)
agentic develop "Build interactive React prototype" \
    '{"framework":"React + Tailwind","deploy":"Vercel"}'

# 5. Handoff
agentic design "Create developer handoff documentation" \
    '{"format":"Figma annotations + Markdown"}'
```

### Deliverables:
- User research report
- User personas (3-5)
- Journey maps
- Wireframes
- High-fidelity mockups
- Design system
- Interactive prototype (optional)
- Developer handoff docs

### Economics:
- Bill: $5K-$15K
- Time: 10-20 hours
- Rate: $250-$1,500/hr

---

## Template 5: E-commerce Integration ($5K-$12K, 1 week)

### Client Request:
"Connect our system to [Shopify/Stripe/etc] for payments"

### Workflow:
```bash
# 1. Initialize
agentic init ecommerce-integration
cd ~/agentic-projects/ecommerce-integration

# 2. Plan
agentic plan "Build integration with [platform] for [functionality]" \

# 3. Develop Integration
agentic develop "Create [platform] API client with authentication and error handling" \
    '{"api":"[platform] REST API","auth":"OAuth 2.0"}'

agentic develop "Implement webhook handlers for [events]" \
    '{"events":["payment.success","order.created","refund.processed"]}'

agentic develop "Build sync service to keep data in sync" \
    '{"frequency":"real-time","retry_logic":"exponential backoff"}'

# 4. Tests
agentic test "Write integration tests with mocked [platform] API"

# 5. Security
agentic audit "Scan for API key exposure, webhook validation, data leakage"

# 6. Deploy
agentic deploy "Deploy with queue system for reliable webhook processing" \
    '{"queue":"Redis + Celery","monitoring":"Sentry"}'
```

### Deliverables:
- Integration code
- Webhook handlers
- Error handling & retries
- Tests
- Documentation
- Deployment

### Economics:
- Bill: $5K-$12K
- Time: 8-15 hours
- Rate: $625-$1,500/hr

---

## Template 6: Compliance Documentation ($3K-$8K, 3-5 days)

### Client Request:
"We need SOC 2 / HIPAA / GDPR documentation"

### Workflow:
```bash
# 1. Initialize
agentic init compliance-docs-soc2
cd ~/agentic-projects/compliance-docs-soc2

# 2. Gap Analysis
agentic audit "Assess current state against SOC 2 requirements" \
    '{"requirements":["access control","encryption","logging","incident response","backups"]}'

# 3. Policy Documents
agentic develop "Generate security policy documents for SOC 2" \
    '{"policies":["access control","data handling","incident response","change management"]}'

# 4. Implementation Code
agentic develop "Implement audit logging for all data access"
agentic develop "Add encryption at rest using AWS KMS"
agentic deploy "Set up automated backups with encryption"

# 5. Testing
agentic test "Write tests to validate compliance controls"

# 6. Documentation
agentic develop "Create compliance documentation package" \
    '{"includes":["policies","procedures","evidence","test results"]}'
```

### Deliverables:
- Gap analysis report
- Policy documents
- Procedure documentation
- Implementation code
- Test evidence
- Compliance checklist

### Economics:
- Bill: $3K-$8K
- Time: 6-12 hours
- Rate: $500-$1,333/hr

---

## Template 7: Data Migration ($8K-$20K, 1-2 weeks)

### Client Request:
"Migrate data from [old system] to [new system]"

### Workflow:
```bash
# 1. Initialize
agentic init data-migration-project
cd ~/agentic-projects/data-migration-project

# 2. Plan
agentic plan "Migrate [X records] from [source] to [destination]" \
    '{"source":"MySQL","destination":"PostgreSQL","data_volume":"1M records"}'

# 3. Analysis
agentic develop "Analyze source schema and create mapping to destination" \
    '{"source_tables":["users","orders","products"]}'

# 4. ETL Scripts
agentic develop "Create ETL script to extract from [source]" \
    '{"batch_size":"10000","error_handling":"log and continue"}'

agentic develop "Create transformation logic for data cleanup" \
    '{"transformations":["date formats","null handling","data validation"]}'

agentic develop "Create load script with transaction safety" \
    '{"destination":"PostgreSQL","rollback":"on error"}'

# 5. Tests
agentic test "Write data validation tests comparing source and destination"

# 6. Dry Run
agentic develop "Create dry-run mode to test migration without committing"

# 7. Deployment
agentic deploy "Create migration runbook with rollback procedures"
```

### Deliverables:
- Schema mapping document
- ETL scripts
- Data validation tests
- Dry-run results
- Migration runbook
- Rollback procedure

### Economics:
- Bill: $8K-$20K
- Time: 15-30 hours
- Rate: $533-$1,333/hr

---

## Quick Command Reference

### Common Patterns:

**Create database schema:**
```bash
agentic develop "Create [ORM] models for [entities]" \
    '{"orm":"SQLAlchemy","database":"PostgreSQL"}'
```

**Create API endpoint:**
```bash
agentic develop "Create [framework] endpoint [METHOD /path]" \
    '{"framework":"FastAPI","auth":"JWT","validation":"Pydantic"}'
```

**Write tests:**
```bash
agentic test "Write pytest tests for [functionality]"
```

**Security scan:**
```bash
agentic audit "Scan for [vulnerability types]"
```

**Create deployment:**
```bash
agentic deploy "Docker Compose with [services]"
```

**Design UI:**
```bash
agentic design "Design [component/screen] with [requirements]" \
    '{"style":"[modern/minimal/etc]","platform":"[web/mobile]"}'
```

**User research:**
```bash
agentic research "Create personas for [audience]" \
    '{"demographics":"[...]","behaviors":"[...]"}'
```

---

## Pricing Guide

| Project Type | Price Range | Time | Complexity |
|--------------|-------------|------|------------|
| Simple API | $3K-$5K | 3-5 days | Low |
| Complex API | $8K-$15K | 1-2 weeks | Medium |
| UI/UX Design | $5K-$15K | 1-2 weeks | Low-Medium |
| Security Audit | $8K-$20K | 1-2 weeks | Medium |
| Full SaaS | $15K-$50K | 3-6 weeks | High |
| Enterprise | $50K-$150K | 2-3 months | Very High |

### Pricing Formula:
```
Base price = (Estimated traditional hours) × $150/hr
Your profit = Base price - (Your actual hours × $100/hr opportunity cost)
Margin target = 80%+
```

**Example:**
- Traditional: 40 hours
- Base price: $6,000
- Your time: 8 hours
- Your cost: $800
- Profit: $5,200 (87% margin)

---

## Next Steps

1. **Pick a template** based on your skills
2. **Find your first client** (friends, LinkedIn, cold email)
3. **Offer 50% discount** for first 3 clients
4. **Deliver using agents** (follow template)
5. **Get testimonial** and case study
6. **Repeat** at full price

After 5 projects, you'll have:
- Strong portfolio
- Client testimonials
- Refined process
- $20K-$40K revenue
- Ready to scale to $50K+/month
