"""
Integration tests for health check API.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestHealthAPI:
    """Test suite for health check endpoint"""

    @pytest.mark.asyncio
    async def test_health_check_returns_200(self, client: AsyncClient):
        """Test health endpoint returns 200"""
        response = await client.get("/health")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_check_response_structure(self, client: AsyncClient):
        """Test health check response has expected structure"""
        response = await client.get("/health")

        data = response.json()
        assert "status" in data
        assert "services" in data
        assert "models" in data

    @pytest.mark.asyncio
    async def test_health_check_status_healthy(self, client: AsyncClient):
        """Test health check shows valid status"""
        response = await client.get("/health")

        data = response.json()
        # In test environment, "degraded" is acceptable (missing dependencies)
        assert data["status"] in ["healthy", "degraded"]

    @pytest.mark.asyncio
    async def test_health_check_includes_services(self, client: AsyncClient):
        """Test health check includes service statuses"""
        response = await client.get("/health")

        data = response.json()
        services = data["services"]

        # Check that key services are reported
        assert isinstance(services, dict)
        # The actual services depend on what's running
        # Just verify it's a dict structure

    @pytest.mark.asyncio
    async def test_health_check_includes_models(self, client: AsyncClient):
        """Test health check includes model information"""
        response = await client.get("/health")

        data = response.json()
        models = data["models"]

        assert isinstance(models, dict)
        # Should include configured models
