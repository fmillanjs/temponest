"""
Temponest SDK - Scheduler Service Client
"""
from typing import List, Optional, Dict, Any
from .client import BaseClient, AsyncBaseClient
from .models import (
    ScheduledTask,
    TaskExecution,
    ScheduleCreateRequest,
)
from .exceptions import ScheduleNotFoundError


class SchedulerClient:
    """Client for task scheduling"""

    def __init__(self, client: BaseClient):
        self.client = client
        # Override base_url to point to scheduler service
        self.base_url = self.client.base_url.replace(":9000", ":9003")

    def create(
        self,
        agent_id: str,
        cron_expression: str,
        task_config: Dict[str, Any],
    ) -> ScheduledTask:
        """
        Create a scheduled task

        Args:
            agent_id: ID of the agent to execute
            cron_expression: Cron expression for scheduling
            task_config: Configuration for the task execution

        Returns:
            Created scheduled task

        Raises:
            TemponestAPIError: On API errors
        """
        request = ScheduleCreateRequest(
            agent_id=agent_id,
            cron_expression=cron_expression,
            task_config=task_config,
        )

        # Use scheduler service URL
        original_url = self.client.base_url
        try:
            self.client.base_url = self.base_url
            response = self.client.post("/schedules/", json=request.model_dump())
            return ScheduledTask(**response)
        finally:
            self.client.base_url = original_url

    def get(self, schedule_id: str) -> ScheduledTask:
        """
        Get a scheduled task by ID

        Args:
            schedule_id: Schedule ID

        Returns:
            Scheduled task

        Raises:
            ScheduleNotFoundError: If schedule not found
        """
        original_url = self.client.base_url
        try:
            self.client.base_url = self.base_url
            response = self.client.get(f"/schedules/{schedule_id}")
            return ScheduledTask(**response)
        except Exception as e:
            if "404" in str(e):
                raise ScheduleNotFoundError(f"Schedule {schedule_id} not found")
            raise
        finally:
            self.client.base_url = original_url

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        agent_id: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[ScheduledTask]:
        """
        List scheduled tasks

        Args:
            skip: Number to skip
            limit: Maximum to return
            agent_id: Filter by agent ID
            is_active: Filter by active status

        Returns:
            List of scheduled tasks
        """
        params = {"skip": skip, "limit": limit}
        if agent_id:
            params["agent_id"] = agent_id
        if is_active is not None:
            params["is_active"] = is_active

        original_url = self.client.base_url
        try:
            self.client.base_url = self.base_url
            response = self.client.get("/schedules/", params=params)
            return [ScheduledTask(**task) for task in response]
        finally:
            self.client.base_url = original_url

    def update(
        self,
        schedule_id: str,
        cron_expression: Optional[str] = None,
        task_config: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None,
    ) -> ScheduledTask:
        """
        Update a scheduled task

        Args:
            schedule_id: Schedule ID
            cron_expression: New cron expression
            task_config: New task configuration
            is_active: New active status

        Returns:
            Updated scheduled task

        Raises:
            ScheduleNotFoundError: If schedule not found
        """
        update_data = {}
        if cron_expression is not None:
            update_data["cron_expression"] = cron_expression
        if task_config is not None:
            update_data["task_config"] = task_config
        if is_active is not None:
            update_data["is_active"] = is_active

        original_url = self.client.base_url
        try:
            self.client.base_url = self.base_url
            response = self.client.patch(f"/schedules/{schedule_id}", json=update_data)
            return ScheduledTask(**response)
        except Exception as e:
            if "404" in str(e):
                raise ScheduleNotFoundError(f"Schedule {schedule_id} not found")
            raise
        finally:
            self.client.base_url = original_url

    def delete(self, schedule_id: str) -> None:
        """
        Delete a scheduled task

        Args:
            schedule_id: Schedule ID

        Raises:
            ScheduleNotFoundError: If schedule not found
        """
        original_url = self.client.base_url
        try:
            self.client.base_url = self.base_url
            self.client.delete(f"/schedules/{schedule_id}")
        except Exception as e:
            if "404" in str(e):
                raise ScheduleNotFoundError(f"Schedule {schedule_id} not found")
            raise
        finally:
            self.client.base_url = original_url

    def pause(self, schedule_id: str) -> ScheduledTask:
        """
        Pause a scheduled task

        Args:
            schedule_id: Schedule ID

        Returns:
            Updated scheduled task

        Raises:
            ScheduleNotFoundError: If schedule not found
        """
        return self.update(schedule_id, is_active=False)

    def resume(self, schedule_id: str) -> ScheduledTask:
        """
        Resume a scheduled task

        Args:
            schedule_id: Schedule ID

        Returns:
            Updated scheduled task

        Raises:
            ScheduleNotFoundError: If schedule not found
        """
        return self.update(schedule_id, is_active=True)

    def trigger(self, schedule_id: str) -> TaskExecution:
        """
        Manually trigger a scheduled task

        Args:
            schedule_id: Schedule ID

        Returns:
            Task execution

        Raises:
            ScheduleNotFoundError: If schedule not found
        """
        original_url = self.client.base_url
        try:
            self.client.base_url = self.base_url
            response = self.client.post(f"/schedules/{schedule_id}/trigger")
            return TaskExecution(**response)
        except Exception as e:
            if "404" in str(e):
                raise ScheduleNotFoundError(f"Schedule {schedule_id} not found")
            raise
        finally:
            self.client.base_url = original_url

    def get_executions(
        self,
        schedule_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TaskExecution]:
        """
        Get executions for a scheduled task

        Args:
            schedule_id: Schedule ID
            skip: Number to skip
            limit: Maximum to return

        Returns:
            List of task executions
        """
        params = {"skip": skip, "limit": limit}

        original_url = self.client.base_url
        try:
            self.client.base_url = self.base_url
            response = self.client.get(
                f"/schedules/{schedule_id}/executions",
                params=params
            )
            return [TaskExecution(**execution) for execution in response]
        finally:
            self.client.base_url = original_url


class AsyncSchedulerClient:
    """Async client for task scheduling"""

    def __init__(self, client: AsyncBaseClient):
        self.client = client
        self.base_url = self.client.base_url.replace(":9000", ":9003")

    async def create(
        self,
        agent_id: str,
        cron_expression: str,
        task_config: Dict[str, Any],
    ) -> ScheduledTask:
        """Create a scheduled task (async)"""
        request = ScheduleCreateRequest(
            agent_id=agent_id,
            cron_expression=cron_expression,
            task_config=task_config,
        )

        original_url = self.client.base_url
        try:
            self.client.base_url = self.base_url
            response = await self.client.post("/schedules/", json=request.model_dump())
            return ScheduledTask(**response)
        finally:
            self.client.base_url = original_url

    async def get(self, schedule_id: str) -> ScheduledTask:
        """Get a scheduled task by ID (async)"""
        original_url = self.client.base_url
        try:
            self.client.base_url = self.base_url
            response = await self.client.get(f"/schedules/{schedule_id}")
            return ScheduledTask(**response)
        except Exception as e:
            if "404" in str(e):
                raise ScheduleNotFoundError(f"Schedule {schedule_id} not found")
            raise
        finally:
            self.client.base_url = original_url

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        agent_id: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[ScheduledTask]:
        """List scheduled tasks (async)"""
        params = {"skip": skip, "limit": limit}
        if agent_id:
            params["agent_id"] = agent_id
        if is_active is not None:
            params["is_active"] = is_active

        original_url = self.client.base_url
        try:
            self.client.base_url = self.base_url
            response = await self.client.get("/schedules/", params=params)
            return [ScheduledTask(**task) for task in response]
        finally:
            self.client.base_url = original_url

    async def update(
        self,
        schedule_id: str,
        **kwargs
    ) -> ScheduledTask:
        """Update a scheduled task (async)"""
        update_data = {k: v for k, v in kwargs.items() if v is not None}

        original_url = self.client.base_url
        try:
            self.client.base_url = self.base_url
            response = await self.client.patch(f"/schedules/{schedule_id}", json=update_data)
            return ScheduledTask(**response)
        except Exception as e:
            if "404" in str(e):
                raise ScheduleNotFoundError(f"Schedule {schedule_id} not found")
            raise
        finally:
            self.client.base_url = original_url

    async def delete(self, schedule_id: str) -> None:
        """Delete a scheduled task (async)"""
        original_url = self.client.base_url
        try:
            self.client.base_url = self.base_url
            await self.client.delete(f"/schedules/{schedule_id}")
        except Exception as e:
            if "404" in str(e):
                raise ScheduleNotFoundError(f"Schedule {schedule_id} not found")
            raise
        finally:
            self.client.base_url = original_url

    async def pause(self, schedule_id: str) -> ScheduledTask:
        """Pause a scheduled task (async)"""
        return await self.update(schedule_id, is_active=False)

    async def resume(self, schedule_id: str) -> ScheduledTask:
        """Resume a scheduled task (async)"""
        return await self.update(schedule_id, is_active=True)

    async def trigger(self, schedule_id: str) -> TaskExecution:
        """Manually trigger a scheduled task (async)"""
        original_url = self.client.base_url
        try:
            self.client.base_url = self.base_url
            response = await self.client.post(f"/schedules/{schedule_id}/trigger")
            return TaskExecution(**response)
        except Exception as e:
            if "404" in str(e):
                raise ScheduleNotFoundError(f"Schedule {schedule_id} not found")
            raise
        finally:
            self.client.base_url = original_url

    async def get_executions(
        self,
        schedule_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TaskExecution]:
        """Get executions for a scheduled task (async)"""
        params = {"skip": skip, "limit": limit}

        original_url = self.client.base_url
        try:
            self.client.base_url = self.base_url
            response = await self.client.get(
                f"/schedules/{schedule_id}/executions",
                params=params
            )
            return [TaskExecution(**execution) for execution in response]
        finally:
            self.client.base_url = original_url
