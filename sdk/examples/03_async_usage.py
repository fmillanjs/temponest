"""
Example 3: Async Usage

This example demonstrates how to:
1. Use the async client
2. Make concurrent requests
3. Manage async context
"""

import asyncio
from temponest_sdk import AsyncTemponestClient


async def create_multiple_agents(client, count=3):
    """Create multiple agents concurrently"""
    tasks = []
    for i in range(count):
        tasks.append(
            client.agents.create(
                name=f"AsyncAgent{i+1}",
                model="llama3.2:latest",
                system_prompt=f"You are assistant number {i+1}.",
            )
        )

    agents = await asyncio.gather(*tasks)
    return agents


async def execute_agents_parallel(client, agents):
    """Execute multiple agents in parallel"""
    tasks = []
    for agent in agents:
        tasks.append(
            client.agents.execute(
                agent_id=agent.id,
                user_message="Hello! What is your purpose?"
            )
        )

    results = await asyncio.gather(*tasks)
    return results


async def main():
    # Use async context manager
    async with AsyncTemponestClient(base_url="http://localhost:9000") as client:
        try:
            # Create multiple agents concurrently
            print("Creating 3 agents concurrently...")
            agents = await create_multiple_agents(client, count=3)
            print(f"✓ Created {len(agents)} agents:")
            for agent in agents:
                print(f"  - {agent.name} ({agent.id})")

            # Execute all agents in parallel
            print("\nExecuting all agents in parallel...")
            results = await execute_agents_parallel(client, agents)
            print(f"✓ Got {len(results)} results:")
            for i, result in enumerate(results):
                print(f"\n  Agent {i+1} Response:")
                print(f"    Status: {result.status}")
                print(f"    Response: {result.response[:100]}...")
                print(f"    Tokens: {result.tokens_used}")

            # List agents
            print("\nListing agents...")
            all_agents = await client.agents.list(limit=10)
            print(f"✓ Total agents: {len(all_agents)}")

            # Clean up all agents
            print("\nCleaning up agents...")
            delete_tasks = [client.agents.delete(agent.id) for agent in agents]
            await asyncio.gather(*delete_tasks)
            print("✓ All agents deleted")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
