"""
Unit tests for data models in main.py.
Tests ApprovalRequest and ApprovalResponse models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from main import ApprovalRequest, ApprovalResponse


class TestApprovalRequest:
    """Test ApprovalRequest model"""

    def test_approval_request_creation(self):
        """Test creating an ApprovalRequest with all fields"""
        request = ApprovalRequest(
            workflow_id="wf-123",
            run_id="run-456",
            task_description="Deploy to production",
            risk_level="high",
            context={"environment": "prod", "service": "api"}
        )

        assert request.workflow_id == "wf-123"
        assert request.run_id == "run-456"
        assert request.task_description == "Deploy to production"
        assert request.risk_level == "high"
        assert request.context == {"environment": "prod", "service": "api"}

    def test_approval_request_minimal(self):
        """Test creating an ApprovalRequest with minimal fields"""
        request = ApprovalRequest(
            workflow_id="wf-123",
            run_id="run-456",
            task_description="Test task",
            risk_level="low"
        )

        assert request.workflow_id == "wf-123"
        assert request.run_id == "run-456"
        assert request.task_description == "Test task"
        assert request.risk_level == "low"
        assert request.context == {}  # Default empty dict

    def test_approval_request_missing_fields(self):
        """Test ApprovalRequest validation with missing required fields"""
        with pytest.raises(ValidationError) as exc_info:
            ApprovalRequest(
                workflow_id="wf-123",
                # Missing run_id, task_description, risk_level
            )

        errors = exc_info.value.errors()
        assert len(errors) == 3
        field_names = [error["loc"][0] for error in errors]
        assert "run_id" in field_names
        assert "task_description" in field_names
        assert "risk_level" in field_names

    def test_approval_request_context_types(self):
        """Test ApprovalRequest with various context types"""
        # Empty context
        request1 = ApprovalRequest(
            workflow_id="wf-1",
            run_id="run-1",
            task_description="Task 1",
            risk_level="low",
            context={}
        )
        assert request1.context == {}

        # Nested context
        request2 = ApprovalRequest(
            workflow_id="wf-2",
            run_id="run-2",
            task_description="Task 2",
            risk_level="medium",
            context={
                "metadata": {
                    "author": "john",
                    "version": "1.0"
                },
                "tags": ["urgent", "deployment"]
            }
        )
        assert request2.context["metadata"]["author"] == "john"
        assert "urgent" in request2.context["tags"]

    def test_approval_request_risk_levels(self):
        """Test ApprovalRequest with different risk levels"""
        for risk_level in ["low", "medium", "high", "critical"]:
            request = ApprovalRequest(
                workflow_id="wf-123",
                run_id="run-456",
                task_description="Test task",
                risk_level=risk_level
            )
            assert request.risk_level == risk_level


class TestApprovalResponse:
    """Test ApprovalResponse model"""

    def test_approval_response_pending(self):
        """Test ApprovalResponse for pending approval"""
        response = ApprovalResponse(
            approval_id="approval-123",
            status="pending"
        )

        assert response.approval_id == "approval-123"
        assert response.status == "pending"
        assert response.approved_by is None
        assert response.approved_at is None

    def test_approval_response_approved(self):
        """Test ApprovalResponse for approved approval"""
        now = datetime.utcnow()

        response = ApprovalResponse(
            approval_id="approval-456",
            status="approved",
            approved_by="john@example.com",
            approved_at=now
        )

        assert response.approval_id == "approval-456"
        assert response.status == "approved"
        assert response.approved_by == "john@example.com"
        assert response.approved_at == now

    def test_approval_response_denied(self):
        """Test ApprovalResponse for denied approval"""
        now = datetime.utcnow()

        response = ApprovalResponse(
            approval_id="approval-789",
            status="denied",
            approved_by="admin@example.com",
            approved_at=now
        )

        assert response.approval_id == "approval-789"
        assert response.status == "denied"
        assert response.approved_by == "admin@example.com"
        assert response.approved_at == now

    def test_approval_response_missing_approval_id(self):
        """Test ApprovalResponse validation with missing approval_id"""
        with pytest.raises(ValidationError) as exc_info:
            ApprovalResponse(status="pending")

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"][0] == "approval_id"

    def test_approval_response_missing_status(self):
        """Test ApprovalResponse validation with missing status"""
        with pytest.raises(ValidationError) as exc_info:
            ApprovalResponse(approval_id="approval-123")

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"][0] == "status"

    def test_approval_response_optional_fields(self):
        """Test ApprovalResponse with optional fields as None"""
        response = ApprovalResponse(
            approval_id="approval-123",
            status="pending",
            approved_by=None,
            approved_at=None
        )

        assert response.approved_by is None
        assert response.approved_at is None
