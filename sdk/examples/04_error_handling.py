"""
Example 4: Error Handling

This example demonstrates how to:
1. Handle different types of SDK exceptions
2. Implement retry logic
3. Handle rate limiting
"""

from temponest_sdk import TemponestClient
from temponest_sdk.exceptions import (
    AgentNotFoundError,
    ValidationError,
    RateLimitError,
    AuthenticationError,
    ServerError,
    TemponestAPIError,
)
import time


def execute_with_retry(client, agent_id, message, max_retries=3):
    """Execute agent with retry logic"""
    for attempt in range(max_retries):
        try:
            result = client.agents.execute(
                agent_id=agent_id,
                user_message=message
            )
            return result

        except RateLimitError as e:
            if e.retry_after:
                print(f"Rate limited. Retrying after {e.retry_after}s...")
                time.sleep(e.retry_after)
            else:
                print(f"Rate limited. Retrying in {2 ** attempt}s...")
                time.sleep(2 ** attempt)

        except ServerError as e:
            if attempt < max_retries - 1:
                print(f"Server error. Retrying (attempt {attempt + 1}/{max_retries})...")
                time.sleep(2 ** attempt)
            else:
                raise

    raise Exception("Max retries exceeded")


def main():
    client = TemponestClient(base_url="http://localhost:9000")

    try:
        # Example 1: Handle agent not found
        print("Example 1: Agent Not Found")
        try:
            agent = client.agents.get("non-existent-id")
        except AgentNotFoundError as e:
            print(f"✓ Caught AgentNotFoundError: {e}")

        # Example 2: Handle validation errors
        print("\nExample 2: Validation Error")
        try:
            agent = client.agents.create(
                name="",  # Invalid: empty name
                model="llama3.2:latest"
            )
        except ValidationError as e:
            print(f"✓ Caught ValidationError: {e}")

        # Example 3: Handle authentication errors
        print("\nExample 3: Authentication Error")
        try:
            bad_client = TemponestClient(
                base_url="http://localhost:9000",
                auth_token="invalid-token"
            )
            agents = bad_client.agents.list()
        except AuthenticationError as e:
            print(f"✓ Caught AuthenticationError: {e}")
        finally:
            bad_client.close()

        # Example 4: Create a valid agent for retry testing
        print("\nExample 4: Retry Logic")
        agent = client.agents.create(
            name="RetryTestAgent",
            model="llama3.2:latest"
        )
        print(f"✓ Created agent: {agent.id}")

        try:
            result = execute_with_retry(
                client,
                agent_id=agent.id,
                message="Hello!",
                max_retries=3
            )
            print(f"✓ Execution succeeded: {result.status}")
        except Exception as e:
            print(f"✗ Execution failed after retries: {e}")

        # Clean up
        client.agents.delete(agent.id)

        # Example 5: Generic error handling
        print("\nExample 5: Generic Error Handling")
        try:
            # Try to get a non-existent agent
            client.agents.get("bad-id")
        except TemponestAPIError as e:
            # This will catch any API error
            print(f"✓ Caught TemponestAPIError: {e}")
            print(f"  Status code: {e.status_code}")
            print(f"  Message: {e.message}")

    except Exception as e:
        print(f"Unexpected error: {e}")

    finally:
        client.close()


if __name__ == "__main__":
    main()
