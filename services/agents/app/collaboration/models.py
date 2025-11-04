"""
Data models for agent collaboration
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class AgentRole(str, Enum):
    """Agent roles in collaboration"""
    OVERSEER = "overseer"
    DEVELOPER = "developer"
    QA_TESTER = "qa_tester"
    DEVOPS = "devops"
    DESIGNER = "designer"
    SECURITY_AUDITOR = "security_auditor"


class TaskStatus(str, Enum):
    """Status of a collaborative task"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_INPUT = "waiting_for_input"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CollaborationPattern(str, Enum):
    """Patterns for agent collaboration"""
    SEQUENTIAL = "sequential"  # One agent after another
    PARALLEL = "parallel"      # Multiple agents work simultaneously
    ITERATIVE = "iterative"    # Agents work in feedback loops
    HIERARCHICAL = "hierarchical"  # Overseer delegates to specialists


class AgentTask(BaseModel):
    """A task assigned to a specific agent"""
    id: UUID = Field(default_factory=uuid4)
    agent_role: AgentRole
    task_description: str
    context: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[UUID] = Field(default_factory=list)  # Task IDs this depends on
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3


class CollaborationWorkspace(BaseModel):
    """Shared workspace for agent collaboration"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    pattern: CollaborationPattern
    tasks: List[AgentTask] = Field(default_factory=list)
    shared_context: Dict[str, Any] = Field(default_factory=dict)
    artifacts: Dict[str, Any] = Field(default_factory=dict)  # Shared files, data, etc.
    messages: List[Dict[str, Any]] = Field(default_factory=list)  # Inter-agent communication
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: TaskStatus = TaskStatus.PENDING


class CollaborationRequest(BaseModel):
    """Request to start a collaborative task"""
    name: str = Field(..., description="Name of the collaboration session")
    description: str = Field(..., description="Overall goal of the collaboration")
    pattern: CollaborationPattern = Field(default=CollaborationPattern.HIERARCHICAL)
    initial_context: Dict[str, Any] = Field(default_factory=dict)
    agents: List[AgentRole] = Field(..., description="Agents to involve in collaboration")
    workflow_steps: Optional[List[Dict[str, Any]]] = Field(None, description="Predefined workflow steps")


class CollaborationResponse(BaseModel):
    """Response from a collaboration session"""
    workspace_id: UUID
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_duration_ms: Optional[int] = None
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
