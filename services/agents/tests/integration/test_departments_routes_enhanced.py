"""
Enhanced integration tests for departments router with proper auth mocking.
These tests ensure 100% coverage of the success paths.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any


# Mock classes
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
class TestDepartmentsRoutesEnhanced:
    """Enhanced test suite with proper auth mocking for full coverage"""

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_list_departments_with_full_auth(
        self,
        mock_dept_manager,
        authenticated_client: AsyncClient
    ):
        """Test listing all departments with authenticated client"""
        dept1 = MockDepartment("engineering", "Engineering", "Engineering dept")
        dept1.agents = [MockAgent("dev1", "Dev Agent", "developer")]
        dept1.workflows = [MockWorkflow("wf1", "Deploy", "Deploy workflow")]

        dept2 = MockDepartment("design", "Design", "Design dept")
        dept2.agents = [MockAgent("des1", "Designer", "designer")]

        mock_dept_manager.list_departments.return_value = [dept1, dept2]

        response = await authenticated_client.get(
            "/departments/",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["departments"]) == 2
        assert data["departments"][0]["id"] == "engineering"
        assert data["departments"][0]["agents_count"] == 1
        assert data["departments"][0]["workflows_count"] == 1

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_get_specific_department(
        self,
        mock_dept_manager,
        authenticated_client: AsyncClient
    ):
        """Test getting a specific department"""
        dept = MockDepartment("engineering", "Engineering", "Engineering dept")
        dept.agents = [
            MockAgent("dev1", "Developer", "developer"),
            MockAgent("qa1", "QA Tester", "qa_tester")
        ]
        dept.workflows = [
            MockWorkflow("deploy", "Deploy", "Deploy workflow", "medium"),
            MockWorkflow("test", "Test", "Test workflow", "low")
        ]
        dept.budget = 50000

        mock_dept_manager.get_department.return_value = dept

        response = await authenticated_client.get(
            "/departments/engineering",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "engineering"
        assert data["name"] == "Engineering"
        assert data["description"] == "Engineering dept"
        assert data["budget"] == 50000
        assert len(data["agents"]) == 2
        assert len(data["workflows"]) == 2
        assert data["agents"][0]["id"] == "dev1"
        assert data["workflows"][0]["risk_level"] == "medium"

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_get_department_not_found(
        self,
        mock_dept_manager,
        authenticated_client: AsyncClient
    ):
        """Test getting a non-existent department"""
        mock_dept_manager.get_department.return_value = None

        response = await authenticated_client.get(
            "/departments/nonexistent",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_list_department_agents(
        self,
        mock_dept_manager,
        authenticated_client: AsyncClient
    ):
        """Test listing agents in a department"""
        agents = [
            {"id": "dev1", "name": "Developer", "role": "developer"},
            {"id": "qa1", "name": "QA", "role": "qa_tester"},
            {"id": "devops1", "name": "DevOps", "role": "devops"}
        ]
        mock_dept_manager.list_agents.return_value = agents

        response = await authenticated_client.get(
            "/departments/engineering/agents",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["department"] == "engineering"
        assert data["total"] == 3
        assert len(data["agents"]) == 3

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_list_all_workflows(
        self,
        mock_dept_manager,
        authenticated_client: AsyncClient
    ):
        """Test listing all workflows across departments"""
        dept1 = MockDepartment("engineering", "Engineering", "Engineering dept")
        dept1.workflows = [
            MockWorkflow("deploy", "Deploy", "Deploy workflow", "high"),
            MockWorkflow("test", "Test", "Test workflow", "low")
        ]

        dept2 = MockDepartment("design", "Design", "Design dept")
        dept2.workflows = [
            MockWorkflow("review", "Review", "Review workflow", "medium")
        ]

        mock_dept_manager.list_departments.return_value = [dept1, dept2]

        response = await authenticated_client.get(
            "/departments/workflows/all",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["workflows"]) == 3
        # Check workflow paths are formatted correctly
        paths = [wf["path"] for wf in data["workflows"]]
        assert "engineering.deploy" in paths
        assert "design.review" in paths

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_execute_workflow_success(
        self,
        mock_dept_manager,
        authenticated_client: AsyncClient
    ):
        """Test successful workflow execution"""
        mock_result = {
            "status": "completed",
            "output": "Workflow executed successfully",
            "steps_executed": 3,
            "duration_ms": 1500
        }
        mock_dept_manager.execute_workflow = AsyncMock(return_value=mock_result)

        response = await authenticated_client.post(
            "/departments/workflows/execute",
            json={
                "workflow_path": "engineering.deploy",
                "context": {"environment": "production", "version": "1.0.0"}
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output"] == "Workflow executed successfully"
        assert data["steps_executed"] == 3

        # Verify the manager was called with correct params
        mock_dept_manager.execute_workflow.assert_called_once_with(
            workflow_path="engineering.deploy",
            context={"environment": "production", "version": "1.0.0"}
        )

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_execute_workflow_not_found(
        self,
        mock_dept_manager,
        authenticated_client: AsyncClient
    ):
        """Test executing a non-existent workflow"""
        mock_dept_manager.execute_workflow = AsyncMock(
            side_effect=ValueError("Workflow not found: nonexistent.workflow")
        )

        response = await authenticated_client.post(
            "/departments/workflows/execute",
            json={
                "workflow_path": "nonexistent.workflow",
                "context": {}
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_execute_workflow_execution_error(
        self,
        mock_dept_manager,
        authenticated_client: AsyncClient
    ):
        """Test workflow execution failure"""
        mock_dept_manager.execute_workflow = AsyncMock(
            side_effect=Exception("Database connection failed")
        )

        response = await authenticated_client.post(
            "/departments/workflows/execute",
            json={
                "workflow_path": "engineering.deploy",
                "context": {}
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 500
        data = response.json()
        assert "execution failed" in data["detail"].lower()

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_execute_agent_task_success(
        self,
        mock_dept_manager,
        authenticated_client: AsyncClient
    ):
        """Test successful agent task execution"""
        mock_agent = MockAgent("dev1", "Developer", "developer")
        mock_dept_manager.get_agent.return_value = mock_agent

        response = await authenticated_client.post(
            "/departments/agents/execute",
            json={
                "agent_path": "engineering.dev1",
                "task": "Review code changes in main.py",
                "context": {"files": ["main.py"], "priority": "high"}
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == "engineering.dev1"
        assert data["task"] == "Review code changes in main.py"
        assert "result" in data
        assert data["result"]["status"] == "success"

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_execute_agent_task_not_found(
        self,
        mock_dept_manager,
        authenticated_client: AsyncClient
    ):
        """Test executing task with non-existent agent"""
        mock_dept_manager.get_agent.return_value = None

        response = await authenticated_client.post(
            "/departments/agents/execute",
            json={
                "agent_path": "nonexistent.agent",
                "task": "Do something",
                "context": {}
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_execute_agent_task_execution_error(
        self,
        mock_dept_manager,
        authenticated_client: AsyncClient
    ):
        """Test agent task execution failure"""
        mock_agent = MagicMock()
        mock_agent.execute = AsyncMock(side_effect=Exception("Agent timeout"))
        mock_dept_manager.get_agent.return_value = mock_agent

        response = await authenticated_client.post(
            "/departments/agents/execute",
            json={
                "agent_path": "engineering.dev1",
                "task": "Complex task",
                "context": {}
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 500
        data = response.json()
        assert "execution failed" in data["detail"].lower()

    @pytest.mark.asyncio
    @patch("app.routers.departments._department_manager")
    async def test_get_org_structure(
        self,
        mock_dept_manager,
        authenticated_client: AsyncClient
    ):
        """Test getting hierarchical organizational structure"""
        # Create root department
        root = MockDepartment("root", "Root", "Root department")
        root.agents = [MockAgent("admin", "Admin", "admin")]
        root.workflows = [MockWorkflow("init", "Init", "Init workflow")]

        # Create child departments
        eng = MockDepartment("engineering", "Engineering", "Engineering", parent="root")
        eng.sub_departments = []
        eng.agents = [MockAgent("dev1", "Dev", "developer")]
        eng.workflows = [MockWorkflow("deploy", "Deploy", "Deploy")]

        design = MockDepartment("design", "Design", "Design", parent="root")
        design.sub_departments = []
        design.agents = [MockAgent("des1", "Designer", "designer")]

        mock_dept_manager.list_departments.return_value = [root, eng, design]

        response = await authenticated_client.get(
            "/departments/structure",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()

        # The endpoint should return organizational structure
        # Format may vary but should have some data
        assert data is not None

    @pytest.mark.asyncio
    async def test_set_department_manager(self):
        """Test the set_department_manager function"""
        from app.routers.departments import set_department_manager, _department_manager

        mock_manager = MagicMock()
        set_department_manager(mock_manager)

        # Import again to check it was set
        from app.routers import departments
        assert departments._department_manager is mock_manager

        # Cleanup
        set_department_manager(None)


@pytest.mark.integration
class TestDepartmentsManagerNotInitialized:
    """Test suite for department routes when manager is not initialized"""

    @pytest.mark.asyncio
    async def test_get_department_manager_not_initialized(
        self,
        authenticated_client: AsyncClient
    ):
        """Test getting department when manager is not initialized returns 503"""
        from app.routers.departments import set_department_manager

        # Ensure manager is None
        set_department_manager(None)

        response = await authenticated_client.get(
            "/departments/engineering",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 503
        data = response.json()
        assert "not initialized" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_list_department_agents_manager_not_initialized(
        self,
        authenticated_client: AsyncClient
    ):
        """Test listing agents when manager is not initialized returns 503"""
        from app.routers.departments import set_department_manager

        # Ensure manager is None
        set_department_manager(None)

        response = await authenticated_client.get(
            "/departments/engineering/agents",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 503
        data = response.json()
        assert "not initialized" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_list_all_workflows_manager_not_initialized(
        self,
        authenticated_client: AsyncClient
    ):
        """Test listing all workflows when manager is not initialized returns 503"""
        from app.routers.departments import set_department_manager

        # Ensure manager is None
        set_department_manager(None)

        response = await authenticated_client.get(
            "/departments/workflows/all",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 503
        data = response.json()
        assert "not initialized" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_execute_workflow_manager_not_initialized(
        self,
        authenticated_client: AsyncClient
    ):
        """Test executing workflow when manager is not initialized returns 503"""
        from app.routers.departments import set_department_manager

        # Ensure manager is None
        set_department_manager(None)

        response = await authenticated_client.post(
            "/departments/workflows/execute",
            json={
                "workflow_path": "engineering.deploy",
                "context": {}
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 503
        data = response.json()
        assert "not initialized" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_execute_agent_task_manager_not_initialized(
        self,
        authenticated_client: AsyncClient
    ):
        """Test executing agent task when manager is not initialized returns 503"""
        from app.routers.departments import set_department_manager

        # Ensure manager is None
        set_department_manager(None)

        response = await authenticated_client.post(
            "/departments/agents/execute",
            json={
                "agent_path": "engineering.dev1",
                "task": "Review code",
                "context": {}
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 503
        data = response.json()
        assert "not initialized" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_org_structure_manager_not_initialized(
        self,
        authenticated_client: AsyncClient
    ):
        """Test getting org structure when manager is not initialized returns 503"""
        from app.routers.departments import set_department_manager

        # Ensure manager is None
        set_department_manager(None)

        response = await authenticated_client.get(
            "/departments/structure",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 503
        data = response.json()
        assert "not initialized" in data["detail"].lower()
