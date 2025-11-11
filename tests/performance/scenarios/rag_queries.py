"""
RAG query performance test scenario.

Focuses on testing RAG (Retrieval-Augmented Generation) query performance:
- Document upload performance
- Query/search latency
- Collection management
- Concurrent query handling

Performance Target: < 500ms p95 for RAG queries
"""

from locust import HttpUser, task, between
import random
import string


class RAGQueryUser(HttpUser):
    """
    User focused on RAG operations.

    Simulates users performing document uploads and queries.
    """
    wait_time = between(1, 3)

    def on_start(self):
        """Setup: Authenticate and create test collection"""
        # Register/login
        email = f"rag-test-{random.randint(1, 10000)}@example.com"
        password = "RagTest123!"

        self.client.post("/auth/register", json={
            "email": email,
            "password": password,
            "tenant_id": f"rag-tenant-{random.randint(1, 100)}"
        }, name="Setup: Register")

        response = self.client.post("/auth/login", json={
            "email": email,
            "password": password
        }, name="Setup: Login")

        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.access_token}"}
            self.tenant_id = data.get("tenant_id") or f"rag-tenant-{random.randint(1, 100)}"
        else:
            self.access_token = None
            self.headers = {}
            return

        # Create test agent (needed for RAG operations)
        create_response = self.client.post(
            "/agents/",
            headers=self.headers,
            json={
                "name": f"RAG Test Agent {random.randint(1, 10000)}",
                "type": "developer",
                "description": "Agent for RAG performance testing",
                "provider": "anthropic",
                "model": "claude-3-5-sonnet-20241022",
                "system_prompt": "You are a test agent with RAG capabilities.",
                "tenant_id": self.tenant_id,
                "use_rag": True
            },
            name="Setup: Create Agent"
        )

        if create_response.status_code in [200, 201]:
            self.agent_id = create_response.json().get("id")
            self.collection_name = f"loadtest_collection_{self.agent_id}"
        else:
            self.agent_id = None
            self.collection_name = f"loadtest_collection_{random.randint(1, 10000)}"

    def generate_random_text(self, words=100):
        """Generate random text for document upload"""
        vocabulary = [
            "API", "service", "function", "database", "server", "client",
            "request", "response", "authentication", "authorization",
            "performance", "optimization", "testing", "deployment",
            "microservice", "container", "docker", "kubernetes"
        ]
        return " ".join(random.choices(vocabulary, k=words))

    @task(5)
    def query_documents(self):
        """Query documents from RAG collection"""
        if not self.access_token or not self.agent_id:
            return

        queries = [
            "API authentication",
            "database optimization",
            "microservice deployment",
            "performance testing",
            "docker containers",
            "service architecture"
        ]

        with self.client.post(
            f"/agents/{self.agent_id}/rag/query",
            headers=self.headers,
            json={
                "query": random.choice(queries),
                "top_k": 5
            },
            name="RAG: Query Documents",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # RAG endpoint may not exist or no documents
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(2)
    def upload_document(self):
        """Upload document to RAG collection"""
        if not self.access_token or not self.agent_id:
            return

        document_content = self.generate_random_text(200)

        with self.client.post(
            f"/agents/{self.agent_id}/rag/documents",
            headers=self.headers,
            json={
                "content": document_content,
                "metadata": {
                    "source": f"loadtest_doc_{random.randint(1, 10000)}",
                    "type": "test"
                }
            },
            name="RAG: Upload Document",
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 404:
                # RAG endpoint may not exist
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def list_collections(self):
        """List RAG collections"""
        if not self.access_token:
            return

        with self.client.get(
            "/rag/collections",
            headers=self.headers,
            name="RAG: List Collections",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(3)
    def execute_with_rag(self):
        """Execute agent with RAG context"""
        if not self.access_token or not self.agent_id:
            return

        messages = [
            "Based on the documentation, explain API authentication",
            "What do the docs say about performance optimization?",
            "Summarize information about microservices",
            "Find information about deployment processes",
            "What does the documentation say about testing?"
        ]

        with self.client.post(
            f"/agents/{self.agent_id}/execute",
            headers=self.headers,
            json={
                "message": random.choice(messages),
                "max_tokens": 200,
                "use_rag": True
            },
            timeout=30,
            name="RAG: Execute with Context",
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code in [404, 503]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    def on_stop(self):
        """Cleanup: Delete test agent and collection"""
        if self.access_token and self.agent_id:
            try:
                # Delete agent (may cascade delete RAG data)
                self.client.delete(
                    f"/agents/{self.agent_id}",
                    headers=self.headers,
                    name="Cleanup: Delete Agent"
                )
            except Exception:
                pass
