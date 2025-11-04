# Temponest SDK

Official Python SDK for the Temponest Agentic Platform - Build, deploy, and manage AI agents with ease.

## Features

- **Agent Management**: Create, execute, and manage AI agents programmatically
- **Scheduling**: Schedule agent executions with flexible cron expressions
- **RAG Integration**: Manage knowledge bases and document collections
- **Cost Tracking**: Monitor token usage and costs across providers
- **Collaboration**: Orchestrate multi-agent collaboration patterns
- **Async Support**: Full async/await support for high-performance applications
- **Type Safety**: Comprehensive type hints and Pydantic models

## Installation

```bash
pip install temponest-sdk
```

For development:

```bash
pip install temponest-sdk[dev]
```

## Quick Start

```python
from temponest_sdk import TemponestClient

# Initialize the client
client = TemponestClient(
    base_url="http://localhost:9000",
    auth_token="your-auth-token"
)

# Create an agent
agent = client.agents.create(
    name="MyAgent",
    description="An intelligent assistant",
    model="llama3.2:latest",
    system_prompt="You are a helpful assistant.",
    tools=["web_search", "calculator"]
)

# Execute the agent
result = client.agents.execute(
    agent_id=agent.id,
    user_message="What is the weather today?",
    context={"location": "San Francisco"}
)

print(result.response)
```

## Async Usage

```python
import asyncio
from temponest_sdk import AsyncTemponestClient

async def main():
    async with AsyncTemponestClient(
        base_url="http://localhost:9000",
        auth_token="your-auth-token"
    ) as client:
        # Create and execute agent
        agent = await client.agents.create(
            name="AsyncAgent",
            model="llama3.2:latest"
        )

        result = await client.agents.execute(
            agent_id=agent.id,
            user_message="Hello!"
        )

        print(result.response)

asyncio.run(main())
```

## Scheduling Agents

```python
# Schedule an agent to run daily at 9 AM
schedule = client.scheduler.create(
    agent_id=agent.id,
    cron_expression="0 9 * * *",
    task_config={
        "user_message": "Generate daily report",
        "context": {"report_type": "summary"}
    }
)

# List scheduled tasks
tasks = client.scheduler.list()

# Pause a schedule
client.scheduler.pause(schedule.id)
```

## RAG and Knowledge Management

```python
# Create a collection
collection = client.rag.create_collection(
    name="company_docs",
    description="Company documentation"
)

# Upload documents
client.rag.upload_documents(
    collection_id=collection.id,
    files=["./docs/policy.pdf", "./docs/handbook.pdf"]
)

# Query the knowledge base
results = client.rag.query(
    collection_id=collection.id,
    query="What is the vacation policy?",
    top_k=5
)
```

## Multi-Agent Collaboration

```python
# Create multiple agents
researcher = client.agents.create(name="Researcher", model="llama3.2:latest")
writer = client.agents.create(name="Writer", model="llama3.2:latest")
editor = client.agents.create(name="Editor", model="llama3.2:latest")

# Sequential collaboration pattern
result = client.collaboration.execute_sequential(
    agents=[researcher, writer, editor],
    initial_message="Write an article about AI safety",
    pattern_config={
        "pass_full_history": True
    }
)

# Parallel collaboration pattern
results = client.collaboration.execute_parallel(
    agents=[researcher, researcher, researcher],
    messages=[
        "Research AI ethics",
        "Research AI regulation",
        "Research AI safety"
    ]
)
```

## Cost Tracking

```python
# Get cost summary
costs = client.costs.get_summary(
    start_date="2025-01-01",
    end_date="2025-01-31"
)

print(f"Total cost: ${costs.total_usd}")
print(f"By provider: {costs.by_provider}")
print(f"By agent: {costs.by_agent}")

# Set budget alerts
client.costs.set_budget(
    daily_limit_usd=50.0,
    monthly_limit_usd=1000.0,
    alert_threshold=0.8
)
```

## Error Handling

```python
from temponest_sdk.exceptions import (
    TemponestAPIError,
    AgentNotFoundError,
    RateLimitError,
    AuthenticationError
)

try:
    result = client.agents.execute(
        agent_id="invalid-id",
        user_message="Hello"
    )
except AgentNotFoundError as e:
    print(f"Agent not found: {e}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e.retry_after} seconds")
except TemponestAPIError as e:
    print(f"API error: {e.status_code} - {e.message}")
```

## Configuration

### Environment Variables

```bash
TEMPONEST_BASE_URL=http://localhost:9000
TEMPONEST_AUTH_TOKEN=your-token-here
TEMPONEST_TIMEOUT=30
TEMPONEST_MAX_RETRIES=3
```

### Client Configuration

```python
client = TemponestClient(
    base_url="http://localhost:9000",
    auth_token="your-token",
    timeout=30.0,
    max_retries=3,
    retry_backoff_factor=0.5,
    verify_ssl=True
)
```

## Documentation

Full documentation is available at: https://docs.temponest.com

## Support

- GitHub Issues: https://github.com/temponest/sdk/issues
- Email: support@temponest.com
- Discord: https://discord.gg/temponest

## License

MIT License - see LICENSE file for details
