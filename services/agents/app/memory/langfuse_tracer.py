"""
Langfuse Tracer - LLM observability with RAG citation tracking.
Traces all agent executions, model calls, and retrieval operations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context
import json


class LangfuseTracer:
    """Langfuse integration for tracing LLM calls and RAG operations"""

    def __init__(
        self,
        public_key: Optional[str],
        secret_key: Optional[str],
        host: str = "http://langfuse:3000"
    ):
        self.enabled = bool(public_key and secret_key)

        if self.enabled:
            self.client = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=host
            )
            print("✅ Langfuse tracer initialized")
        else:
            self.client = None
            print("⚠️  Langfuse tracer disabled (missing keys)")

        self.trace_count = 0

    def is_healthy(self) -> bool:
        """Check if Langfuse is reachable"""
        if not self.enabled:
            return True  # Not an error if disabled

        try:
            # Simple health check - try to flush
            self.client.flush()
            return True
        except Exception:
            return False

    def get_trace_count(self) -> int:
        """Get number of traces created"""
        return self.trace_count

    def trace_agent_execution(
        self,
        agent_name: str,
        task_id: str,
        task: str,
        context: Dict[str, Any],
        model_info: Dict[str, Any]
    ) -> Optional[str]:
        """
        Start a trace for an agent execution.

        Returns trace_id if enabled, None otherwise.
        """
        if not self.enabled:
            return None

        trace = self.client.trace(
            name=f"agent.{agent_name}",
            user_id="system",
            session_id=task_id,
            metadata={
                "agent": agent_name,
                "task_id": task_id,
                "task": task,
                "context": context,
                "model": model_info.get("model"),
                "temperature": model_info.get("temperature"),
                "top_p": model_info.get("top_p"),
                "max_tokens": model_info.get("max_tokens"),
                "seed": model_info.get("seed"),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        self.trace_count += 1
        return trace.id

    def trace_llm_call(
        self,
        trace_id: Optional[str],
        model: str,
        prompt: str,
        response: str,
        tokens_used: int,
        latency_ms: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Trace a single LLM call within an agent execution"""
        if not self.enabled or not trace_id:
            return

        self.client.generation(
            trace_id=trace_id,
            name="llm_call",
            model=model,
            model_parameters={
                "temperature": metadata.get("temperature") if metadata else None,
                "top_p": metadata.get("top_p") if metadata else None,
                "max_tokens": metadata.get("max_tokens") if metadata else None,
                "seed": metadata.get("seed") if metadata else None
            },
            input=prompt,
            output=response,
            usage={
                "input": tokens_used,
                "output": tokens_used,
                "total": tokens_used
            },
            metadata={
                **(metadata or {}),
                "latency_ms": latency_ms
            }
        )

    def trace_rag_retrieval(
        self,
        trace_id: Optional[str],
        query: str,
        citations: List[Dict[str, Any]],
        top_k: int,
        min_score: float
    ):
        """
        Trace a RAG retrieval operation with citations.

        Citations should include: source, version, score, content
        """
        if not self.enabled or not trace_id:
            return

        # Format citations for display
        citation_summary = []
        for i, cit in enumerate(citations[:top_k], 1):
            citation_summary.append({
                "rank": i,
                "source": cit.get("source", "unknown"),
                "version": cit.get("version", "unknown"),
                "score": round(cit.get("score", 0), 3),
                "content_preview": cit.get("content", "")[:200]
            })

        self.client.span(
            trace_id=trace_id,
            name="rag_retrieval",
            input={"query": query, "top_k": top_k, "min_score": min_score},
            output={"citations": citation_summary, "count": len(citations)},
            metadata={
                "retrieval_type": "semantic_search",
                "vector_db": "qdrant",
                "grounding_quality": "sufficient" if len(citations) >= 2 else "insufficient"
            }
        )

    def trace_tool_execution(
        self,
        trace_id: Optional[str],
        tool_name: str,
        inputs: Dict[str, Any],
        output: Any,
        success: bool,
        error: Optional[str] = None
    ):
        """Trace a tool execution (file ops, API calls, etc.)"""
        if not self.enabled or not trace_id:
            return

        self.client.span(
            trace_id=trace_id,
            name=f"tool.{tool_name}",
            input=inputs,
            output={"result": output, "success": success, "error": error},
            metadata={
                "tool_type": tool_name,
                "status": "success" if success else "failed"
            }
        )

    def trace_approval_request(
        self,
        trace_id: Optional[str],
        risk_level: str,
        task_description: str,
        approval_status: str,
        approved_by: Optional[str] = None
    ):
        """Trace a human approval request"""
        if not self.enabled or not trace_id:
            return

        self.client.span(
            trace_id=trace_id,
            name="human_approval",
            input={"risk_level": risk_level, "task": task_description},
            output={"status": approval_status, "approved_by": approved_by},
            metadata={
                "approval_type": "human_in_loop",
                "risk_level": risk_level
            }
        )

    def trace_budget_check(
        self,
        trace_id: Optional[str],
        tokens_used: int,
        budget: int,
        within_budget: bool
    ):
        """Trace budget enforcement check"""
        if not self.enabled or not trace_id:
            return

        self.client.event(
            trace_id=trace_id,
            name="budget_check",
            metadata={
                "tokens_used": tokens_used,
                "budget": budget,
                "within_budget": within_budget,
                "utilization_pct": round((tokens_used / budget) * 100, 2) if budget > 0 else 0
            }
        )

    def flush(self):
        """Flush pending traces to Langfuse"""
        if self.enabled:
            self.client.flush()
