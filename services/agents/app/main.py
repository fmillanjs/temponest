"""
Agentic Company - Agent Service
FastAPI application that exposes CrewAI agents (Overseer, Developer) with RAG and Langfuse tracing.
"""

import time
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import tiktoken

from settings import settings
from agents.overseer import OverseerAgent
from agents.developer import DeveloperAgent
from memory.rag import RAGMemory
from memory.langfuse_tracer import LangfuseTracer


# Request/Response Models
class AgentRequest(BaseModel):
    """Request to invoke an agent"""
    task: str = Field(..., description="Task description for the agent")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    idempotency_key: Optional[str] = Field(default=None, description="Idempotency key for mutations")
    risk_level: str = Field(default="low", description="Risk level: low, medium, high")


class AgentResponse(BaseModel):
    """Response from agent invocation"""
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    tokens_used: int
    latency_ms: int
    model_info: Dict[str, Any]
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    services: Dict[str, str]
    models: Dict[str, str]


# Global state
rag_memory: Optional[RAGMemory] = None
langfuse_tracer: Optional[LangfuseTracer] = None
overseer_agent: Optional[OverseerAgent] = None
developer_agent: Optional[DeveloperAgent] = None
idempotency_cache: Dict[str, AgentResponse] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic"""
    global rag_memory, langfuse_tracer, overseer_agent, developer_agent

    # Startup
    print("🚀 Starting Agent Service...")

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

    # Initialize agents
    overseer_agent = OverseerAgent(
        rag_memory=rag_memory,
        tracer=langfuse_tracer,
        chat_model=settings.CHAT_MODEL,
        temperature=settings.MODEL_TEMPERATURE,
        top_p=settings.MODEL_TOP_P,
        max_tokens=settings.MODEL_MAX_TOKENS,
        seed=settings.MODEL_SEED
    )

    developer_agent = DeveloperAgent(
        rag_memory=rag_memory,
        tracer=langfuse_tracer,
        code_model=settings.CODE_MODEL,
        temperature=settings.MODEL_TEMPERATURE,
        top_p=settings.MODEL_TOP_P,
        max_tokens=settings.MODEL_MAX_TOKENS,
        seed=settings.MODEL_SEED
    )

    print("✅ Agent Service ready!")

    yield

    # Shutdown
    print("🛑 Shutting down Agent Service...")
    if langfuse_tracer:
        langfuse_tracer.flush()


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


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    services = {
        "qdrant": "healthy" if rag_memory and rag_memory.is_healthy() else "unhealthy",
        "langfuse": "healthy" if langfuse_tracer and langfuse_tracer.is_healthy() else "unhealthy",
        "overseer": "ready" if overseer_agent else "not_initialized",
        "developer": "ready" if developer_agent else "not_initialized",
    }

    return HealthResponse(
        status="healthy" if all(v in ["healthy", "ready"] for v in services.values()) else "degraded",
        services=services,
        models={
            "chat": settings.CHAT_MODEL,
            "code": settings.CODE_MODEL,
            "embedding": settings.EMBEDDING_MODEL
        }
    )


@app.post("/overseer/run", response_model=AgentResponse)
async def run_overseer(request: AgentRequest):
    """
    Run the Overseer agent to coordinate and decompose goals.

    The Overseer:
    - Breaks down high-level goals into concrete tasks
    - Validates tasks against RAG knowledge base (≥2 citations required)
    - Routes tasks to appropriate agents (Developer, etc.)
    - Enforces budget and latency guardrails
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
                "model": settings.CHAT_MODEL,
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
            model_info={"model": settings.CHAT_MODEL},
            error=str(e)
        )


@app.post("/developer/run", response_model=AgentResponse)
async def run_developer(request: AgentRequest):
    """
    Run the Developer agent to generate code (CRUD APIs, schemas, frontend components).

    The Developer:
    - Generates production-ready code with tests
    - Follows best practices from RAG knowledge base
    - Creates migrations, API endpoints, and UI components
    - Validates generated code syntax and structure
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

        response = AgentResponse(
            task_id=task_id,
            status="completed",
            result=result,
            citations=citations,
            tokens_used=count_tokens(str(result)),
            latency_ms=latency_ms,
            model_info={
                "model": settings.CODE_MODEL,
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
            model_info={"model": settings.CODE_MODEL},
            error=str(e)
        )


@app.get("/metrics")
async def get_metrics():
    """Get operational metrics"""
    return {
        "idempotency_cache_size": len(idempotency_cache),
        "rag_collection_size": await rag_memory.get_collection_size() if rag_memory else 0,
        "langfuse_traces": langfuse_tracer.get_trace_count() if langfuse_tracer else 0
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
