"""
Pydantic models for scheduler service
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from uuid import UUID


class ScheduleType(str, Enum):
    """Schedule type enum"""
    CRON = "cron"
    INTERVAL = "interval"
    ONCE = "once"


class ExecutionStatus(str, Enum):
    """Execution status enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class CreateScheduledTaskRequest(BaseModel):
    """Request to create a scheduled task"""
    name: str = Field(..., description="Task name")
    description: Optional[str] = Field(None, description="Task description")

    # Schedule configuration
    schedule_type: ScheduleType = Field(..., description="Schedule type")
    cron_expression: Optional[str] = Field(None, description="Cron expression (for cron type)")
    interval_seconds: Optional[int] = Field(None, description="Interval in seconds (for interval type)")
    scheduled_time: Optional[datetime] = Field(None, description="Scheduled time (for once type)")
    timezone: str = Field(default="UTC", description="Timezone for schedule")

    # Agent configuration
    agent_name: str = Field(..., description="Agent to execute (e.g., developer, overseer)")
    task_payload: Dict[str, Any] = Field(..., description="Task payload for agent")

    # Project/workflow context
    project_id: Optional[str] = Field(None, description="Project ID")
    workflow_id: Optional[str] = Field(None, description="Workflow ID")

    # Execution settings
    timeout_seconds: int = Field(default=300, description="Task timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay_seconds: int = Field(default=60, description="Delay between retries")

    # Status
    is_active: bool = Field(default=True, description="Whether task is active")
    is_paused: bool = Field(default=False, description="Whether task is paused")


class UpdateScheduledTaskRequest(BaseModel):
    """Request to update a scheduled task"""
    name: Optional[str] = None
    description: Optional[str] = None
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    scheduled_time: Optional[datetime] = None
    timezone: Optional[str] = None
    task_payload: Optional[Dict[str, Any]] = None
    timeout_seconds: Optional[int] = None
    max_retries: Optional[int] = None
    retry_delay_seconds: Optional[int] = None
    is_active: Optional[bool] = None
    is_paused: Optional[bool] = None


class ScheduledTaskResponse(BaseModel):
    """Response for scheduled task"""
    id: UUID
    tenant_id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    schedule_type: ScheduleType
    cron_expression: Optional[str]
    interval_seconds: Optional[int]
    scheduled_time: Optional[datetime]
    timezone: str
    agent_name: str
    task_payload: Dict[str, Any]
    project_id: Optional[str]
    workflow_id: Optional[str]
    timeout_seconds: int
    max_retries: int
    retry_delay_seconds: int
    is_active: bool
    is_paused: bool
    created_at: datetime
    updated_at: datetime
    last_execution_at: Optional[datetime]
    next_execution_at: Optional[datetime]
    total_executions: int
    successful_executions: int
    failed_executions: int


class TaskExecutionResponse(BaseModel):
    """Response for task execution"""
    id: UUID
    scheduled_task_id: UUID
    execution_number: int
    status: ExecutionStatus
    agent_task_id: Optional[str]
    agent_name: str
    scheduled_for: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    tokens_used: int
    cost_usd: float
    retry_count: int
    max_retries: int
    created_at: datetime
    updated_at: datetime


class TaskExecutionListResponse(BaseModel):
    """Response for list of task executions"""
    executions: List[TaskExecutionResponse]
    total: int
    page: int
    page_size: int


class ScheduledTaskListResponse(BaseModel):
    """Response for list of scheduled tasks"""
    tasks: List[ScheduledTaskResponse]
    total: int
    page: int
    page_size: int


class SchedulerHealthResponse(BaseModel):
    """Health check response"""
    status: str
    scheduler_running: bool
    active_jobs: int
    database_connected: bool
    agent_service_available: bool
