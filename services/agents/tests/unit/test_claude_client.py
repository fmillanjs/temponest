"""
Comprehensive unit tests for Claude API client.
Aims to boost coverage from 15% to 85%+
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx


@pytest.mark.unit
class TestClaudeClientInit:
    """Test ClaudeClient initialization"""

    def test_init_with_session_token(self):
        """Test initialization with session token"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient(session_token="sk-ant-test-token-123")

        assert client.session_token == "sk-ant-test-token-123"
        assert client.auth_url is None
        assert client.api_url == "https://api.anthropic.com/v1/messages"
        assert client.anthropic_version == "2023-06-01"
        assert client._authenticated is False

    def test_init_with_auth_url(self):
        """Test initialization with auth URL"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient(auth_url="https://opencode.ai/api/auth")

        assert client.auth_url == "https://opencode.ai/api/auth"
        assert client.session_token is None
        assert client._authenticated is False

    def test_init_with_custom_api_url(self):
        """Test initialization with custom API URL"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient(
            session_token="test-token",
            api_url="https://custom-api.example.com/v1/messages"
        )

        assert client.api_url == "https://custom-api.example.com/v1/messages"

    def test_init_with_custom_version(self):
        """Test initialization with custom Anthropic version"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient(
            session_token="test-token",
            anthropic_version="2024-01-01"
        )

        assert client.anthropic_version == "2024-01-01"

    def test_init_with_all_params(self):
        """Test initialization with all parameters"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient(
            auth_url="https://auth.example.com",
            session_token="token-123",
            api_url="https://api.example.com",
            anthropic_version="2024-06-01"
        )

        assert client.auth_url == "https://auth.example.com"
        assert client.session_token == "token-123"
        assert client.api_url == "https://api.example.com"
        assert client.anthropic_version == "2024-06-01"


@pytest.mark.unit
class TestClaudeClientAuthenticate:
    """Test ClaudeClient authentication"""

    @pytest.mark.asyncio
    async def test_authenticate_with_existing_session_token(self):
        """Test authentication when session token already exists"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient(session_token="sk-ant-existing-token")

        result = await client.authenticate()

        assert result is True
        assert client._authenticated is True
        assert client.session_token == "sk-ant-existing-token"

    @pytest.mark.asyncio
    async def test_authenticate_no_auth_url_or_token(self):
        """Test authentication fails when neither auth_url nor token provided"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient()

        with pytest.raises(ValueError, match="Either auth_url or session_token must be provided"):
            await client.authenticate()

    @pytest.mark.asyncio
    async def test_authenticate_via_url_success(self):
        """Test successful authentication via URL"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient(auth_url="https://auth.example.com/api/auth")

        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "token": "fetched-token-123",
            "expires_at": "2024-12-31"
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_http_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.return_value = mock_response
            mock_http_client.return_value = mock_client_instance

            result = await client.authenticate()

        assert result is True
        assert client._authenticated is True
        assert client.session_token == "fetched-token-123"
        mock_client_instance.get.assert_called_once_with("https://auth.example.com/api/auth")

    @pytest.mark.asyncio
    async def test_authenticate_via_url_session_token_key(self):
        """Test authentication via URL with session_token key"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient(auth_url="https://auth.example.com")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "session_token": "session-token-456"
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_http_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.return_value = mock_response
            mock_http_client.return_value = mock_client_instance

            result = await client.authenticate()

        assert result is True
        assert client.session_token == "session-token-456"

    @pytest.mark.asyncio
    async def test_authenticate_via_url_no_token_in_response(self):
        """Test authentication fails when no token in response"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient(auth_url="https://auth.example.com")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": "Authentication failed"
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_http_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.return_value = mock_response
            mock_http_client.return_value = mock_client_instance

            with pytest.raises(ValueError, match="No token found in auth response"):
                await client.authenticate()

    @pytest.mark.asyncio
    async def test_authenticate_via_url_http_error(self):
        """Test authentication handles HTTP errors"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient(auth_url="https://auth.example.com")

        with patch("httpx.AsyncClient") as mock_http_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.side_effect = httpx.HTTPStatusError(
                "404 Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404)
            )
            mock_http_client.return_value = mock_client_instance

            with pytest.raises(httpx.HTTPStatusError):
                await client.authenticate()


@pytest.mark.unit
class TestClaudeClientComplete:
    """Test ClaudeClient complete() method"""

    @pytest.mark.asyncio
    async def test_complete_success_with_api_key(self):
        """Test successful completion with API key"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient(session_token="sk-ant-api-key-123")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"text": "This is the completion response"}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 10, "output_tokens": 20},
            "model": "claude-sonnet-4-20250514"
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_http_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.post.return_value = mock_response
            mock_http_client.return_value = mock_client_instance

            result = await client.complete(prompt="Hello Claude!")

        assert result["text"] == "This is the completion response"
        assert result["stop_reason"] == "end_turn"
        assert result["usage"]["input_tokens"] == 10
        assert result["usage"]["output_tokens"] == 20

        # Verify API key auth header
        call_args = mock_client_instance.post.call_args
        headers = call_args[1]["headers"]
        assert headers["x-api-key"] == "sk-ant-api-key-123"

    @pytest.mark.asyncio
    async def test_complete_success_with_bearer_token(self):
        """Test successful completion with bearer token"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient(session_token="bearer-token-xyz")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"text": "Response with bearer token"}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 5, "output_tokens": 15}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_http_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.post.return_value = mock_response
            mock_http_client.return_value = mock_client_instance

            result = await client.complete(prompt="Test prompt")

        assert result["text"] == "Response with bearer token"

        # Verify bearer auth header
        call_args = mock_client_instance.post.call_args
        headers = call_args[1]["headers"]
        assert headers["authorization"] == "Bearer bearer-token-xyz"

    @pytest.mark.asyncio
    async def test_complete_with_system_prompt(self):
        """Test completion with system prompt"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient(session_token="test-token")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"text": "Response"}],
            "stop_reason": "end_turn",
            "usage": {}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_http_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.post.return_value = mock_response
            mock_http_client.return_value = mock_client_instance

            await client.complete(
                prompt="User prompt",
                system="You are a helpful assistant"
            )

        # Verify system prompt in request body
        call_args = mock_client_instance.post.call_args
        request_body = call_args[1]["json"]
        assert request_body["system"] == "You are a helpful assistant"

    @pytest.mark.asyncio
    async def test_complete_with_stop_sequences(self):
        """Test completion with stop sequences"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient(session_token="test-token")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"text": "Response"}],
            "stop_reason": "stop_sequence",
            "usage": {}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_http_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.post.return_value = mock_response
            mock_http_client.return_value = mock_client_instance

            await client.complete(
                prompt="Test",
                stop_sequences=["END", "STOP"]
            )

        # Verify stop sequences in request
        call_args = mock_client_instance.post.call_args
        request_body = call_args[1]["json"]
        assert request_body["stop_sequences"] == ["END", "STOP"]

    @pytest.mark.asyncio
    async def test_complete_with_custom_parameters(self):
        """Test completion with custom parameters"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient(session_token="test-token")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"text": "Response"}],
            "stop_reason": "max_tokens",
            "usage": {}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_http_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.post.return_value = mock_response
            mock_http_client.return_value = mock_client_instance

            await client.complete(
                prompt="Test",
                model="claude-opus-4-20250514",
                temperature=0.7,
                max_tokens=8000,
                top_p=0.95
            )

        # Verify parameters
        call_args = mock_client_instance.post.call_args
        request_body = call_args[1]["json"]
        assert request_body["model"] == "claude-opus-4-20250514"
        assert request_body["temperature"] == 0.7
        assert request_body["max_tokens"] == 8000
        assert request_body["top_p"] == 0.95

    @pytest.mark.asyncio
    async def test_complete_authenticates_if_not_authenticated(self):
        """Test complete() calls authenticate() if not authenticated"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient(session_token="test-token")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"text": "Response"}],
            "stop_reason": "end_turn",
            "usage": {}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_http_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.post.return_value = mock_response
            mock_http_client.return_value = mock_client_instance

            assert client._authenticated is False
            await client.complete(prompt="Test")
            assert client._authenticated is True

    @pytest.mark.asyncio
    async def test_complete_fails_without_session_token(self):
        """Test complete() fails if no session token"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient()

        with pytest.raises(ValueError, match="Either auth_url or session_token must be provided"):
            await client.complete(prompt="Test")

    @pytest.mark.asyncio
    async def test_complete_http_status_error(self):
        """Test complete() handles HTTP status errors"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient(session_token="test-token")

        with patch("httpx.AsyncClient") as mock_http_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None

            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Bad request: Invalid model"

            mock_client_instance.post.side_effect = httpx.HTTPStatusError(
                "400 Bad Request",
                request=MagicMock(),
                response=mock_response
            )
            mock_http_client.return_value = mock_client_instance

            with pytest.raises(Exception, match="Claude API error"):
                await client.complete(prompt="Test")

    @pytest.mark.asyncio
    async def test_complete_generic_error(self):
        """Test complete() handles generic errors"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient(session_token="test-token")

        with patch("httpx.AsyncClient") as mock_http_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.post.side_effect = Exception("Network error")
            mock_http_client.return_value = mock_client_instance

            with pytest.raises(Exception, match="Network error"):
                await client.complete(prompt="Test")

    @pytest.mark.asyncio
    async def test_complete_empty_content_response(self):
        """Test complete() handles empty content in response"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient(session_token="test-token")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [],
            "stop_reason": "end_turn",
            "usage": {}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_http_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.post.return_value = mock_response
            mock_http_client.return_value = mock_client_instance

            result = await client.complete(prompt="Test")

        assert result["text"] == ""


@pytest.mark.unit
class TestClaudeClientChat:
    """Test ClaudeClient chat() method"""

    @pytest.mark.asyncio
    async def test_chat_success(self):
        """Test successful chat with message history"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient(session_token="sk-ant-test-key")

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"text": "I'm doing well, thank you!"}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 20, "output_tokens": 10}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_http_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.post.return_value = mock_response
            mock_http_client.return_value = mock_client_instance

            result = await client.chat(messages=messages)

        assert result["text"] == "I'm doing well, thank you!"
        assert result["usage"]["input_tokens"] == 20

        # Verify messages in request
        call_args = mock_client_instance.post.call_args
        request_body = call_args[1]["json"]
        assert request_body["messages"] == messages

    @pytest.mark.asyncio
    async def test_chat_with_system_prompt(self):
        """Test chat with system prompt"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient(session_token="test-token")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"text": "Response"}],
            "stop_reason": "end_turn",
            "usage": {}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_http_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.post.return_value = mock_response
            mock_http_client.return_value = mock_client_instance

            await client.chat(
                messages=[{"role": "user", "content": "Test"}],
                system="You are a coding assistant"
            )

        # Verify system prompt
        call_args = mock_client_instance.post.call_args
        request_body = call_args[1]["json"]
        assert request_body["system"] == "You are a coding assistant"

    @pytest.mark.asyncio
    async def test_chat_authenticates_if_needed(self):
        """Test chat() authenticates if not authenticated"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient(session_token="test-token")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"text": "Response"}],
            "stop_reason": "end_turn",
            "usage": {}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_http_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.post.return_value = mock_response
            mock_http_client.return_value = mock_client_instance

            assert client._authenticated is False
            await client.chat(messages=[{"role": "user", "content": "Hi"}])
            assert client._authenticated is True

    @pytest.mark.asyncio
    async def test_chat_fails_without_token(self):
        """Test chat() fails if no session token"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient()

        with pytest.raises(ValueError):
            await client.chat(messages=[{"role": "user", "content": "Test"}])

    @pytest.mark.asyncio
    async def test_chat_http_error(self):
        """Test chat() handles HTTP errors"""
        from app.llm.claude_client import ClaudeClient

        client = ClaudeClient(session_token="test-token")

        with patch("httpx.AsyncClient") as mock_http_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None

            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.text = "Rate limit exceeded"

            mock_client_instance.post.side_effect = httpx.HTTPStatusError(
                "429 Too Many Requests",
                request=MagicMock(),
                response=mock_response
            )
            mock_http_client.return_value = mock_client_instance

            with pytest.raises(Exception, match="Claude API error"):
                await client.chat(messages=[{"role": "user", "content": "Test"}])


@pytest.mark.unit
class TestClaudeClientFactory:
    """Test ClaudeClientFactory"""

    def test_from_url_auth(self):
        """Test factory method for URL-based auth"""
        from app.llm.claude_client import ClaudeClientFactory

        client = ClaudeClientFactory.from_url_auth("https://auth.example.com")

        assert client.auth_url == "https://auth.example.com"
        assert client.session_token is None

    def test_from_session_token(self):
        """Test factory method for session token"""
        from app.llm.claude_client import ClaudeClientFactory

        client = ClaudeClientFactory.from_session_token("token-123")

        assert client.session_token == "token-123"
        assert client.auth_url is None
        assert client.api_url == "https://api.anthropic.com/v1/messages"

    def test_from_session_token_custom_url(self):
        """Test factory method for session token with custom URL"""
        from app.llm.claude_client import ClaudeClientFactory

        client = ClaudeClientFactory.from_session_token(
            "token-456",
            api_url="https://custom.api.com/v1/messages"
        )

        assert client.session_token == "token-456"
        assert client.api_url == "https://custom.api.com/v1/messages"

    def test_from_api_key(self):
        """Test factory method for API key"""
        from app.llm.claude_client import ClaudeClientFactory

        client = ClaudeClientFactory.from_api_key("sk-ant-api-key-789")

        assert client.session_token == "sk-ant-api-key-789"
        assert client.auth_url is None

    def test_from_api_key_custom_url(self):
        """Test factory method for API key with custom URL"""
        from app.llm.claude_client import ClaudeClientFactory

        client = ClaudeClientFactory.from_api_key(
            "sk-ant-key-999",
            api_url="https://proxy.api.com"
        )

        assert client.session_token == "sk-ant-key-999"
        assert client.api_url == "https://proxy.api.com"
