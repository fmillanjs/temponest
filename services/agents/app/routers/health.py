"""
Health and metrics API endpoints.
Extracted from main.py to improve code organization.
"""

from fastapi import APIRouter, Depends
from typing import Optional
from shared.auth import AuthContext, require_permission
from app.models import HealthResponse
from app.settings import settings

router = APIRouter(tags=["health"])

# Global state (injected from main.py)
_cache: Optional[any] = None
_rag_memory: Optional[any] = None
_langfuse_tracer: Optional[any] = None
_db_pool: Optional[any] = None
_overseer_agent: Optional[any] = None
_developer_agent: Optional[any] = None
_qa_tester_agent: Optional[any] = None
_devops_agent: Optional[any] = None
_designer_agent: Optional[any] = None
_security_auditor_agent: Optional[any] = None
_ux_researcher_agent: Optional[any] = None
_idempotency_cache: Optional[dict] = None


def set_health_dependencies(
    cache=None,
    rag_memory=None,
    langfuse_tracer=None,
    db_pool=None,
    overseer_agent=None,
    developer_agent=None,
    qa_tester_agent=None,
    devops_agent=None,
    designer_agent=None,
    security_auditor_agent=None,
    ux_researcher_agent=None,
    idempotency_cache=None
):
    """Set global dependencies for health endpoints"""
    global _cache, _rag_memory, _langfuse_tracer, _db_pool
    global _overseer_agent, _developer_agent, _qa_tester_agent, _devops_agent
    global _designer_agent, _security_auditor_agent, _ux_researcher_agent
    global _idempotency_cache

    _cache = cache
    _rag_memory = rag_memory
    _langfuse_tracer = langfuse_tracer
    _db_pool = db_pool
    _overseer_agent = overseer_agent
    _developer_agent = developer_agent
    _qa_tester_agent = qa_tester_agent
    _devops_agent = devops_agent
    _designer_agent = designer_agent
    _security_auditor_agent = security_auditor_agent
    _ux_researcher_agent = ux_researcher_agent
    _idempotency_cache = idempotency_cache


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint with Redis caching.

    Cache Key: health:agents
    TTL: 10 seconds
    """
    cache_key = "health:agents"

    # Try to get from cache
    if _cache:
        try:
            cached_health = await _cache.get(cache_key)
            if cached_health:
                return HealthResponse(**cached_health)
        except Exception as e:
            print(f"Health check cache read error: {e}")

    # Cache miss - check health
    qdrant_healthy = _rag_memory and _rag_memory.is_healthy()
    langfuse_healthy = _langfuse_tracer and _langfuse_tracer.is_healthy()
    database_healthy = _db_pool is not None

    services = {
        "qdrant": "healthy" if qdrant_healthy else "unhealthy",
        "langfuse": "healthy" if langfuse_healthy else "unhealthy",
        "database": "healthy" if database_healthy else "unhealthy",
        "cache": "healthy" if _cache else "unhealthy",
        "overseer": "ready" if _overseer_agent else "not_initialized",
        "developer": "ready" if _developer_agent else "not_initialized",
        "qa_tester": "ready" if _qa_tester_agent else "not_initialized",
        "devops": "ready" if _devops_agent else "not_initialized",
        "designer": "ready" if _designer_agent else "not_initialized",
        "security_auditor": "ready" if _security_auditor_agent else "not_initialized",
        "ux_researcher": "ready" if _ux_researcher_agent else "not_initialized",
    }

    # Update Prometheus metrics
    from app.metrics import MetricsRecorder, db_pool_size, agent_service_health
    MetricsRecorder.update_service_health("qdrant", qdrant_healthy)
    MetricsRecorder.update_service_health("langfuse", langfuse_healthy)
    MetricsRecorder.update_service_health("database", database_healthy)

    # Set agent service health (1 if overall healthy)
    agent_service_health.set(1.0 if all(v in ["healthy", "ready"] for v in services.values()) else 0.0)

    # Update database pool metrics
    if _db_pool:
        pool_size = _db_pool.get_size()
        pool_free = _db_pool.get_idle_size()
        pool_in_use = pool_size - pool_free
        db_pool_size.labels(pool_type="size").set(pool_size)
        db_pool_size.labels(pool_type="available").set(pool_free)
        db_pool_size.labels(pool_type="in_use").set(pool_in_use)

    health_response = HealthResponse(
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

    # Cache for 10 seconds
    if _cache:
        try:
            await _cache.set(cache_key, health_response.dict(), ttl=10)
        except Exception as e:
            print(f"Health check cache write error: {e}")

    return health_response


@router.get("/api/metrics")
async def get_api_metrics(
    current_user: AuthContext = Depends(require_permission("agents:read"))
):
    """
    Get operational metrics (application-level).

    Requires: agents:read permission
    """
    return {
        "idempotency_cache_size": len(_idempotency_cache) if _idempotency_cache else 0,
        "rag_collection_size": await _rag_memory.get_collection_size() if _rag_memory else 0,
        "langfuse_traces": _langfuse_tracer.get_trace_count() if _langfuse_tracer else 0,
        "tenant_id": current_user.tenant_id
    }
