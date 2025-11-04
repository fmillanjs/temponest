"""
Temponest SDK - Official Python Client for the Agentic Platform

Usage:
    from temponest_sdk import TemponestClient

    client = TemponestClient(
        base_url="http://localhost:9000",
        auth_token="your-token"
    )

    # Create and execute an agent
    agent = client.agents.create(
        name="MyAgent",
        model="llama3.2:latest"
    )

    result = client.agents.execute(
        agent_id=agent.id,
        user_message="Hello!"
    )
"""

from .main import TemponestClient, AsyncTemponestClient
from .models import (
    Agent,
    AgentExecution,
    ScheduledTask,
    TaskExecution,
    Collection,
    Document,
    QueryResult,
    CollaborationSession,
    CostSummary,
    BudgetConfig,
)
from .webhooks import Webhook, WebhookDelivery
from .exceptions import (
    TemponestError,
    TemponestAPIError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    AgentNotFoundError,
    ScheduleNotFoundError,
    CollectionNotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
    ConnectionError,
    TimeoutError,
    ConfigurationError,
)

__version__ = "1.0.0"
__all__ = [
    # Main clients
    "TemponestClient",
    "AsyncTemponestClient",
    # Models
    "Agent",
    "AgentExecution",
    "ScheduledTask",
    "TaskExecution",
    "Collection",
    "Document",
    "QueryResult",
    "CollaborationSession",
    "CostSummary",
    "BudgetConfig",
    "Webhook",
    "WebhookDelivery",
    # Exceptions
    "TemponestError",
    "TemponestAPIError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "AgentNotFoundError",
    "ScheduleNotFoundError",
    "CollectionNotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
    "ConnectionError",
    "TimeoutError",
    "ConfigurationError",
]
