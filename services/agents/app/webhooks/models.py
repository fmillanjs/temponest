"""
Pydantic models for webhook and event system.
"""

from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID


class EventType(str, Enum):
    """Event types that can trigger webhooks"""
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    BUDGET_WARNING = "budget.warning"
    BUDGET_EXCEEDED = "budget.exceeded"
    BUDGET_CRITICAL = "budget.critical"
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_APPROVED = "approval.approved"
    APPROVAL_REJECTED = "approval.rejected"
    AGENT_ERROR = "agent.error"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"


class DeliveryStatus(str, Enum):
    """Webhook delivery status"""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class WebhookCreate(BaseModel):
    """Request model for creating a webhook"""
    name: str = Field(..., min_length=1, max_length=255, description="Webhook name")
    url: str = Field(..., description="Webhook endpoint URL")
    description: Optional[str] = Field(None, description="Webhook description")
    events: List[EventType] = Field(..., min_items=1, description="Events to subscribe to")
    project_filter: Optional[str] = Field(None, max_length=255, description="Filter by project ID")
    workflow_filter: Optional[str] = Field(None, max_length=255, description="Filter by workflow ID")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry attempts")
    retry_delay_seconds: int = Field(60, ge=10, le=3600, description="Initial retry delay in seconds")
    timeout_seconds: int = Field(30, ge=5, le=120, description="Request timeout in seconds")
    custom_headers: Dict[str, str] = Field(default_factory=dict, description="Custom HTTP headers")
    is_active: bool = Field(True, description="Whether webhook is active")

    @validator('url')
    def validate_url(cls, v):
        """Ensure URL is valid HTTPS"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class WebhookUpdate(BaseModel):
    """Request model for updating a webhook"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[str] = None
    description: Optional[str] = None
    events: Optional[List[EventType]] = Field(None, min_items=1)
    project_filter: Optional[str] = Field(None, max_length=255)
    workflow_filter: Optional[str] = Field(None, max_length=255)
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    retry_delay_seconds: Optional[int] = Field(None, ge=10, le=3600)
    timeout_seconds: Optional[int] = Field(None, ge=5, le=120)
    custom_headers: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None

    @validator('url')
    def validate_url(cls, v):
        """Ensure URL is valid if provided"""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class WebhookResponse(BaseModel):
    """Response model for webhook"""
    id: UUID
    tenant_id: UUID
    user_id: Optional[UUID]
    name: str
    url: str
    description: Optional[str]
    events: List[EventType]
    project_filter: Optional[str]
    workflow_filter: Optional[str]
    max_retries: int
    retry_delay_seconds: int
    timeout_seconds: int
    custom_headers: Dict[str, str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_triggered_at: Optional[datetime]
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int

    class Config:
        from_attributes = True


class WebhookListResponse(BaseModel):
    """Response model for webhook list"""
    webhooks: List[WebhookResponse]
    total: int
    page: int
    page_size: int


class EventPayload(BaseModel):
    """Base event payload"""
    event_type: EventType
    event_id: str
    source: str
    tenant_id: UUID
    user_id: Optional[UUID]
    project_id: Optional[str]
    workflow_id: Optional[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any]


class TaskStartedPayload(BaseModel):
    """Payload for task.started event"""
    task_id: str
    agent_name: str
    task_description: str
    user_id: UUID
    tenant_id: UUID
    project_id: Optional[str]
    workflow_id: Optional[str]
    started_at: datetime


class TaskCompletedPayload(BaseModel):
    """Payload for task.completed event"""
    task_id: str
    agent_name: str
    status: str
    tokens_used: int
    latency_ms: int
    cost_usd: Optional[float]
    user_id: UUID
    tenant_id: UUID
    project_id: Optional[str]
    workflow_id: Optional[str]
    completed_at: datetime


class TaskFailedPayload(BaseModel):
    """Payload for task.failed event"""
    task_id: str
    agent_name: str
    error_message: str
    user_id: UUID
    tenant_id: UUID
    project_id: Optional[str]
    workflow_id: Optional[str]
    failed_at: datetime


class BudgetAlertPayload(BaseModel):
    """Payload for budget alert events"""
    alert_type: str  # warning, exceeded, critical
    budget_id: UUID
    budget_type: str  # daily, weekly, monthly, total
    budget_amount_usd: float
    current_spend_usd: float
    threshold_pct: int
    tenant_id: UUID
    user_id: Optional[UUID]
    project_id: Optional[str]
    alert_time: datetime


class WebhookDeliveryResponse(BaseModel):
    """Response model for webhook delivery"""
    id: UUID
    webhook_id: UUID
    event_type: EventType
    event_id: str
    status: DeliveryStatus
    attempts: int
    max_attempts: int
    scheduled_at: datetime
    next_retry_at: Optional[datetime]
    delivered_at: Optional[datetime]
    http_status_code: Optional[int]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebhookHealthResponse(BaseModel):
    """Response model for webhook health stats"""
    id: UUID
    tenant_id: UUID
    name: str
    url: str
    is_active: bool
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    success_rate_pct: float
    last_triggered_at: Optional[datetime]
    pending_count: int
    retrying_count: int
    recent_failed_count: int

    class Config:
        from_attributes = True


class EventLogResponse(BaseModel):
    """Response model for event log"""
    id: UUID
    tenant_id: UUID
    user_id: Optional[UUID]
    event_type: EventType
    event_id: str
    source: str
    payload: Dict[str, Any]
    project_id: Optional[str]
    workflow_id: Optional[str]
    webhook_count: int
    created_at: datetime

    class Config:
        from_attributes = True
