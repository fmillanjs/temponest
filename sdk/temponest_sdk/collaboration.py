"""
Temponest SDK - Collaboration Service Client
"""
from typing import List, Optional, Dict, Any, Literal
from .client import BaseClient, AsyncBaseClient
from .models import CollaborationSession


class CollaborationClient:
    """Client for multi-agent collaboration"""

    def __init__(self, client: BaseClient):
        self.client = client

    def execute_sequential(
        self,
        agent_ids: List[str],
        initial_message: str,
        pass_full_history: bool = True,
        max_iterations: int = 10,
        context: Optional[Dict[str, Any]] = None,
    ) -> CollaborationSession:
        """
        Execute agents in sequential pattern

        Each agent processes the output of the previous agent in sequence.

        Args:
            agent_ids: List of agent IDs (order matters)
            initial_message: Initial message for first agent
            pass_full_history: Whether to pass full conversation history
            max_iterations: Maximum iterations
            context: Additional context

        Returns:
            Collaboration session with results

        Example:
            ```python
            session = client.collaboration.execute_sequential(
                agent_ids=[researcher_id, writer_id, editor_id],
                initial_message="Write an article about AI",
                pass_full_history=True
            )
            ```
        """
        payload = {
            "pattern": "sequential",
            "agent_ids": agent_ids,
            "initial_message": initial_message,
            "config": {
                "pass_full_history": pass_full_history,
                "max_iterations": max_iterations,
            },
            "context": context or {}
        }

        response = self.client.post("/collaboration/execute", json=payload)
        return CollaborationSession(**response)

    def execute_parallel(
        self,
        agent_ids: List[str],
        messages: List[str],
        aggregate_results: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ) -> CollaborationSession:
        """
        Execute agents in parallel pattern

        Each agent processes its message independently and concurrently.

        Args:
            agent_ids: List of agent IDs
            messages: List of messages (one per agent)
            aggregate_results: Whether to aggregate results
            context: Additional context

        Returns:
            Collaboration session with results

        Example:
            ```python
            session = client.collaboration.execute_parallel(
                agent_ids=[analyst1_id, analyst2_id, analyst3_id],
                messages=[
                    "Analyze market trends",
                    "Analyze competitor data",
                    "Analyze customer feedback"
                ]
            )
            ```
        """
        if len(agent_ids) != len(messages):
            raise ValueError("Number of agents must match number of messages")

        payload = {
            "pattern": "parallel",
            "agent_ids": agent_ids,
            "messages": messages,
            "config": {
                "aggregate_results": aggregate_results,
            },
            "context": context or {}
        }

        response = self.client.post("/collaboration/execute", json=payload)
        return CollaborationSession(**response)

    def execute_iterative(
        self,
        agent_ids: List[str],
        initial_message: str,
        max_iterations: int = 5,
        convergence_threshold: float = 0.9,
        context: Optional[Dict[str, Any]] = None,
    ) -> CollaborationSession:
        """
        Execute agents in iterative pattern

        Agents iterate on the same task until convergence or max iterations.

        Args:
            agent_ids: List of agent IDs
            initial_message: Initial message
            max_iterations: Maximum iterations
            convergence_threshold: Quality threshold for convergence
            context: Additional context

        Returns:
            Collaboration session with results

        Example:
            ```python
            session = client.collaboration.execute_iterative(
                agent_ids=[generator_id, critic_id],
                initial_message="Design a logo",
                max_iterations=5
            )
            ```
        """
        payload = {
            "pattern": "iterative",
            "agent_ids": agent_ids,
            "initial_message": initial_message,
            "config": {
                "max_iterations": max_iterations,
                "convergence_threshold": convergence_threshold,
            },
            "context": context or {}
        }

        response = self.client.post("/collaboration/execute", json=payload)
        return CollaborationSession(**response)

    def execute_hierarchical(
        self,
        coordinator_id: str,
        worker_ids: List[str],
        task: str,
        delegation_strategy: Literal["round_robin", "capability_based", "load_balanced"] = "capability_based",
        context: Optional[Dict[str, Any]] = None,
    ) -> CollaborationSession:
        """
        Execute agents in hierarchical pattern

        A coordinator agent delegates subtasks to worker agents.

        Args:
            coordinator_id: ID of coordinator agent
            worker_ids: List of worker agent IDs
            task: Main task to accomplish
            delegation_strategy: How to delegate tasks
            context: Additional context

        Returns:
            Collaboration session with results

        Example:
            ```python
            session = client.collaboration.execute_hierarchical(
                coordinator_id=manager_id,
                worker_ids=[dev1_id, dev2_id, dev3_id],
                task="Build a web application",
                delegation_strategy="capability_based"
            )
            ```
        """
        payload = {
            "pattern": "hierarchical",
            "coordinator_id": coordinator_id,
            "worker_ids": worker_ids,
            "task": task,
            "config": {
                "delegation_strategy": delegation_strategy,
            },
            "context": context or {}
        }

        response = self.client.post("/collaboration/execute", json=payload)
        return CollaborationSession(**response)

    def get_session(self, session_id: str) -> CollaborationSession:
        """
        Get a collaboration session by ID

        Args:
            session_id: Session ID

        Returns:
            Collaboration session
        """
        response = self.client.get(f"/collaboration/sessions/{session_id}")
        return CollaborationSession(**response)

    def list_sessions(
        self,
        skip: int = 0,
        limit: int = 100,
        pattern: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[CollaborationSession]:
        """
        List collaboration sessions

        Args:
            skip: Number to skip
            limit: Maximum to return
            pattern: Filter by pattern
            status: Filter by status

        Returns:
            List of sessions
        """
        params = {"skip": skip, "limit": limit}
        if pattern:
            params["pattern"] = pattern
        if status:
            params["status"] = status

        response = self.client.get("/collaboration/sessions/", params=params)
        return [CollaborationSession(**session) for session in response]

    def cancel_session(self, session_id: str) -> None:
        """
        Cancel a running collaboration session

        Args:
            session_id: Session ID
        """
        self.client.post(f"/collaboration/sessions/{session_id}/cancel")


class AsyncCollaborationClient:
    """Async client for multi-agent collaboration"""

    def __init__(self, client: AsyncBaseClient):
        self.client = client

    async def execute_sequential(
        self,
        agent_ids: List[str],
        initial_message: str,
        pass_full_history: bool = True,
        max_iterations: int = 10,
        context: Optional[Dict[str, Any]] = None,
    ) -> CollaborationSession:
        """Execute agents in sequential pattern (async)"""
        payload = {
            "pattern": "sequential",
            "agent_ids": agent_ids,
            "initial_message": initial_message,
            "config": {
                "pass_full_history": pass_full_history,
                "max_iterations": max_iterations,
            },
            "context": context or {}
        }

        response = await self.client.post("/collaboration/execute", json=payload)
        return CollaborationSession(**response)

    async def execute_parallel(
        self,
        agent_ids: List[str],
        messages: List[str],
        aggregate_results: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ) -> CollaborationSession:
        """Execute agents in parallel pattern (async)"""
        if len(agent_ids) != len(messages):
            raise ValueError("Number of agents must match number of messages")

        payload = {
            "pattern": "parallel",
            "agent_ids": agent_ids,
            "messages": messages,
            "config": {
                "aggregate_results": aggregate_results,
            },
            "context": context or {}
        }

        response = await self.client.post("/collaboration/execute", json=payload)
        return CollaborationSession(**response)

    async def execute_iterative(
        self,
        agent_ids: List[str],
        initial_message: str,
        max_iterations: int = 5,
        convergence_threshold: float = 0.9,
        context: Optional[Dict[str, Any]] = None,
    ) -> CollaborationSession:
        """Execute agents in iterative pattern (async)"""
        payload = {
            "pattern": "iterative",
            "agent_ids": agent_ids,
            "initial_message": initial_message,
            "config": {
                "max_iterations": max_iterations,
                "convergence_threshold": convergence_threshold,
            },
            "context": context or {}
        }

        response = await self.client.post("/collaboration/execute", json=payload)
        return CollaborationSession(**response)

    async def execute_hierarchical(
        self,
        coordinator_id: str,
        worker_ids: List[str],
        task: str,
        delegation_strategy: Literal["round_robin", "capability_based", "load_balanced"] = "capability_based",
        context: Optional[Dict[str, Any]] = None,
    ) -> CollaborationSession:
        """Execute agents in hierarchical pattern (async)"""
        payload = {
            "pattern": "hierarchical",
            "coordinator_id": coordinator_id,
            "worker_ids": worker_ids,
            "task": task,
            "config": {
                "delegation_strategy": delegation_strategy,
            },
            "context": context or {}
        }

        response = await self.client.post("/collaboration/execute", json=payload)
        return CollaborationSession(**response)

    async def get_session(self, session_id: str) -> CollaborationSession:
        """Get a collaboration session by ID (async)"""
        response = await self.client.get(f"/collaboration/sessions/{session_id}")
        return CollaborationSession(**response)

    async def list_sessions(
        self,
        skip: int = 0,
        limit: int = 100,
        pattern: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[CollaborationSession]:
        """List collaboration sessions (async)"""
        params = {"skip": skip, "limit": limit}
        if pattern:
            params["pattern"] = pattern
        if status:
            params["status"] = status

        response = await self.client.get("/collaboration/sessions/", params=params)
        return [CollaborationSession(**session) for session in response]

    async def cancel_session(self, session_id: str) -> None:
        """Cancel a running collaboration session (async)"""
        await self.client.post(f"/collaboration/sessions/{session_id}/cancel")
