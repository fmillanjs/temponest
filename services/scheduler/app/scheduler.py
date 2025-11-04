"""
APScheduler-based task scheduler
Polls database for scheduled tasks and executes them via agent service
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from uuid import UUID
import pytz
from croniter import croniter
import httpx

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from db import DatabaseManager
from settings import settings


class TaskScheduler:
    """Manages scheduled task execution using APScheduler"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)
        self.http_client: Optional[httpx.AsyncClient] = None
        self.active_executions: Dict[UUID, asyncio.Task] = {}

    async def start(self):
        """Start the scheduler"""
        # Create HTTP client for agent service calls
        self.http_client = httpx.AsyncClient(
            base_url=settings.agent_service_url,
            timeout=httpx.Timeout(300.0)  # 5 minute timeout for agent calls
        )

        # Add recurring job to poll for scheduled tasks
        self.scheduler.add_job(
            self._poll_scheduled_tasks,
            trigger=IntervalTrigger(seconds=settings.scheduler_poll_interval_seconds),
            id='poll_scheduled_tasks',
            name='Poll database for scheduled tasks',
            max_instances=1,
            replace_existing=True
        )

        self.scheduler.start()
        print(f"✅ Scheduler started (polling every {settings.scheduler_poll_interval_seconds}s)")

    async def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            print("✅ Scheduler stopped")

        # Cancel active executions
        for task in self.active_executions.values():
            task.cancel()

        if self.http_client:
            await self.http_client.aclose()

    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self.scheduler.running

    def get_active_jobs_count(self) -> int:
        """Get count of active jobs"""
        return len(self.active_executions)

    async def _poll_scheduled_tasks(self):
        """Poll database for tasks that need to be executed"""
        try:
            # Get tasks that need execution
            tasks = await self.db_manager.get_scheduled_tasks_to_execute(
                limit=settings.scheduler_max_instances - len(self.active_executions)
            )

            for task in tasks:
                # Check if we're at max capacity
                if len(self.active_executions) >= settings.scheduler_max_instances:
                    print(f"⚠️  Max concurrent executions reached ({settings.scheduler_max_instances})")
                    break

                # Execute task asynchronously
                task_id = task['id']
                execution_task = asyncio.create_task(self._execute_scheduled_task(task))
                self.active_executions[task_id] = execution_task

                # Clean up after execution completes
                execution_task.add_done_callback(lambda t, tid=task_id: self.active_executions.pop(tid, None))

        except Exception as e:
            print(f"❌ Error polling scheduled tasks: {e}")

    async def _execute_scheduled_task(self, task: Dict[str, Any]):
        """Execute a scheduled task by calling the agent service"""
        task_id = task['id']
        task_name = task['name']
        agent_name = task['agent_name']

        print(f"🚀 Executing scheduled task: {task_name} (ID: {task_id}, Agent: {agent_name})")

        start_time = time.time()
        execution_id: Optional[UUID] = None

        try:
            # Get execution count and create execution record
            execution_number = await self.db_manager.get_task_execution_count(task_id) + 1

            execution_id = await self.db_manager.create_task_execution(
                scheduled_task_id=task_id,
                tenant_id=task['tenant_id'],
                user_id=task['user_id'],
                agent_name=agent_name,
                scheduled_for=datetime.utcnow(),
                execution_number=execution_number,
                max_retries=task['max_retries']
            )

            # Call agent service
            agent_response = await self._call_agent_service(
                agent_name=agent_name,
                task_payload=task['task_payload'],
                tenant_id=task['tenant_id'],
                user_id=task['user_id'],
                project_id=task.get('project_id'),
                workflow_id=task.get('workflow_id'),
                timeout=task['timeout_seconds']
            )

            # Update execution as started
            await self.db_manager.update_task_execution_started(
                execution_id=execution_id,
                agent_task_id=agent_response.get('task_id', 'unknown')
            )

            # Check if execution was successful
            if agent_response.get('status') == 'success':
                duration_ms = int((time.time() - start_time) * 1000)

                await self.db_manager.update_task_execution_completed(
                    execution_id=execution_id,
                    result=agent_response.get('result', {}),
                    tokens_used=agent_response.get('tokens_used', 0),
                    cost_usd=agent_response.get('cost_info', {}).get('total_cost_usd', 0.0),
                    duration_ms=duration_ms
                )

                print(f"✅ Task {task_name} completed successfully (Duration: {duration_ms}ms)")

            else:
                error_message = agent_response.get('error', 'Unknown error')
                await self.db_manager.update_task_execution_failed(
                    execution_id=execution_id,
                    error_message=error_message,
                    retry_count=0
                )

                print(f"❌ Task {task_name} failed: {error_message}")

        except Exception as e:
            print(f"❌ Error executing task {task_name}: {e}")

            if execution_id:
                await self.db_manager.update_task_execution_failed(
                    execution_id=execution_id,
                    error_message=str(e),
                    retry_count=0
                )

        finally:
            # Calculate next execution time and update task
            try:
                next_execution = self._calculate_next_execution(task)
                if next_execution:
                    await self.db_manager.update_next_execution_time(task_id, next_execution)
                    print(f"📅 Next execution for {task_name}: {next_execution}")
            except Exception as e:
                print(f"❌ Error calculating next execution for {task_name}: {e}")

    async def _call_agent_service(
        self,
        agent_name: str,
        task_payload: Dict[str, Any],
        tenant_id: UUID,
        user_id: UUID,
        project_id: Optional[str],
        workflow_id: Optional[str],
        timeout: int
    ) -> Dict[str, Any]:
        """Call the agent service to execute a task"""

        # Prepare request payload
        request_data = {
            "task": task_payload.get("task", ""),
            "context": task_payload.get("context", {}),
            "risk_level": task_payload.get("risk_level", "low"),
            "project_id": project_id,
            "workflow_id": workflow_id
        }

        # Make request to agent service
        # Note: We need to add authentication headers here
        headers = {
            "X-Tenant-ID": str(tenant_id),
            "X-User-ID": str(user_id)
        }

        try:
            response = await self.http_client.post(
                f"/agents/{agent_name}/execute",
                json=request_data,
                headers=headers,
                timeout=timeout
            )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "error": f"Agent service returned {e.response.status_code}: {e.response.text}"
            }
        except httpx.TimeoutException:
            return {
                "status": "error",
                "error": f"Agent service timeout after {timeout} seconds"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to call agent service: {str(e)}"
            }

    def _calculate_next_execution(self, task: Dict[str, Any]) -> Optional[datetime]:
        """Calculate the next execution time based on schedule type"""
        schedule_type = task['schedule_type']
        timezone_str = task.get('timezone', 'UTC')
        tz = pytz.timezone(timezone_str)
        now = datetime.now(tz)

        if schedule_type == 'cron':
            cron_expression = task['cron_expression']
            if not cron_expression:
                return None

            try:
                cron = croniter(cron_expression, now)
                next_time = cron.get_next(datetime)
                # Convert to UTC for storage
                return next_time.astimezone(pytz.UTC).replace(tzinfo=None)
            except Exception as e:
                print(f"❌ Invalid cron expression '{cron_expression}': {e}")
                return None

        elif schedule_type == 'interval':
            interval_seconds = task['interval_seconds']
            if not interval_seconds or interval_seconds <= 0:
                return None

            next_time = now + timedelta(seconds=interval_seconds)
            # Convert to UTC for storage
            return next_time.astimezone(pytz.UTC).replace(tzinfo=None)

        elif schedule_type == 'once':
            # One-time tasks don't have a next execution
            return None

        return None

    async def trigger_task_now(self, task_id: UUID, tenant_id: UUID) -> bool:
        """Manually trigger a task execution immediately"""
        try:
            # Get the task
            task = await self.db_manager.get_scheduled_task(task_id, tenant_id)
            if not task:
                return False

            # Check if task is active
            if not task['is_active']:
                return False

            # Execute task
            await self._execute_scheduled_task(task)
            return True

        except Exception as e:
            print(f"❌ Error triggering task {task_id}: {e}")
            return False
