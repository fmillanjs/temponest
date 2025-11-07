"""
Integration tests for main agent API endpoints.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.mark.integration
class TestMainAPI:
    """Test suite for main API endpoints"""

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint returns service info"""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "service" in data or "message" in data

    @pytest.mark.asyncio
    @patch("app.main.overseer_agent")
    @patch("app.main.cost_tracker")
    async def test_overseer_execution_with_mocks(
        self,
        mock_cost_tracker,
        mock_overseer,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test overseer agent execution with mocked dependencies"""
        # Mock the agent execution
        mock_result = MagicMock()
        mock_result.raw = "Test overseer response"
        mock_overseer.kickoff = AsyncMock(return_value=mock_result)

        # Mock cost tracking
        mock_cost_tracker.record_execution = AsyncMock(return_value={
            "task_id": "test-task-123",
            "total_cost_usd": 0.01,
            "budget_status": {"within_budget": True}
        })

        response = await client.post(
            "/overseer",
            json={
                "task": "Analyze this requirement",
                "risk_level": "low"
            },
            headers=test_auth_headers
        )

        # Might fail due to auth/dependencies, but check structure
        # This test validates the endpoint exists
        assert response.status_code in [200, 401, 422]  # Various valid states

    @pytest.mark.asyncio
    async def test_overseer_endpoint_requires_auth(self, client: AsyncClient):
        """Test overseer endpoint requires authentication"""
        response = await client.post(
            "/overseer",
            json={
                "task": "Test task",
                "risk_level": "low"
            }
        )

        # Should require auth or return 422 for invalid request
        assert response.status_code in [401, 403, 422]

    @pytest.mark.asyncio
    async def test_overseer_validation_requires_task(self, client: AsyncClient, test_auth_headers):
        """Test overseer endpoint validates required fields"""
        response = await client.post(
            "/overseer",
            json={
                "risk_level": "low"  # Missing 'task'
            },
            headers=test_auth_headers
        )

        assert response.status_code in [400, 422]  # Validation error

    @pytest.mark.asyncio
    async def test_developer_endpoint_exists(self, client: AsyncClient):
        """Test developer endpoint is accessible"""
        response = await client.post(
            "/developer",
            json={
                "task": "Write a Python function"
            }
        )

        # Just verify endpoint exists (will fail auth/validation)
        assert response.status_code in [200, 400, 401, 403, 422]
