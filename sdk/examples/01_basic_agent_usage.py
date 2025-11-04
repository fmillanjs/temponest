"""
Example 1: Basic Agent Usage

This example demonstrates how to:
1. Initialize the Temponest client
2. Create a simple agent
3. Execute the agent with a message
4. Retrieve execution results
"""

from temponest_sdk import TemponestClient

def main():
    # Initialize the client
    # By default, it reads from TEMPONEST_BASE_URL and TEMPONEST_AUTH_TOKEN environment variables
    client = TemponestClient(
        base_url="http://localhost:9000",
        # auth_token="your-token-here"  # Optional if using env var
    )

    try:
        # Create a simple agent
        print("Creating agent...")
        agent = client.agents.create(
            name="SimpleAssistant",
            description="A helpful AI assistant",
            model="llama3.2:latest",
            provider="ollama",
            system_prompt="You are a helpful and concise AI assistant.",
            temperature=0.7,
        )
        print(f"✓ Agent created: {agent.name} (ID: {agent.id})")

        # Execute the agent
        print("\nExecuting agent...")
        execution = client.agents.execute(
            agent_id=agent.id,
            user_message="What is the capital of France?",
            context={"language": "English"}
        )
        print(f"✓ Execution completed (ID: {execution.id})")
        print(f"Status: {execution.status}")
        print(f"Response: {execution.response}")

        # Check execution details
        print(f"\nExecution Details:")
        print(f"  Tokens used: {execution.tokens_used}")
        print(f"  Cost: ${execution.cost_usd:.6f}")
        print(f"  Execution time: {execution.execution_time_seconds:.2f}s")

        # List all agents
        print("\nListing all agents...")
        agents = client.agents.list(limit=10)
        print(f"✓ Found {len(agents)} agents:")
        for a in agents:
            print(f"  - {a.name} ({a.model})")

        # Update the agent
        print("\nUpdating agent...")
        updated_agent = client.agents.update(
            agent_id=agent.id,
            description="An updated helpful AI assistant",
            temperature=0.8
        )
        print(f"✓ Agent updated: {updated_agent.description}")

        # Clean up - delete the agent
        print("\nCleaning up...")
        client.agents.delete(agent.id)
        print(f"✓ Agent deleted")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Close the client
        client.close()


if __name__ == "__main__":
    main()
