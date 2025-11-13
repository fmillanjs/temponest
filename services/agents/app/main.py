"""
Agentic Company - Agent Service
FastAPI application that exposes CrewAI agents (Overseer, Developer) with RAG and Langfuse tracing.
"""

import time
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from decimal import Decimal
import asyncpg

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.settings import settings
from app.limiter import limiter
from app.agents.factory import AgentFactory
from app.memory.rag import RAGMemory
from app.memory.langfuse_tracer import LangfuseTracer
from app.departments.manager import DepartmentManager
from app.models import AgentRequest, AgentResponse
from app.utils import (
    count_tokens_async,
    enforce_budget_async,
    validate_citations,
    record_execution_cost
)
from app.routers import departments as departments_router
from app.routers import webhooks as webhooks_router
from app.routers import health as health_router
from shared.auth import (
    AuthClient,
    AuthContext,
    set_auth_client,
    get_current_user,
    require_permission,
    require_any_permission
)
from app.cost.calculator import CostCalculator
from app.cost.tracker import CostTracker
from app.webhooks import EventDispatcher, WebhookManager, EventType

# Import shared Redis client
from shared.redis import RedisCache


# Global state
rag_memory: Optional[RAGMemory] = None
langfuse_tracer: Optional[LangfuseTracer] = None
overseer_agent: Optional[Any] = None  # Can be OverseerAgent or future OverseerAgentV2
developer_agent: Optional[Any] = None  # Can be DeveloperAgent or DeveloperAgentV2
qa_tester_agent: Optional[Any] = None  # QA Tester Agent
devops_agent: Optional[Any] = None  # DevOps Agent
designer_agent: Optional[Any] = None  # Designer/UX Agent
security_auditor_agent: Optional[Any] = None  # Security Auditor Agent
ux_researcher_agent: Optional[Any] = None  # UX Researcher Agent
department_manager: Optional[DepartmentManager] = None
idempotency_cache: Dict[str, AgentResponse] = {}

# Cost tracking
db_pool: Optional[asyncpg.Pool] = None
cost_calculator: Optional[CostCalculator] = None
cost_tracker: Optional[CostTracker] = None

# Webhook system
webhook_manager: Optional[WebhookManager] = None
event_dispatcher: Optional[EventDispatcher] = None

# Collaboration system
collaboration_manager: Optional[Any] = None

# Redis cache
cache: Optional[RedisCache] = None

# Background task flag
_metrics_task: Optional[asyncio.Task] = None


async def update_metrics_periodically():
    """Background task to update health metrics every 15 seconds"""
    while True:
        try:
            # Update service health metrics
            from app.metrics import MetricsRecorder, agent_service_health, db_pool_size

            if rag_memory:
                MetricsRecorder.update_service_health("qdrant", rag_memory.is_healthy())
            if langfuse_tracer:
                MetricsRecorder.update_service_health("langfuse", langfuse_tracer.is_healthy())
            if db_pool:
                MetricsRecorder.update_service_health("database", True)

                # Update pool metrics
                pool_size = db_pool.get_size()
                pool_free = db_pool.get_idle_size()
                pool_in_use = pool_size - pool_free
                db_pool_size.labels(pool_type="size").set(pool_size)
                db_pool_size.labels(pool_type="available").set(pool_free)
                db_pool_size.labels(pool_type="in_use").set(pool_in_use)

            # Update overall health
            all_healthy = (
                (rag_memory and rag_memory.is_healthy()) and
                (langfuse_tracer and langfuse_tracer.is_healthy()) and
                (db_pool is not None)
            )
            agent_service_health.set(1.0 if all_healthy else 0.0)

        except Exception as e:
            print(f"Error updating metrics: {e}")

        await asyncio.sleep(15)  # Update every 15 seconds


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic"""
    global rag_memory, langfuse_tracer, overseer_agent, developer_agent, qa_tester_agent, devops_agent, designer_agent, security_auditor_agent, ux_researcher_agent, department_manager
    global db_pool, cost_calculator, cost_tracker
    global webhook_manager, event_dispatcher
    global collaboration_manager, cache

    # Startup
    print("🚀 Starting Agent Service...")

    # Initialize Redis cache
    print("🔴 Initializing Redis cache...")
    cache = RedisCache(url=settings.REDIS_URL)
    try:
        await cache.connect()
        print(f"   ✅ Connected to Redis at {settings.REDIS_URL}")
    except Exception as e:
        print(f"   ⚠️  Failed to connect to Redis: {e}. Caching will be disabled.")
        cache = None

    # Initialize database pool for cost tracking
    print("💾 Initializing cost tracking...")

    async def setup_db_connection(conn):
        """Setup database connection with optimized settings"""
        await conn.execute("SET statement_timeout = '30s'")
        await conn.execute("SET idle_in_transaction_session_timeout = '60s'")

    try:
        # OPTIMIZED: Tuned connection pool for agents service (highest traffic)
        db_pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=15,              # Increased from 2 (agents is highest traffic)
            max_size=100,             # Increased from 10 (handle heavy load)
            max_queries=50000,        # NEW: Recycle connections after 50k queries
            max_inactive_connection_lifetime=300.0,  # NEW: Close idle connections after 5 min
            command_timeout=30,       # Reduced from 60 (fail fast)
            timeout=10.0,             # NEW: Max wait time for connection from pool
            setup=setup_db_connection # NEW: Connection setup hook
        )
        print("   ✅ Database pool created (pool: 15-100)")

        # Load pricing from database
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT provider, model_name, input_price_per_1m, output_price_per_1m FROM model_pricing WHERE is_active = true"
            )

        # Build pricing dictionary
        db_pricing = {}
        for row in rows:
            provider = row["provider"].lower()
            model = row["model_name"]
            if provider not in db_pricing:
                db_pricing[provider] = {}
            db_pricing[provider][model] = {
                "input": Decimal(str(row["input_price_per_1m"])),
                "output": Decimal(str(row["output_price_per_1m"]))
            }

        print(f"   ✅ Loaded pricing for {len(rows)} models")

        # Initialize webhook system first (needed by cost tracker)
        webhook_manager = WebhookManager(db_pool=db_pool)
        event_dispatcher = EventDispatcher(db_pool=db_pool)
        webhooks_router.set_webhook_manager(webhook_manager)
        print("   ✅ Webhook system initialized")

        # Initialize cost calculator and tracker (with event dispatcher for alerts)
        cost_calculator = CostCalculator(db_pricing=db_pricing)
        cost_tracker = CostTracker(
            db_pool=db_pool,
            calculator=cost_calculator,
            event_dispatcher=event_dispatcher
        )
        print("   ✅ Cost tracking initialized")

    except Exception as e:
        print(f"   ⚠️  Cost tracking/webhooks disabled: {e}")
        db_pool = None
        cost_calculator = None
        cost_tracker = None
        webhook_manager = None
        event_dispatcher = None

    # Initialize auth client
    auth_client = AuthClient(
        auth_service_url=settings.AUTH_SERVICE_URL,
        jwt_secret=settings.JWT_SECRET_KEY,
        cache=cache
    )
    set_auth_client(auth_client)
    print(f"   Auth client configured: {settings.AUTH_SERVICE_URL}")

    # Initialize RAG memory
    rag_memory = RAGMemory(
        qdrant_url=settings.QDRANT_URL,
        collection_name="agentic_knowledge",
        embedding_model=settings.EMBEDDING_MODEL,
        cache=cache
    )
    await rag_memory.initialize()

    # Initialize Langfuse tracer
    langfuse_tracer = LangfuseTracer(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        host=settings.LANGFUSE_HOST
    )

    # Initialize legacy agents (backward compatibility)
    print(f"   Overseer Provider: {settings.OVERSEER_PROVIDER}")
    print(f"   Developer Provider: {settings.DEVELOPER_PROVIDER}")

    overseer_agent = AgentFactory.create_overseer(
        rag_memory=rag_memory,
        tracer=langfuse_tracer
    )

    developer_agent = AgentFactory.create_developer(
        rag_memory=rag_memory,
        tracer=langfuse_tracer
    )

    qa_tester_agent = AgentFactory.create_qa_tester(
        rag_memory=rag_memory,
        tracer=langfuse_tracer
    )
    print(f"   QA Tester initialized")

    devops_agent = AgentFactory.create_devops(
        rag_memory=rag_memory,
        tracer=langfuse_tracer
    )
    print(f"   DevOps initialized")

    designer_agent = AgentFactory.create_designer(
        rag_memory=rag_memory,
        tracer=langfuse_tracer
    )
    print(f"   Designer/UX initialized")

    security_auditor_agent = AgentFactory.create_security_auditor(
        rag_memory=rag_memory,
        tracer=langfuse_tracer
    )
    print(f"   Security Auditor initialized")

    ux_researcher_agent = AgentFactory.create_ux_researcher(
        rag_memory=rag_memory,
        tracer=langfuse_tracer
    )
    print(f"   UX Researcher initialized")

    # Initialize Department Manager (new organizational structure)
    print("\n🏢 Loading Organizational Structure...")
    import os
    config_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "departments")
    department_manager = DepartmentManager(
        config_dir=config_dir,
        rag_memory=rag_memory,
        tracer=langfuse_tracer
    )
    await department_manager.load_all_departments()

    # Inject department manager into router
    departments_router.set_department_manager(department_manager)

    # Initialize Collaboration Manager
    print("\n🤝 Initializing Collaboration Framework...")
    from app.collaboration.manager import CollaborationManager
    from app.collaboration.models import AgentRole

    agents_dict = {
        AgentRole.OVERSEER: overseer_agent,
        AgentRole.DEVELOPER: developer_agent,
        AgentRole.QA_TESTER: qa_tester_agent,
        AgentRole.DEVOPS: devops_agent,
        AgentRole.DESIGNER: designer_agent,
        AgentRole.SECURITY_AUDITOR: security_auditor_agent,
        AgentRole.UX_RESEARCHER: ux_researcher_agent
    }

    collaboration_manager = CollaborationManager(agents_dict=agents_dict)
    print("   ✅ Collaboration manager initialized with 7 agents")

    # Start background metrics task
    print("\n📊 Starting metrics background task...")
    global _metrics_task
    _metrics_task = asyncio.create_task(update_metrics_periodically())
    print("   ✅ Metrics task started")

    print("✅ Agent Service ready!")

    # Set health router dependencies
    health_router.set_health_dependencies(
        cache=cache,
        rag_memory=rag_memory,
        langfuse_tracer=langfuse_tracer,
        db_pool=db_pool,
        overseer_agent=overseer_agent,
        developer_agent=developer_agent,
        qa_tester_agent=qa_tester_agent,
        devops_agent=devops_agent,
        designer_agent=designer_agent,
        security_auditor_agent=security_auditor_agent,
        ux_researcher_agent=ux_researcher_agent,
        idempotency_cache=idempotency_cache
    )

    yield

    # Shutdown
    print("🛑 Shutting down Agent Service...")

    # Cancel metrics task
    if _metrics_task:
        _metrics_task.cancel()
        try:
            await _metrics_task
        except asyncio.CancelledError:
            pass
        print("   Metrics task stopped")

    if langfuse_tracer:
        langfuse_tracer.flush()
    if auth_client:
        await auth_client.close()
    if event_dispatcher:
        await event_dispatcher.close()
        print("   Event dispatcher closed")
    if db_pool:
        await db_pool.close()
        print("   Database pool closed")


app = FastAPI(
    title="Agentic Company - Agent Service",
    description="CrewAI agents with RAG and human-in-the-loop approvals",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter to app state
app.state.limiter = limiter

# Add rate limit exception handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router.router)
app.include_router(departments_router.router)
app.include_router(webhooks_router.router)
from app.routers import collaboration as collaboration_router
app.include_router(collaboration_router.router)

# Prometheus metrics
from prometheus_client import make_asgi_app
from app.metrics import MetricsRecorder, service_info

# Initialize service info
service_info.info({
    'version': '1.0.0',
    'service': 'agent-service',
    'environment': 'production'
})

# Mount prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.post("/overseer/run", response_model=AgentResponse)
@limiter.limit("20/minute")
async def run_overseer(
    request: Request,
    agent_request: AgentRequest,
    current_user: AuthContext = Depends(require_permission("agents:execute"))
):
    """
    Run the Overseer agent to coordinate and decompose goals.

    The Overseer:
    - Breaks down high-level goals into concrete tasks
    - Validates tasks against RAG knowledge base (≥2 citations required)
    - Routes tasks to appropriate agents (Developer, etc.)
    - Enforces budget and latency guardrails

    Requires: agents:execute permission
    """
    if not overseer_agent:
        raise HTTPException(status_code=503, detail="Overseer agent not initialized")

    # Check idempotency
    if agent_request.idempotency_key and agent_request.idempotency_key in idempotency_cache:
        return idempotency_cache[agent_request.idempotency_key]

    # Enforce budget
    if not enforce_budget(agent_request.task):
        raise HTTPException(
            status_code=400,
            detail=f"Task exceeds token budget of {settings.BUDGET_TOKENS_PER_TASK}"
        )

    task_id = str(uuid4())
    start_time = time.time()

    try:
        # Run agent
        result = await overseer_agent.execute(
            task=agent_request.task,
            context=agent_request.context or {},
            task_id=task_id
        )

        # Validate citations
        citations = result.get("citations", [])
        if not validate_citations(citations):
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient grounding: found {len(citations)} citations, need ≥2 with score ≥{settings.RAG_MIN_SCORE}"
            )

        # Check latency SLO
        latency_ms = int((time.time() - start_time) * 1000)
        if latency_ms > settings.LATENCY_SLO_MS:
            print(f"⚠️  SLO violated: {latency_ms}ms > {settings.LATENCY_SLO_MS}ms")

        # Count tokens asynchronously
        tokens_used = await count_tokens_async(str(result))

        response = AgentResponse(
            task_id=task_id,
            status="completed",
            result=result,
            citations=citations,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            model_info={
                "model": settings.get_model_for_agent("overseer"),
                "temperature": settings.MODEL_TEMPERATURE,
                "top_p": settings.MODEL_TOP_P,
                "max_tokens": settings.MODEL_MAX_TOKENS,
                "seed": settings.MODEL_SEED
            }
        )

        # Cache for idempotency
        if request.idempotency_key:
            idempotency_cache[request.idempotency_key] = response

        return response

    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return AgentResponse(
            task_id=task_id,
            status="failed",
            citations=[],
            tokens_used=0,
            latency_ms=latency_ms,
            model_info={"model": settings.get_model_for_agent("overseer")},
            error=str(e)
        )


@app.post("/developer/run", response_model=AgentResponse)
async def run_developer(
    request: AgentRequest,
    current_user: AuthContext = Depends(require_permission("agents:execute"))
):
    """
    Run the Developer agent to generate code (CRUD APIs, schemas, frontend components).

    The Developer:
    - Generates production-ready code with tests
    - Follows best practices from RAG knowledge base
    - Creates migrations, API endpoints, and UI components
    - Validates generated code syntax and structure

    Requires: agents:execute permission
    """
    if not developer_agent:
        raise HTTPException(status_code=503, detail="Developer agent not initialized")

    # Check idempotency
    if request.idempotency_key and request.idempotency_key in idempotency_cache:
        return idempotency_cache[request.idempotency_key]

    # Enforce budget
    if not enforce_budget(request.task):
        raise HTTPException(
            status_code=400,
            detail=f"Task exceeds token budget of {settings.BUDGET_TOKENS_PER_TASK}"
        )

    task_id = str(uuid4())
    start_time = time.time()

    # Publish task.started event
    if event_dispatcher:
        try:
            await event_dispatcher.publish_event(
                event_type=EventType.TASK_STARTED,
                event_id=task_id,
                source="agents",
                tenant_id=UUID(current_user.tenant_id),
                user_id=UUID(current_user.user_id),
                project_id=request.project_id,
                workflow_id=request.workflow_id,
                data={
                    "task_id": task_id,
                    "agent_name": "developer",
                    "task_description": request.task[:200],  # Truncate for event payload
                    "user_email": current_user.email,
                    "started_at": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            print(f"Failed to publish task.started event: {e}")

    try:
        # Run agent
        result = await developer_agent.execute(
            task=request.task,
            context=request.context or {},
            task_id=task_id
        )

        # Validate citations
        citations = result.get("citations", [])
        if not validate_citations(citations):
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient grounding: found {len(citations)} citations, need ≥2 with score ≥{settings.RAG_MIN_SCORE}"
            )

        # Check latency SLO
        latency_ms = int((time.time() - start_time) * 1000)
        if latency_ms > settings.LATENCY_SLO_MS:
            print(f"⚠️  SLO violated: {latency_ms}ms > {settings.LATENCY_SLO_MS}ms")

        # Count tokens asynchronously
        tokens_used = await count_tokens_async(str(result))

        # Record costs
        cost_info = await record_execution_cost(
            cost_tracker=cost_tracker,
            task_id=task_id,
            agent_name="developer",
            user_context=current_user,
            model_provider=settings.DEVELOPER_PROVIDER,
            model_name=settings.get_model_for_agent("developer"),
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            status="completed",
            project_id=request.project_id,
            workflow_id=request.workflow_id,
            citations_count=len(citations)
        )

        # Publish task.completed event
        if event_dispatcher:
            try:
                await event_dispatcher.publish_event(
                    event_type=EventType.TASK_COMPLETED,
                    event_id=task_id,
                    source="agents",
                    tenant_id=UUID(current_user.tenant_id),
                    user_id=UUID(current_user.user_id),
                    project_id=request.project_id,
                    workflow_id=request.workflow_id,
                    data={
                        "task_id": task_id,
                        "agent_name": "developer",
                        "status": "completed",
                        "tokens_used": tokens_used,
                        "latency_ms": latency_ms,
                        "cost_usd": cost_info.get("total_cost_usd") if cost_info else None,
                        "citations_count": len(citations),
                        "completed_at": datetime.utcnow().isoformat()
                    }
                )
            except Exception as e:
                print(f"Failed to publish task.completed event: {e}")

        response = AgentResponse(
            task_id=task_id,
            status="completed",
            result=result,
            citations=citations,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            model_info={
                "model": settings.get_model_for_agent("developer"),
                "temperature": settings.MODEL_TEMPERATURE,
                "top_p": settings.MODEL_TOP_P,
                "max_tokens": settings.MODEL_MAX_TOKENS,
                "seed": settings.MODEL_SEED,
                "agent": "developer"
            },
            cost_info=cost_info
        )

        # Cache for idempotency
        if request.idempotency_key:
            idempotency_cache[request.idempotency_key] = response

        return response

    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)

        # Record failed execution cost
        await record_execution_cost(
            cost_tracker=cost_tracker,
            task_id=task_id,
            agent_name="developer",
            user_context=current_user,
            model_provider=settings.DEVELOPER_PROVIDER,
            model_name=settings.get_model_for_agent("developer"),
            tokens_used=0,
            latency_ms=latency_ms,
            status="failed"
        )

        # Publish task.failed event
        if event_dispatcher:
            try:
                await event_dispatcher.publish_event(
                    event_type=EventType.TASK_FAILED,
                    event_id=task_id,
                    source="agents",
                    tenant_id=UUID(current_user.tenant_id),
                    user_id=UUID(current_user.user_id),
                    project_id=request.project_id,
                    workflow_id=request.workflow_id,
                    data={
                        "task_id": task_id,
                        "agent_name": "developer",
                        "error_message": str(e),
                        "latency_ms": latency_ms,
                        "failed_at": datetime.utcnow().isoformat()
                    }
                )
            except Exception as event_error:
                print(f"Failed to publish task.failed event: {event_error}")

        return AgentResponse(
            task_id=task_id,
            status="failed",
            citations=[],
            tokens_used=0,
            latency_ms=latency_ms,
            model_info={"model": settings.get_model_for_agent("developer")},
            error=str(e)
        )


@app.post("/qa-tester/run", response_model=AgentResponse)
async def run_qa_tester(
    request: AgentRequest,
    current_user: AuthContext = Depends(require_permission("agents:execute"))
):
    """
    Run the QA Tester agent to generate comprehensive test suites.

    The QA Tester:
    - Generates pytest test suites (unit, integration, E2E)
    - Calculates code coverage and identifies gaps
    - Creates test fixtures and mocks
    - Validates test quality with best practices
    - Aims for ≥80% code coverage

    Requires: agents:execute permission
    """
    if not qa_tester_agent:
        raise HTTPException(status_code=503, detail="QA Tester agent not initialized")

    # Check idempotency
    if request.idempotency_key and request.idempotency_key in idempotency_cache:
        return idempotency_cache[request.idempotency_key]

    # Enforce budget (QA tests need more tokens)
    if not enforce_budget(request.task, budget=settings.BUDGET_TOKENS_PER_TASK * 2):
        raise HTTPException(
            status_code=400,
            detail=f"Task exceeds token budget of {settings.BUDGET_TOKENS_PER_TASK * 2}"
        )

    task_id = str(uuid4())
    start_time = time.time()

    try:
        # Run agent
        result = await qa_tester_agent.execute(
            task=request.task,
            context=request.context or {},
            task_id=task_id
        )

        # Validate citations
        citations = result.get("citations", [])
        if not validate_citations(citations):
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient grounding: found {len(citations)} citations, need ≥2 with score ≥{settings.RAG_MIN_SCORE}"
            )

        # Check latency SLO (relaxed for test generation)
        latency_ms = int((time.time() - start_time) * 1000)
        if latency_ms > settings.LATENCY_SLO_MS * 2:
            print(f"⚠️  SLO violated: {latency_ms}ms > {settings.LATENCY_SLO_MS * 2}ms")

        # Count tokens asynchronously
        tokens_used = await count_tokens_async(str(result))

        response = AgentResponse(
            task_id=task_id,
            status="completed",
            result=result,
            citations=citations,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            model_info={
                "model": settings.get_model_for_agent("developer"),
                "temperature": settings.MODEL_TEMPERATURE,
                "top_p": settings.MODEL_TOP_P,
                "max_tokens": settings.MODEL_MAX_TOKENS * 2,
                "seed": settings.MODEL_SEED,
                "agent": "qa_tester"
            }
        )

        # Cache for idempotency
        if request.idempotency_key:
            idempotency_cache[request.idempotency_key] = response

        return response

    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return AgentResponse(
            task_id=task_id,
            status="failed",
            citations=[],
            tokens_used=0,
            latency_ms=latency_ms,
            model_info={"model": settings.get_model_for_agent("developer")},
            error=str(e)
        )


@app.post("/devops/run", response_model=AgentResponse)
async def run_devops(
    request: AgentRequest,
    current_user: AuthContext = Depends(require_permission("agents:execute"))
):
    """
    Run the DevOps agent to generate infrastructure code.

    The DevOps Agent:
    - Generates Kubernetes manifests (Deployments, Services, ConfigMaps)
    - Creates Terraform configurations for cloud infrastructure
    - Optimizes Docker builds (multi-stage, caching, security)
    - Generates CI/CD pipelines (GitHub Actions, GitLab CI)
    - Creates Helm charts for application deployment
    - Applies infrastructure best practices and security hardening

    Requires: agents:execute permission
    """
    if not devops_agent:
        raise HTTPException(status_code=503, detail="DevOps agent not initialized")

    # Check idempotency
    if request.idempotency_key and request.idempotency_key in idempotency_cache:
        return idempotency_cache[request.idempotency_key]

    # Enforce budget (Infrastructure needs more tokens)
    if not enforce_budget(request.task, budget=settings.BUDGET_TOKENS_PER_TASK * 2):
        raise HTTPException(
            status_code=400,
            detail=f"Task exceeds token budget of {settings.BUDGET_TOKENS_PER_TASK * 2}"
        )

    task_id = str(uuid4())
    start_time = time.time()

    try:
        # Run agent
        result = await devops_agent.execute(
            task=request.task,
            context=request.context or {},
            task_id=task_id
        )

        # Validate citations
        citations = result.get("citations", [])
        if not validate_citations(citations):
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient grounding: found {len(citations)} citations, need ≥2 with score ≥{settings.RAG_MIN_SCORE}"
            )

        # Check latency SLO (relaxed for infrastructure generation)
        latency_ms = int((time.time() - start_time) * 1000)
        if latency_ms > settings.LATENCY_SLO_MS * 2:
            print(f"⚠️  SLO violated: {latency_ms}ms > {settings.LATENCY_SLO_MS * 2}ms")

        # Count tokens asynchronously
        tokens_used = await count_tokens_async(str(result))

        response = AgentResponse(
            task_id=task_id,
            status="completed",
            result=result,
            citations=citations,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            model_info={
                "model": settings.get_model_for_agent("developer"),
                "temperature": settings.MODEL_TEMPERATURE,
                "top_p": settings.MODEL_TOP_P,
                "max_tokens": settings.MODEL_MAX_TOKENS * 2,
                "seed": settings.MODEL_SEED,
                "agent": "devops"
            }
        )

        # Cache for idempotency
        if request.idempotency_key:
            idempotency_cache[request.idempotency_key] = response

        return response

    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return AgentResponse(
            task_id=task_id,
            status="failed",
            citations=[],
            tokens_used=0,
            latency_ms=latency_ms,
            model_info={"model": settings.get_model_for_agent("developer")},
            error=str(e)
        )


@app.post("/designer/run", response_model=AgentResponse)
async def run_designer(
    request: AgentRequest,
    current_user: AuthContext = Depends(require_permission("agents:execute"))
):
    """
    Run the Designer/UX agent to generate UI/UX designs.

    The Designer/UX Agent:
    - Generates wireframes (ASCII art, Mermaid diagrams)
    - Creates design systems (color palettes, typography, spacing scales)
    - Generates component specifications with all variants and states
    - Creates design tokens (JSON, CSS, Tailwind formats)
    - Validates WCAG 2.1 Level AA accessibility compliance
    - Provides responsive design strategies (mobile, tablet, desktop)

    Requires: agents:execute permission
    """
    if not designer_agent:
        raise HTTPException(status_code=503, detail="Designer/UX agent not initialized")

    # Check idempotency
    if request.idempotency_key and request.idempotency_key in idempotency_cache:
        return idempotency_cache[request.idempotency_key]

    # Enforce budget (Design needs more tokens)
    if not enforce_budget(request.task, budget=settings.BUDGET_TOKENS_PER_TASK * 2):
        raise HTTPException(
            status_code=400,
            detail=f"Task exceeds token budget of {settings.BUDGET_TOKENS_PER_TASK * 2}"
        )

    task_id = str(uuid4())
    start_time = time.time()

    try:
        # Run agent
        result = await designer_agent.execute(
            task=request.task,
            context=request.context or {},
            task_id=task_id
        )

        # Validate citations
        citations = result.get("citations", [])
        if not validate_citations(citations):
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient grounding: found {len(citations)} citations, need ≥2 with score ≥{settings.RAG_MIN_SCORE}"
            )

        # Check latency SLO (relaxed for design generation)
        latency_ms = int((time.time() - start_time) * 1000)
        if latency_ms > settings.LATENCY_SLO_MS * 2:
            print(f"⚠️  SLO violated: {latency_ms}ms > {settings.LATENCY_SLO_MS * 2}ms")

        # Count tokens asynchronously
        tokens_used = await count_tokens_async(str(result))

        response = AgentResponse(
            task_id=task_id,
            status="completed",
            result=result,
            citations=citations,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            model_info={
                "model": settings.get_model_for_agent("developer"),
                "temperature": 0.3,  # Slightly higher for creative design
                "top_p": settings.MODEL_TOP_P,
                "max_tokens": settings.MODEL_MAX_TOKENS * 2,
                "seed": settings.MODEL_SEED,
                "agent": "designer"
            }
        )

        # Cache for idempotency
        if request.idempotency_key:
            idempotency_cache[request.idempotency_key] = response

        return response

    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return AgentResponse(
            task_id=task_id,
            status="failed",
            citations=[],
            tokens_used=0,
            latency_ms=latency_ms,
            model_info={"model": settings.get_model_for_agent("developer")},
            error=str(e)
        )


@app.post("/security-auditor/run", response_model=AgentResponse)
async def run_security_auditor(
    request: AgentRequest,
    current_user: AuthContext = Depends(require_permission("agents:execute"))
):
    """
    Run the Security Auditor agent to scan for vulnerabilities.

    The Security Auditor Agent:
    - Scans code for OWASP Top 10:2021 vulnerabilities
    - Checks for common security issues (SQL injection, XSS, CSRF, etc.)
    - Validates authentication and authorization patterns
    - Scans dependencies for known CVEs
    - Detects hardcoded secrets and credentials
    - Validates security headers and configurations
    - Generates security reports with severity ratings (Critical/High/Medium/Low)

    Requires: agents:execute permission
    """
    if not security_auditor_agent:
        raise HTTPException(status_code=503, detail="Security Auditor agent not initialized")

    # Check idempotency
    if request.idempotency_key and request.idempotency_key in idempotency_cache:
        return idempotency_cache[request.idempotency_key]

    # Enforce budget (Security audit needs more tokens)
    if not enforce_budget(request.task, budget=settings.BUDGET_TOKENS_PER_TASK * 2):
        raise HTTPException(
            status_code=400,
            detail=f"Task exceeds token budget of {settings.BUDGET_TOKENS_PER_TASK * 2}"
        )

    task_id = str(uuid4())
    start_time = time.time()

    try:
        # Run agent
        result = await security_auditor_agent.execute(
            task=request.task,
            context=request.context or {},
            task_id=task_id
        )

        # Validate citations
        citations = result.get("citations", [])
        if not validate_citations(citations):
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient grounding: found {len(citations)} citations, need ≥2 with score ≥{settings.RAG_MIN_SCORE}"
            )

        # Check latency SLO (relaxed for security analysis)
        latency_ms = int((time.time() - start_time) * 1000)
        if latency_ms > settings.LATENCY_SLO_MS * 2:
            print(f"⚠️  SLO violated: {latency_ms}ms > {settings.LATENCY_SLO_MS * 2}ms")

        # Count tokens asynchronously
        tokens_used = await count_tokens_async(str(result))

        response = AgentResponse(
            task_id=task_id,
            status="completed",
            result=result,
            citations=citations,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            model_info={
                "model": settings.get_model_for_agent("developer"),
                "temperature": 0.1,  # Very low for precise security analysis
                "top_p": settings.MODEL_TOP_P,
                "max_tokens": settings.MODEL_MAX_TOKENS * 2,
                "seed": settings.MODEL_SEED,
                "agent": "security_auditor"
            }
        )

        # Cache for idempotency
        if request.idempotency_key:
            idempotency_cache[request.idempotency_key] = response

        return response

    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return AgentResponse(
            task_id=task_id,
            status="failed",
            citations=[],
            tokens_used=0,
            latency_ms=latency_ms,
            model_info={"model": settings.get_model_for_agent("developer")},
            error=str(e)
        )


@app.post("/ux-researcher/run", response_model=AgentResponse)
async def run_ux_researcher(
    request: AgentRequest,
    current_user: AuthContext = Depends(require_permission("agents:execute"))
):
    """
    Run the UX Researcher agent to conduct user research.

    The UX Researcher Agent:
    - Creates detailed user personas with motivations and pain points
    - Generates user journey maps for different scenarios
    - Conducts competitive analysis and market research
    - Analyzes user feedback to identify patterns and insights
    - Creates survey questions and interview scripts
    - Generates usability testing plans
    - Provides actionable recommendations based on research

    Requires: agents:execute permission
    """
    if not ux_researcher_agent:
        raise HTTPException(status_code=503, detail="UX Researcher agent not initialized")

    # Check idempotency
    if request.idempotency_key and request.idempotency_key in idempotency_cache:
        return idempotency_cache[request.idempotency_key]

    # Enforce budget (Research needs more tokens)
    if not enforce_budget(request.task, budget=settings.BUDGET_TOKENS_PER_TASK * 2):
        raise HTTPException(
            status_code=400,
            detail=f"Task exceeds token budget of {settings.BUDGET_TOKENS_PER_TASK * 2}"
        )

    task_id = str(uuid4())
    start_time = time.time()

    try:
        # Run agent
        result = await ux_researcher_agent.execute(
            task=request.task,
            context=request.context or {},
            task_id=task_id
        )

        # Validate citations
        citations = result.get("citations", [])
        if not validate_citations(citations):
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient grounding: found {len(citations)} citations, need ≥2 with score ≥{settings.RAG_MIN_SCORE}"
            )

        # Check latency SLO (relaxed for research)
        latency_ms = int((time.time() - start_time) * 1000)
        if latency_ms > settings.LATENCY_SLO_MS * 2:
            print(f"⚠️  SLO violated: {latency_ms}ms > {settings.LATENCY_SLO_MS * 2}ms")

        # Count tokens asynchronously
        tokens_used = await count_tokens_async(str(result))

        response = AgentResponse(
            task_id=task_id,
            status="completed",
            result=result,
            citations=citations,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            model_info={
                "model": settings.get_model_for_agent("developer"),
                "temperature": 0.4,  # Higher for creative persona development
                "top_p": settings.MODEL_TOP_P,
                "max_tokens": settings.MODEL_MAX_TOKENS * 2,
                "seed": settings.MODEL_SEED,
                "agent": "ux_researcher"
            }
        )

        # Cache for idempotency
        if request.idempotency_key:
            idempotency_cache[request.idempotency_key] = response

        return response

    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return AgentResponse(
            task_id=task_id,
            status="failed",
            citations=[],
            tokens_used=0,
            latency_ms=latency_ms,
            model_info={"model": settings.get_model_for_agent("developer")},
            error=str(e)
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
