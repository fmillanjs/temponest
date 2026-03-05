# Coding Conventions

**Analysis Date:** 2026-03-04

## Naming Patterns

**Files:**
- Snake_case for all Python modules: `cost_calculator.py`, `webhook_manager.py`, `langfuse_tracer.py`
- Test files prefixed with `test_`: `test_cost_calculator.py`, `test_developer.py`
- Config files in `pytest.ini` format per service (not pyproject.toml)

**Functions:**
- Snake_case for all functions and methods: `calculate_cost()`, `record_execution_cost()`, `count_tokens_async()`
- Async functions suffixed with `_async` when a sync sibling also exists: `count_tokens` / `count_tokens_async`, `enforce_budget` / `enforce_budget_async`
- Private methods prefixed with `_`: `_create_search_code_examples_tool()`, `_format_examples()`, `_identify_task_type()`
- Factory methods prefixed with `create_`: `AgentFactory.create_overseer()`, `AgentFactory.create_developer()`

**Variables:**
- Snake_case for local variables and instance attributes: `task_id`, `start_time`, `latency_ms`
- UPPER_SNAKE_CASE for settings/constants: `BUDGET_TOKENS_PER_TASK`, `LATENCY_SLO_MS`, `REQUIRE_CITATIONS`
- Optional globals initialized to `None` with type annotation: `rag_memory: Optional[RAGMemory] = None`

**Classes:**
- PascalCase for all classes: `CostCalculator`, `DeveloperAgent`, `WebhookManager`, `TempoNestException`
- Test classes prefixed with `Test`: `TestDeveloperAgent`, `TestCostCalculator`, `TestRAGMemory`

**Routes/Endpoints:**
- Kebab-case URL paths: `/overseer/run`, `/qa-tester/run`, `/security-auditor/run`
- Router modules in `app/routers/` directory: `departments.py`, `webhooks.py`, `health.py`

## Code Style

**Formatting:**
- Black is listed in `requirements-test.txt` as `black>=23.7.0,<24.0.0`
- isort for import sorting: `isort>=5.12.0,<6.0.0`
- No observed `.prettierrc` or `pyproject.toml` black config; enforcement is manual/CI

**Linting:**
- flake8: `flake8>=6.1.0,<7.0.0`
- mypy: `mypy>=1.5.0,<2.0.0`
- bandit for security: `bandit>=1.7.0,<2.0.0`
- safety for dependency scanning: `safety>=2.3.0,<3.0.0`

## Import Organization

**Order (observed pattern):**
1. Standard library: `import os`, `import asyncio`, `import time`, `import json`, `import re`
2. Third-party: `from fastapi import ...`, `from pydantic import ...`, `from crewai import ...`
3. Local/shared: `from shared.auth import ...`, `from app.settings import settings`
4. Within-service: `from app.cost.calculator import CostCalculator`

**Path Aliases:**
- `shared.*` maps to `/home/doctor/temponest/shared/` — used for cross-service utilities
- No `__init__.py` barrel pattern for `app/` subdirectories; explicit per-module imports

**Conditional imports:** Heavy dependencies (e.g., `CollaborationManager`) are imported inline inside `lifespan()` to avoid circular imports.

## Error Handling

**Patterns:**
- FastAPI endpoints use `HTTPException` for HTTP-level errors:
  ```python
  raise HTTPException(status_code=503, detail="Overseer agent not initialized")
  raise HTTPException(status_code=400, detail=f"Task exceeds token budget of {settings.BUDGET_TOKENS_PER_TASK}")
  ```
- Business logic uses typed exceptions from `shared/exceptions.py` inheriting `TempoNestException`:
  - `AuthenticationError` (401), `AuthorizationError` (403), `ResourceNotFoundError` (404)
  - `ValidationError` (422), `BudgetExceededError`, `CitationValidationError`
  - `ServiceUnavailableError` (503), `DatabaseError` (500), `AgentExecutionError` (500)
- Non-critical failures (cache, event dispatch) are caught and logged with `print(f"Failed to ...: {e}")` — execution continues
- Agent endpoint failure pattern: catch all exceptions, return `AgentResponse(status="failed", error=str(e))` rather than raising

**Agent endpoint try/except template (use this pattern for all agent routes):**
```python
try:
    result = await agent.execute(task=request.task, context=request.context or {}, task_id=task_id)
    citations = result.get("citations", [])
    if settings.REQUIRE_CITATIONS and not validate_citations(citations):
        raise HTTPException(status_code=400, detail="Insufficient grounding: ...")
    latency_ms = int((time.time() - start_time) * 1000)
    tokens_used = await count_tokens_async(str(result))
    return AgentResponse(task_id=task_id, status="completed", ...)
except Exception as e:
    latency_ms = int((time.time() - start_time) * 1000)
    return AgentResponse(task_id=task_id, status="failed", citations=[], tokens_used=0, latency_ms=latency_ms, model_info={...}, error=str(e))
```

## Logging

**Framework:** Python stdlib `logging` wrapped in `shared/logging_config.py` as `ServiceLogger`.

**Configuration:** `setup_logging(service_name, log_level)` returns a configured `logging.Logger`. Format: `"%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"`

**Patterns:**
- Startup/shutdown logging uses `print()` with emoji directly in `main.py` lifespan (not `ServiceLogger`)
- `ServiceLogger` emoji conventions: startup=`🚀`, shutdown=`🛑`, success=`✅`, warning=`⚠️`, error=`❌`, critical=`🚨`
- Non-critical errors (cost tracking, event dispatch) use `print(f"Failed to ...: {e}")` inline
- In production code, avoid `print()` — use `ServiceLogger` from `shared/logging_config.py`

## Comments

**When to Comment:**
- Module-level docstrings on every file describing purpose and responsibilities
- Class docstrings: brief one-liner `"""Calculate costs for LLM API usage"""`
- Method docstrings with Args/Returns when non-obvious
- Inline comments for non-obvious logic and configuration sections (e.g., `# OPTIMIZED: Tuned connection pool`)

**Section dividers in conftest.py:**
```python
# ============================================================
# SECTION NAME
# ============================================================
```

**Docstring style:** NumPy-style Args/Returns blocks (not Google style):
```python
def calculate_cost(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> Tuple[Decimal, Decimal, Decimal]:
    """
    Calculate cost for LLM usage.

    Args:
        provider: Model provider (claude, openai, ollama)
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Tuple of (input_cost_usd, output_cost_usd, total_cost_usd)
    """
```

## Function Design

**Size:** Agent endpoint handlers in `main.py` are 50-100 lines; extract helpers to `utils.py`

**Parameters:** Dependencies injected via constructor (not global lookups):
```python
class DeveloperAgent:
    def __init__(self, rag_memory: RAGMemory, tracer: LangfuseTracer, code_model: str, temperature: float = 0.2, ...)
```

**Async:** All I/O-bound operations are async (`async def`). Sync wrappers provided when needed (`enforce_budget` / `enforce_budget_async`). CPU-bound sync work offloaded with `asyncio.to_thread()`.

**Return Values:**
- Agent `execute()` methods return `Dict[str, Any]`
- API endpoints return Pydantic models (`AgentResponse`, `AgentRequest`)
- Cost methods return `Tuple[Decimal, Decimal, Decimal]` for (input, output, total)
- Optional returns typed as `Optional[T]` and documented

## Settings Pattern

Settings loaded from environment using `pydantic_settings.BaseSettings`:
```python
class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://..."
    LANGFUSE_PUBLIC_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()  # Singleton at module level
```

Use `settings.*` for all configuration — never hardcode URLs or keys.

## Module Design

**Exports:** Important modules expose `__all__` in `__init__.py`:
```python
# shared/webhooks/__init__.py
from .event_dispatcher import EventDispatcher
from .webhook_manager import WebhookManager
__all__ = ["EventDispatcher", "WebhookManager", ...]
```

**Barrel Files:** Used sparingly. `app/routers/` modules expose a `router` and a `set_*()` injection function:
```python
# app/routers/webhooks.py
router = APIRouter()
_webhook_manager: Optional[WebhookManager] = None

def set_webhook_manager(manager: WebhookManager):
    global _webhook_manager
    _webhook_manager = manager
```

---

*Convention analysis: 2026-03-04*
