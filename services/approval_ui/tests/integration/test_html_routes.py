"""
Integration tests for HTML routes.
Tests dashboard and approval detail pages.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock
from httpx import AsyncClient


class TestDashboardEndpoint:
    """Test GET / (dashboard) endpoint"""

    @pytest.mark.asyncio
    async def test_dashboard_with_pending_approvals(self, app_with_mocks):
        """Test dashboard showing pending approvals"""
        app, db_conn, _, _, _ = app_with_mocks

        # Mock pending approvals
        mock_rows = [
            {
                "id": "approval-1",
                "workflow_id": "wf-1",
                "task_description": "Deploy production",
                "risk_level": "high",
                "created_at": datetime.utcnow()
            },
            {
                "id": "approval-2",
                "workflow_id": "wf-2",
                "task_description": "Update database",
                "risk_level": "medium",
                "created_at": datetime.utcnow()
            }
        ]

        db_conn.fetch = AsyncMock(return_value=mock_rows)

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

        # Check that the SQL query was called with correct filtering
        db_conn.fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_dashboard_empty(self, app_with_mocks):
        """Test dashboard with no pending approvals"""
        app, db_conn, _, _, _ = app_with_mocks

        db_conn.fetch = AsyncMock(return_value=[])

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    @pytest.mark.asyncio
    async def test_dashboard_database_unavailable(self, app_with_mocks):
        """Test dashboard when database is unavailable"""
        app, db_conn, workflow_handle, auth_client, auth_context = app_with_mocks
        import main as main_module
        main_module.db_pool = None

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")

        assert response.status_code == 503
        assert "Service Unavailable" in response.text


class TestApprovalDetailEndpoint:
    """Test GET /approval/{approval_id} endpoint"""

    @pytest.mark.asyncio
    async def test_approval_detail_success(self, app_with_mocks):
        """Test approval detail page with valid approval"""
        app, db_conn, _, _, _ = app_with_mocks

        # Mock approval data
        mock_row = {
            "id": "approval-123",
            "workflow_id": "wf-456",
            "run_id": "run-789",
            "task_description": "Deploy to production",
            "risk_level": "high",
            "context": {"environment": "prod"},
            "status": "pending",
            "approved_by": None,
            "created_at": datetime.utcnow(),
            "approved_at": None
        }

        db_conn.fetchrow = AsyncMock(return_value=mock_row)

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/approval/approval-123")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

        # Verify database query was made
        db_conn.fetchrow.assert_called_once()

    @pytest.mark.asyncio
    async def test_approval_detail_not_found(self, app_with_mocks):
        """Test approval detail page with non-existent approval"""
        app, db_conn, _, _, _ = app_with_mocks

        db_conn.fetchrow = AsyncMock(return_value=None)

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/approval/non-existent-id")

        assert response.status_code == 404
        assert "Approval Not Found" in response.text

    @pytest.mark.asyncio
    async def test_approval_detail_database_unavailable(self, app_with_mocks):
        """Test approval detail when database is unavailable"""
        app, db_conn, workflow_handle, auth_client, auth_context = app_with_mocks
        import main as main_module
        main_module.db_pool = None

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/approval/approval-123")

        assert response.status_code == 503
        assert "Service Unavailable" in response.text

    @pytest.mark.asyncio
    async def test_approval_detail_approved(self, app_with_mocks):
        """Test approval detail page for approved approval"""
        app, db_conn, _, _, _ = app_with_mocks

        # Mock approved approval data
        mock_row = {
            "id": "approval-123",
            "workflow_id": "wf-456",
            "run_id": "run-789",
            "task_description": "Deploy to production",
            "risk_level": "high",
            "context": {"environment": "prod"},
            "status": "approved",
            "approved_by": "john@example.com",
            "created_at": datetime.utcnow(),
            "approved_at": datetime.utcnow()
        }

        db_conn.fetchrow = AsyncMock(return_value=mock_row)

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/approval/approval-123")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
