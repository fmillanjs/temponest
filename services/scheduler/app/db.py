"""
Database operations for scheduler service
"""
import asyncpg
import json
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from uuid import UUID
from settings import settings


class DatabaseManager:
    """Manages database connections and operations"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Create database connection pool with optimized settings"""
        # OPTIMIZED: Tuned connection pool for scheduler service (moderate traffic)
        self.pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=5,               # Increased from 2 (keep connections ready)
            max_size=20,              # Increased from 10 (handle concurrent tasks)
            max_queries=30000,        # NEW: Recycle connections after 30k queries
            max_inactive_connection_lifetime=600.0,  # NEW: Close idle connections after 10 min
            command_timeout=30,       # Reduced from 60 (fail fast)
            timeout=5.0,              # NEW: Max wait time for connection from pool
            setup=self._setup_connection  # NEW: Connection setup hook
        )
        print("✅ Database connection pool created (pool: 5-20)")

    async def _setup_connection(self, conn):
        """Setup connection with optimized settings"""
        # Set statement timeout to prevent long-running queries
        await conn.execute("SET statement_timeout = '30s'")
        # Set idle_in_transaction_session_timeout to prevent blocking
        await conn.execute("SET idle_in_transaction_session_timeout = '60s'")

    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            print("✅ Database connection pool closed")

    async def get_scheduled_tasks_to_execute(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get scheduled tasks that need to be executed now"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    id, tenant_id, user_id, name, agent_name, task_payload,
                    project_id, workflow_id, timeout_seconds, max_retries,
                    schedule_type, cron_expression, interval_seconds,
                    scheduled_time, timezone, retry_delay_seconds
                FROM scheduled_tasks
                WHERE is_active = true
                    AND is_paused = false
                    AND next_execution_at <= CURRENT_TIMESTAMP
                ORDER BY next_execution_at
                LIMIT $1
            """, limit)

            # Parse task_payload from JSON string to dict for each task
            tasks = []
            for row in rows:
                task = dict(row)
                if isinstance(task.get('task_payload'), str):
                    task['task_payload'] = json.loads(task['task_payload'])
                tasks.append(task)

            return tasks

    async def update_next_execution_time(self, task_id: UUID, next_execution: datetime):
        """Update the next execution time for a scheduled task"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE scheduled_tasks
                SET next_execution_at = $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
            """, next_execution, task_id)

    async def create_task_execution(
        self,
        scheduled_task_id: UUID,
        tenant_id: UUID,
        user_id: UUID,
        agent_name: str,
        scheduled_for: datetime,
        execution_number: int,
        max_retries: int
    ) -> UUID:
        """Create a new task execution record"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO task_executions (
                    scheduled_task_id, tenant_id, user_id, agent_name,
                    scheduled_for, status, execution_number, max_retries
                )
                VALUES ($1, $2, $3, $4, $5, 'pending', $6, $7)
                RETURNING id
            """, scheduled_task_id, tenant_id, user_id, agent_name,
                scheduled_for, execution_number, max_retries)

            return row['id']

    async def update_task_execution_started(self, execution_id: UUID, agent_task_id: str):
        """Mark task execution as started"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE task_executions
                SET status = 'running',
                    started_at = CURRENT_TIMESTAMP,
                    agent_task_id = $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
            """, agent_task_id, execution_id)

    async def update_task_execution_completed(
        self,
        execution_id: UUID,
        result: Dict[str, Any],
        tokens_used: int,
        cost_usd: float,
        duration_ms: int
    ):
        """Mark task execution as completed"""
        # Convert result dict to JSON string for JSONB column
        result_json = json.dumps(result) if isinstance(result, dict) else result

        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE task_executions
                SET status = 'completed',
                    completed_at = CURRENT_TIMESTAMP,
                    result = $1,
                    tokens_used = $2,
                    cost_usd = $3,
                    duration_ms = $4,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $5
            """, result_json, tokens_used, cost_usd, duration_ms, execution_id)

    async def update_task_execution_failed(
        self,
        execution_id: UUID,
        error_message: str,
        retry_count: int
    ):
        """Mark task execution as failed"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE task_executions
                SET status = 'failed',
                    completed_at = CURRENT_TIMESTAMP,
                    error_message = $1,
                    retry_count = $2,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $3
            """, error_message, retry_count, execution_id)

    async def get_task_execution_count(self, scheduled_task_id: UUID) -> int:
        """Get the current execution count for a scheduled task"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT total_executions
                FROM scheduled_tasks
                WHERE id = $1
            """, scheduled_task_id)

            return row['total_executions'] if row else 0

    async def get_scheduled_task(self, task_id: UUID, tenant_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a scheduled task by ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT *
                FROM scheduled_tasks
                WHERE id = $1 AND tenant_id = $2
            """, task_id, tenant_id)

            if not row:
                return None

            task = dict(row)
            # Parse task_payload from JSON string to dict if needed
            if isinstance(task.get('task_payload'), str):
                task['task_payload'] = json.loads(task['task_payload'])
            return task

    async def list_scheduled_tasks(
        self,
        tenant_id: UUID,
        page: int = 1,
        page_size: int = 50,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List scheduled tasks for a tenant"""
        offset = (page - 1) * page_size

        async with self.pool.acquire() as conn:
            # Build query
            where_clauses = ["tenant_id = $1"]
            params = [tenant_id]
            param_idx = 2

            if is_active is not None:
                where_clauses.append(f"is_active = ${param_idx}")
                params.append(is_active)
                param_idx += 1

            where_clause = " AND ".join(where_clauses)

            # Get total count
            count_query = f"SELECT COUNT(*) FROM scheduled_tasks WHERE {where_clause}"
            total = await conn.fetchval(count_query, *params)

            # Get tasks
            list_query = f"""
                SELECT *
                FROM scheduled_tasks
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """
            params.extend([page_size, offset])
            rows = await conn.fetch(list_query, *params)

            # Parse task_payload from JSON string to dict for each task
            tasks = []
            for row in rows:
                task = dict(row)
                if isinstance(task.get('task_payload'), str):
                    task['task_payload'] = json.loads(task['task_payload'])
                tasks.append(task)

            return tasks, total

    async def create_scheduled_task(
        self,
        tenant_id: UUID,
        user_id: UUID,
        name: str,
        description: Optional[str],
        schedule_type: str,
        agent_name: str,
        task_payload: Dict[str, Any],
        cron_expression: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        scheduled_time: Optional[datetime] = None,
        timezone: str = "UTC",
        project_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        timeout_seconds: int = 300,
        max_retries: int = 3,
        retry_delay_seconds: int = 60,
        is_active: bool = True,
        is_paused: bool = False
    ) -> UUID:
        """Create a new scheduled task"""
        # Convert task_payload dict to JSON string for JSONB column
        task_payload_json = json.dumps(task_payload) if isinstance(task_payload, dict) else task_payload

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO scheduled_tasks (
                    tenant_id, user_id, name, description, schedule_type,
                    agent_name, task_payload, cron_expression, interval_seconds,
                    scheduled_time, timezone, project_id, workflow_id,
                    timeout_seconds, max_retries, retry_delay_seconds,
                    is_active, is_paused, created_by
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
                RETURNING id
            """, tenant_id, user_id, name, description, schedule_type,
                agent_name, task_payload_json, cron_expression, interval_seconds,
                scheduled_time, timezone, project_id, workflow_id,
                timeout_seconds, max_retries, retry_delay_seconds,
                is_active, is_paused, user_id)

            return row['id']

    async def update_scheduled_task(
        self,
        task_id: UUID,
        tenant_id: UUID,
        **updates
    ) -> bool:
        """Update a scheduled task"""
        if not updates:
            return False

        # Whitelist of allowed columns to prevent SQL injection
        ALLOWED_COLUMNS = {
            'name', 'description', 'cron_expression', 'interval_seconds',
            'scheduled_time', 'timezone', 'task_payload', 'timeout_seconds',
            'max_retries', 'retry_delay_seconds', 'is_active', 'is_paused'
        }

        # Build SET clause with validated columns
        set_parts = []
        params = []
        param_idx = 1

        for key, value in updates.items():
            if value is not None:
                # Validate column name against whitelist
                if key not in ALLOWED_COLUMNS:
                    raise ValueError(f"Invalid column name: {key}")
                set_parts.append(f"{key} = ${param_idx}")
                params.append(value)
                param_idx += 1

        if not set_parts:
            return False

        set_parts.append(f"updated_at = CURRENT_TIMESTAMP")
        set_clause = ", ".join(set_parts)

        # Add WHERE clause params
        params.extend([task_id, tenant_id])

        async with self.pool.acquire() as conn:
            result = await conn.execute(f"""
                UPDATE scheduled_tasks
                SET {set_clause}
                WHERE id = ${param_idx} AND tenant_id = ${param_idx + 1}
            """, *params)

            return result.split()[-1] == "1"

    async def delete_scheduled_task(self, task_id: UUID, tenant_id: UUID) -> bool:
        """Delete a scheduled task"""
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM scheduled_tasks
                WHERE id = $1 AND tenant_id = $2
            """, task_id, tenant_id)

            return result.split()[-1] == "1"

    async def list_task_executions(
        self,
        scheduled_task_id: UUID,
        tenant_id: UUID,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List task executions for a scheduled task"""
        offset = (page - 1) * page_size

        async with self.pool.acquire() as conn:
            # Get total count
            total = await conn.fetchval("""
                SELECT COUNT(*)
                FROM task_executions
                WHERE scheduled_task_id = $1 AND tenant_id = $2
            """, scheduled_task_id, tenant_id)

            # Get executions
            rows = await conn.fetch("""
                SELECT *
                FROM task_executions
                WHERE scheduled_task_id = $1 AND tenant_id = $2
                ORDER BY created_at DESC
                LIMIT $3 OFFSET $4
            """, scheduled_task_id, tenant_id, page_size, offset)

            # Convert rows to dicts and handle type conversions
            executions = []
            for row in rows:
                execution = dict(row)
                # Convert Decimal to float for cost_usd
                if execution.get('cost_usd') is not None:
                    from decimal import Decimal
                    if isinstance(execution['cost_usd'], Decimal):
                        execution['cost_usd'] = float(execution['cost_usd'])
                # Parse result from JSON string to dict if needed
                if isinstance(execution.get('result'), str):
                    execution['result'] = json.loads(execution['result'])
                executions.append(execution)

            return executions, total
