"""
Shared models for the agents service.
Extracted from main.py to improve code organization.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List


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
