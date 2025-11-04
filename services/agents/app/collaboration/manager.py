"""
Collaboration Manager - Coordinates multiple agents working together
"""
import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from datetime import datetime

from .models import (
    AgentRole,
    TaskStatus,
    CollaborationPattern,
    AgentTask,
    CollaborationWorkspace,
    CollaborationRequest,
    CollaborationResponse
)


class CollaborationManager:
    """
    Manages multi-agent collaboration workflows.
    Coordinates task execution, handoffs, and shared context.
    """

    def __init__(self, agents_dict: Dict[AgentRole, Any]):
        """
        Initialize collaboration manager with available agents.

        Args:
            agents_dict: Dictionary mapping AgentRole to agent instances
        """
        self.agents = agents_dict
        self.active_workspaces: Dict[UUID, CollaborationWorkspace] = {}

    async def start_collaboration(
        self,
        request: CollaborationRequest,
        tenant_id: UUID,
        user_id: UUID
    ) -> CollaborationResponse:
        """
        Start a new collaboration session.

        Args:
            request: Collaboration request details
            tenant_id: Tenant ID for context
            user_id: User ID for context

        Returns:
            CollaborationResponse with results
        """
        start_time = time.time()

        # Create workspace
        workspace = CollaborationWorkspace(
            name=request.name,
            description=request.description,
            pattern=request.pattern,
            shared_context={
                "tenant_id": str(tenant_id),
                "user_id": str(user_id),
                **request.initial_context
            }
        )

        self.active_workspaces[workspace.id] = workspace

        try:
            # Execute workflow based on pattern
            if request.pattern == CollaborationPattern.SEQUENTIAL:
                await self._execute_sequential(workspace, request)
            elif request.pattern == CollaborationPattern.PARALLEL:
                await self._execute_parallel(workspace, request)
            elif request.pattern == CollaborationPattern.ITERATIVE:
                await self._execute_iterative(workspace, request)
            elif request.pattern == CollaborationPattern.HIERARCHICAL:
                await self._execute_hierarchical(workspace, request)

            # Calculate statistics
            tasks_completed = sum(1 for task in workspace.tasks if task.status == TaskStatus.COMPLETED)
            tasks_failed = sum(1 for task in workspace.tasks if task.status == TaskStatus.FAILED)

            # Determine overall status
            if tasks_failed > 0:
                workspace.status = TaskStatus.FAILED
            elif tasks_completed == len(workspace.tasks):
                workspace.status = TaskStatus.COMPLETED
            else:
                workspace.status = TaskStatus.IN_PROGRESS

            duration_ms = int((time.time() - start_time) * 1000)

            return CollaborationResponse(
                workspace_id=workspace.id,
                status=workspace.status,
                result=workspace.shared_context.get("final_result"),
                tasks_completed=tasks_completed,
                tasks_failed=tasks_failed,
                total_duration_ms=duration_ms,
                artifacts=workspace.artifacts
            )

        except Exception as e:
            workspace.status = TaskStatus.FAILED
            return CollaborationResponse(
                workspace_id=workspace.id,
                status=TaskStatus.FAILED,
                error=str(e),
                tasks_completed=0,
                tasks_failed=len(workspace.tasks)
            )

        finally:
            workspace.updated_at = datetime.utcnow()

    async def _execute_sequential(
        self,
        workspace: CollaborationWorkspace,
        request: CollaborationRequest
    ):
        """Execute tasks sequentially in order"""

        # If workflow steps are provided, use them
        if request.workflow_steps:
            for step in request.workflow_steps:
                agent_role = AgentRole(step["agent"])
                task = AgentTask(
                    agent_role=agent_role,
                    task_description=step["task"],
                    context=step.get("context", {})
                )
                workspace.tasks.append(task)

                # Execute task
                await self._execute_task(workspace, task)

                # If task failed, stop sequential execution
                if task.status == TaskStatus.FAILED:
                    break

        else:
            # Default: Overseer delegates to each agent in sequence
            for agent_role in request.agents:
                task = AgentTask(
                    agent_role=agent_role,
                    task_description=request.description,
                    context=workspace.shared_context
                )
                workspace.tasks.append(task)

                await self._execute_task(workspace, task)

                if task.status == TaskStatus.FAILED:
                    break

    async def _execute_parallel(
        self,
        workspace: CollaborationWorkspace,
        request: CollaborationRequest
    ):
        """Execute tasks in parallel"""

        # Create tasks for all agents
        tasks = []
        for agent_role in request.agents:
            task = AgentTask(
                agent_role=agent_role,
                task_description=request.description,
                context=workspace.shared_context
            )
            workspace.tasks.append(task)
            tasks.append(self._execute_task(workspace, task))

        # Execute all tasks in parallel
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_iterative(
        self,
        workspace: CollaborationWorkspace,
        request: CollaborationRequest
    ):
        """Execute tasks in iterative feedback loops"""

        max_iterations = 3
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            workspace.shared_context["iteration"] = iteration

            # Execute each agent in sequence
            for agent_role in request.agents:
                task = AgentTask(
                    agent_role=agent_role,
                    task_description=f"Iteration {iteration}: {request.description}",
                    context=workspace.shared_context
                )
                workspace.tasks.append(task)

                await self._execute_task(workspace, task)

                # Check if refinement is needed
                if task.result and task.result.get("refinement_needed") is False:
                    # Task is complete, no more iterations needed
                    return

    async def _execute_hierarchical(
        self,
        workspace: CollaborationWorkspace,
        request: CollaborationRequest
    ):
        """Execute tasks hierarchically with Overseer coordinating"""

        # First, Overseer analyzes and creates a plan
        overseer_task = AgentTask(
            agent_role=AgentRole.OVERSEER,
            task_description=f"Analyze and create execution plan for: {request.description}",
            context=workspace.shared_context
        )
        workspace.tasks.append(overseer_task)

        await self._execute_task(workspace, overseer_task)

        if overseer_task.status == TaskStatus.FAILED:
            return

        # Get the execution plan from Overseer
        execution_plan = overseer_task.result.get("execution_plan", [])

        # Execute tasks based on Overseer's plan
        for step in execution_plan:
            agent_role = AgentRole(step.get("agent", "developer"))
            task = AgentTask(
                agent_role=agent_role,
                task_description=step.get("task", request.description),
                context={**workspace.shared_context, **step.get("context", {})}
            )
            workspace.tasks.append(task)

            await self._execute_task(workspace, task)

            # If critical task fails, stop execution
            if task.status == TaskStatus.FAILED and step.get("critical", False):
                break

    async def _execute_task(
        self,
        workspace: CollaborationWorkspace,
        task: AgentTask
    ) -> AgentTask:
        """
        Execute a single agent task.

        Args:
            workspace: The collaboration workspace
            task: The task to execute

        Returns:
            Updated task with results
        """
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.utcnow()

        try:
            # Get the agent for this role
            agent = self.agents.get(task.agent_role)
            if not agent:
                raise ValueError(f"Agent not available for role: {task.agent_role}")

            # Prepare context with workspace information
            agent_context = {
                **task.context,
                "workspace_id": str(workspace.id),
                "workspace_name": workspace.name,
                "shared_context": workspace.shared_context,
                "previous_tasks": [
                    {
                        "agent": t.agent_role.value,
                        "task": t.task_description,
                        "result": t.result
                    }
                    for t in workspace.tasks
                    if t.status == TaskStatus.COMPLETED and t.id != task.id
                ]
            }

            # Execute agent task
            # Note: This is a simplified version. In practice, you'd call the actual agent's execute method
            result = await self._call_agent(agent, task.task_description, agent_context)

            # Update task with result
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()

            # Update workspace shared context with task result
            workspace.shared_context[f"task_{task.id}_result"] = result

            # Log message in workspace
            workspace.messages.append({
                "timestamp": datetime.utcnow().isoformat(),
                "agent": task.agent_role.value,
                "message": f"Completed: {task.task_description}",
                "result_summary": result.get("summary", "No summary available")
            })

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.utcnow()

            workspace.messages.append({
                "timestamp": datetime.utcnow().isoformat(),
                "agent": task.agent_role.value,
                "message": f"Failed: {task.task_description}",
                "error": str(e)
            })

        return task

    async def _call_agent(
        self,
        agent: Any,
        task_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call an agent to execute a task.

        This is a simplified implementation. In practice, you'd integrate
        with the actual agent execution methods.

        Args:
            agent: The agent instance
            task_description: Description of the task
            context: Context for the agent

        Returns:
            Result dictionary
        """
        # TODO: Implement actual agent execution
        # For now, return a mock result
        return {
            "status": "success",
            "summary": f"Executed task: {task_description}",
            "details": context,
            "refinement_needed": False
        }

    def get_workspace(self, workspace_id: UUID) -> Optional[CollaborationWorkspace]:
        """Get a workspace by ID"""
        return self.active_workspaces.get(workspace_id)

    def list_workspaces(self) -> List[CollaborationWorkspace]:
        """List all active workspaces"""
        return list(self.active_workspaces.values())
