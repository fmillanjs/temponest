"""
Unit tests for main Temponest SDK client
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from temponest_sdk import TemponestClient
from temponest_sdk.agents import AgentsClient
from temponest_sdk.scheduler import SchedulerClient
from temponest_sdk.rag import RAGClient
from temponest_sdk.collaboration import CollaborationClient
from temponest_sdk.costs import CostsClient
from temponest_sdk.webhooks import WebhooksClient


class TestTemponestClientInitialization:
    """Test Temponest client initialization"""

    def test_init_with_params(self, clean_env):
        """Test initialization with parameters"""
        client = TemponestClient(
            base_url="http://test.com",
            auth_token="test-token"
        )

        assert client._client.base_url == "http://test.com/"
        assert client._client.auth_token == "test-token"
        assert isinstance(client.agents, AgentsClient)
        assert isinstance(client.scheduler, SchedulerClient)
        assert isinstance(client.rag, RAGClient)
        assert isinstance(client.collaboration, CollaborationClient)
        assert isinstance(client.costs, CostsClient)
        assert isinstance(client.webhooks, WebhooksClient)

    def test_init_with_env_vars(self, set_env):
        """Test initialization with environment variables"""
        client = TemponestClient()

        assert client._client.base_url == "http://localhost:9000/"
        assert client._client.auth_token == "test-token"

    def test_context_manager(self, clean_env):
        """Test using client as context manager"""
        with TemponestClient(base_url="http://test.com") as client:
            assert client is not None
            assert isinstance(client.agents, AgentsClient)

    def test_manual_close(self, clean_env):
        """Test manually closing client"""
        client = TemponestClient(base_url="http://test.com")
        client.close()
        # No exception means success
