"""
Temponest SDK - Main Client
"""
from typing import Optional
from .client import BaseClient, AsyncBaseClient
from .agents import AgentsClient, AsyncAgentsClient
from .scheduler import SchedulerClient, AsyncSchedulerClient


class TemponestClient:
    """
    Main client for the Temponest Agentic Platform

    Example:
        ```python
        from temponest_sdk import TemponestClient

        client = TemponestClient(
            base_url="http://localhost:9000",
            auth_token="your-token"
        )

        # Create an agent
        agent = client.agents.create(
            name="MyAgent",
            model="llama3.2:latest",
            system_prompt="You are a helpful assistant."
        )

        # Execute the agent
        result = client.agents.execute(
            agent_id=agent.id,
            user_message="Hello, how can you help me?"
        )

        print(result.response)
        ```
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        auth_token: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff_factor: float = 0.5,
        verify_ssl: bool = True,
    ):
        """
        Initialize the Temponest client

        Args:
            base_url: Base URL for the API (default: from TEMPONEST_BASE_URL env var)
            auth_token: Authentication token (default: from TEMPONEST_AUTH_TOKEN env var)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_backoff_factor: Backoff factor for retries
            verify_ssl: Whether to verify SSL certificates
        """
        self._client = BaseClient(
            base_url=base_url,
            auth_token=auth_token,
            timeout=timeout,
            max_retries=max_retries,
            retry_backoff_factor=retry_backoff_factor,
            verify_ssl=verify_ssl,
        )

        # Initialize service clients
        self.agents = AgentsClient(self._client)
        self.scheduler = SchedulerClient(self._client)

    def close(self) -> None:
        """Close the HTTP client"""
        self._client.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


class AsyncTemponestClient:
    """
    Async client for the Temponest Agentic Platform

    Example:
        ```python
        import asyncio
        from temponest_sdk import AsyncTemponestClient

        async def main():
            async with AsyncTemponestClient(
                base_url="http://localhost:9000",
                auth_token="your-token"
            ) as client:
                # Create an agent
                agent = await client.agents.create(
                    name="MyAgent",
                    model="llama3.2:latest"
                )

                # Execute the agent
                result = await client.agents.execute(
                    agent_id=agent.id,
                    user_message="Hello!"
                )

                print(result.response)

        asyncio.run(main())
        ```
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        auth_token: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff_factor: float = 0.5,
        verify_ssl: bool = True,
    ):
        """
        Initialize the async Temponest client

        Args:
            base_url: Base URL for the API (default: from TEMPONEST_BASE_URL env var)
            auth_token: Authentication token (default: from TEMPONEST_AUTH_TOKEN env var)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_backoff_factor: Backoff factor for retries
            verify_ssl: Whether to verify SSL certificates
        """
        self._client = AsyncBaseClient(
            base_url=base_url,
            auth_token=auth_token,
            timeout=timeout,
            max_retries=max_retries,
            retry_backoff_factor=retry_backoff_factor,
            verify_ssl=verify_ssl,
        )

        # Initialize async service clients
        self.agents = AsyncAgentsClient(self._client)
        self.scheduler = AsyncSchedulerClient(self._client)

    async def close(self) -> None:
        """Close the HTTP client"""
        await self._client.close()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
