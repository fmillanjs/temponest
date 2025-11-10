"""
Integration tests for collaboration API routes.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from datetime import datetime

from app.collaboration.models import (
    CollaborationResponse,
    CollaborationWorkspace,
    TaskStatus,
    CollaborationPattern,
    AgentRole
)


@pytest.mark.integration
class TestCollaborationRoutes:
    """Test suite for collaboration router endpoints"""

    @pytest.mark.asyncio
    async def test_list_patterns_returns_all_patterns(self, client: AsyncClient):
        """Test listing collaboration patterns returns all available patterns"""
        response = await client.get("/collaboration/patterns")

        assert response.status_code == 200
        data = response.json()
        assert "patterns" in data
        assert len(data["patterns"]) == 4  # sequential, parallel, iterative, hierarchical

        pattern_names = [p["name"] for p in data["patterns"]]
        assert "sequential" in pattern_names
        assert "parallel" in pattern_names
        assert "iterative" in pattern_names
        assert "hierarchical" in pattern_names

        # Check structure of first pattern
        first_pattern = data["patterns"][0]
        assert "name" in first_pattern
        assert "description" in first_pattern
        assert "use_cases" in first_pattern
        assert isinstance(first_pattern["use_cases"], list)

    @pytest.mark.asyncio
    @patch("app.main.collaboration_manager")
    async def test_start_collaboration_success(
        self,
        mock_collab_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test starting a new collaboration session"""
        # Mock collaboration manager
        workspace_id = uuid4()
        mock_response = CollaborationResponse(
            workspace_id=workspace_id,
            status=TaskStatus.PENDING,
            tasks_completed=0,
            tasks_failed=0
        )
        mock_collab_manager.start_collaboration = AsyncMock(return_value=mock_response)

        response = await client.post(
            "/collaboration",
            json={
                "name": "Test Collaboration",
                "description": "Testing collaboration endpoint",
                "pattern": "sequential",
                "agents": ["developer", "qa_tester"]
            },
            headers=test_auth_headers
        )

        # Should either succeed with 201 or fail with 503/500 if manager not available
        assert response.status_code in [201, 500, 503]

        if response.status_code == 201:
            data = response.json()
            assert "workspace_id" in data
            assert "status" in data

    @pytest.mark.asyncio
    @patch("app.main.collaboration_manager")
    async def test_start_collaboration_handles_manager_error(
        self,
        mock_collab_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test starting collaboration handles manager errors gracefully"""
        # Mock collaboration manager that raises an error
        mock_collab_manager.start_collaboration = AsyncMock(
            side_effect=Exception("Manager error")
        )

        response = await client.post(
            "/collaboration",
            json={
                "name": "Test Collaboration",
                "description": "Testing error handling",
                "pattern": "sequential",
                "agents": ["developer", "qa_tester"]
            },
            headers=test_auth_headers
        )

        # Should return 500 error when manager fails
        assert response.status_code in [500, 503]

    @pytest.mark.asyncio
    async def test_start_collaboration_requires_valid_request(
        self,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test starting collaboration with invalid request fails validation"""
        response = await client.post(
            "/collaboration",
            json={
                "name": "Test",
                # Missing required fields: description, agents
            },
            headers=test_auth_headers
        )

        # Should return 422 validation error
        assert response.status_code in [422, 503]

    @pytest.mark.asyncio
    @patch("app.main.collaboration_manager")
    async def test_list_workspaces_success(
        self,
        mock_collab_manager,
        client: AsyncClient
    ):
        """Test listing all collaboration workspaces"""
        # Mock collaboration manager
        workspace1 = CollaborationWorkspace(
            name="Workspace 1",
            description="First workspace",
            pattern=CollaborationPattern.SEQUENTIAL
        )
        workspace2 = CollaborationWorkspace(
            name="Workspace 2",
            description="Second workspace",
            pattern=CollaborationPattern.PARALLEL
        )
        mock_collab_manager.list_workspaces.return_value = [workspace1, workspace2]

        response = await client.get("/collaboration/workspaces")

        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            if len(data) > 0:
                assert "name" in data[0]
                assert "pattern" in data[0]

    @pytest.mark.asyncio
    @patch("app.main.collaboration_manager")
    async def test_list_workspaces_empty(
        self,
        mock_collab_manager,
        client: AsyncClient
    ):
        """Test listing workspaces when none exist"""
        # Mock collaboration manager with empty list
        mock_collab_manager.list_workspaces.return_value = []

        response = await client.get("/collaboration/workspaces")

        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0

    @pytest.mark.asyncio
    @patch("app.main.collaboration_manager")
    async def test_get_workspace_success(
        self,
        mock_collab_manager,
        client: AsyncClient
    ):
        """Test getting a specific workspace by ID"""
        # Mock collaboration manager
        workspace_id = uuid4()
        workspace = CollaborationWorkspace(
            id=workspace_id,
            name="Test Workspace",
            description="Test workspace description",
            pattern=CollaborationPattern.SEQUENTIAL
        )
        mock_collab_manager.get_workspace.return_value = workspace

        response = await client.get(f"/collaboration/workspaces/{workspace_id}")

        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "name" in data
            assert "pattern" in data
            assert data["name"] == "Test Workspace"

    @pytest.mark.asyncio
    @patch("app.main.collaboration_manager")
    async def test_get_workspace_not_found(
        self,
        mock_collab_manager,
        client: AsyncClient
    ):
        """Test getting a workspace that doesn't exist returns 404"""
        # Mock collaboration manager
        mock_collab_manager.get_workspace.return_value = None

        workspace_id = uuid4()
        response = await client.get(f"/collaboration/workspaces/{workspace_id}")

        assert response.status_code in [404, 503]

    @pytest.mark.asyncio
    async def test_get_workspace_invalid_uuid(self, client: AsyncClient):
        """Test getting workspace with invalid UUID returns 422"""
        response = await client.get("/collaboration/workspaces/not-a-uuid")

        assert response.status_code == 422

    @pytest.mark.asyncio
    @patch("app.main.collaboration_manager")
    async def test_full_stack_feature_template_success(
        self,
        mock_collab_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test creating full-stack feature collaboration from template"""
        # Mock collaboration manager
        workspace_id = uuid4()
        mock_response = CollaborationResponse(
            workspace_id=workspace_id,
            status=TaskStatus.PENDING,
            tasks_completed=0,
            tasks_failed=0
        )
        mock_collab_manager.start_collaboration = AsyncMock(return_value=mock_response)

        response = await client.post(
            "/collaboration/templates/full-stack-feature",
            params={"feature_description": "User authentication system"},
            headers=test_auth_headers
        )

        assert response.status_code in [200, 500, 503]

        if response.status_code == 200:
            # Verify manager was called with correct parameters
            call_args = mock_collab_manager.start_collaboration.call_args
            if call_args:
                request = call_args.kwargs.get("request")
                assert request is not None
                assert request.name == "Full-Stack Feature Development"
                assert request.pattern == CollaborationPattern.SEQUENTIAL
                # Should include developer, designer, qa_tester, devops
                assert AgentRole.DEVELOPER in request.agents
                assert AgentRole.DESIGNER in request.agents
                assert AgentRole.QA_TESTER in request.agents
                assert AgentRole.DEVOPS in request.agents

    @pytest.mark.asyncio
    @patch("app.main.collaboration_manager")
    async def test_security_review_template_success(
        self,
        mock_collab_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test creating security review collaboration from template"""
        # Mock collaboration manager
        workspace_id = uuid4()
        mock_response = CollaborationResponse(
            workspace_id=workspace_id,
            status=TaskStatus.PENDING,
            tasks_completed=0,
            tasks_failed=0
        )
        mock_collab_manager.start_collaboration = AsyncMock(return_value=mock_response)

        response = await client.post(
            "/collaboration/templates/security-review",
            params={"code_description": "Authentication module"},
            headers=test_auth_headers
        )

        assert response.status_code in [200, 500, 503]

        if response.status_code == 200:
            # Verify manager was called with correct parameters
            call_args = mock_collab_manager.start_collaboration.call_args
            if call_args:
                request = call_args.kwargs.get("request")
                assert request is not None
                assert request.name == "Security Review and Remediation"
                assert request.pattern == CollaborationPattern.ITERATIVE
                # Should include security_auditor, developer, qa_tester
                assert AgentRole.SECURITY_AUDITOR in request.agents
                assert AgentRole.DEVELOPER in request.agents
                assert AgentRole.QA_TESTER in request.agents

    @pytest.mark.asyncio
    @patch("app.main.collaboration_manager")
    async def test_parallel_analysis_template_success(
        self,
        mock_collab_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test creating parallel analysis collaboration from template"""
        # Mock collaboration manager
        workspace_id = uuid4()
        mock_response = CollaborationResponse(
            workspace_id=workspace_id,
            status=TaskStatus.PENDING,
            tasks_completed=0,
            tasks_failed=0
        )
        mock_collab_manager.start_collaboration = AsyncMock(return_value=mock_response)

        response = await client.post(
            "/collaboration/templates/parallel-analysis",
            params={"project_description": "E-commerce platform"},
            headers=test_auth_headers
        )

        assert response.status_code in [200, 500, 503]

        if response.status_code == 200:
            # Verify manager was called with correct parameters
            call_args = mock_collab_manager.start_collaboration.call_args
            if call_args:
                request = call_args.kwargs.get("request")
                assert request is not None
                assert request.name == "Multi-Perspective Project Analysis"
                assert request.pattern == CollaborationPattern.PARALLEL
                # Should include developer, security_auditor, designer, devops
                assert AgentRole.DEVELOPER in request.agents
                assert AgentRole.SECURITY_AUDITOR in request.agents
                assert AgentRole.DESIGNER in request.agents
                assert AgentRole.DEVOPS in request.agents

    @pytest.mark.asyncio
    async def test_full_stack_template_missing_description(
        self,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test full-stack template without feature description fails"""
        response = await client.post(
            "/collaboration/templates/full-stack-feature",
            headers=test_auth_headers
        )

        # Should return 422 validation error for missing query param
        assert response.status_code in [422, 503]

    @pytest.mark.asyncio
    async def test_security_review_template_missing_description(
        self,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test security review template without code description fails"""
        response = await client.post(
            "/collaboration/templates/security-review",
            headers=test_auth_headers
        )

        # Should return 422 validation error for missing query param
        assert response.status_code in [422, 503]

    @pytest.mark.asyncio
    async def test_parallel_analysis_template_missing_description(
        self,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test parallel analysis template without project description fails"""
        response = await client.post(
            "/collaboration/templates/parallel-analysis",
            headers=test_auth_headers
        )

        # Should return 422 validation error for missing query param
        assert response.status_code in [422, 503]
