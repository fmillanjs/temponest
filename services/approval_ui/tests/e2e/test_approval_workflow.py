"""
End-to-end tests for complete approval workflows.
Tests full user journeys from creation to approval/denial.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock
from httpx import AsyncClient


class TestCompleteApprovalWorkflow:
    """Test complete approval workflow from creation to resolution"""

    @pytest.mark.asyncio
    async def test_create_and_approve_workflow(
        self, async_client, valid_jwt_token, sample_approval_request, app_with_mocks
    ):
        """Test complete workflow: create -> list -> get -> approve"""
        _, db_conn, workflow_handle, _, _ = app_with_mocks

        # Step 1: Create approval request
        db_conn.execute = AsyncMock()

        create_response = await async_client.post(
            "/api/approvals",
            json=sample_approval_request,
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert create_response.status_code == 200
        approval_data = create_response.json()
        approval_id = approval_data["approval_id"]
        assert approval_data["status"] == "pending"

        # Step 2: List approvals (should include our new one)
        mock_list_rows = [{
            "id": approval_id,
            "workflow_id": sample_approval_request["workflow_id"],
            "task_description": sample_approval_request["task_description"],
            "risk_level": sample_approval_request["risk_level"],
            "status": "pending",
            "approved_by": None,
            "created_at": datetime.utcnow(),
            "approved_at": None
        }]

        db_conn.fetch = AsyncMock(return_value=mock_list_rows)

        list_response = await async_client.get(
            "/api/approvals?status=pending",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert list_response.status_code == 200
        approvals_list = list_response.json()
        assert len(approvals_list) == 1
        assert approvals_list[0]["id"] == approval_id
        assert approvals_list[0]["status"] == "pending"

        # Step 3: Get specific approval details
        mock_get_row = {
            "id": approval_id,
            "status": "pending",
            "approved_by": None,
            "approved_at": None
        }

        db_conn.fetchrow = AsyncMock(return_value=mock_get_row)

        get_response = await async_client.get(
            f"/api/approvals/{approval_id}",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert get_response.status_code == 200
        approval_detail = get_response.json()
        assert approval_detail["approval_id"] == approval_id
        assert approval_detail["status"] == "pending"

        # Step 4: Approve the request
        mock_approval_row = {
            "workflow_id": sample_approval_request["workflow_id"],
            "run_id": sample_approval_request["run_id"],
            "status": "pending"
        }

        db_conn.fetchrow = AsyncMock(return_value=mock_approval_row)
        workflow_handle.signal = AsyncMock()

        approve_response = await async_client.post(
            f"/api/approvals/{approval_id}/approve",
            data={"approver": "john@example.com", "reason": "LGTM"},
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert approve_response.status_code == 200
        approve_data = approve_response.json()
        assert approve_data["status"] == "approved"

        # Verify Temporal signal was sent
        workflow_handle.signal.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_and_deny_workflow(
        self, async_client, valid_jwt_token, sample_approval_request, app_with_mocks
    ):
        """Test complete workflow: create -> deny"""
        _, db_conn, workflow_handle, _, _ = app_with_mocks

        # Step 1: Create approval request
        db_conn.execute = AsyncMock()

        create_response = await async_client.post(
            "/api/approvals",
            json=sample_approval_request,
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert create_response.status_code == 200
        approval_data = create_response.json()
        approval_id = approval_data["approval_id"]

        # Step 2: Deny the request
        mock_approval_row = {
            "workflow_id": sample_approval_request["workflow_id"],
            "run_id": sample_approval_request["run_id"],
            "status": "pending"
        }

        db_conn.fetchrow = AsyncMock(return_value=mock_approval_row)
        workflow_handle.signal = AsyncMock()

        deny_response = await async_client.post(
            f"/api/approvals/{approval_id}/deny",
            data={"approver": "admin@example.com", "reason": "Security concerns"},
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert deny_response.status_code == 200
        deny_data = deny_response.json()
        assert deny_data["status"] == "denied"

        # Verify Temporal signal was sent with correct data
        workflow_handle.signal.assert_called_once()
        call_args = workflow_handle.signal.call_args
        assert call_args[0][1]["status"] == "denied"
        assert call_args[0][1]["reason"] == "Security concerns"

    @pytest.mark.asyncio
    async def test_multiple_approvals_workflow(
        self, async_client, valid_jwt_token, app_with_mocks
    ):
        """Test workflow with multiple concurrent approvals"""
        _, db_conn, workflow_handle, _, _ = app_with_mocks

        db_conn.execute = AsyncMock()

        # Create multiple approval requests
        approval_ids = []

        for i in range(3):
            request = {
                "workflow_id": f"wf-{i}",
                "run_id": f"run-{i}",
                "task_description": f"Task {i}",
                "risk_level": ["low", "medium", "high"][i]
            }

            response = await async_client.post(
                "/api/approvals",
                json=request,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )

            assert response.status_code == 200
            approval_ids.append(response.json()["approval_id"])

        # List all pending approvals
        mock_rows = [
            {
                "id": approval_ids[i],
                "workflow_id": f"wf-{i}",
                "task_description": f"Task {i}",
                "risk_level": ["low", "medium", "high"][i],
                "status": "pending",
                "approved_by": None,
                "created_at": datetime.utcnow(),
                "approved_at": None
            }
            for i in range(3)
        ]

        db_conn.fetch = AsyncMock(return_value=mock_rows)

        list_response = await async_client.get(
            "/api/approvals",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert list_response.status_code == 200
        approvals = list_response.json()
        assert len(approvals) == 3

        # Approve the high-risk one
        db_conn.fetchrow = AsyncMock(return_value={
            "workflow_id": "wf-2",
            "run_id": "run-2",
            "status": "pending"
        })
        workflow_handle.signal = AsyncMock()

        approve_response = await async_client.post(
            f"/api/approvals/{approval_ids[2]}/approve",
            data={"approver": "manager@example.com", "reason": "High priority approved"},
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert approve_response.status_code == 200

    @pytest.mark.asyncio
    async def test_double_approval_prevention(
        self, async_client, valid_jwt_token, sample_approval_request, app_with_mocks
    ):
        """Test that approvals cannot be processed twice"""
        _, db_conn, workflow_handle, _, _ = app_with_mocks

        # Create approval
        db_conn.execute = AsyncMock()

        create_response = await async_client.post(
            "/api/approvals",
            json=sample_approval_request,
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        approval_id = create_response.json()["approval_id"]

        # First approval succeeds
        db_conn.fetchrow = AsyncMock(return_value={
            "workflow_id": sample_approval_request["workflow_id"],
            "run_id": sample_approval_request["run_id"],
            "status": "pending"
        })
        workflow_handle.signal = AsyncMock()

        first_approve = await async_client.post(
            f"/api/approvals/{approval_id}/approve",
            data={"approver": "user1@example.com", "reason": "OK"},
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert first_approve.status_code == 200

        # Second approval fails (already processed)
        db_conn.fetchrow = AsyncMock(return_value={
            "workflow_id": sample_approval_request["workflow_id"],
            "run_id": sample_approval_request["run_id"],
            "status": "approved"  # Already approved
        })

        second_approve = await async_client.post(
            f"/api/approvals/{approval_id}/approve",
            data={"approver": "user2@example.com", "reason": "Also OK"},
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert second_approve.status_code == 400
        assert "already processed" in second_approve.json()["detail"]


class TestApprovalWorkflowWithRiskLevels:
    """Test workflows with different risk levels"""

    @pytest.mark.asyncio
    async def test_high_risk_approval_workflow(
        self, async_client, valid_jwt_token, app_with_mocks
    ):
        """Test high-risk approval workflow"""
        _, db_conn, workflow_handle, _, _ = app_with_mocks

        high_risk_request = {
            "workflow_id": "wf-high-risk",
            "run_id": "run-high-risk",
            "task_description": "Delete production database",
            "risk_level": "high",
            "context": {
                "impact": "critical",
                "reversible": False
            }
        }

        db_conn.execute = AsyncMock()

        response = await async_client.post(
            "/api/approvals",
            json=high_risk_request,
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "pending"

    @pytest.mark.asyncio
    async def test_low_risk_approval_workflow(
        self, async_client, valid_jwt_token, app_with_mocks
    ):
        """Test low-risk approval workflow"""
        _, db_conn, workflow_handle, _, _ = app_with_mocks

        low_risk_request = {
            "workflow_id": "wf-low-risk",
            "run_id": "run-low-risk",
            "task_description": "Update documentation",
            "risk_level": "low",
            "context": {
                "impact": "minimal",
                "reversible": True
            }
        }

        db_conn.execute = AsyncMock()

        response = await async_client.post(
            "/api/approvals",
            json=low_risk_request,
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "pending"


class TestApprovalWorkflowErrorHandling:
    """Test error handling in approval workflows"""

    @pytest.mark.asyncio
    async def test_workflow_with_temporal_failure(
        self, async_client, valid_jwt_token, sample_approval_request, app_with_mocks
    ):
        """Test approval workflow when Temporal signal fails"""
        _, db_conn, workflow_handle, _, _ = app_with_mocks

        # Create approval
        db_conn.execute = AsyncMock()

        create_response = await async_client.post(
            "/api/approvals",
            json=sample_approval_request,
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        approval_id = create_response.json()["approval_id"]

        # Approve with Temporal failure
        db_conn.fetchrow = AsyncMock(return_value={
            "workflow_id": sample_approval_request["workflow_id"],
            "run_id": sample_approval_request["run_id"],
            "status": "pending"
        })
        workflow_handle.signal = AsyncMock(side_effect=Exception("Temporal connection failed"))

        # The endpoint should raise the exception
        with pytest.raises(Exception):
            await async_client.post(
                f"/api/approvals/{approval_id}/approve",
                data={"approver": "john@example.com", "reason": "OK"},
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )

    @pytest.mark.asyncio
    async def test_workflow_with_database_failure(
        self, async_client, valid_jwt_token, sample_approval_request, app_with_mocks
    ):
        """Test approval workflow when database fails"""
        _, db_conn, workflow_handle, _, _ = app_with_mocks

        # Database failure on create
        db_conn.execute = AsyncMock(side_effect=Exception("Database connection failed"))

        with pytest.raises(Exception):
            await async_client.post(
                "/api/approvals",
                json=sample_approval_request,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
