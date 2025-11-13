# API Documentation Deployment Guide

## Overview

TempoNest uses FastAPI's built-in OpenAPI (Swagger) documentation for all API services. This guide explains how to access, deploy, and customize the API documentation.

## Quick Access

### Development Environment

Once Docker services are running, access API docs at:

| Service | Docs URL | ReDoc URL |
|---------|----------|-----------|
| **Agents Service** | http://localhost:9000/docs | http://localhost:9000/redoc |
| **Approval Service** | http://localhost:8000/docs | http://localhost:8000/redoc |
| **Scheduler Service** | http://localhost:9001/docs | http://localhost:9001/redoc |

### Production Environment

API documentation should be:
1. **Publicly accessible** for external developers
2. **Authentication-gated** for internal/admin APIs
3. **Versioned** alongside API releases

## FastAPI Documentation Configuration

### Current Implementation

Each service's `main.py` includes auto-generated docs:

```python
# services/agents/app/main.py
app = FastAPI(
    title="TempoNest Agents API",
    description="AI agent orchestration and execution service",
    version="1.0.0",
    docs_url="/docs",           # Swagger UI
    redoc_url="/redoc",         # ReDoc UI
    openapi_url="/openapi.json" # OpenAPI spec
)
```

### Enhanced Configuration

Add more metadata to improve documentation quality:

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="TempoNest Agents API",
        version="1.0.0",
        description="""
        ## TempoNest Agents API

        Orchestrate and execute AI agents with CrewAI, LangChain, and Ollama.

        ### Features
        - Multi-agent collaboration
        - Department-based agent organization
        - RAG-powered knowledge retrieval
        - LLM tracing with Langfuse

        ### Authentication
        All endpoints require Bearer token authentication:
        ```
        Authorization: Bearer <your_jwt_token>
        ```

        ### Rate Limiting
        - 100 requests per minute per IP
        - 1000 requests per hour per tenant

        ### Support
        - Documentation: https://docs.temponest.com
        - Issues: https://github.com/temponest/issues
        """,
        routes=app.routes,
        contact={
            "name": "TempoNest Support",
            "email": "support@temponest.com",
            "url": "https://temponest.com/support"
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
        },
        servers=[
            {
                "url": "https://api.temponest.com",
                "description": "Production server"
            },
            {
                "url": "https://staging-api.temponest.com",
                "description": "Staging server"
            },
            {
                "url": "http://localhost:9000",
                "description": "Development server"
            }
        ],
        tags=[
            {
                "name": "agents",
                "description": "Agent management and execution"
            },
            {
                "name": "collaboration",
                "description": "Multi-agent collaboration workflows"
            },
            {
                "name": "departments",
                "description": "Department and team organization"
            }
        ]
    )

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

## Deployment Options

### Option 1: Serve from FastAPI (Recommended for Internal)

**Pros:**
- Always up-to-date with code
- No separate deployment needed
- Auto-generated from code

**Cons:**
- Requires running service
- Couples docs with API

**Access:**
```bash
# Already available at /docs endpoint
curl http://localhost:9000/docs
```

### Option 2: Static OpenAPI Spec Export

Generate and host static OpenAPI spec:

```bash
# Export OpenAPI JSON
curl http://localhost:9000/openapi.json > openapi-agents.json

# Host with nginx or serve static
```

**docker-compose.yml:**

```yaml
services:
  api-docs:
    image: swaggerapi/swagger-ui
    ports:
      - "8080:8080"
    environment:
      - URLS=[
          { url: "/specs/agents.json", name: "Agents API" },
          { url: "/specs/approval.json", name: "Approval API" },
          { url: "/specs/scheduler.json", name: "Scheduler API" }
        ]
    volumes:
      - ./docs/openapi:/usr/share/nginx/html/specs:ro
```

### Option 3: Documentation Portal (Recommended for Public)

Use dedicated documentation platform:

**Stoplight Elements:**

```html
<!-- docs/index.html -->
<!DOCTYPE html>
<html>
<head>
    <title>TempoNest API Documentation</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://unpkg.com/@stoplight/elements/web-components.min.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/@stoplight/elements/styles.min.css">
</head>
<body>
    <elements-api
        apiDescriptionUrl="/openapi.json"
        router="hash"
        layout="sidebar"
        logo="https://temponest.com/logo.png"
    />
</body>
</html>
```

**ReadMe.com / Redocly / Postman:**

Export OpenAPI specs and import to these platforms for enhanced features:
- Interactive API playground
- Code generation
- Versioning
- Analytics

## Authentication in Documentation

### Enable "Try it out" with Authentication

Add security schemes to FastAPI:

```python
from fastapi.security import HTTPBearer
from fastapi.openapi.models import OAuthFlows, OAuthFlowPassword

security = HTTPBearer()

app = FastAPI(
    # ... other config
    openapi_tags=[
        {
            "name": "agents",
            "description": "Agent operations",
            "externalDocs": {
                "description": "Agent Guide",
                "url": "https://docs.temponest.com/agents"
            }
        }
    ]
)

# Add security scheme
@app.get("/")
async def root():
    return {"message": "TempoNest API"}

# Endpoints automatically show auth requirement
@app.get("/agents", dependencies=[Depends(security)])
async def list_agents():
    return []
```

### Swagger UI Authorization

Users can click "Authorize" button and enter JWT token to test authenticated endpoints.

## Versioning API Documentation

### URL Versioning

```python
# services/agents/app/main.py
app_v1 = FastAPI(
    title="TempoNest Agents API v1",
    version="1.0.0",
    docs_url="/v1/docs",
    openapi_url="/v1/openapi.json"
)

app_v2 = FastAPI(
    title="TempoNest Agents API v2",
    version="2.0.0",
    docs_url="/v2/docs",
    openapi_url="/v2/openapi.json"
)

# Mount on main app
app = FastAPI()
app.mount("/v1", app_v1)
app.mount("/v2", app_v2)
```

### Changelog in Documentation

Add changelog to API description:

```python
description = """
## Changelog

### v1.0.0 (2025-01-13)
- Initial release
- Agent execution endpoints
- Collaboration workflows
- Department management

### v0.9.0 (2024-12-15)
- Beta release
- Core agent functionality
"""
```

## Production Deployment Checklist

### Pre-Deployment

- [ ] Add comprehensive endpoint descriptions
- [ ] Document all request/response models
- [ ] Add example requests and responses
- [ ] Include error code documentation
- [ ] Add authentication guides
- [ ] Document rate limits
- [ ] Add versioning information

### Nginx Configuration

Expose docs through reverse proxy:

```nginx
# /etc/nginx/sites-available/temponest-api

server {
    listen 443 ssl http2;
    server_name api.temponest.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/api.temponest.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.temponest.com/privkey.pem;

    # API documentation (public)
    location /docs {
        proxy_pass http://localhost:9000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /redoc {
        proxy_pass http://localhost:9000/redoc;
        proxy_set_header Host $host;
    }

    location /openapi.json {
        proxy_pass http://localhost:9000/openapi.json;
        proxy_set_header Host $host;

        # CORS for OpenAPI spec
        add_header Access-Control-Allow-Origin "*";
        add_header Access-Control-Allow-Methods "GET, OPTIONS";
    }

    # API endpoints (authenticated)
    location /api {
        proxy_pass http://localhost:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Docker Compose Production

```yaml
services:
  agents:
    # ... existing config
    environment:
      - API_DOCS_ENABLED=true  # Control docs availability
      - API_DOCS_URL=/docs
      - OPENAPI_URL=/openapi.json
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.agents-docs.rule=Host(`api.temponest.com`) && PathPrefix(`/docs`)"
      - "traefik.http.routers.agents-docs.entrypoints=websecure"
      - "traefik.http.routers.agents-docs.tls.certresolver=letsencrypt"
```

## Disabling Documentation in Production

For security, you may want to disable docs in production:

```python
# services/agents/app/main.py
import os

DOCS_ENABLED = os.getenv("API_DOCS_ENABLED", "true").lower() == "true"

app = FastAPI(
    title="TempoNest Agents API",
    version="1.0.0",
    docs_url="/docs" if DOCS_ENABLED else None,
    redoc_url="/redoc" if DOCS_ENABLED else None,
    openapi_url="/openapi.json" if DOCS_ENABLED else None
)
```

## Monitoring Documentation Access

Track documentation usage with Prometheus:

```python
from prometheus_client import Counter

docs_access_counter = Counter(
    'api_docs_access_total',
    'Total API documentation page views',
    ['service', 'page']
)

@app.get("/docs", include_in_schema=False)
async def custom_docs():
    docs_access_counter.labels(service='agents', page='swagger').inc()
    return get_swagger_ui_html(openapi_url="/openapi.json", title="API Docs")
```

## Best Practices

1. **Keep Docs Updated**: Auto-generate from code whenever possible
2. **Add Examples**: Include request/response examples for all endpoints
3. **Document Errors**: List all possible error codes and meanings
4. **Version Control**: Track API versions and breaking changes
5. **Security**: Don't expose internal-only endpoints in public docs
6. **Testing**: Include curl examples and Postman collections
7. **Performance**: Cache OpenAPI spec generation

## Example Endpoint Documentation

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List

router = APIRouter()

class AgentCreate(BaseModel):
    """Request model for creating a new agent."""
    name: str = Field(..., description="Agent name", example="code-reviewer")
    role: str = Field(..., description="Agent role", example="developer")
    department: str = Field(..., description="Department", example="engineering")

class AgentResponse(BaseModel):
    """Response model for agent operations."""
    id: str = Field(..., description="Unique agent ID", example="ag_123456")
    name: str
    role: str
    department: str
    status: str = Field(..., description="Agent status", example="active")

@router.post(
    "/agents",
    response_model=AgentResponse,
    status_code=201,
    summary="Create a new agent",
    description="""
    Create a new AI agent with specified role and department.

    The agent will be initialized and ready to execute tasks.
    """,
    response_description="Successfully created agent",
    responses={
        201: {
            "description": "Agent created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "ag_123456",
                        "name": "code-reviewer",
                        "role": "developer",
                        "department": "engineering",
                        "status": "active"
                    }
                }
            }
        },
        400: {
            "description": "Invalid request",
            "content": {
                "application/json": {
                    "example": {"detail": "Agent name already exists"}
                }
            }
        },
        401: {"description": "Unauthorized - missing or invalid token"},
        403: {"description": "Forbidden - insufficient permissions"},
        429: {"description": "Rate limit exceeded"}
    },
    tags=["agents"]
)
async def create_agent(agent: AgentCreate):
    """Create a new agent endpoint."""
    # Implementation
    pass
```

## Next Steps

1. **Implement** enhanced OpenAPI configuration in all services
2. **Deploy** documentation to production domain
3. **Set up** Swagger UI with authentication
4. **Create** Postman collection from OpenAPI spec
5. **Monitor** documentation usage and feedback
6. **Automate** documentation updates in CI/CD

## References

- [FastAPI OpenAPI Documentation](https://fastapi.tiangolo.com/tutorial/metadata/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)
- [ReDoc](https://github.com/Redocly/redoc)

---

**Last Updated**: 2025-01-13
**Owner**: Engineering Team
**Review Frequency**: With each API version release
