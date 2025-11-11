"""
API endpoints performance test scenario.

Focuses on testing general API endpoint performance:
- Authentication endpoints
- CRUD operations
- List/pagination performance
- Health checks
- Error handling performance

Performance Target: < 200ms p95 for API endpoints
"""

from locust import HttpUser, task, between
import random


class APIEndpointUser(HttpUser):
    """
    User focused on general API endpoint operations.

    Simulates typical API usage patterns across all services.
    """
    wait_time = between(0.5, 2)  # Fast operations

    def on_start(self):
        """Setup: Authenticate user"""
        email = f"api-test-{random.randint(1, 10000)}@example.com"
        password = "ApiTest123!"
        self.tenant_id = f"api-tenant-{random.randint(1, 100)}"

        # Register
        self.client.post("/auth/register", json={
            "email": email,
            "password": password,
            "tenant_id": self.tenant_id
        }, name="Setup: Register")

        # Login
        response = self.client.post("/auth/login", json={
            "email": email,
            "password": password
        }, name="Setup: Login")

        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.access_token}"}
            self.user_id = data.get("user_id")
        else:
            self.access_token = None
            self.headers = {}

        self.agent_ids = []
        self.schedule_ids = []

    @task(10)
    def health_check_auth(self):
        """Health check - Auth service"""
        with self.client.get(
            "/health",
            name="Health: Auth",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(10)
    def health_check_agents(self):
        """Health check - Agents service"""
        with self.client.get(
            "http://localhost:9000/health",
            name="Health: Agents",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(10)
    def health_check_scheduler(self):
        """Health check - Scheduler service"""
        with self.client.get(
            "http://localhost:9003/health",
            name="Health: Scheduler",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(8)
    def get_user_info(self):
        """Get current user info"""
        if not self.access_token:
            return

        with self.client.get(
            "/auth/me",
            headers=self.headers,
            name="Auth: Get User Info",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(6)
    def list_agents_paginated(self):
        """List agents with pagination"""
        if not self.access_token:
            return

        page = random.randint(1, 3)
        page_size = random.choice([10, 20, 50])

        with self.client.get(
            f"http://localhost:9000/agents/?page={page}&page_size={page_size}",
            headers=self.headers,
            name="API: List Agents (paginated)",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(6)
    def list_schedules_paginated(self):
        """List schedules with pagination"""
        if not self.access_token:
            return

        page = random.randint(1, 3)
        page_size = random.choice([10, 20, 50])

        with self.client.get(
            f"http://localhost:9003/schedules/?page={page}&page_size={page_size}",
            headers=self.headers,
            name="API: List Schedules (paginated)",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(3)
    def create_agent_fast(self):
        """Create agent (testing create endpoint performance)"""
        if not self.access_token:
            return

        with self.client.post(
            "http://localhost:9000/agents/",
            headers=self.headers,
            json={
                "name": f"API Test Agent {random.randint(1, 100000)}",
                "type": random.choice(["developer", "qa_tester", "designer"]),
                "description": "Fast API test",
                "provider": "anthropic",
                "model": "claude-3-5-sonnet-20241022",
                "system_prompt": "Test",
                "tenant_id": self.tenant_id
            },
            name="API: Create Agent",
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                agent_id = response.json().get("id")
                if agent_id:
                    self.agent_ids.append(agent_id)
                response.success()
            else:
                response.failure(f"Create failed: {response.status_code}")

    @task(2)
    def get_agent_by_id(self):
        """Get agent by ID"""
        if not self.access_token or not self.agent_ids:
            return

        agent_id = random.choice(self.agent_ids)

        with self.client.get(
            f"http://localhost:9000/agents/{agent_id}",
            headers=self.headers,
            name="API: Get Agent by ID",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Remove from list
                self.agent_ids.remove(agent_id)
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(2)
    def create_schedule_fast(self):
        """Create schedule (testing create endpoint performance)"""
        if not self.access_token or not self.agent_ids:
            return

        agent_id = random.choice(self.agent_ids)

        with self.client.post(
            "http://localhost:9003/schedules/",
            headers=self.headers,
            json={
                "name": f"API Test Schedule {random.randint(1, 100000)}",
                "agent_id": agent_id,
                "cron_expression": "0 0 * * *",
                "task_payload": {},
                "is_active": False,
                "tenant_id": self.tenant_id
            },
            name="API: Create Schedule",
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                schedule_id = response.json().get("id")
                if schedule_id:
                    self.schedule_ids.append(schedule_id)
                response.success()
            else:
                response.failure(f"Create failed: {response.status_code}")

    @task(1)
    def delete_agent(self):
        """Delete agent (testing delete endpoint performance)"""
        if not self.access_token or not self.agent_ids:
            return

        agent_id = self.agent_ids.pop(0) if self.agent_ids else None
        if not agent_id:
            return

        with self.client.delete(
            f"http://localhost:9000/agents/{agent_id}",
            headers=self.headers,
            name="API: Delete Agent",
            catch_response=True
        ) as response:
            if response.status_code in [200, 204]:
                response.success()
            elif response.status_code == 404:
                response.success()
            else:
                response.failure(f"Delete failed: {response.status_code}")

    @task(1)
    def delete_schedule(self):
        """Delete schedule (testing delete endpoint performance)"""
        if not self.access_token or not self.schedule_ids:
            return

        schedule_id = self.schedule_ids.pop(0) if self.schedule_ids else None
        if not schedule_id:
            return

        with self.client.delete(
            f"http://localhost:9003/schedules/{schedule_id}",
            headers=self.headers,
            name="API: Delete Schedule",
            catch_response=True
        ) as response:
            if response.status_code in [200, 204]:
                response.success()
            elif response.status_code == 404:
                response.success()
            else:
                response.failure(f"Delete failed: {response.status_code}")

    @task(2)
    def test_invalid_request(self):
        """Test error handling performance (invalid requests)"""
        if not self.access_token:
            return

        # Invalid agent creation (empty name)
        with self.client.post(
            "http://localhost:9000/agents/",
            headers=self.headers,
            json={
                "name": "",
                "type": "invalid",
                "tenant_id": self.tenant_id
            },
            name="API: Error Handling (400)",
            catch_response=True
        ) as response:
            if response.status_code in [400, 422]:
                response.success()  # Expected error
            else:
                response.failure(f"Expected validation error, got: {response.status_code}")

    @task(2)
    def test_not_found(self):
        """Test not found error handling performance"""
        if not self.access_token:
            return

        fake_id = "00000000-0000-0000-0000-000000000000"

        with self.client.get(
            f"http://localhost:9000/agents/{fake_id}",
            headers=self.headers,
            name="API: Error Handling (404)",
            catch_response=True
        ) as response:
            if response.status_code == 404:
                response.success()  # Expected error
            else:
                response.failure(f"Expected 404, got: {response.status_code}")

    def on_stop(self):
        """Cleanup: Delete all created resources"""
        if not self.access_token:
            return

        # Delete remaining schedules
        for schedule_id in self.schedule_ids:
            try:
                self.client.delete(
                    f"http://localhost:9003/schedules/{schedule_id}",
                    headers=self.headers,
                    name="Cleanup: Delete Schedule"
                )
            except Exception:
                pass

        # Delete remaining agents
        for agent_id in self.agent_ids:
            try:
                self.client.delete(
                    f"http://localhost:9000/agents/{agent_id}",
                    headers=self.headers,
                    name="Cleanup: Delete Agent"
                )
            except Exception:
                pass
