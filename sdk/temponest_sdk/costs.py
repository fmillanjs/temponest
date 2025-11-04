"""
Temponest SDK - Cost Tracking Service Client
"""
from typing import Optional, Dict, Any
from datetime import datetime, date
from .client import BaseClient, AsyncBaseClient
from .models import CostSummary, BudgetConfig


class CostsClient:
    """Client for cost tracking and budget management"""

    def __init__(self, client: BaseClient):
        self.client = client

    def get_summary(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> CostSummary:
        """
        Get cost summary for a time period

        Args:
            start_date: Start date (ISO format: YYYY-MM-DD)
            end_date: End date (ISO format: YYYY-MM-DD)
            agent_id: Filter by agent ID
            project_id: Filter by project ID

        Returns:
            Cost summary

        Example:
            ```python
            summary = client.costs.get_summary(
                start_date="2025-01-01",
                end_date="2025-01-31"
            )
            print(f"Total cost: ${summary.total_usd}")
            print(f"By provider: {summary.by_provider}")
            ```
        """
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if agent_id:
            params["agent_id"] = agent_id
        if project_id:
            params["project_id"] = project_id

        response = self.client.get("/costs/summary", params=params)
        return CostSummary(**response)

    def get_daily_costs(
        self,
        days: int = 30,
    ) -> Dict[str, float]:
        """
        Get daily cost breakdown

        Args:
            days: Number of days to retrieve

        Returns:
            Dictionary mapping dates to costs
        """
        params = {"days": days}
        response = self.client.get("/costs/daily", params=params)
        return response

    def get_hourly_costs(
        self,
        hours: int = 24,
    ) -> Dict[str, float]:
        """
        Get hourly cost breakdown

        Args:
            hours: Number of hours to retrieve

        Returns:
            Dictionary mapping timestamps to costs
        """
        params = {"hours": hours}
        response = self.client.get("/costs/hourly", params=params)
        return response

    def get_agent_costs(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        top_n: int = 10,
    ) -> Dict[str, float]:
        """
        Get costs by agent

        Args:
            start_date: Start date
            end_date: End date
            top_n: Number of top agents to return

        Returns:
            Dictionary mapping agent IDs/names to costs
        """
        params = {"top_n": top_n}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        response = self.client.get("/costs/by-agent", params=params)
        return response

    def get_provider_costs(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Get costs by provider (OpenAI, Anthropic, etc.)

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary mapping providers to costs
        """
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        response = self.client.get("/costs/by-provider", params=params)
        return response

    def get_model_costs(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Get costs by model

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary mapping models to costs
        """
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        response = self.client.get("/costs/by-model", params=params)
        return response

    def get_budget(self) -> BudgetConfig:
        """
        Get current budget configuration

        Returns:
            Budget configuration
        """
        response = self.client.get("/costs/budget")
        return BudgetConfig(**response)

    def set_budget(
        self,
        daily_limit_usd: Optional[float] = None,
        monthly_limit_usd: Optional[float] = None,
        alert_threshold: float = 0.8,
    ) -> BudgetConfig:
        """
        Set budget limits

        Args:
            daily_limit_usd: Daily spending limit in USD
            monthly_limit_usd: Monthly spending limit in USD
            alert_threshold: Threshold (0-1) at which to send alerts

        Returns:
            Updated budget configuration

        Example:
            ```python
            budget = client.costs.set_budget(
                daily_limit_usd=50.0,
                monthly_limit_usd=1000.0,
                alert_threshold=0.8  # Alert at 80%
            )
            ```
        """
        payload = {
            "daily_limit_usd": daily_limit_usd,
            "monthly_limit_usd": monthly_limit_usd,
            "alert_threshold": alert_threshold,
        }

        response = self.client.post("/costs/budget", json=payload)
        return BudgetConfig(**response)

    def get_budget_status(self) -> Dict[str, Any]:
        """
        Get current budget usage status

        Returns:
            Dictionary with budget usage information including:
            - daily_usage: Current daily spending
            - daily_limit: Daily limit
            - daily_percentage: Percentage of daily budget used
            - monthly_usage: Current monthly spending
            - monthly_limit: Monthly limit
            - monthly_percentage: Percentage of monthly budget used
            - alerts_triggered: Number of alerts triggered
        """
        response = self.client.get("/costs/budget/status")
        return response

    def get_forecast(
        self,
        days: int = 7,
    ) -> Dict[str, float]:
        """
        Get cost forecast for upcoming days

        Args:
            days: Number of days to forecast

        Returns:
            Dictionary mapping dates to forecasted costs
        """
        params = {"days": days}
        response = self.client.get("/costs/forecast", params=params)
        return response

    def export_report(
        self,
        start_date: str,
        end_date: str,
        format: str = "csv",
    ) -> bytes:
        """
        Export cost report

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            format: Export format (csv, pdf, xlsx)

        Returns:
            Report file content as bytes
        """
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "format": format,
        }

        response = self.client.get("/costs/export", params=params)
        return response


class AsyncCostsClient:
    """Async client for cost tracking and budget management"""

    def __init__(self, client: AsyncBaseClient):
        self.client = client

    async def get_summary(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> CostSummary:
        """Get cost summary for a time period (async)"""
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if agent_id:
            params["agent_id"] = agent_id
        if project_id:
            params["project_id"] = project_id

        response = await self.client.get("/costs/summary", params=params)
        return CostSummary(**response)

    async def get_daily_costs(
        self,
        days: int = 30,
    ) -> Dict[str, float]:
        """Get daily cost breakdown (async)"""
        params = {"days": days}
        response = await self.client.get("/costs/daily", params=params)
        return response

    async def get_budget(self) -> BudgetConfig:
        """Get current budget configuration (async)"""
        response = await self.client.get("/costs/budget")
        return BudgetConfig(**response)

    async def set_budget(
        self,
        daily_limit_usd: Optional[float] = None,
        monthly_limit_usd: Optional[float] = None,
        alert_threshold: float = 0.8,
    ) -> BudgetConfig:
        """Set budget limits (async)"""
        payload = {
            "daily_limit_usd": daily_limit_usd,
            "monthly_limit_usd": monthly_limit_usd,
            "alert_threshold": alert_threshold,
        }

        response = await self.client.post("/costs/budget", json=payload)
        return BudgetConfig(**response)

    async def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget usage status (async)"""
        response = await self.client.get("/costs/budget/status")
        return response

    async def get_forecast(
        self,
        days: int = 7,
    ) -> Dict[str, float]:
        """Get cost forecast (async)"""
        params = {"days": days}
        response = await self.client.get("/costs/forecast", params=params)
        return response
