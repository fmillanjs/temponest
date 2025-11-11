"""
Locust performance test suite for TempoNest platform.

Usage:
    # Run with Web UI
    locust -f tests/performance/locustfile.py --host=http://localhost:9002

    # Run headless with 100 users, 10 spawn rate for 5 minutes
    locust -f tests/performance/locustfile.py --host=http://localhost:9002 \
           --users 100 --spawn-rate 10 --run-time 5m --headless

    # Generate HTML report
    locust -f tests/performance/locustfile.py --host=http://localhost:9002 \
           --users 100 --spawn-rate 10 --run-time 5m --headless \
           --html=tests/performance/reports/performance_report.html

Performance Targets:
    - Agent execution: < 2s p95
    - RAG query: < 500ms p95
    - API endpoints: < 200ms p95
    - Concurrent users: 100+
"""

from locust import HttpUser, task, between, events
import random
import json
import time
from datetime import datetime


class TempoNestUser(HttpUser):
    """
    Simulates a TempoNest platform user performing various operations.

    Tasks are weighted by frequency:
    - High frequency: List agents/schedules (3x)
    - Medium frequency: Get agent details (2x)
    - Low frequency: Create/execute agents (1x)
    """
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """
        Called when a user starts. Authenticates and sets up user session.
        """
        # Register/login user
        email = f"loadtest-{random.randint(1, 10000)}@example.com"
        password = "LoadTest123!"

        # Try to register (may already exist)
        self.client.post("/auth/register", json={
            "email": email,
            "password": password,
            "tenant_id": f"loadtest-tenant-{random.randint(1, 100)}"
        }, name="/auth/register (setup)")

        # Login to get token
        response = self.client.post("/auth/login", json={
            "email": email,
            "password": password
        }, name="/auth/login (setup)")

        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.access_token}"}
            self.user_id = data.get("user_id")
            self.tenant_id = data.get("tenant_id") or f"loadtest-tenant-{random.randint(1, 100)}"
        else:
            self.access_token = None
            self.headers = {}
            self.user_id = None
            self.tenant_id = f"loadtest-tenant-{random.randint(1, 100)}"

        # Store agent ID for later use
        self.agent_id = None
        self.schedule_id = None

    @task(3)
    def list_agents(self):
        """List agents (high frequency operation)"""
        if not self.access_token:
            return

        with self.client.get(
            "/agents/",
            headers=self.headers,
            name="/agents/ (list)",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(2)
    def get_agent_details(self):
        """Get agent details (medium frequency operation)"""
        if not self.access_token or not self.agent_id:
            return

        with self.client.get(
            f"/agents/{self.agent_id}",
            headers=self.headers,
            name="/agents/{id} (get)",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Agent might have been deleted
                self.agent_id = None
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def create_agent(self):
        """Create an agent (low frequency operation)"""
        if not self.access_token:
            return

        agent_types = ["developer", "qa_tester", "designer", "devops"]

        with self.client.post(
            "/agents/",
            headers=self.headers,
            json={
                "name": f"LoadTest Agent {random.randint(1, 10000)}",
                "type": random.choice(agent_types),
                "description": "Performance test agent",
                "provider": "anthropic",
                "model": "claude-3-5-sonnet-20241022",
                "system_prompt": "You are a test agent for load testing.",
                "tenant_id": self.tenant_id
            },
            name="/agents/ (create)",
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                data = response.json()
                self.agent_id = data.get("id")
                response.success()
            else:
                response.failure(f"Failed to create agent: {response.status_code}")

    @task(3)
    def list_schedules(self):
        """List schedules (high frequency operation)"""
        if not self.access_token:
            return

        with self.client.get(
            "/schedules/",
            headers=self.headers,
            name="/schedules/ (list)",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(2)
    def get_schedule_details(self):
        """Get schedule details (medium frequency operation)"""
        if not self.access_token or not self.schedule_id:
            return

        with self.client.get(
            f"/schedules/{self.schedule_id}",
            headers=self.headers,
            name="/schedules/{id} (get)",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Schedule might have been deleted
                self.schedule_id = None
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def create_schedule(self):
        """Create a schedule (low frequency operation)"""
        if not self.access_token or not self.agent_id:
            # Need an agent first
            return

        cron_expressions = [
            "0 0 * * *",     # Daily at midnight
            "*/15 * * * *",  # Every 15 minutes
            "0 */6 * * *",   # Every 6 hours
            "0 9 * * 1-5"    # Weekdays at 9am
        ]

        with self.client.post(
            "/schedules/",
            headers=self.headers,
            json={
                "name": f"LoadTest Schedule {random.randint(1, 10000)}",
                "agent_id": self.agent_id,
                "cron_expression": random.choice(cron_expressions),
                "task_payload": {"test": "load test payload"},
                "is_active": False,  # Don't actually run
                "tenant_id": self.tenant_id
            },
            name="/schedules/ (create)",
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                data = response.json()
                self.schedule_id = data.get("id")
                response.success()
            else:
                response.failure(f"Failed to create schedule: {response.status_code}")

    @task(1)
    def health_check(self):
        """Health check endpoint (low frequency)"""
        with self.client.get(
            "/health",
            name="/health",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    def on_stop(self):
        """
        Called when a user stops. Cleanup resources.
        """
        # Cleanup: delete created resources
        if self.access_token and self.schedule_id:
            try:
                self.client.delete(
                    f"/schedules/{self.schedule_id}",
                    headers=self.headers,
                    name="/schedules/{id} (cleanup)"
                )
            except Exception:
                pass

        if self.access_token and self.agent_id:
            try:
                self.client.delete(
                    f"/agents/{self.agent_id}",
                    headers=self.headers,
                    name="/agents/{id} (cleanup)"
                )
            except Exception:
                pass


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the test starts"""
    print(f"\n{'='*60}")
    print(f"TempoNest Performance Test Started")
    print(f"Host: {environment.host}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the test stops"""
    print(f"\n{'='*60}")
    print(f"TempoNest Performance Test Completed")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # Print summary statistics
    stats = environment.stats
    total_stats = stats.total

    print(f"Total Requests: {total_stats.num_requests}")
    print(f"Failed Requests: {total_stats.num_failures}")
    print(f"Average Response Time: {total_stats.avg_response_time:.2f}ms")
    print(f"Median Response Time: {total_stats.median_response_time:.2f}ms")
    print(f"95th Percentile: {total_stats.get_response_time_percentile(0.95):.2f}ms")
    print(f"99th Percentile: {total_stats.get_response_time_percentile(0.99):.2f}ms")
    print(f"Requests/sec: {total_stats.total_rps:.2f}")
    print(f"\n{'='*60}\n")
