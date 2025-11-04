"""
Cost Tracker - Records and manages cost tracking for agent executions.

Stores costs in PostgreSQL and checks against budgets.
"""

from typing import Dict, Any, Optional, List
from decimal import Decimal
from uuid import UUID
import asyncpg
from datetime import datetime

from .calculator import CostCalculator


class CostTracker:
    """Track costs and manage budgets"""

    def __init__(self, db_pool: asyncpg.Pool, calculator: CostCalculator):
        """
        Initialize cost tracker.

        Args:
            db_pool: AsyncPG connection pool
            calculator: Cost calculator instance
        """
        self.db_pool = db_pool
        self.calculator = calculator

    async def record_execution(
        self,
        task_id: str,
        agent_name: str,
        user_id: Optional[UUID],
        tenant_id: UUID,
        model_provider: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
        status: str = "completed",
        project_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Record an agent execution with costs.

        Returns:
            Dict with cost info and budget status
        """
        # Calculate costs
        input_cost, output_cost, total_cost = self.calculator.calculate_cost(
            provider=model_provider,
            model=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )

        total_tokens = input_tokens + output_tokens

        # Insert into cost_tracking table
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO cost_tracking (
                    task_id, agent_name, user_id, tenant_id,
                    project_id, workflow_id,
                    model_provider, model_name,
                    input_tokens, output_tokens, total_tokens,
                    input_cost_usd, output_cost_usd, total_cost_usd,
                    latency_ms, status, context
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                """,
                task_id, agent_name, user_id, tenant_id,
                project_id, workflow_id,
                model_provider, model_name,
                input_tokens, output_tokens, total_tokens,
                input_cost, output_cost, total_cost,
                latency_ms, status, context
            )

            # Check and update budgets
            budget_status = await self._check_budgets(
                conn, tenant_id, user_id, project_id, total_cost
            )

        return {
            "task_id": task_id,
            "total_cost_usd": float(total_cost),
            "input_cost_usd": float(input_cost),
            "output_cost_usd": float(output_cost),
            "total_tokens": total_tokens,
            "budget_status": budget_status
        }

    async def _check_budgets(
        self,
        conn: asyncpg.Connection,
        tenant_id: UUID,
        user_id: Optional[UUID],
        project_id: Optional[str],
        cost_usd: Decimal
    ) -> Dict[str, Any]:
        """Check budgets and create alerts if needed"""
        # Call the check_and_update_budget function
        results = await conn.fetch(
            """
            SELECT * FROM check_and_update_budget($1, $2, $3, $4)
            """,
            tenant_id, user_id, project_id, cost_usd
        )

        if not results or results[0]["exceeded"] is None:
            return {
                "within_budget": True,
                "alerts": []
            }

        alerts = []
        exceeded = False

        for row in results:
            if row["exceeded"]:
                exceeded = True

            if row["alert_type"]:
                alerts.append({
                    "budget_id": str(row["budget_id"]),
                    "alert_type": row["alert_type"]
                })

        return {
            "within_budget": not exceeded,
            "budget_exceeded": exceeded,
            "alerts": alerts
        }

    async def get_cost_summary(
        self,
        tenant_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "agent"  # agent, project, user, daily
    ) -> List[Dict[str, Any]]:
        """
        Get cost summary grouped by specified dimension.

        Args:
            tenant_id: Tenant ID to filter by
            start_date: Optional start date filter
            end_date: Optional end date filter
            group_by: Grouping dimension (agent, project, user, daily)

        Returns:
            List of cost summaries
        """
        # Build query based on grouping
        if group_by == "agent":
            query = """
                SELECT
                    agent_name,
                    COUNT(*) as total_executions,
                    SUM(total_tokens) as total_tokens,
                    SUM(total_cost_usd) as total_cost_usd,
                    AVG(total_cost_usd) as avg_cost_per_execution,
                    AVG(latency_ms) as avg_latency_ms
                FROM cost_tracking
                WHERE tenant_id = $1
                AND ($2::timestamp IS NULL OR created_at >= $2)
                AND ($3::timestamp IS NULL OR created_at <= $3)
                GROUP BY agent_name
                ORDER BY total_cost_usd DESC
            """
        elif group_by == "project":
            query = """
                SELECT
                    project_id,
                    COUNT(*) as total_executions,
                    SUM(total_tokens) as total_tokens,
                    SUM(total_cost_usd) as total_cost_usd,
                    AVG(total_cost_usd) as avg_cost_per_execution
                FROM cost_tracking
                WHERE tenant_id = $1
                AND project_id IS NOT NULL
                AND ($2::timestamp IS NULL OR created_at >= $2)
                AND ($3::timestamp IS NULL OR created_at <= $3)
                GROUP BY project_id
                ORDER BY total_cost_usd DESC
            """
        elif group_by == "user":
            query = """
                SELECT
                    user_id,
                    COUNT(*) as total_executions,
                    SUM(total_tokens) as total_tokens,
                    SUM(total_cost_usd) as total_cost_usd,
                    AVG(total_cost_usd) as avg_cost_per_execution
                FROM cost_tracking
                WHERE tenant_id = $1
                AND user_id IS NOT NULL
                AND ($2::timestamp IS NULL OR created_at >= $2)
                AND ($3::timestamp IS NULL OR created_at <= $3)
                GROUP BY user_id
                ORDER BY total_cost_usd DESC
            """
        elif group_by == "daily":
            query = """
                SELECT
                    DATE(created_at) as date,
                    COUNT(*) as total_executions,
                    SUM(total_tokens) as total_tokens,
                    SUM(total_cost_usd) as total_cost_usd
                FROM cost_tracking
                WHERE tenant_id = $1
                AND ($2::timestamp IS NULL OR created_at >= $2)
                AND ($3::timestamp IS NULL OR created_at <= $3)
                GROUP BY DATE(created_at)
                ORDER BY DATE(created_at) DESC
            """
        else:
            raise ValueError(f"Invalid group_by: {group_by}")

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, tenant_id, start_date, end_date)

        # Convert to dict
        results = []
        for row in rows:
            result = dict(row)
            # Convert Decimal to float for JSON serialization
            if "total_cost_usd" in result:
                result["total_cost_usd"] = float(result["total_cost_usd"])
            if "avg_cost_per_execution" in result:
                result["avg_cost_per_execution"] = float(result["avg_cost_per_execution"])
            # Convert UUID to string
            if "user_id" in result and result["user_id"]:
                result["user_id"] = str(result["user_id"])
            results.append(result)

        return results

    async def get_budgets(
        self,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        project_id: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get budgets for tenant/user/project"""
        query = """
            SELECT
                id, tenant_id, user_id, project_id,
                budget_type, budget_amount_usd, current_spend_usd,
                period_start, period_end,
                alert_threshold_pct, critical_threshold_pct,
                is_active, last_reset_at, notes,
                created_at, updated_at
            FROM cost_budgets
            WHERE 1=1
            AND ($1::UUID IS NULL OR tenant_id = $1)
            AND ($2::UUID IS NULL OR user_id = $2)
            AND ($3::VARCHAR IS NULL OR project_id = $3)
            AND ($4::BOOLEAN = false OR is_active = true)
            ORDER BY created_at DESC
        """

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, tenant_id, user_id, project_id, active_only)

        results = []
        for row in rows:
            result = dict(row)
            # Convert types
            if result.get("id"):
                result["id"] = str(result["id"])
            if result.get("tenant_id"):
                result["tenant_id"] = str(result["tenant_id"])
            if result.get("user_id"):
                result["user_id"] = str(result["user_id"])
            if result.get("budget_amount_usd"):
                result["budget_amount_usd"] = float(result["budget_amount_usd"])
            if result.get("current_spend_usd"):
                result["current_spend_usd"] = float(result["current_spend_usd"])

            # Calculate utilization
            if result["budget_amount_usd"] > 0:
                utilization = (result["current_spend_usd"] / result["budget_amount_usd"]) * 100
                result["utilization_pct"] = round(utilization, 2)
            else:
                result["utilization_pct"] = 0

            results.append(result)

        return results

    async def create_budget(
        self,
        tenant_id: Optional[UUID],
        user_id: Optional[UUID],
        project_id: Optional[str],
        budget_type: str,
        budget_amount_usd: Decimal,
        alert_threshold_pct: int = 80,
        critical_threshold_pct: int = 95,
        period_days: Optional[int] = None,
        notes: Optional[str] = None,
        created_by: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Create a new budget.

        Args:
            tenant_id: Tenant ID (required for tenant-level budgets)
            user_id: User ID (required for user-level budgets)
            project_id: Project ID (required for project-level budgets)
            budget_type: daily, weekly, monthly, or total
            budget_amount_usd: Budget amount in USD
            alert_threshold_pct: Alert at this % of budget (default 80)
            critical_threshold_pct: Critical alert at this % (default 95)
            period_days: Custom period in days (for total budgets)
            notes: Optional notes
            created_by: User who created the budget

        Returns:
            Created budget info
        """
        # Validate: exactly one of tenant/user/project must be set
        scope_count = sum([
            tenant_id is not None,
            user_id is not None,
            project_id is not None
        ])
        if scope_count != 1:
            raise ValueError("Exactly one of tenant_id, user_id, or project_id must be set")

        # Calculate period_end
        period_end = None
        if budget_type == "daily":
            period_days = 1
        elif budget_type == "weekly":
            period_days = 7
        elif budget_type == "monthly":
            period_days = 30

        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO cost_budgets (
                    tenant_id, user_id, project_id,
                    budget_type, budget_amount_usd,
                    alert_threshold_pct, critical_threshold_pct,
                    period_end, notes, created_by
                ) VALUES ($1, $2, $3, $4, $5, $6, $7,
                    CASE WHEN $8::INTEGER IS NOT NULL
                        THEN CURRENT_TIMESTAMP + ($8 || ' days')::INTERVAL
                        ELSE NULL
                    END,
                    $9, $10)
                RETURNING id, created_at
                """,
                tenant_id, user_id, project_id,
                budget_type, budget_amount_usd,
                alert_threshold_pct, critical_threshold_pct,
                period_days, notes, created_by
            )

        return {
            "id": str(row["id"]),
            "budget_type": budget_type,
            "budget_amount_usd": float(budget_amount_usd),
            "alert_threshold_pct": alert_threshold_pct,
            "critical_threshold_pct": critical_threshold_pct,
            "created_at": row["created_at"]
        }

    async def get_alerts(
        self,
        tenant_id: UUID,
        unacknowledged_only: bool = True,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get cost alerts for a tenant"""
        query = """
            SELECT
                ca.id, ca.budget_id, ca.alert_type,
                ca.threshold_pct, ca.current_spend_usd, ca.budget_amount_usd,
                ca.is_acknowledged, ca.acknowledged_by, ca.acknowledged_at,
                ca.message, ca.created_at,
                cb.budget_type,
                COALESCE(cb.project_id, u.email, t.name) as scope_name
            FROM cost_alerts ca
            JOIN cost_budgets cb ON ca.budget_id = cb.id
            LEFT JOIN users u ON cb.user_id = u.id
            LEFT JOIN tenants t ON cb.tenant_id = t.id
            WHERE ca.tenant_id = $1
            AND ($2::BOOLEAN = false OR ca.is_acknowledged = false)
            ORDER BY ca.created_at DESC
            LIMIT $3
        """

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, tenant_id, unacknowledged_only, limit)

        results = []
        for row in rows:
            result = dict(row)
            # Convert types
            if result.get("id"):
                result["id"] = str(result["id"])
            if result.get("budget_id"):
                result["budget_id"] = str(result["budget_id"])
            if result.get("acknowledged_by"):
                result["acknowledged_by"] = str(result["acknowledged_by"])
            if result.get("current_spend_usd"):
                result["current_spend_usd"] = float(result["current_spend_usd"])
            if result.get("budget_amount_usd"):
                result["budget_amount_usd"] = float(result["budget_amount_usd"])

            results.append(result)

        return results

    async def acknowledge_alert(
        self,
        alert_id: UUID,
        acknowledged_by: UUID
    ) -> bool:
        """Mark an alert as acknowledged"""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE cost_alerts
                SET is_acknowledged = true,
                    acknowledged_by = $2,
                    acknowledged_at = CURRENT_TIMESTAMP
                WHERE id = $1
                """,
                alert_id, acknowledged_by
            )

        return result == "UPDATE 1"
