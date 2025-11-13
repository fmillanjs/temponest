"""
Utility functions for the agents service.
Extracted from main.py to improve code organization.
"""

import asyncio
import tiktoken
from typing import Dict, Any, List, Optional
from shared.auth import AuthContext
from app.settings import settings


# Token counting utilities
def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Count tokens in text using tiktoken (synchronous)"""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


async def count_tokens_async(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Count tokens in text using tiktoken (async wrapper)"""
    return await asyncio.to_thread(count_tokens, text, model)


# Guardrail: Budget enforcement
def enforce_budget(text: str, budget: int = settings.BUDGET_TOKENS_PER_TASK) -> bool:
    """Check if text fits within token budget"""
    tokens = count_tokens(text)
    return tokens <= budget


async def enforce_budget_async(text: str, budget: int = settings.BUDGET_TOKENS_PER_TASK) -> bool:
    """Check if text fits within token budget (async)"""
    tokens = await count_tokens_async(text)
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
    cost_tracker,  # CostTracker instance
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
