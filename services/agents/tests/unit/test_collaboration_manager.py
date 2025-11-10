"""
Unit tests for Collaboration Manager.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from datetime import datetime

from app.collaboration.manager import CollaborationManager
from app.collaboration.models import (
    AgentRole,
    TaskStatus,
    CollaborationPattern,
    AgentTask,
    CollaborationWorkspace,
    CollaborationRequest,
    CollaborationResponse
)


@pytest.mark.unit
class TestCollaborationManagerInit:
    """Test suite for CollaborationManager initialization"""

    def test_init_with_empty_agents(self):
        """Test initializing manager with no agents"""
        manager = CollaborationManager(agents_dict={})
        assert manager.agents == {}
        assert manager.active_workspaces == {}

    def test_init_with_agents(self):
        """Test initializing manager with agents"""
        mock_agent = MagicMock()
        agents = {AgentRole.DEVELOPER: mock_agent}

        manager = CollaborationManager(agents_dict=agents)
        assert manager.agents == agents
        assert AgentRole.DEVELOPER in manager.agents
        assert manager.active_workspaces == {}


@pytest.mark.unit
class TestCollaborationManagerSequential:
    """Test suite for sequential collaboration pattern"""

    @pytest.mark.asyncio
    async def test_sequential_execution_with_workflow_steps(self):
        """Test sequential execution with predefined workflow steps"""
        mock_agent = MagicMock()
        agents = {AgentRole.DEVELOPER: mock_agent}
        manager = CollaborationManager(agents_dict=agents)

        # Mock _call_agent to return success
        manager._call_agent = AsyncMock(return_value={
            "status": "success",
            "summary": "Task completed",
            "refinement_needed": False
        })

        request = CollaborationRequest(
            name="Test Sequential",
            description="Test sequential workflow",
            pattern=CollaborationPattern.SEQUENTIAL,
            agents=[AgentRole.DEVELOPER],
            workflow_steps=[
                {"agent": "developer", "task": "Step 1", "context": {}},
                {"agent": "developer", "task": "Step 2", "context": {}}
            ],
            initial_context={}
        )

        tenant_id = uuid4()
        user_id = uuid4()

        response = await manager.start_collaboration(request, tenant_id, user_id)

        assert response.status == TaskStatus.COMPLETED
        assert response.tasks_completed == 2
        assert response.tasks_failed == 0
        assert len(manager._call_agent.mock_calls) == 2

    @pytest.mark.asyncio
    async def test_sequential_execution_without_workflow_steps(self):
        """Test sequential execution without predefined steps"""
        mock_agent1 = MagicMock()
        mock_agent2 = MagicMock()
        agents = {
            AgentRole.DEVELOPER: mock_agent1,
            AgentRole.QA_TESTER: mock_agent2
        }
        manager = CollaborationManager(agents_dict=agents)

        manager._call_agent = AsyncMock(return_value={
            "status": "success",
            "summary": "Task completed",
            "refinement_needed": False
        })

        request = CollaborationRequest(
            name="Test Sequential",
            description="Test task",
            pattern=CollaborationPattern.SEQUENTIAL,
            agents=[AgentRole.DEVELOPER, AgentRole.QA_TESTER],
            initial_context={}
        )

        response = await manager.start_collaboration(request, uuid4(), uuid4())

        assert response.status == TaskStatus.COMPLETED
        assert response.tasks_completed == 2
        assert len(manager._call_agent.mock_calls) == 2

    @pytest.mark.asyncio
    async def test_sequential_execution_stops_on_failure(self):
        """Test sequential execution stops when a task fails"""
        mock_agent = MagicMock()
        agents = {AgentRole.DEVELOPER: mock_agent}
        manager = CollaborationManager(agents_dict=agents)

        # First call succeeds, second call fails
        manager._call_agent = AsyncMock(side_effect=[
            {"status": "success", "summary": "First task OK"},
            Exception("Task failed")
        ])

        request = CollaborationRequest(
            name="Test Sequential Failure",
            description="Test task",
            pattern=CollaborationPattern.SEQUENTIAL,
            agents=[AgentRole.DEVELOPER, AgentRole.DEVELOPER],
            initial_context={}
        )

        response = await manager.start_collaboration(request, uuid4(), uuid4())

        # First task completes, second fails, so should stop
        assert response.tasks_completed == 1
        assert response.tasks_failed == 1
        assert response.status == TaskStatus.FAILED


@pytest.mark.unit
class TestCollaborationManagerParallel:
    """Test suite for parallel collaboration pattern"""

    @pytest.mark.asyncio
    async def test_parallel_execution_all_success(self):
        """Test parallel execution when all tasks succeed"""
        mock_agent1 = MagicMock()
        mock_agent2 = MagicMock()
        agents = {
            AgentRole.DEVELOPER: mock_agent1,
            AgentRole.DESIGNER: mock_agent2
        }
        manager = CollaborationManager(agents_dict=agents)

        manager._call_agent = AsyncMock(return_value={
            "status": "success",
            "summary": "Task completed"
        })

        request = CollaborationRequest(
            name="Test Parallel",
            description="Test parallel execution",
            pattern=CollaborationPattern.PARALLEL,
            agents=[AgentRole.DEVELOPER, AgentRole.DESIGNER],
            initial_context={}
        )

        response = await manager.start_collaboration(request, uuid4(), uuid4())

        assert response.status == TaskStatus.COMPLETED
        assert response.tasks_completed == 2
        assert response.tasks_failed == 0

    @pytest.mark.asyncio
    async def test_parallel_execution_with_failures(self):
        """Test parallel execution with some task failures"""
        mock_agent1 = MagicMock()
        mock_agent2 = MagicMock()
        agents = {
            AgentRole.DEVELOPER: mock_agent1,
            AgentRole.DESIGNER: mock_agent2
        }
        manager = CollaborationManager(agents_dict=agents)

        # One succeeds, one fails
        call_count = [0]
        async def mock_call(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return {"status": "success", "summary": "OK"}
            else:
                raise Exception("Task failed")

        manager._call_agent = mock_call

        request = CollaborationRequest(
            name="Test Parallel Failures",
            description="Test task",
            pattern=CollaborationPattern.PARALLEL,
            agents=[AgentRole.DEVELOPER, AgentRole.DESIGNER],
            initial_context={}
        )

        response = await manager.start_collaboration(request, uuid4(), uuid4())

        # One succeeds, one fails
        assert response.tasks_completed == 1
        assert response.tasks_failed == 1
        assert response.status == TaskStatus.FAILED


@pytest.mark.unit
class TestCollaborationManagerIterative:
    """Test suite for iterative collaboration pattern"""

    @pytest.mark.asyncio
    async def test_iterative_execution_completes_early(self):
        """Test iterative execution stops early when refinement not needed"""
        mock_agent = MagicMock()
        agents = {AgentRole.DEVELOPER: mock_agent}
        manager = CollaborationManager(agents_dict=agents)

        manager._call_agent = AsyncMock(return_value={
            "status": "success",
            "summary": "Task completed",
            "refinement_needed": False  # No refinement needed
        })

        request = CollaborationRequest(
            name="Test Iterative",
            description="Test iterative workflow",
            pattern=CollaborationPattern.ITERATIVE,
            agents=[AgentRole.DEVELOPER],
            initial_context={}
        )

        response = await manager.start_collaboration(request, uuid4(), uuid4())

        # Should complete after first iteration
        assert response.status == TaskStatus.COMPLETED
        assert response.tasks_completed == 1
        assert len(manager._call_agent.mock_calls) == 1

    @pytest.mark.asyncio
    async def test_iterative_execution_max_iterations(self):
        """Test iterative execution reaches max iterations"""
        mock_agent = MagicMock()
        agents = {AgentRole.DEVELOPER: mock_agent}
        manager = CollaborationManager(agents_dict=agents)

        manager._call_agent = AsyncMock(return_value={
            "status": "success",
            "summary": "Task completed",
            "refinement_needed": True  # Always needs refinement
        })

        request = CollaborationRequest(
            name="Test Iterative Max",
            description="Test task",
            pattern=CollaborationPattern.ITERATIVE,
            agents=[AgentRole.DEVELOPER],
            initial_context={}
        )

        response = await manager.start_collaboration(request, uuid4(), uuid4())

        # Should complete all 3 iterations (max)
        assert response.tasks_completed == 3
        assert len(manager._call_agent.mock_calls) == 3

    @pytest.mark.asyncio
    async def test_iterative_execution_with_multiple_agents(self):
        """Test iterative execution with multiple agents"""
        mock_agent1 = MagicMock()
        mock_agent2 = MagicMock()
        agents = {
            AgentRole.DEVELOPER: mock_agent1,
            AgentRole.QA_TESTER: mock_agent2
        }
        manager = CollaborationManager(agents_dict=agents)

        call_count = [0]
        async def mock_call(*args, **kwargs):
            call_count[0] += 1
            # Stop after first iteration (2 agents = 2 calls)
            return {
                "status": "success",
                "summary": "OK",
                "refinement_needed": False if call_count[0] == 2 else True
            }

        manager._call_agent = mock_call

        request = CollaborationRequest(
            name="Test Iterative Multi",
            description="Test task",
            pattern=CollaborationPattern.ITERATIVE,
            agents=[AgentRole.DEVELOPER, AgentRole.QA_TESTER],
            initial_context={}
        )

        response = await manager.start_collaboration(request, uuid4(), uuid4())

        # Should complete first iteration with 2 agents
        assert response.tasks_completed == 2
        assert call_count[0] == 2


@pytest.mark.unit
class TestCollaborationManagerHierarchical:
    """Test suite for hierarchical collaboration pattern"""

    @pytest.mark.asyncio
    async def test_hierarchical_execution_with_plan(self):
        """Test hierarchical execution with Overseer creating a plan"""
        mock_overseer = MagicMock()
        mock_developer = MagicMock()
        agents = {
            AgentRole.OVERSEER: mock_overseer,
            AgentRole.DEVELOPER: mock_developer
        }
        manager = CollaborationManager(agents_dict=agents)

        call_count = [0]
        async def mock_call(agent, task_desc, context):
            call_count[0] += 1
            if call_count[0] == 1:  # Overseer creates plan
                return {
                    "status": "success",
                    "execution_plan": [
                        {"agent": "developer", "task": "Implement feature", "context": {}},
                        {"agent": "developer", "task": "Write tests", "context": {}}
                    ]
                }
            else:  # Developers execute tasks
                return {"status": "success", "summary": "Task done"}

        manager._call_agent = mock_call

        request = CollaborationRequest(
            name="Test Hierarchical",
            description="Build feature",
            pattern=CollaborationPattern.HIERARCHICAL,
            agents=[AgentRole.OVERSEER, AgentRole.DEVELOPER],
            initial_context={}
        )

        response = await manager.start_collaboration(request, uuid4(), uuid4())

        # Overseer + 2 developer tasks = 3 total
        assert response.tasks_completed == 3
        assert call_count[0] == 3

    @pytest.mark.asyncio
    async def test_hierarchical_execution_overseer_fails(self):
        """Test hierarchical execution when Overseer fails"""
        mock_overseer = MagicMock()
        agents = {AgentRole.OVERSEER: mock_overseer}
        manager = CollaborationManager(agents_dict=agents)

        manager._call_agent = AsyncMock(side_effect=Exception("Overseer failed"))

        request = CollaborationRequest(
            name="Test Hierarchical Failure",
            description="Build feature",
            pattern=CollaborationPattern.HIERARCHICAL,
            agents=[AgentRole.OVERSEER],
            initial_context={}
        )

        response = await manager.start_collaboration(request, uuid4(), uuid4())

        # Overseer fails, no further execution
        assert response.tasks_failed == 1
        assert response.status == TaskStatus.FAILED

    @pytest.mark.asyncio
    async def test_hierarchical_execution_stops_on_critical_failure(self):
        """Test hierarchical execution stops when critical task fails"""
        mock_overseer = MagicMock()
        mock_developer = MagicMock()
        agents = {
            AgentRole.OVERSEER: mock_overseer,
            AgentRole.DEVELOPER: mock_developer
        }
        manager = CollaborationManager(agents_dict=agents)

        call_count = [0]
        async def mock_call(agent, task_desc, context):
            call_count[0] += 1
            if call_count[0] == 1:  # Overseer creates plan with critical task
                return {
                    "status": "success",
                    "execution_plan": [
                        {"agent": "developer", "task": "Critical task", "context": {}, "critical": True},
                        {"agent": "developer", "task": "Optional task", "context": {}}
                    ]
                }
            elif call_count[0] == 2:  # First developer task fails
                raise Exception("Critical task failed")
            else:  # Should never reach here
                return {"status": "success", "summary": "Task done"}

        manager._call_agent = mock_call

        request = CollaborationRequest(
            name="Test Critical Failure",
            description="Build feature",
            pattern=CollaborationPattern.HIERARCHICAL,
            agents=[AgentRole.OVERSEER, AgentRole.DEVELOPER],
            initial_context={}
        )

        response = await manager.start_collaboration(request, uuid4(), uuid4())

        # Overseer completes, first task fails (critical), second never runs
        assert response.tasks_completed == 1
        assert response.tasks_failed == 1
        assert call_count[0] == 2  # Overseer + 1 failed task


@pytest.mark.unit
class TestCollaborationManagerExecuteTask:
    """Test suite for _execute_task method"""

    @pytest.mark.asyncio
    async def test_execute_task_success(self):
        """Test successful task execution"""
        mock_agent = MagicMock()
        agents = {AgentRole.DEVELOPER: mock_agent}
        manager = CollaborationManager(agents_dict=agents)

        workspace = CollaborationWorkspace(
            name="Test Workspace",
            description="Test",
            pattern=CollaborationPattern.SEQUENTIAL,
            shared_context={}
        )

        task = AgentTask(
            agent_role=AgentRole.DEVELOPER,
            task_description="Test task",
            context={}
        )

        manager._call_agent = AsyncMock(return_value={
            "status": "success",
            "summary": "Task completed"
        })

        result = await manager._execute_task(workspace, task)

        assert result.status == TaskStatus.COMPLETED
        assert result.result is not None
        assert result.error is None
        assert result.started_at is not None
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_execute_task_agent_not_available(self):
        """Test task execution when agent is not available"""
        manager = CollaborationManager(agents_dict={})

        workspace = CollaborationWorkspace(
            name="Test Workspace",
            description="Test",
            pattern=CollaborationPattern.SEQUENTIAL,
            shared_context={}
        )

        task = AgentTask(
            agent_role=AgentRole.DEVELOPER,
            task_description="Test task",
            context={}
        )

        result = await manager._execute_task(workspace, task)

        assert result.status == TaskStatus.FAILED
        assert result.error is not None
        assert "not available" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_task_agent_raises_exception(self):
        """Test task execution when agent raises exception"""
        mock_agent = MagicMock()
        agents = {AgentRole.DEVELOPER: mock_agent}
        manager = CollaborationManager(agents_dict=agents)

        workspace = CollaborationWorkspace(
            name="Test Workspace",
            description="Test",
            pattern=CollaborationPattern.SEQUENTIAL,
            shared_context={}
        )

        task = AgentTask(
            agent_role=AgentRole.DEVELOPER,
            task_description="Test task",
            context={}
        )

        manager._call_agent = AsyncMock(side_effect=Exception("Agent error"))

        result = await manager._execute_task(workspace, task)

        assert result.status == TaskStatus.FAILED
        assert result.error == "Agent error"
        assert len(workspace.messages) == 1
        assert "Failed" in workspace.messages[0]["message"]

    @pytest.mark.asyncio
    async def test_execute_task_updates_workspace_context(self):
        """Test task execution updates workspace shared context"""
        mock_agent = MagicMock()
        agents = {AgentRole.DEVELOPER: mock_agent}
        manager = CollaborationManager(agents_dict=agents)

        workspace = CollaborationWorkspace(
            name="Test Workspace",
            description="Test",
            pattern=CollaborationPattern.SEQUENTIAL,
            shared_context={"initial": "data"}
        )

        task = AgentTask(
            agent_role=AgentRole.DEVELOPER,
            task_description="Test task",
            context={}
        )

        manager._call_agent = AsyncMock(return_value={
            "status": "success",
            "summary": "Task completed",
            "data": "result"
        })

        await manager._execute_task(workspace, task)

        # Check that workspace context was updated
        assert f"task_{task.id}_result" in workspace.shared_context
        assert workspace.shared_context[f"task_{task.id}_result"]["data"] == "result"

    @pytest.mark.asyncio
    async def test_execute_task_includes_previous_task_context(self):
        """Test task execution includes context from previous tasks"""
        mock_agent = MagicMock()
        agents = {AgentRole.DEVELOPER: mock_agent}
        manager = CollaborationManager(agents_dict=agents)

        workspace = CollaborationWorkspace(
            name="Test Workspace",
            description="Test",
            pattern=CollaborationPattern.SEQUENTIAL,
            shared_context={}
        )

        # Add a completed task
        completed_task = AgentTask(
            agent_role=AgentRole.DESIGNER,
            task_description="Previous task",
            context={}
        )
        completed_task.status = TaskStatus.COMPLETED
        completed_task.result = {"design": "mockup"}
        workspace.tasks.append(completed_task)

        # Add a new task
        task = AgentTask(
            agent_role=AgentRole.DEVELOPER,
            task_description="Current task",
            context={}
        )

        captured_context = {}
        async def capture_context(agent, task_desc, context):
            captured_context.update(context)
            return {"status": "success"}

        manager._call_agent = capture_context

        await manager._execute_task(workspace, task)

        # Verify previous tasks were included in context
        assert "previous_tasks" in captured_context
        assert len(captured_context["previous_tasks"]) == 1
        assert captured_context["previous_tasks"][0]["agent"] == "designer"
        assert captured_context["previous_tasks"][0]["result"] == {"design": "mockup"}


@pytest.mark.unit
class TestCollaborationManagerCallAgent:
    """Test suite for _call_agent method"""

    @pytest.mark.asyncio
    async def test_call_agent_returns_mock_result(self):
        """Test _call_agent returns a mock result"""
        manager = CollaborationManager(agents_dict={})

        result = await manager._call_agent(
            agent=MagicMock(),
            task_description="Test task",
            context={"key": "value"}
        )

        assert result["status"] == "success"
        assert "Test task" in result["summary"]
        assert result["refinement_needed"] is False
        assert result["details"] == {"key": "value"}


@pytest.mark.unit
class TestCollaborationManagerWorkspaceManagement:
    """Test suite for workspace management methods"""

    def test_get_workspace_exists(self):
        """Test getting an existing workspace"""
        manager = CollaborationManager(agents_dict={})

        workspace = CollaborationWorkspace(
            name="Test",
            description="Test workspace",
            pattern=CollaborationPattern.SEQUENTIAL,
            shared_context={}
        )
        manager.active_workspaces[workspace.id] = workspace

        result = manager.get_workspace(workspace.id)
        assert result == workspace
        assert result.name == "Test"

    def test_get_workspace_not_exists(self):
        """Test getting a non-existent workspace returns None"""
        manager = CollaborationManager(agents_dict={})

        result = manager.get_workspace(uuid4())
        assert result is None

    def test_list_workspaces_empty(self):
        """Test listing workspaces when none exist"""
        manager = CollaborationManager(agents_dict={})

        result = manager.list_workspaces()
        assert result == []

    def test_list_workspaces_with_data(self):
        """Test listing workspaces with active workspaces"""
        manager = CollaborationManager(agents_dict={})

        workspace1 = CollaborationWorkspace(
            name="Workspace 1",
            description="First",
            pattern=CollaborationPattern.SEQUENTIAL,
            shared_context={}
        )
        workspace2 = CollaborationWorkspace(
            name="Workspace 2",
            description="Second",
            pattern=CollaborationPattern.PARALLEL,
            shared_context={}
        )

        manager.active_workspaces[workspace1.id] = workspace1
        manager.active_workspaces[workspace2.id] = workspace2

        result = manager.list_workspaces()
        assert len(result) == 2
        assert workspace1 in result
        assert workspace2 in result


@pytest.mark.unit
class TestCollaborationManagerExceptionHandling:
    """Test suite for exception handling"""

    @pytest.mark.asyncio
    async def test_start_collaboration_handles_exception(self):
        """Test start_collaboration handles exceptions gracefully"""
        manager = CollaborationManager(agents_dict={})

        # Patch _execute_sequential to raise an exception
        with patch.object(manager, '_execute_sequential', side_effect=Exception("Execution failed")):
            request = CollaborationRequest(
                name="Test Error",
                description="Test error handling",
                pattern=CollaborationPattern.SEQUENTIAL,
                agents=[AgentRole.DEVELOPER],
                initial_context={}
            )

            response = await manager.start_collaboration(request, uuid4(), uuid4())

            assert response.status == TaskStatus.FAILED
            assert response.error == "Execution failed"
            assert response.tasks_failed == 0  # No tasks were created yet

    @pytest.mark.asyncio
    async def test_start_collaboration_updates_workspace_timestamp(self):
        """Test start_collaboration updates workspace updated_at timestamp"""
        manager = CollaborationManager(agents_dict={})

        manager._call_agent = AsyncMock(return_value={"status": "success"})

        request = CollaborationRequest(
            name="Test Timestamp",
            description="Test",
            pattern=CollaborationPattern.SEQUENTIAL,
            agents=[AgentRole.DEVELOPER],
            initial_context={}
        )

        response = await manager.start_collaboration(request, uuid4(), uuid4())

        # Get the workspace
        workspace = manager.get_workspace(response.workspace_id)
        assert workspace.updated_at is not None


@pytest.mark.unit
class TestCollaborationManagerIntegration:
    """Integration tests for collaboration manager"""

    @pytest.mark.asyncio
    async def test_full_sequential_workflow(self):
        """Test complete sequential workflow from start to finish"""
        mock_developer = MagicMock()
        mock_qa = MagicMock()
        agents = {
            AgentRole.DEVELOPER: mock_developer,
            AgentRole.QA_TESTER: mock_qa
        }
        manager = CollaborationManager(agents_dict=agents)

        manager._call_agent = AsyncMock(return_value={
            "status": "success",
            "summary": "Completed",
            "refinement_needed": False
        })

        request = CollaborationRequest(
            name="Build Feature",
            description="Build and test a new feature",
            pattern=CollaborationPattern.SEQUENTIAL,
            agents=[AgentRole.DEVELOPER, AgentRole.QA_TESTER],
            initial_context={"feature": "auth"}
        )

        tenant_id = uuid4()
        user_id = uuid4()

        response = await manager.start_collaboration(request, tenant_id, user_id)

        # Verify response
        assert response.status == TaskStatus.COMPLETED
        assert response.tasks_completed == 2
        assert response.tasks_failed == 0
        assert response.total_duration_ms >= 0  # Can be 0 in fast test environments

        # Verify workspace
        workspace = manager.get_workspace(response.workspace_id)
        assert workspace is not None
        assert workspace.name == "Build Feature"
        assert len(workspace.tasks) == 2
        assert workspace.shared_context["feature"] == "auth"
        assert str(tenant_id) in workspace.shared_context["tenant_id"]

    @pytest.mark.asyncio
    async def test_full_parallel_workflow(self):
        """Test complete parallel workflow"""
        mock_developer = MagicMock()
        mock_designer = MagicMock()
        agents = {
            AgentRole.DEVELOPER: mock_developer,
            AgentRole.DESIGNER: mock_designer
        }
        manager = CollaborationManager(agents_dict=agents)

        manager._call_agent = AsyncMock(return_value={
            "status": "success",
            "summary": "Done"
        })

        request = CollaborationRequest(
            name="Parallel Work",
            description="Work in parallel",
            pattern=CollaborationPattern.PARALLEL,
            agents=[AgentRole.DEVELOPER, AgentRole.DESIGNER],
            initial_context={}
        )

        response = await manager.start_collaboration(request, uuid4(), uuid4())

        assert response.status == TaskStatus.COMPLETED
        assert response.tasks_completed == 2

        workspace = manager.get_workspace(response.workspace_id)
        assert len(workspace.tasks) == 2
