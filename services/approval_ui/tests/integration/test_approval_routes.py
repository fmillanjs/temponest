"""
Integration tests for approval API routes.
Tests all API endpoints with mocked dependencies.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock
from httpx import AsyncClient


class TestHealthEndpoint:
    """Test /health endpoint"""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, async_client):
        """Test health check when all services connected"""
        response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["temporal"] == "connected"

    @pytest.mark.asyncio
    async def test_health_check_no_database(self, app_with_mocks):
        """Test health check when database is disconnected"""
        app, db_conn, workflow_handle, auth_client, auth_context = app_with_mocks
        import main as main_module
        main_module.db_pool = None

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "disconnected"


class TestCreateApprovalEndpoint:
    """Test POST /api/approvals endpoint"""

    @pytest.mark.asyncio
    async def test_create_approval_success(
        self, async_client, sample_approval_request, valid_jwt_token, app_with_mocks
    ):
        """Test creating an approval request successfully"""
        _, db_conn, _, _, _ = app_with_mocks

        # Mock database insert
        db_conn.execute = AsyncMock()

        response = await async_client.post(
            "/api/approvals",
            json=sample_approval_request,
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert "approval_id" in data
        assert data["approved_by"] is None
        assert data["approved_at"] is None

        # Verify database was called
        db_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_approval_unauthorized(self, async_client, sample_approval_request):
        """Test creating approval without authentication"""
        response = await async_client.post(
            "/api/approvals",
            json=sample_approval_request
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_approval_no_permission(
        self, async_client, sample_approval_request, valid_jwt_token, app_with_mocks
    ):
        """Test creating approval without required permission"""
        _, _, _, auth_client, _ = app_with_mocks
        auth_client.check_permission.return_value = False

        response = await async_client.post(
            "/api/approvals",
            json=sample_approval_request,
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 403
        assert "Missing required permission" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_approval_invalid_data(self, async_client, valid_jwt_token):
        """Test creating approval with invalid data"""
        invalid_request = {
            "workflow_id": "wf-123"
            # Missing required fields
        }

        response = await async_client.post(
            "/api/approvals",
            json=invalid_request,
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_approval_database_unavailable(
        self, sample_approval_request, valid_jwt_token, app_with_mocks
    ):
        """Test creating approval when database is unavailable"""
        app, db_conn, workflow_handle, auth_client, auth_context = app_with_mocks
        import main as main_module
        main_module.db_pool = None

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/approvals",
                json=sample_approval_request,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )

        assert response.status_code == 503
        assert "Database not available" in response.json()["detail"]


class TestGetApprovalEndpoint:
    """Test GET /api/approvals/{approval_id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_approval_success(
        self, async_client, valid_jwt_token, sample_approval_db_row, app_with_mocks
    ):
        """Test getting an approval by ID"""
        _, db_conn, _, _, _ = app_with_mocks
        db_conn.fetchrow = AsyncMock(return_value=sample_approval_db_row)

        approval_id = sample_approval_db_row["id"]
        response = await async_client.get(
            f"/api/approvals/{approval_id}",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["approval_id"] == approval_id
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_approval_not_found(
        self, async_client, valid_jwt_token, app_with_mocks
    ):
        """Test getting a non-existent approval"""
        _, db_conn, _, _, _ = app_with_mocks
        db_conn.fetchrow = AsyncMock(return_value=None)

        response = await async_client.get(
            "/api/approvals/non-existent-id",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 404
        assert "Approval not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_approval_unauthorized(self, async_client):
        """Test getting approval without authentication"""
        response = await async_client.get("/api/approvals/test-id")

        assert response.status_code == 401


class TestListApprovalsEndpoint:
    """Test GET /api/approvals endpoint"""

    @pytest.mark.asyncio
    async def test_list_approvals_all(
        self, async_client, valid_jwt_token, app_with_mocks
    ):
        """Test listing all approvals"""
        _, db_conn, _, _, _ = app_with_mocks

        mock_rows = [
            {
                "id": "approval-1",
                "workflow_id": "wf-1",
                "task_description": "Task 1",
                "risk_level": "high",
                "status": "pending",
                "approved_by": None,
                "created_at": datetime.utcnow(),
                "approved_at": None
            },
            {
                "id": "approval-2",
                "workflow_id": "wf-2",
                "task_description": "Task 2",
                "risk_level": "low",
                "status": "approved",
                "approved_by": "john@example.com",
                "created_at": datetime.utcnow(),
                "approved_at": datetime.utcnow()
            }
        ]

        db_conn.fetch = AsyncMock(return_value=mock_rows)

        response = await async_client.get(
            "/api/approvals",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "approval-1"
        assert data[1]["id"] == "approval-2"

    @pytest.mark.asyncio
    async def test_list_approvals_filtered_by_status(
        self, async_client, valid_jwt_token, app_with_mocks
    ):
        """Test listing approvals filtered by status"""
        _, db_conn, _, _, _ = app_with_mocks

        mock_rows = [
            {
                "id": "approval-1",
                "workflow_id": "wf-1",
                "task_description": "Task 1",
                "risk_level": "high",
                "status": "pending",
                "approved_by": None,
                "created_at": datetime.utcnow(),
                "approved_at": None
            }
        ]

        db_conn.fetch = AsyncMock(return_value=mock_rows)

        response = await async_client.get(
            "/api/approvals?status=pending",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_list_approvals_empty(
        self, async_client, valid_jwt_token, app_with_mocks
    ):
        """Test listing approvals when none exist"""
        _, db_conn, _, _, _ = app_with_mocks
        db_conn.fetch = AsyncMock(return_value=[])

        response = await async_client.get(
            "/api/approvals",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestApproveTaskEndpoint:
    """Test POST /api/approvals/{approval_id}/approve endpoint"""

    @pytest.mark.asyncio
    async def test_approve_task_success(
        self, async_client, valid_jwt_token, app_with_mocks
    ):
        """Test approving a task successfully"""
        _, db_conn, workflow_handle, _, _ = app_with_mocks

        # Mock database fetchrow (get approval)
        db_conn.fetchrow = AsyncMock(return_value={
            "workflow_id": "wf-123",
            "run_id": "run-456",
            "status": "pending"
        })

        # Mock database execute (update approval and audit log)
        db_conn.execute = AsyncMock()

        # Mock workflow signal
        workflow_handle.signal = AsyncMock()

        response = await async_client.post(
            "/api/approvals/test-approval-id/approve",
            data={"approver": "john@example.com", "reason": "Looks good"},
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["approval_id"] == "test-approval-id"

        # Verify workflow signal was sent
        workflow_handle.signal.assert_called_once()
        call_args = workflow_handle.signal.call_args
        assert call_args[0][0] == "approval_signal"
        assert call_args[0][1]["status"] == "approved"
        assert call_args[0][1]["approver"] == "john@example.com"

    @pytest.mark.asyncio
    async def test_approve_task_not_found(
        self, async_client, valid_jwt_token, app_with_mocks
    ):
        """Test approving a non-existent task"""
        _, db_conn, _, _, _ = app_with_mocks
        db_conn.fetchrow = AsyncMock(return_value=None)

        response = await async_client.post(
            "/api/approvals/non-existent-id/approve",
            data={"approver": "john@example.com", "reason": "Test"},
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 404
        assert "Approval not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_approve_task_already_processed(
        self, async_client, valid_jwt_token, app_with_mocks
    ):
        """Test approving a task that's already processed"""
        _, db_conn, _, _, _ = app_with_mocks

        db_conn.fetchrow = AsyncMock(return_value={
            "workflow_id": "wf-123",
            "run_id": "run-456",
            "status": "approved"  # Already approved
        })

        response = await async_client.post(
            "/api/approvals/test-approval-id/approve",
            data={"approver": "john@example.com", "reason": "Test"},
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 400
        assert "Approval already processed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_approve_task_no_permission(
        self, async_client, valid_jwt_token, app_with_mocks
    ):
        """Test approving without required permission"""
        _, _, _, auth_client, _ = app_with_mocks
        auth_client.check_permission.return_value = False

        response = await async_client.post(
            "/api/approvals/test-approval-id/approve",
            data={"approver": "john@example.com", "reason": "Test"},
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 403


class TestDenyTaskEndpoint:
    """Test POST /api/approvals/{approval_id}/deny endpoint"""

    @pytest.mark.asyncio
    async def test_deny_task_success(
        self, async_client, valid_jwt_token, app_with_mocks
    ):
        """Test denying a task successfully"""
        _, db_conn, workflow_handle, _, _ = app_with_mocks

        # Mock database fetchrow (get approval)
        db_conn.fetchrow = AsyncMock(return_value={
            "workflow_id": "wf-123",
            "run_id": "run-456",
            "status": "pending"
        })

        # Mock database execute
        db_conn.execute = AsyncMock()

        # Mock workflow signal
        workflow_handle.signal = AsyncMock()

        response = await async_client.post(
            "/api/approvals/test-approval-id/deny",
            data={"approver": "admin@example.com", "reason": "Too risky"},
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "denied"
        assert data["approval_id"] == "test-approval-id"

        # Verify workflow signal was sent
        workflow_handle.signal.assert_called_once()
        call_args = workflow_handle.signal.call_args
        assert call_args[0][0] == "approval_signal"
        assert call_args[0][1]["status"] == "denied"
        assert call_args[0][1]["reason"] == "Too risky"

    @pytest.mark.asyncio
    async def test_deny_task_not_found(
        self, async_client, valid_jwt_token, app_with_mocks
    ):
        """Test denying a non-existent task"""
        _, db_conn, _, _, _ = app_with_mocks
        db_conn.fetchrow = AsyncMock(return_value=None)

        response = await async_client.post(
            "/api/approvals/non-existent-id/deny",
            data={"approver": "admin@example.com", "reason": "Test"},
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 404
        assert "Approval not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_deny_task_already_processed(
        self, async_client, valid_jwt_token, app_with_mocks
    ):
        """Test denying a task that's already processed"""
        _, db_conn, _, _, _ = app_with_mocks

        db_conn.fetchrow = AsyncMock(return_value={
            "workflow_id": "wf-123",
            "run_id": "run-456",
            "status": "denied"  # Already denied
        })

        response = await async_client.post(
            "/api/approvals/test-approval-id/deny",
            data={"approver": "admin@example.com", "reason": "Test"},
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 400
        assert "Approval already processed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_deny_task_missing_reason(
        self, async_client, valid_jwt_token, app_with_mocks
    ):
        """Test denying without providing a reason"""
        response = await async_client.post(
            "/api/approvals/test-approval-id/deny",
            data={"approver": "admin@example.com"},  # Missing reason
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 422  # Validation error
