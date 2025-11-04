"""
Temponest SDK Data Models
"""
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# Agent Models
class Agent(BaseModel):
    """Agent model"""
    model_config = ConfigDict(extra='allow')

    id: str
    tenant_id: str
    name: str
    description: Optional[str] = None
    model: str
    provider: str = "ollama"
    system_prompt: Optional[str] = None
    tools: List[str] = Field(default_factory=list)
    rag_collection_ids: List[str] = Field(default_factory=list)
    max_iterations: int = 10
    temperature: float = 0.7
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class AgentExecution(BaseModel):
    """Agent execution model"""
    model_config = ConfigDict(extra='allow')

    id: str
    agent_id: str
    tenant_id: str
    status: Literal["pending", "running", "completed", "failed"]
    user_message: str
    response: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    tools_used: List[str] = Field(default_factory=list)
    tokens_used: Dict[str, int] = Field(default_factory=dict)
    cost_usd: float = 0.0
    execution_time_seconds: Optional[float] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


# Scheduler Models
class ScheduledTask(BaseModel):
    """Scheduled task model"""
    model_config = ConfigDict(extra='allow')

    id: str
    tenant_id: str
    agent_id: str
    cron_expression: str
    task_config: Dict[str, Any]
    is_active: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    created_at: datetime
    updated_at: datetime


class TaskExecution(BaseModel):
    """Task execution model"""
    model_config = ConfigDict(extra='allow')

    id: str
    task_id: str
    agent_execution_id: Optional[str] = None
    status: Literal["pending", "running", "completed", "failed"]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


# RAG Models
class Collection(BaseModel):
    """RAG collection model"""
    model_config = ConfigDict(extra='allow')

    id: str
    tenant_id: str
    name: str
    description: Optional[str] = None
    embedding_model: str = "nomic-embed-text"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    document_count: int = 0
    created_at: datetime
    updated_at: datetime


class Document(BaseModel):
    """Document model"""
    model_config = ConfigDict(extra='allow')

    id: str
    collection_id: str
    filename: str
    content_type: str
    size_bytes: int
    chunk_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class QueryResult(BaseModel):
    """RAG query result"""
    model_config = ConfigDict(extra='allow')

    chunks: List[Dict[str, Any]]
    query: str
    collection_id: str
    total_results: int


# Collaboration Models
class CollaborationSession(BaseModel):
    """Multi-agent collaboration session"""
    model_config = ConfigDict(extra='allow')

    id: str
    tenant_id: str
    pattern: Literal["sequential", "parallel", "iterative", "hierarchical"]
    agent_ids: List[str]
    status: Literal["pending", "running", "completed", "failed"]
    results: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    completed_at: Optional[datetime] = None


# Cost Models
class CostSummary(BaseModel):
    """Cost tracking summary"""
    model_config = ConfigDict(extra='allow')

    total_usd: float
    by_provider: Dict[str, float]
    by_model: Dict[str, float]
    by_agent: Dict[str, float]
    total_tokens: Dict[str, int]
    period_start: datetime
    period_end: datetime


class BudgetConfig(BaseModel):
    """Budget configuration"""
    model_config = ConfigDict(extra='allow')

    daily_limit_usd: Optional[float] = None
    monthly_limit_usd: Optional[float] = None
    alert_threshold: float = 0.8


# Request/Response Models
class AgentCreateRequest(BaseModel):
    """Request to create an agent"""
    model_config = ConfigDict(extra='allow')

    name: str
    description: Optional[str] = None
    model: str
    provider: str = "ollama"
    system_prompt: Optional[str] = None
    tools: List[str] = Field(default_factory=list)
    rag_collection_ids: List[str] = Field(default_factory=list)
    max_iterations: int = 10
    temperature: float = 0.7
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentExecuteRequest(BaseModel):
    """Request to execute an agent"""
    model_config = ConfigDict(extra='allow')

    user_message: str
    context: Dict[str, Any] = Field(default_factory=dict)
    stream: bool = False


class ScheduleCreateRequest(BaseModel):
    """Request to create a schedule"""
    model_config = ConfigDict(extra='allow')

    agent_id: str
    cron_expression: str
    task_config: Dict[str, Any]


class CollectionCreateRequest(BaseModel):
    """Request to create a RAG collection"""
    model_config = ConfigDict(extra='allow')

    name: str
    description: Optional[str] = None
    embedding_model: str = "nomic-embed-text"
    chunk_size: int = 1000
    chunk_overlap: int = 200


class QueryRequest(BaseModel):
    """Request to query RAG collection"""
    model_config = ConfigDict(extra='allow')

    query: str
    top_k: int = 5
    filter: Optional[Dict[str, Any]] = None
