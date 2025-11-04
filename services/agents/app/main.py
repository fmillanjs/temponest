"""
Agentic Company - Agent Service
FastAPI application that exposes CrewAI agents (Overseer, Developer) with RAG and Langfuse tracing.
"""

import time
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from decimal import Decimal
import asyncpg

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import tiktoken

from settings import settings
from agents.factory import AgentFactory
from memory.rag import RAGMemory
from memory.langfuse_tracer import LangfuseTracer
from departments.manager import DepartmentManager
from routers import departments as departments_router
from auth_client import AuthClient, AuthContext
from auth_middleware import (
    set_auth_client,
    get_current_user,
    require_permission,
    require_any_permission
)
from cost.calculator import CostCalculator
from cost.tracker import CostTracker
from webhooks import EventDispatcher, WebhookManager, EventType
from routers import webhooks as webhooks_router


# Request/Response Models
class AgentRequest(BaseModel):
    """Request to invoke an agent"""
    task: str = Field(..., description="Task description for the agent")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    idempotency_key: Optional[str] = Field(default=None, description="Idempotency key for mutations")
    risk_level: str = Field(default="low", description="Risk level: low, medium, high")
    project_id: Optional[str] = Field(default=None, description="Project ID for cost tracking")
    workflow_id: Optional[str] = Field(default=None, description="Workflow ID for cost tracking")


class AgentResponse(BaseModel):
    """Response from agent invocation"""
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    tokens_used: int
    latency_ms: int
    model_info: Dict[str, Any]
    cost_info: Optional[Dict[str, Any]] = None  # Cost tracking info
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    services: Dict[str, str]
    models: Dict[str, str]


# Global state
rag_memory: Optional[RAGMemory] = None
langfuse_tracer: Optional[LangfuseTracer] = None
overseer_agent: Optional[Any] = None  # Can be OverseerAgent or future OverseerAgentV2
developer_agent: Optional[Any] = None  # Can be DeveloperAgent or DeveloperAgentV2
qa_tester_agent: Optional[Any] = None  # QA Tester Agent
devops_agent: Optional[Any] = None  # DevOps Agent
designer_agent: Optional[Any] = None  # Designer/UX Agent
security_auditor_agent: Optional[Any] = None  # Security Auditor Agent
department_manager: Optional[DepartmentManager] = None
idempotency_cache: Dict[str, AgentResponse] = {}

# Cost tracking
db_pool: Optional[asyncpg.Pool] = None
cost_calculator: Optional[CostCalculator] = None
cost_tracker: Optional[CostTracker] = None

# Webhook system
webhook_manager: Optional[WebhookManager] = None
event_dispatcher: Optional[EventDispatcher] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic"""
    global rag_memory, langfuse_tracer, overseer_agent, developer_agent, qa_tester_agent, devops_agent, designer_agent, security_auditor_agent, department_manager
    global db_pool, cost_calculator, cost_tracker
    global webhook_manager, event_dispatcher

    # Startup
    print("🚀 Starting Agent Service...")

    # Initialize database pool for cost tracking
    print("💾 Initializing cost tracking...")
    try:
        db_pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        print("   ✅ Database pool created")

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

        # Initialize cost calculator and tracker
        cost_calculator = CostCalculator(db_pricing=db_pricing)
        cost_tracker = CostTracker(db_pool=db_pool, calculator=cost_calculator)
        print("   ✅ Cost tracking initialized")

        # Initialize webhook system
        webhook_manager = WebhookManager(db_pool=db_pool)
        event_dispatcher = EventDispatcher(db_pool=db_pool)
        webhooks_router.set_webhook_manager(webhook_manager)
        print("   ✅ Webhook system initialized")

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
        jwt_secret=settings.JWT_SECRET_KEY
    )
    set_auth_client(auth_client)
    print(f"   Auth client configured: {settings.AUTH_SERVICE_URL}")

    # Initialize RAG memory
    rag_memory = RAGMemory(
        qdrant_url=settings.QDRANT_URL,
        collection_name="agentic_knowledge",
        embedding_model=settings.EMBEDDING_MODEL
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

    print("✅ Agent Service ready!")

    yield

    # Shutdown
    print("🛑 Shutting down Agent Service...")
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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(departments_router.router)
app.include_router(webhooks_router.router)


# Token counting utility
def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Count tokens in text using tiktoken"""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


# Guardrail: Budget enforcement
def enforce_budget(text: str, budget: int = settings.BUDGET_TOKENS_PER_TASK) -> bool:
    """Check if text fits within token budget"""
    tokens = count_tokens(text)
    return tokens <= budget


# Guardrail: Citation validation
def validate_citations(citations: List[Dict[str, Any]]) -> bool:
    """Ensure at least 2 relevant citations"""
    if len(citations) < 2:
        return False

    # Check that citations have required fields
    for citation in citations[:2]:
        if not all(key in citation for key in ["source", "version", "score"]):
            return False
        if citation["score"] < settings.RAG_MIN_SCORE:
            return False

    return True


# Cost tracking helper
async def record_execution_cost(
    task_id: str,
    agent_name: str,
    user_context: AuthContext,
    model_provider: str,
    model_name: str,
    tokens_used: int,
    latency_ms: int,
    status: str = "completed",
    project_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    citations_count: int = 0
) -> Optional[Dict[str, Any]]:
    """Record execution cost and check budgets"""
    if not cost_tracker:
        return None

    try:
        # Estimate input/output split (rough heuristic: 40% input, 60% output)
        input_tokens = int(tokens_used * 0.4)
        output_tokens = tokens_used - input_tokens

        # Record execution
        cost_info = await cost_tracker.record_execution(
            task_id=task_id,
            agent_name=agent_name,
            user_id=user_context.user_id,
            tenant_id=user_context.tenant_id,
            model_provider=model_provider,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            status=status,
            project_id=project_id,
            workflow_id=workflow_id,
            context={"citations_count": citations_count}
        )

        return cost_info

    except Exception as e:
        print(f"Failed to record cost: {e}")
        return None


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    services = {
        "qdrant": "healthy" if rag_memory and rag_memory.is_healthy() else "unhealthy",
        "langfuse": "healthy" if langfuse_tracer and langfuse_tracer.is_healthy() else "unhealthy",
        "overseer": "ready" if overseer_agent else "not_initialized",
        "developer": "ready" if developer_agent else "not_initialized",
        "qa_tester": "ready" if qa_tester_agent else "not_initialized",
        "devops": "ready" if devops_agent else "not_initialized",
        "designer": "ready" if designer_agent else "not_initialized",
        "security_auditor": "ready" if security_auditor_agent else "not_initialized",
    }

    return HealthResponse(
        status="healthy" if all(v in ["healthy", "ready"] for v in services.values()) else "degraded",
        services=services,
        models={
            "overseer_provider": settings.OVERSEER_PROVIDER,
            "overseer_model": settings.get_model_for_agent("overseer"),
            "developer_provider": settings.DEVELOPER_PROVIDER,
            "developer_model": settings.get_model_for_agent("developer"),
            "embedding": settings.EMBEDDING_MODEL
        }
    )


@app.post("/overseer/run", response_model=AgentResponse)
async def run_overseer(
    request: AgentRequest,
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

    try:
        # Run agent
        result = await overseer_agent.execute(
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

        response = AgentResponse(
            task_id=task_id,
            status="completed",
            result=result,
            citations=citations,
            tokens_used=count_tokens(str(result)),
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

        tokens_used = count_tokens(str(result))

        # Record costs
        cost_info = await record_execution_cost(
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
            task_id=task_id,
            agent_name="developer",
            user_context=current_user,
            model_provider=settings.DEVELOPER_PROVIDER,
            model_name=settings.get_model_for_agent("developer"),
            tokens_used=0,
            latency_ms=latency_ms,
            status="failed"
        )

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

        response = AgentResponse(
            task_id=task_id,
            status="completed",
            result=result,
            citations=citations,
            tokens_used=count_tokens(str(result)),
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

        response = AgentResponse(
            task_id=task_id,
            status="completed",
            result=result,
            citations=citations,
            tokens_used=count_tokens(str(result)),
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

        response = AgentResponse(
            task_id=task_id,
            status="completed",
            result=result,
            citations=citations,
            tokens_used=count_tokens(str(result)),
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

        response = AgentResponse(
            task_id=task_id,
            status="completed",
            result=result,
            citations=citations,
            tokens_used=count_tokens(str(result)),
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


@app.get("/metrics")
async def get_metrics(
    current_user: AuthContext = Depends(require_permission("agents:read"))
):
    """
    Get operational metrics.

    Requires: agents:read permission
    """
    return {
        "idempotency_cache_size": len(idempotency_cache),
        "rag_collection_size": await rag_memory.get_collection_size() if rag_memory else 0,
        "langfuse_traces": langfuse_tracer.get_trace_count() if langfuse_tracer else 0,
        "tenant_id": current_user.tenant_id
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
