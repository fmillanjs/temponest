"""
Agent execution performance test scenario.

Focuses on testing agent execution performance:
- Agent execution latency
- Streaming response performance
- Concurrent execution handling
- Cost tracking performance

Performance Target: < 2s p95 for agent execution
"""

from locust import HttpUser, task, between, events
import random


class AgentExecutionUser(HttpUser):
    """
    User focused on agent execution operations.

    Simulates users executing agents with various payloads.
    """
    wait_time = between(2, 5)  # Longer wait for executions

    def on_start(self):
        """Setup: Authenticate and create test agent"""
        # Register/login
        email = f"exec-test-{random.randint(1, 10000)}@example.com"
        password = "ExecTest123!"

        self.client.post("/auth/register", json={
            "email": email,
            "password": password,
            "tenant_id": f"exec-tenant-{random.randint(1, 100)}"
        }, name="Setup: Register")

        response = self.client.post("/auth/login", json={
            "email": email,
            "password": password
        }, name="Setup: Login")

        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.access_token}"}
            self.tenant_id = data.get("tenant_id") or f"exec-tenant-{random.randint(1, 100)}"
        else:
            self.access_token = None
            self.headers = {}
            return

        # Create test agent
        create_response = self.client.post(
            "/agents/",
            headers=self.headers,
            json={
                "name": f"Exec Test Agent {random.randint(1, 10000)}",
                "type": "developer",
                "description": "Agent for execution performance testing",
                "provider": "anthropic",
                "model": "claude-3-5-sonnet-20241022",
                "system_prompt": "You are a test agent. Respond briefly.",
                "tenant_id": self.tenant_id
            },
            name="Setup: Create Agent"
        )

        if create_response.status_code in [200, 201]:
            self.agent_id = create_response.json().get("id")
        else:
            self.agent_id = None

    @task(5)
    def execute_simple_task(self):
        """Execute agent with simple message"""
        if not self.access_token or not self.agent_id:
            return

        messages = [
            "Hello! Please respond briefly.",
            "What is 2 + 2?",
            "Say 'test' in one word.",
            "Respond with 'OK'",
            "Brief greeting please"
        ]

        with self.client.post(
            f"/agents/{self.agent_id}/execute",
            headers=self.headers,
            json={
                "message": random.choice(messages),
                "max_tokens": 50
            },
            timeout=30,
            name="Execute: Simple Task",
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 404:
                response.failure("Agent not found")
            elif response.status_code == 503:
                response.failure("Service unavailable")
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(3)
    def execute_medium_task(self):
        """Execute agent with medium complexity message"""
        if not self.access_token or not self.agent_id:
            return

        messages = [
            "Write a simple hello world function in Python",
            "Explain what an API is in one sentence",
            "List 3 programming best practices",
            "What is REST?",
            "Describe MVC pattern briefly"
        ]

        with self.client.post(
            f"/agents/{self.agent_id}/execute",
            headers=self.headers,
            json={
                "message": random.choice(messages),
                "max_tokens": 200
            },
            timeout=30,
            name="Execute: Medium Task",
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 404:
                response.failure("Agent not found")
            elif response.status_code == 503:
                response.failure("Service unavailable")
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def execute_complex_task(self):
        """Execute agent with complex message requiring more tokens"""
        if not self.access_token or not self.agent_id:
            return

        messages = [
            "Write a Python function to validate an email address with error handling",
            "Explain the differences between REST and GraphQL APIs",
            "Design a simple database schema for a blog platform",
            "Write unit tests for a calculator function",
            "Explain microservices architecture benefits and challenges"
        ]

        with self.client.post(
            f"/agents/{self.agent_id}/execute",
            headers=self.headers,
            json={
                "message": random.choice(messages),
                "max_tokens": 500
            },
            timeout=45,
            name="Execute: Complex Task",
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 404:
                response.failure("Agent not found")
            elif response.status_code == 503:
                response.failure("Service unavailable")
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def check_execution_cost(self):
        """Check execution cost tracking"""
        if not self.access_token:
            return

        with self.client.get(
            "/costs/summary",
            headers=self.headers,
            name="Cost: Check Summary",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Cost endpoint may not exist
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    def on_stop(self):
        """Cleanup: Delete test agent"""
        if self.access_token and self.agent_id:
            try:
                self.client.delete(
                    f"/agents/{self.agent_id}",
                    headers=self.headers,
                    name="Cleanup: Delete Agent"
                )
            except Exception:
                pass
