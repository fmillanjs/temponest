"""
API endpoints for scheduled tasks management
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from uuid import UUID

from models import (
    CreateScheduledTaskRequest,
    UpdateScheduledTaskRequest,
    ScheduledTaskResponse,
    ScheduledTaskListResponse,
    TaskExecutionListResponse,
    TaskExecutionResponse
)
from db import DatabaseManager
from scheduler import TaskScheduler
from auth_middleware import get_current_user
from auth_client import AuthContext


router = APIRouter(prefix="/schedules", tags=["schedules"])


# Dependency injection
def get_db_manager() -> DatabaseManager:
    """Get database manager from app state"""
    from main import db_manager
    return db_manager


def get_scheduler() -> TaskScheduler:
    """Get scheduler from app state"""
    from main import task_scheduler
    return task_scheduler


@router.post("", response_model=ScheduledTaskResponse, status_code=201)
async def create_scheduled_task(
    request: CreateScheduledTaskRequest,
    db: DatabaseManager = Depends(get_db_manager),
    scheduler: TaskScheduler = Depends(get_scheduler),
    auth_context: AuthContext = Depends(get_current_user)
):
    """Create a new scheduled task"""
    tenant_id = UUID(auth_context.tenant_id)
    user_id = UUID(auth_context.user_id)

    # Validate schedule configuration
    if request.schedule_type.value == "cron" and not request.cron_expression:
        raise HTTPException(status_code=400, detail="cron_expression required for cron schedule type")

    if request.schedule_type.value == "interval" and not request.interval_seconds:
        raise HTTPException(status_code=400, detail="interval_seconds required for interval schedule type")

    if request.schedule_type.value == "once" and not request.scheduled_time:
        raise HTTPException(status_code=400, detail="scheduled_time required for once schedule type")

    # Create task in database
    task_id = await db.create_scheduled_task(
        tenant_id=tenant_id,
        user_id=user_id,
        name=request.name,
        description=request.description,
        schedule_type=request.schedule_type.value,
        agent_name=request.agent_name,
        task_payload=request.task_payload,
        cron_expression=request.cron_expression,
        interval_seconds=request.interval_seconds,
        scheduled_time=request.scheduled_time,
        timezone=request.timezone,
        project_id=request.project_id,
        workflow_id=request.workflow_id,
        timeout_seconds=request.timeout_seconds,
        max_retries=request.max_retries,
        retry_delay_seconds=request.retry_delay_seconds,
        is_active=request.is_active,
        is_paused=request.is_paused
    )

    # Get created task
    task = await db.get_scheduled_task(task_id, tenant_id)
    if not task:
        raise HTTPException(status_code=500, detail="Failed to create scheduled task")

    return ScheduledTaskResponse(**task)


@router.get("", response_model=ScheduledTaskListResponse)
async def list_scheduled_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    is_active: Optional[bool] = None,
    db: DatabaseManager = Depends(get_db_manager),
    auth_context: AuthContext = Depends(get_current_user)
):
    """List scheduled tasks for the current tenant"""
    tenant_id = UUID(auth_context.tenant_id)

    tasks, total = await db.list_scheduled_tasks(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        is_active=is_active
    )

    return ScheduledTaskListResponse(
        tasks=[ScheduledTaskResponse(**task) for task in tasks],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{task_id}", response_model=ScheduledTaskResponse)
async def get_scheduled_task(
    task_id: UUID,
    db: DatabaseManager = Depends(get_db_manager),
    auth_context: AuthContext = Depends(get_current_user)
):
    """Get a scheduled task by ID"""
    tenant_id = UUID(auth_context.tenant_id)

    task = await db.get_scheduled_task(task_id, tenant_id)
    if not task:
        raise HTTPException(status_code=404, detail="Scheduled task not found")

    return ScheduledTaskResponse(**task)


@router.patch("/{task_id}", response_model=ScheduledTaskResponse)
async def update_scheduled_task(
    task_id: UUID,
    request: UpdateScheduledTaskRequest,
    db: DatabaseManager = Depends(get_db_manager),
    auth_context: AuthContext = Depends(get_current_user)
):
    """Update a scheduled task"""
    tenant_id = UUID(auth_context.tenant_id)

    # Get current task
    task = await db.get_scheduled_task(task_id, tenant_id)
    if not task:
        raise HTTPException(status_code=404, detail="Scheduled task not found")

    # Prepare updates
    updates = request.model_dump(exclude_unset=True)

    # Update task
    success = await db.update_scheduled_task(task_id, tenant_id, **updates)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update scheduled task")

    # Get updated task
    updated_task = await db.get_scheduled_task(task_id, tenant_id)
    return ScheduledTaskResponse(**updated_task)


@router.delete("/{task_id}", status_code=204)
async def delete_scheduled_task(
    task_id: UUID,
    db: DatabaseManager = Depends(get_db_manager),
    auth_context: AuthContext = Depends(get_current_user)
):
    """Delete a scheduled task"""
    tenant_id = UUID(auth_context.tenant_id)

    success = await db.delete_scheduled_task(task_id, tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scheduled task not found")


@router.post("/{task_id}/trigger", status_code=202)
async def trigger_scheduled_task(
    task_id: UUID,
    scheduler: TaskScheduler = Depends(get_scheduler),
    auth_context: AuthContext = Depends(get_current_user)
):
    """Manually trigger a scheduled task to run immediately"""
    tenant_id = UUID(auth_context.tenant_id)

    success = await scheduler.trigger_task_now(task_id, tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scheduled task not found or not active")

    return {"message": "Task triggered successfully"}


@router.post("/{task_id}/pause", response_model=ScheduledTaskResponse)
async def pause_scheduled_task(
    task_id: UUID,
    db: DatabaseManager = Depends(get_db_manager),
    auth_context: AuthContext = Depends(get_current_user)
):
    """Pause a scheduled task"""
    tenant_id = UUID(auth_context.tenant_id)

    task = await db.get_scheduled_task(task_id, tenant_id)
    if not task:
        raise HTTPException(status_code=404, detail="Scheduled task not found")

    await db.update_scheduled_task(task_id, tenant_id, is_paused=True)

    updated_task = await db.get_scheduled_task(task_id, tenant_id)
    return ScheduledTaskResponse(**updated_task)


@router.post("/{task_id}/resume", response_model=ScheduledTaskResponse)
async def resume_scheduled_task(
    task_id: UUID,
    db: DatabaseManager = Depends(get_db_manager),
    auth_context: AuthContext = Depends(get_current_user)
):
    """Resume a paused scheduled task"""
    tenant_id = UUID(auth_context.tenant_id)

    task = await db.get_scheduled_task(task_id, tenant_id)
    if not task:
        raise HTTPException(status_code=404, detail="Scheduled task not found")

    await db.update_scheduled_task(task_id, tenant_id, is_paused=False)

    updated_task = await db.get_scheduled_task(task_id, tenant_id)
    return ScheduledTaskResponse(**updated_task)


@router.get("/{task_id}/executions", response_model=TaskExecutionListResponse)
async def list_task_executions(
    task_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: DatabaseManager = Depends(get_db_manager),
    auth_context: AuthContext = Depends(get_current_user)
):
    """List executions for a scheduled task"""
    tenant_id = UUID(auth_context.tenant_id)

    # Verify task exists
    task = await db.get_scheduled_task(task_id, tenant_id)
    if not task:
        raise HTTPException(status_code=404, detail="Scheduled task not found")

    executions, total = await db.list_task_executions(
        scheduled_task_id=task_id,
        tenant_id=tenant_id,
        page=page,
        page_size=page_size
    )

    return TaskExecutionListResponse(
        executions=[TaskExecutionResponse(**execution) for execution in executions],
        total=total,
        page=page,
        page_size=page_size
    )
