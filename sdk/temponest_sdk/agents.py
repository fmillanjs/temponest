"""
Temponest SDK - Agent Service Client
"""
from typing import List, Optional, Dict, Any
from .client import BaseClient, AsyncBaseClient
from .models import (
    Agent,
    AgentExecution,
    AgentCreateRequest,
    AgentExecuteRequest,
)
from .exceptions import AgentNotFoundError


class AgentsClient:
    """Client for agent management and execution"""

    def __init__(self, client: BaseClient):
        self.client = client

    def create(
        self,
        name: str,
        model: str,
        description: Optional[str] = None,
        provider: str = "ollama",
        system_prompt: Optional[str] = None,
        tools: Optional[List[str]] = None,
        rag_collection_ids: Optional[List[str]] = None,
        max_iterations: int = 10,
        temperature: float = 0.7,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Agent:
        """
        Create a new agent

        Args:
            name: Agent name
            model: Model name (e.g., "llama3.2:latest")
            description: Agent description
            provider: Model provider (default: "ollama")
            system_prompt: System prompt for the agent
            tools: List of tool names to enable
            rag_collection_ids: List of RAG collection IDs
            max_iterations: Maximum iterations for agent loop
            temperature: Model temperature
            metadata: Custom metadata

        Returns:
            Created agent

        Raises:
            TemponestAPIError: On API errors
        """
        request = AgentCreateRequest(
            name=name,
            model=model,
            description=description,
            provider=provider,
            system_prompt=system_prompt,
            tools=tools or [],
            rag_collection_ids=rag_collection_ids or [],
            max_iterations=max_iterations,
            temperature=temperature,
            metadata=metadata or {},
        )

        response = self.client.post("/agents/", json=request.model_dump())
        return Agent(**response)

    def get(self, agent_id: str) -> Agent:
        """
        Get an agent by ID

        Args:
            agent_id: Agent ID

        Returns:
            Agent object

        Raises:
            AgentNotFoundError: If agent not found
        """
        try:
            response = self.client.get(f"/agents/{agent_id}")
            return Agent(**response)
        except Exception as e:
            if "404" in str(e):
                raise AgentNotFoundError(f"Agent {agent_id} not found")
            raise

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> List[Agent]:
        """
        List agents

        Args:
            skip: Number of agents to skip
            limit: Maximum number of agents to return
            search: Search query

        Returns:
            List of agents
        """
        params = {"skip": skip, "limit": limit}
        if search:
            params["search"] = search

        response = self.client.get("/agents/", params=params)
        return [Agent(**agent) for agent in response]

    def update(
        self,
        agent_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[str]] = None,
        rag_collection_ids: Optional[List[str]] = None,
        max_iterations: Optional[int] = None,
        temperature: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Agent:
        """
        Update an agent

        Args:
            agent_id: Agent ID
            name: New name
            description: New description
            system_prompt: New system prompt
            tools: New tools list
            rag_collection_ids: New RAG collection IDs
            max_iterations: New max iterations
            temperature: New temperature
            metadata: New metadata

        Returns:
            Updated agent

        Raises:
            AgentNotFoundError: If agent not found
        """
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if system_prompt is not None:
            update_data["system_prompt"] = system_prompt
        if tools is not None:
            update_data["tools"] = tools
        if rag_collection_ids is not None:
            update_data["rag_collection_ids"] = rag_collection_ids
        if max_iterations is not None:
            update_data["max_iterations"] = max_iterations
        if temperature is not None:
            update_data["temperature"] = temperature
        if metadata is not None:
            update_data["metadata"] = metadata

        try:
            response = self.client.patch(f"/agents/{agent_id}", json=update_data)
            return Agent(**response)
        except Exception as e:
            if "404" in str(e):
                raise AgentNotFoundError(f"Agent {agent_id} not found")
            raise

    def delete(self, agent_id: str) -> None:
        """
        Delete an agent

        Args:
            agent_id: Agent ID

        Raises:
            AgentNotFoundError: If agent not found
        """
        try:
            self.client.delete(f"/agents/{agent_id}")
        except Exception as e:
            if "404" in str(e):
                raise AgentNotFoundError(f"Agent {agent_id} not found")
            raise

    def execute(
        self,
        agent_id: str,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False,
    ) -> AgentExecution:
        """
        Execute an agent

        Args:
            agent_id: Agent ID
            user_message: User message/prompt
            context: Additional context
            stream: Whether to stream the response

        Returns:
            Agent execution result

        Raises:
            AgentNotFoundError: If agent not found
        """
        request = AgentExecuteRequest(
            user_message=user_message,
            context=context or {},
            stream=stream,
        )

        try:
            response = self.client.post(
                f"/agents/{agent_id}/execute",
                json=request.model_dump()
            )
            return AgentExecution(**response)
        except Exception as e:
            if "404" in str(e):
                raise AgentNotFoundError(f"Agent {agent_id} not found")
            raise

    def execute_stream(
        self,
        agent_id: str,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Execute an agent with streaming response

        Args:
            agent_id: Agent ID
            user_message: User message/prompt
            context: Additional context

        Yields:
            Chunks of the agent's response as they arrive

        Raises:
            AgentNotFoundError: If agent not found

        Example:
            ```python
            for chunk in client.agents.execute_stream(agent_id, "Hello!"):
                print(chunk, end='', flush=True)
            ```
        """
        request = AgentExecuteRequest(
            user_message=user_message,
            context=context or {},
            stream=True,
        )

        try:
            import httpx
            from urllib.parse import urljoin

            url = urljoin(self.client.base_url, f"/agents/{agent_id}/execute")
            headers = self.client._get_headers()

            with httpx.stream(
                "POST",
                url,
                json=request.model_dump(),
                headers=headers,
                timeout=self.client.timeout,
            ) as response:
                if response.status_code >= 400:
                    self.client._handle_error(response)

                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data == "[DONE]":
                            break
                        try:
                            import json
                            chunk_data = json.loads(data)
                            yield chunk_data.get("content", "")
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            if "404" in str(e):
                raise AgentNotFoundError(f"Agent {agent_id} not found")
            raise

    def get_execution(self, execution_id: str) -> AgentExecution:
        """
        Get an execution by ID

        Args:
            execution_id: Execution ID

        Returns:
            Agent execution
        """
        response = self.client.get(f"/executions/{execution_id}")
        return AgentExecution(**response)

    def list_executions(
        self,
        agent_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
    ) -> List[AgentExecution]:
        """
        List agent executions

        Args:
            agent_id: Filter by agent ID
            skip: Number to skip
            limit: Maximum to return
            status: Filter by status

        Returns:
            List of executions
        """
        params = {"skip": skip, "limit": limit}
        if agent_id:
            params["agent_id"] = agent_id
        if status:
            params["status"] = status

        response = self.client.get("/executions/", params=params)
        return [AgentExecution(**execution) for execution in response]


class AsyncAgentsClient:
    """Async client for agent management and execution"""

    def __init__(self, client: AsyncBaseClient):
        self.client = client

    async def create(
        self,
        name: str,
        model: str,
        description: Optional[str] = None,
        provider: str = "ollama",
        system_prompt: Optional[str] = None,
        tools: Optional[List[str]] = None,
        rag_collection_ids: Optional[List[str]] = None,
        max_iterations: int = 10,
        temperature: float = 0.7,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Agent:
        """Create a new agent (async)"""
        request = AgentCreateRequest(
            name=name,
            model=model,
            description=description,
            provider=provider,
            system_prompt=system_prompt,
            tools=tools or [],
            rag_collection_ids=rag_collection_ids or [],
            max_iterations=max_iterations,
            temperature=temperature,
            metadata=metadata or {},
        )

        response = await self.client.post("/agents/", json=request.model_dump())
        return Agent(**response)

    async def get(self, agent_id: str) -> Agent:
        """Get an agent by ID (async)"""
        try:
            response = await self.client.get(f"/agents/{agent_id}")
            return Agent(**response)
        except Exception as e:
            if "404" in str(e):
                raise AgentNotFoundError(f"Agent {agent_id} not found")
            raise

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> List[Agent]:
        """List agents (async)"""
        params = {"skip": skip, "limit": limit}
        if search:
            params["search"] = search

        response = await self.client.get("/agents/", params=params)
        return [Agent(**agent) for agent in response]

    async def update(
        self,
        agent_id: str,
        **kwargs
    ) -> Agent:
        """Update an agent (async)"""
        update_data = {k: v for k, v in kwargs.items() if v is not None}

        try:
            response = await self.client.patch(f"/agents/{agent_id}", json=update_data)
            return Agent(**response)
        except Exception as e:
            if "404" in str(e):
                raise AgentNotFoundError(f"Agent {agent_id} not found")
            raise

    async def delete(self, agent_id: str) -> None:
        """Delete an agent (async)"""
        try:
            await self.client.delete(f"/agents/{agent_id}")
        except Exception as e:
            if "404" in str(e):
                raise AgentNotFoundError(f"Agent {agent_id} not found")
            raise

    async def execute(
        self,
        agent_id: str,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False,
    ) -> AgentExecution:
        """Execute an agent (async)"""
        request = AgentExecuteRequest(
            user_message=user_message,
            context=context or {},
            stream=stream,
        )

        try:
            response = await self.client.post(
                f"/agents/{agent_id}/execute",
                json=request.model_dump()
            )
            return AgentExecution(**response)
        except Exception as e:
            if "404" in str(e):
                raise AgentNotFoundError(f"Agent {agent_id} not found")
            raise

    async def execute_stream(
        self,
        agent_id: str,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Execute an agent with streaming response (async)

        Args:
            agent_id: Agent ID
            user_message: User message/prompt
            context: Additional context

        Yields:
            Chunks of the agent's response as they arrive

        Raises:
            AgentNotFoundError: If agent not found

        Example:
            ```python
            async for chunk in client.agents.execute_stream(agent_id, "Hello!"):
                print(chunk, end='', flush=True)
            ```
        """
        request = AgentExecuteRequest(
            user_message=user_message,
            context=context or {},
            stream=True,
        )

        try:
            import httpx
            from urllib.parse import urljoin
            import json

            url = urljoin(self.client.base_url, f"/agents/{agent_id}/execute")
            headers = self.client._get_headers()

            async with httpx.AsyncClient(timeout=self.client.timeout) as http_client:
                async with http_client.stream(
                    "POST",
                    url,
                    json=request.model_dump(),
                    headers=headers,
                ) as response:
                    if response.status_code >= 400:
                        self.client._handle_error(response)

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]  # Remove "data: " prefix
                            if data == "[DONE]":
                                break
                            try:
                                chunk_data = json.loads(data)
                                yield chunk_data.get("content", "")
                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            if "404" in str(e):
                raise AgentNotFoundError(f"Agent {agent_id} not found")
            raise

    async def get_execution(self, execution_id: str) -> AgentExecution:
        """Get an execution by ID (async)"""
        response = await self.client.get(f"/executions/{execution_id}")
        return AgentExecution(**response)

    async def list_executions(
        self,
        agent_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
    ) -> List[AgentExecution]:
        """List agent executions (async)"""
        params = {"skip": skip, "limit": limit}
        if agent_id:
            params["agent_id"] = agent_id
        if status:
            params["status"] = status

        response = await self.client.get("/executions/", params=params)
        return [AgentExecution(**execution) for execution in response]
