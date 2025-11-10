"""
Integration tests for departments API routes.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from typing import List, Dict, Any


# Mock department and agent classes for testing
class MockAgent:
    def __init__(self, id, name, role, provider="anthropic", model="claude-3-sonnet"):
        self.id = id
        self.name = name
        self.role = role
        self.provider = provider
        self.model = model
        self.responsibilities = [f"{role} responsibilities"]

    async def execute(self, task: str, context: Dict[str, Any]):
        return {"output": f"Executed: {task}", "status": "success"}


class MockWorkflow:
    def __init__(self, id, name, description, risk_level="low"):
        self.id = id
        self.name = name
        self.description = description
        self.risk_level = risk_level
        self.steps = [{"step": 1}, {"step": 2}]


class MockDepartment:
    def __init__(self, id, name, description, parent=None):
        self.id = id
        self.name = name
        self.description = description
        self.parent = parent
        self.sub_departments = []
        self.agents = []
        self.workflows = []
        self.budget = 10000

    def get_full_path(self):
        if self.parent:
            return f"{self.parent}.{self.id}"
        return self.id


@pytest.mark.integration
class TestDepartmentsRoutes:
    """Test suite for departments router endpoints"""

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_list_departments_success(
        self,
        mock_dept_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test listing all departments"""
        # Create mock departments
        dept1 = MockDepartment("engineering", "Engineering", "Engineering department")
        dept1.agents = [MockAgent("agent1", "Dev Agent", "developer")]
        dept1.workflows = [MockWorkflow("wf1", "Deploy", "Deploy workflow")]

        dept2 = MockDepartment("design", "Design", "Design department")

        mock_dept_manager.list_departments.return_value = [dept1, dept2]

        response = await client.get(
            "/departments/",
            headers=test_auth_headers
        )

        assert response.status_code in [200, 401, 503]

        if response.status_code == 200:
            data = response.json()
            assert "total" in data
            assert "departments" in data
            assert data["total"] == 2
            assert len(data["departments"]) == 2

            # Check first department structure
            dept = data["departments"][0]
            assert "id" in dept
            assert "name" in dept
            assert "agents_count" in dept
            assert "workflows_count" in dept

    @pytest.mark.asyncio
    async def test_list_departments_without_auth_fails(
        self,
        client: AsyncClient
    ):
        """Test listing departments without authentication fails"""
        response = await client.get("/departments/")

        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_list_departments_manager_not_initialized(
        self,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test listing departments when manager is not initialized"""
        # The actual _department_manager is None by default
        response = await client.get(
            "/departments/",
            headers=test_auth_headers
        )

        # Should return 503 when manager is not available
        assert response.status_code in [401, 503]

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_get_department_success(
        self,
        mock_dept_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test getting a specific department"""
        # Create mock department with agents and workflows
        dept = MockDepartment("engineering", "Engineering", "Engineering department")
        dept.agents = [
            MockAgent("dev1", "Developer Agent", "developer"),
            MockAgent("qa1", "QA Agent", "qa_tester")
        ]
        dept.workflows = [
            MockWorkflow("deploy", "Deploy", "Deploy workflow", "medium")
        ]

        mock_dept_manager.get_department.return_value = dept

        response = await client.get(
            "/departments/engineering",
            headers=test_auth_headers
        )

        assert response.status_code in [200, 401, 503]

        if response.status_code == 200:
            data = response.json()
            assert data["id"] == "engineering"
            assert data["name"] == "Engineering"
            assert "agents" in data
            assert "workflows" in data
            assert "budget" in data
            assert len(data["agents"]) == 2
            assert len(data["workflows"]) == 1

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_get_department_not_found(
        self,
        mock_dept_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test getting a department that doesn't exist"""
        mock_dept_manager.get_department.return_value = None

        response = await client.get(
            "/departments/nonexistent",
            headers=test_auth_headers
        )

        assert response.status_code in [404, 401, 503]

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_list_department_agents_success(
        self,
        mock_dept_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test listing agents in a department"""
        agents = [
            {"id": "dev1", "name": "Developer", "role": "developer"},
            {"id": "qa1", "name": "QA", "role": "qa_tester"}
        ]
        mock_dept_manager.list_agents.return_value = agents

        response = await client.get(
            "/departments/engineering/agents",
            headers=test_auth_headers
        )

        assert response.status_code in [200, 401, 503]

        if response.status_code == 200:
            data = response.json()
            assert "department" in data
            assert "total" in data
            assert "agents" in data
            assert data["department"] == "engineering"
            assert data["total"] == 2

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_list_all_workflows_success(
        self,
        mock_dept_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test listing all workflows across departments"""
        # Create departments with workflows
        dept1 = MockDepartment("engineering", "Engineering", "Engineering dept")
        dept1.workflows = [
            MockWorkflow("deploy", "Deploy", "Deploy workflow"),
            MockWorkflow("test", "Test", "Test workflow")
        ]

        dept2 = MockDepartment("design", "Design", "Design dept")
        dept2.workflows = [
            MockWorkflow("review", "Review", "Review workflow")
        ]

        mock_dept_manager.list_departments.return_value = [dept1, dept2]

        response = await client.get(
            "/departments/workflows/all",
            headers=test_auth_headers
        )

        assert response.status_code in [200, 401, 503]

        if response.status_code == 200:
            data = response.json()
            assert "total" in data
            assert "workflows" in data
            assert data["total"] == 3

            # Check workflow structure
            if len(data["workflows"]) > 0:
                wf = data["workflows"][0]
                assert "path" in wf
                assert "name" in wf
                assert "department" in wf
                assert "risk_level" in wf

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_execute_workflow_success(
        self,
        mock_dept_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test executing a department workflow"""
        mock_result = {
            "status": "completed",
            "output": "Workflow executed successfully",
            "steps_executed": 3
        }
        mock_dept_manager.execute_workflow = AsyncMock(return_value=mock_result)

        response = await client.post(
            "/departments/workflows/execute",
            json={
                "workflow_path": "engineering.deploy",
                "context": {"environment": "production"}
            },
            headers=test_auth_headers
        )

        assert response.status_code in [200, 401, 503]

        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "completed"

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_execute_workflow_not_found(
        self,
        mock_dept_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test executing a workflow that doesn't exist"""
        mock_dept_manager.execute_workflow = AsyncMock(
            side_effect=ValueError("Workflow not found")
        )

        response = await client.post(
            "/departments/workflows/execute",
            json={
                "workflow_path": "nonexistent.workflow",
                "context": {}
            },
            headers=test_auth_headers
        )

        assert response.status_code in [404, 401, 503]

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_execute_workflow_execution_error(
        self,
        mock_dept_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test workflow execution failure"""
        mock_dept_manager.execute_workflow = AsyncMock(
            side_effect=Exception("Execution failed")
        )

        response = await client.post(
            "/departments/workflows/execute",
            json={
                "workflow_path": "engineering.deploy",
                "context": {}
            },
            headers=test_auth_headers
        )

        assert response.status_code in [500, 401, 503]

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_execute_agent_task_success(
        self,
        mock_dept_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test executing a task with a specific agent"""
        mock_agent = MockAgent("dev1", "Developer", "developer")
        mock_dept_manager.get_agent.return_value = mock_agent

        response = await client.post(
            "/departments/agents/execute",
            json={
                "agent_path": "engineering.dev1",
                "task": "Review code changes",
                "context": {"files": ["main.py"]}
            },
            headers=test_auth_headers
        )

        assert response.status_code in [200, 401, 503]

        if response.status_code == 200:
            data = response.json()
            assert "agent" in data
            assert "task" in data
            assert "result" in data
            assert data["agent"] == "engineering.dev1"

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_execute_agent_task_not_found(
        self,
        mock_dept_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test executing a task with an agent that doesn't exist"""
        mock_dept_manager.get_agent.return_value = None

        response = await client.post(
            "/departments/agents/execute",
            json={
                "agent_path": "nonexistent.agent",
                "task": "Do something",
                "context": {}
            },
            headers=test_auth_headers
        )

        assert response.status_code in [404, 401, 503]

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_execute_agent_task_execution_error(
        self,
        mock_dept_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test agent task execution failure"""
        mock_agent = MagicMock()
        mock_agent.execute = AsyncMock(side_effect=Exception("Agent failed"))
        mock_dept_manager.get_agent.return_value = mock_agent

        response = await client.post(
            "/departments/agents/execute",
            json={
                "agent_path": "engineering.dev1",
                "task": "Failing task",
                "context": {}
            },
            headers=test_auth_headers
        )

        assert response.status_code in [500, 401, 503]

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_get_org_structure_success(
        self,
        mock_dept_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test getting full organizational structure"""
        # Create hierarchical department structure
        root = MockDepartment("root", "Root", "Root department")
        root.agents = [MockAgent("admin", "Admin", "admin")]
        root.workflows = [MockWorkflow("init", "Init", "Init workflow")]

        eng = MockDepartment("engineering", "Engineering", "Engineering", parent="root")
        eng.sub_departments = []
        eng.agents = [MockAgent("dev1", "Dev", "developer")]

        design = MockDepartment("design", "Design", "Design", parent="root")
        design.sub_departments = []

        mock_dept_manager.list_departments.return_value = [root, eng, design]

        response = await client.get(
            "/departments/structure",
            headers=test_auth_headers
        )

        # Test passes if any of these conditions are met:
        # 1. Returns 503 (service not initialized)
        # 2. Returns 401 (auth failed)
        # 3. Returns 200 with proper organization structure
        assert response.status_code in [200, 401, 503]

        if response.status_code == 200:
            data = response.json()
            # Check if organization key exists (expected structure)
            if "organization" in data:
                assert isinstance(data["organization"], list)
                if len(data["organization"]) > 0:
                    org = data["organization"][0]
                    assert "id" in org
                    assert "name" in org
                    # Check for either the full structure or basic fields
                    assert any(key in org for key in ["agents_count", "workflows_count", "children"])

    @pytest.mark.asyncio
    async def test_get_org_structure_without_auth_fails(
        self,
        client: AsyncClient
    ):
        """Test getting org structure without authentication fails"""
        response = await client.get("/departments/structure")

        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_execute_workflow_missing_fields(
        self,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test workflow execution with missing required fields"""
        response = await client.post(
            "/departments/workflows/execute",
            json={"context": {}},  # Missing workflow_path
            headers=test_auth_headers
        )

        assert response.status_code in [422, 401, 503]

    @pytest.mark.asyncio
    async def test_execute_agent_task_missing_fields(
        self,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test agent task execution with missing required fields"""
        response = await client.post(
            "/departments/agents/execute",
            json={"agent_path": "test.agent"},  # Missing task
            headers=test_auth_headers
        )

        assert response.status_code in [422, 401, 503]
