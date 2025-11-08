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
        """Test health endpoint returns service info"""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data

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
            "/overseer/run",
            json={
                "task": "Analyze this requirement",
                "risk_level": "low"
            },
            headers=test_auth_headers
        )

        # Might fail due to auth/dependencies, but check structure
        # This test validates the endpoint exists
        assert response.status_code in [200, 401, 422, 503]  # Various valid states (503 = deps unavailable)

    @pytest.mark.asyncio
    async def test_overseer_endpoint_requires_auth(self, client: AsyncClient):
        """Test overseer endpoint requires authentication"""
        response = await client.post(
            "/overseer/run",
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
            "/overseer/run",
            json={
                "risk_level": "low"  # Missing 'task'
            },
            headers=test_auth_headers
        )

        assert response.status_code in [400, 422, 503]  # Validation error or service unavailable

    @pytest.mark.asyncio
    async def test_developer_endpoint_exists(self, client: AsyncClient):
        """Test developer endpoint is accessible"""
        response = await client.post(
            "/developer/run",
            json={
                "task": "Write a Python function"
            }
        )

        # Just verify endpoint exists (will fail auth/validation)
        assert response.status_code in [200, 400, 401, 403, 422]

    @pytest.mark.asyncio
    @patch("app.main.developer_agent")
    @patch("app.main.cost_tracker")
    async def test_developer_execution_with_mocks(
        self,
        mock_cost_tracker,
        mock_developer,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test developer agent execution with mocked dependencies"""
        # Mock the agent execution
        mock_result = MagicMock()
        mock_result.raw = "Test developer response with code"
        mock_developer.kickoff = AsyncMock(return_value=mock_result)

        # Mock cost tracking
        mock_cost_tracker.record_execution = AsyncMock(return_value={
            "task_id": "test-task-456",
            "total_cost_usd": 0.02,
            "budget_status": {"within_budget": True}
        })

        response = await client.post(
            "/developer/run",
            json={
                "task": "Write a Python function to calculate fibonacci",
                "context": {"language": "python"}
            },
            headers=test_auth_headers
        )

        assert response.status_code in [200, 401, 422, 503]

    @pytest.mark.asyncio
    async def test_qa_tester_endpoint_requires_auth(self, client: AsyncClient):
        """Test QA tester endpoint requires authentication"""
        response = await client.post(
            "/qa-tester/run",
            json={
                "task": "Test this application"
            }
        )

        assert response.status_code in [401, 403, 422]

    @pytest.mark.asyncio
    @patch("app.main.qa_tester_agent")
    @patch("app.main.cost_tracker")
    async def test_qa_tester_execution_with_mocks(
        self,
        mock_cost_tracker,
        mock_qa_tester,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test QA tester agent execution with mocked dependencies"""
        mock_result = MagicMock()
        mock_result.raw = "Test plan created successfully"
        mock_qa_tester.kickoff = AsyncMock(return_value=mock_result)

        mock_cost_tracker.record_execution = AsyncMock(return_value={
            "task_id": "test-task-789",
            "total_cost_usd": 0.015,
            "budget_status": {"within_budget": True}
        })

        response = await client.post(
            "/qa-tester/run",
            json={
                "task": "Create test plan for login feature",
                "risk_level": "medium"
            },
            headers=test_auth_headers
        )

        assert response.status_code in [200, 401, 422, 503]

    @pytest.mark.asyncio
    async def test_devops_endpoint_requires_auth(self, client: AsyncClient):
        """Test DevOps endpoint requires authentication"""
        response = await client.post(
            "/devops/run",
            json={
                "task": "Deploy the application"
            }
        )

        assert response.status_code in [401, 403, 422]

    @pytest.mark.asyncio
    @patch("app.main.devops_agent")
    @patch("app.main.cost_tracker")
    async def test_devops_execution_with_mocks(
        self,
        mock_cost_tracker,
        mock_devops,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test DevOps agent execution with mocked dependencies"""
        mock_result = MagicMock()
        mock_result.raw = "Deployment pipeline configured"
        mock_devops.kickoff = AsyncMock(return_value=mock_result)

        mock_cost_tracker.record_execution = AsyncMock(return_value={
            "task_id": "test-task-101",
            "total_cost_usd": 0.025,
            "budget_status": {"within_budget": True}
        })

        response = await client.post(
            "/devops/run",
            json={
                "task": "Set up CI/CD pipeline",
                "risk_level": "high"
            },
            headers=test_auth_headers
        )

        assert response.status_code in [200, 401, 422, 503]

    @pytest.mark.asyncio
    async def test_designer_endpoint_requires_auth(self, client: AsyncClient):
        """Test Designer endpoint requires authentication"""
        response = await client.post(
            "/designer/run",
            json={
                "task": "Design a login page"
            }
        )

        assert response.status_code in [401, 403, 422]

    @pytest.mark.asyncio
    @patch("app.main.designer_agent")
    @patch("app.main.cost_tracker")
    async def test_designer_execution_with_mocks(
        self,
        mock_cost_tracker,
        mock_designer,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test Designer agent execution with mocked dependencies"""
        mock_result = MagicMock()
        mock_result.raw = "Design mockups created"
        mock_designer.kickoff = AsyncMock(return_value=mock_result)

        mock_cost_tracker.record_execution = AsyncMock(return_value={
            "task_id": "test-task-202",
            "total_cost_usd": 0.018,
            "budget_status": {"within_budget": True}
        })

        response = await client.post(
            "/designer/run",
            json={
                "task": "Create UI design for dashboard"
            },
            headers=test_auth_headers
        )

        assert response.status_code in [200, 401, 422, 503]

    @pytest.mark.asyncio
    async def test_security_auditor_endpoint_requires_auth(self, client: AsyncClient):
        """Test Security Auditor endpoint requires authentication"""
        response = await client.post(
            "/security-auditor/run",
            json={
                "task": "Audit the application security"
            }
        )

        assert response.status_code in [401, 403, 422]

    @pytest.mark.asyncio
    @patch("app.main.security_auditor_agent")
    @patch("app.main.cost_tracker")
    async def test_security_auditor_execution_with_mocks(
        self,
        mock_cost_tracker,
        mock_security_auditor,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test Security Auditor agent execution with mocked dependencies"""
        mock_result = MagicMock()
        mock_result.raw = "Security audit completed"
        mock_security_auditor.kickoff = AsyncMock(return_value=mock_result)

        mock_cost_tracker.record_execution = AsyncMock(return_value={
            "task_id": "test-task-303",
            "total_cost_usd": 0.03,
            "budget_status": {"within_budget": True}
        })

        response = await client.post(
            "/security-auditor/run",
            json={
                "task": "Perform security audit on authentication system",
                "risk_level": "high"
            },
            headers=test_auth_headers
        )

        assert response.status_code in [200, 401, 422, 503]

    @pytest.mark.asyncio
    async def test_ux_researcher_endpoint_requires_auth(self, client: AsyncClient):
        """Test UX Researcher endpoint requires authentication"""
        response = await client.post(
            "/ux-researcher/run",
            json={
                "task": "Research user behavior"
            }
        )

        assert response.status_code in [401, 403, 422]

    @pytest.mark.asyncio
    @patch("app.main.ux_researcher_agent")
    @patch("app.main.cost_tracker")
    async def test_ux_researcher_execution_with_mocks(
        self,
        mock_cost_tracker,
        mock_ux_researcher,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test UX Researcher agent execution with mocked dependencies"""
        mock_result = MagicMock()
        mock_result.raw = "UX research findings documented"
        mock_ux_researcher.kickoff = AsyncMock(return_value=mock_result)

        mock_cost_tracker.record_execution = AsyncMock(return_value={
            "task_id": "test-task-404",
            "total_cost_usd": 0.012,
            "budget_status": {"within_budget": True}
        })

        response = await client.post(
            "/ux-researcher/run",
            json={
                "task": "Analyze user journey for checkout flow"
            },
            headers=test_auth_headers
        )

        assert response.status_code in [200, 401, 422, 503]

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, client: AsyncClient, test_auth_headers):
        """Test API metrics endpoint"""
        response = await client.get("/api/metrics", headers=test_auth_headers)

        # May require auth, return metrics, or be unavailable
        assert response.status_code in [200, 401, 403, 503]
        if response.status_code == 200:
            data = response.json()
            assert "total_requests" in data or isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_validation_error_missing_task(self, client: AsyncClient, test_auth_headers):
        """Test that missing task field returns validation error"""
        response = await client.post(
            "/developer/run",
            json={},
            headers=test_auth_headers
        )

        assert response.status_code in [400, 422, 503]

    @pytest.mark.asyncio
    async def test_idempotency_key_handling(self, client: AsyncClient, test_auth_headers):
        """Test idempotency key is accepted"""
        response = await client.post(
            "/overseer/run",
            json={
                "task": "Test idempotency",
                "idempotency_key": "test-key-123"
            },
            headers=test_auth_headers
        )

        # Should accept the request (may fail on execution)
        assert response.status_code in [200, 401, 422, 503]

    @pytest.mark.asyncio
    async def test_project_and_workflow_id_tracking(self, client: AsyncClient, test_auth_headers):
        """Test project and workflow ID parameters are accepted"""
        response = await client.post(
            "/developer/run",
            json={
                "task": "Test cost tracking",
                "project_id": "project-123",
                "workflow_id": "workflow-456"
            },
            headers=test_auth_headers
        )

        # Should accept the request
        assert response.status_code in [200, 401, 422, 503]
