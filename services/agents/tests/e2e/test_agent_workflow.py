"""
End-to-end tests for agent workflows.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
class TestAgentWorkflow:
    """End-to-end tests for complete agent workflows"""

    @pytest.mark.asyncio
    async def test_health_check_e2e(self, client: AsyncClient):
        """Test end-to-end health check workflow"""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        # In test environment, "degraded" is acceptable (missing dependencies)
        assert data["status"] in ["healthy", "degraded"]
        assert "services" in data
        assert "models" in data

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires full service dependencies")
    async def test_full_agent_execution_workflow(self, client: AsyncClient, test_auth_headers):
        """Test complete agent execution workflow end-to-end"""
        # This test would require:
        # 1. Running Ollama/LLM services
        # 2. Running Qdrant
        # 3. Running Auth service
        # 4. Database with proper schema
        #
        # For now, skipped - run manually with docker-compose

        response = await client.post(
            "/overseer",
            json={
                "task": "Analyze this simple requirement: Create a todo list",
                "context": {"domain": "web development"},
                "risk_level": "low",
                "project_id": "test-project",
                "workflow_id": "test-workflow"
            },
            headers=test_auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "task_id" in data
        assert "status" in data
        assert "result" in data
        assert "tokens_used" in data
        assert "cost_info" in data

        # Verify cost tracking
        assert data["cost_info"]["total_cost_usd"] >= 0
        assert data["cost_info"]["budget_status"]["within_budget"] is True

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires full service dependencies")
    async def test_cost_tracking_workflow(self, client: AsyncClient, test_auth_headers):
        """Test cost tracking throughout agent execution"""
        # 1. Create a budget
        budget_response = await client.post(
            "/cost/budgets",
            json={
                "project_id": "test-project",
                "budget_type": "daily",
                "budget_amount_usd": 10.0,
                "alert_threshold_pct": 80
            },
            headers=test_auth_headers
        )

        assert budget_response.status_code == 200

        # 2. Execute agent (will track costs against budget)
        exec_response = await client.post(
            "/overseer",
            json={
                "task": "Simple task",
                "project_id": "test-project"
            },
            headers=test_auth_headers
        )

        assert exec_response.status_code == 200

        # 3. Check cost summary
        cost_response = await client.get(
            "/cost/summary?project_id=test-project",
            headers=test_auth_headers
        )

        assert cost_response.status_code == 200
        cost_data = cost_response.json()

        assert cost_data["total_executions"] >= 1
        assert cost_data["total_cost_usd"] >= 0
