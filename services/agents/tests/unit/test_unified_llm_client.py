"""
Tests for Unified LLM Client
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import httpx

from app.llm.unified_client import UnifiedLLMClient


class TestUnifiedLLMClientInit:
    """Test UnifiedLLMClient initialization"""

    def test_init_default_values(self):
        """Test initialization with default values"""
        client = UnifiedLLMClient()

        assert client.provider == "ollama"
        assert client.model == "mistral:7b-instruct"
        assert client.temperature == 0.2
        assert client.max_tokens == 4096
        assert client.top_p == 0.9
        assert client.seed == 42
        assert client._initialized is False

    def test_init_ollama_config(self):
        """Test initialization with Ollama configuration"""
        client = UnifiedLLMClient(
            provider="ollama",
            model="llama2:13b",
            ollama_base_url="http://custom-ollama:11434"
        )

        assert client.provider == "ollama"
        assert client.model == "llama2:13b"
        assert client.ollama_base_url == "http://custom-ollama:11434"

    def test_init_claude_config(self):
        """Test initialization with Claude configuration"""
        client = UnifiedLLMClient(
            provider="claude",
            model="claude-sonnet-4-20250514",
            claude_auth_url="https://example.com/auth",
            temperature=0.5,
            max_tokens=8192
        )

        assert client.provider == "claude"
        assert client.model == "claude-sonnet-4-20250514"
        assert client.claude_auth_url == "https://example.com/auth"
        assert client.temperature == 0.5
        assert client.max_tokens == 8192

    def test_init_openai_config(self):
        """Test initialization with OpenAI configuration"""
        client = UnifiedLLMClient(
            provider="openai",
            model="gpt-4",
            openai_api_key="sk-test-key",
            openai_base_url="https://api.openai.com/v1"
        )

        assert client.provider == "openai"
        assert client.model == "gpt-4"
        assert client.openai_api_key == "sk-test-key"
        assert client.openai_base_url == "https://api.openai.com/v1"

    def test_init_custom_parameters(self):
        """Test initialization with custom parameters"""
        client = UnifiedLLMClient(
            temperature=0.8,
            max_tokens=2048,
            top_p=0.95,
            seed=123
        )

        assert client.temperature == 0.8
        assert client.max_tokens == 2048
        assert client.top_p == 0.95
        assert client.seed == 123


class TestUnifiedLLMClientOllama:
    """Test Ollama provider functionality"""

    @pytest.mark.asyncio
    async def test_complete_ollama_success(self):
        """Test successful Ollama completion"""
        # Mock HTTP response
        mock_response = Mock()  # Use Mock, not AsyncMock for response
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={  # json() returns value directly
            "response": "This is a test response from Ollama",
            "prompt_eval_count": 15,
            "eval_count": 25
        })
        mock_response.raise_for_status = Mock()

        # Mock AsyncClient
        with patch('httpx.AsyncClient') as mock_httpx_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_httpx_client.return_value = mock_client_instance

            client = UnifiedLLMClient(provider="ollama", model="mistral:7b")
            result = await client.complete("Test prompt")

            assert result["text"] == "This is a test response from Ollama"
            assert result["usage"]["input_tokens"] == 15
            assert result["usage"]["output_tokens"] == 25
            assert result["model"] == "mistral:7b"

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_complete_ollama_with_system(self, mock_httpx_client):
        """Test Ollama completion with system prompt"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Response",
            "prompt_eval_count": 10,
            "eval_count": 20
        }
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock()
        mock_httpx_client.return_value = mock_client_instance

        client = UnifiedLLMClient(provider="ollama")
        result = await client.complete("Test prompt", system="You are a helpful assistant")

        # Verify system prompt was included in request
        call_args = mock_client_instance.post.call_args
        assert call_args[1]["json"]["system"] == "You are a helpful assistant"

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_complete_ollama_with_overrides(self, mock_httpx_client):
        """Test Ollama completion with temperature and max_tokens overrides"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Response",
            "prompt_eval_count": 10,
            "eval_count": 20
        }
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock()
        mock_httpx_client.return_value = mock_client_instance

        client = UnifiedLLMClient(provider="ollama", temperature=0.2, max_tokens=4096)
        result = await client.complete("Test", temperature=0.8, max_tokens=2048)

        # Verify overrides were used
        call_args = mock_client_instance.post.call_args
        assert call_args[1]["json"]["options"]["temperature"] == 0.8
        assert call_args[1]["json"]["options"]["num_predict"] == 2048


class TestUnifiedLLMClientClaude:
    """Test Claude provider functionality"""

    @pytest.mark.asyncio
    @patch('app.llm.unified_client.ClaudeClientFactory')
    async def test_ensure_initialized_claude_with_auth_url(self, mock_factory):
        """Test Claude initialization with auth URL"""
        mock_claude_client = AsyncMock()
        mock_claude_client.authenticate = AsyncMock()
        mock_factory.from_url_auth.return_value = mock_claude_client

        client = UnifiedLLMClient(
            provider="claude",
            claude_auth_url="https://example.com/auth"
        )

        await client._ensure_initialized()

        assert client._initialized is True
        mock_factory.from_url_auth.assert_called_once_with("https://example.com/auth")
        mock_claude_client.authenticate.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.llm.unified_client.ClaudeClientFactory')
    async def test_ensure_initialized_claude_with_session_token(self, mock_factory):
        """Test Claude initialization with session token"""
        mock_claude_client = AsyncMock()
        mock_claude_client.authenticate = AsyncMock()
        mock_factory.from_session_token.return_value = mock_claude_client

        client = UnifiedLLMClient(
            provider="claude",
            claude_session_token="test-session-token"
        )

        await client._ensure_initialized()

        assert client._initialized is True
        mock_factory.from_session_token.assert_called_once()
        mock_claude_client.authenticate.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_initialized_claude_missing_credentials(self):
        """Test Claude initialization fails without credentials"""
        client = UnifiedLLMClient(provider="claude")

        with pytest.raises(ValueError, match="Claude provider requires either"):
            await client._ensure_initialized()

    @pytest.mark.asyncio
    @patch('app.llm.unified_client.ClaudeClientFactory')
    async def test_complete_claude_success(self, mock_factory):
        """Test successful Claude completion"""
        mock_claude_client = AsyncMock()
        mock_claude_client.authenticate = AsyncMock()
        mock_claude_client.complete = AsyncMock(return_value={
            "text": "This is Claude's response",
            "usage": {"input_tokens": 12, "output_tokens": 30},
            "model": "claude-sonnet-4-20250514"
        })
        mock_factory.from_url_auth.return_value = mock_claude_client

        client = UnifiedLLMClient(
            provider="claude",
            model="claude-sonnet-4-20250514",
            claude_auth_url="https://example.com/auth"
        )

        result = await client.complete("Test prompt")

        assert result["text"] == "This is Claude's response"
        assert result["usage"]["input_tokens"] == 12
        assert result["usage"]["output_tokens"] == 30
        assert result["model"] == "claude-sonnet-4-20250514"

    @pytest.mark.asyncio
    @patch('app.llm.unified_client.ClaudeClientFactory')
    async def test_chat_claude_success(self, mock_factory):
        """Test successful Claude chat"""
        mock_claude_client = AsyncMock()
        mock_claude_client.authenticate = AsyncMock()
        mock_claude_client.chat = AsyncMock(return_value={
            "text": "Chat response",
            "usage": {"input_tokens": 20, "output_tokens": 40},
            "model": "claude-sonnet-4-20250514"
        })
        mock_factory.from_url_auth.return_value = mock_claude_client

        client = UnifiedLLMClient(
            provider="claude",
            claude_auth_url="https://example.com/auth"
        )

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]

        result = await client.chat(messages)

        assert result["text"] == "Chat response"
        mock_claude_client.chat.assert_called_once()


class TestUnifiedLLMClientOpenAI:
    """Test OpenAI provider functionality"""

    @pytest.mark.asyncio
    async def test_complete_openai_success(self):
        """Test successful OpenAI completion"""
        mock_response = Mock()  # Use Mock, not AsyncMock for response
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={  # json() returns value directly
            "choices": [
                {
                    "message": {
                        "content": "This is OpenAI's response"
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 18,
                "completion_tokens": 35
            },
            "model": "gpt-4"
        })
        mock_response.raise_for_status = Mock()

        with patch('httpx.AsyncClient') as mock_httpx_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_httpx_client.return_value = mock_client_instance

            client = UnifiedLLMClient(
                provider="openai",
                model="gpt-4",
                openai_api_key="sk-test-key"
            )

            result = await client.complete("Test prompt")

            assert result["text"] == "This is OpenAI's response"
            assert result["model"] == "gpt-4"
            assert "usage" in result

    @pytest.mark.asyncio
    async def test_complete_openai_missing_api_key(self):
        """Test OpenAI completion fails without API key"""
        client = UnifiedLLMClient(provider="openai")

        with pytest.raises(ValueError, match="OpenAI API key not provided"):
            await client.complete("Test")

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_complete_openai_with_system(self, mock_httpx_client):
        """Test OpenAI completion with system prompt"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}],
            "usage": {},
            "model": "gpt-4"
        }
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock()
        mock_httpx_client.return_value = mock_client_instance

        client = UnifiedLLMClient(
            provider="openai",
            openai_api_key="sk-test"
        )

        await client.complete("Test", system="You are helpful")

        # Verify system message was included
        call_args = mock_client_instance.post.call_args
        messages = call_args[1]["json"]["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are helpful"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Test"

    @pytest.mark.asyncio
    async def test_chat_openai_success(self):
        """Test successful OpenAI chat"""
        mock_response = Mock()  # Use Mock, not AsyncMock for response
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={  # json() returns value directly
            "choices": [{"message": {"content": "Chat response"}}],
            "usage": {},
            "model": "gpt-4"
        })
        mock_response.raise_for_status = Mock()

        with patch('httpx.AsyncClient') as mock_httpx_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_httpx_client.return_value = mock_client_instance

            client = UnifiedLLMClient(
                provider="openai",
                openai_api_key="sk-test"
            )

            messages = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi!"}
            ]

            result = await client.chat(messages)

            assert result["text"] == "Chat response"

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_chat_openai_with_system(self, mock_httpx_client):
        """Test OpenAI chat with system prompt"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}],
            "usage": {},
            "model": "gpt-4"
        }
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock()
        mock_httpx_client.return_value = mock_client_instance

        client = UnifiedLLMClient(
            provider="openai",
            openai_api_key="sk-test"
        )

        messages = [{"role": "user", "content": "Test"}]
        await client.chat(messages, system="Be helpful")

        # Verify system message was prepended
        call_args = mock_client_instance.post.call_args
        sent_messages = call_args[1]["json"]["messages"]
        assert sent_messages[0]["role"] == "system"
        assert sent_messages[0]["content"] == "Be helpful"


class TestUnifiedLLMClientChat:
    """Test chat functionality across providers"""

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_chat_ollama_converts_to_prompt(self, mock_httpx_client):
        """Test Ollama chat converts messages to prompt"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Response",
            "prompt_eval_count": 10,
            "eval_count": 20
        }
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock()
        mock_httpx_client.return_value = mock_client_instance

        client = UnifiedLLMClient(provider="ollama")

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]

        result = await client.chat(messages)

        # Verify messages were converted to prompt
        call_args = mock_client_instance.post.call_args
        prompt = call_args[1]["json"]["prompt"]
        assert "User: Hello" in prompt
        assert "Assistant: Hi there!" in prompt
        assert "How are you?" in prompt
        assert "Assistant:" in prompt  # Prompt for next response


class TestUnifiedLLMClientErrors:
    """Test error handling"""

    @pytest.mark.asyncio
    async def test_complete_unsupported_provider(self):
        """Test error for unsupported provider"""
        client = UnifiedLLMClient(provider="unsupported")  # type: ignore

        with pytest.raises(ValueError, match="Unsupported provider"):
            await client.complete("Test")

    @pytest.mark.asyncio
    async def test_complete_http_error(self):
        """Test handling of HTTP errors"""
        mock_request = Mock()
        mock_request.url = "http://test.com/api/generate"

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error",
            request=mock_request,
            response=mock_response
        )

        with patch('httpx.AsyncClient') as mock_httpx_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_httpx_client.return_value = mock_client_instance

            client = UnifiedLLMClient(provider="ollama")

            with pytest.raises(httpx.HTTPStatusError):
                await client.complete("Test")

    @pytest.mark.asyncio
    @patch('app.llm.unified_client.ClaudeClientFactory')
    async def test_complete_claude_not_initialized(self, mock_factory):
        """Test error when Claude client not initialized"""
        # Simulate initialization failure
        client = UnifiedLLMClient(provider="claude", claude_auth_url="https://test.com")
        client._initialized = True  # Mark as initialized
        client._claude_client = None  # But client is None

        with pytest.raises(ValueError, match="Claude client not initialized"):
            await client.complete("Test")

    @pytest.mark.asyncio
    @patch('app.llm.unified_client.ClaudeClientFactory')
    async def test_chat_claude_not_initialized(self, mock_factory):
        """Test error when Claude client not initialized for chat"""
        client = UnifiedLLMClient(provider="claude", claude_auth_url="https://test.com")
        client._initialized = True
        client._claude_client = None

        with pytest.raises(ValueError, match="Claude client not initialized"):
            await client.chat([{"role": "user", "content": "Test"}])


class TestUnifiedLLMClientReinitialization:
    """Test that initialization only happens once"""

    @pytest.mark.asyncio
    @patch('app.llm.unified_client.ClaudeClientFactory')
    async def test_ensure_initialized_only_once(self, mock_factory):
        """Test that initialization only happens once"""
        mock_claude_client = AsyncMock()
        mock_claude_client.authenticate = AsyncMock()
        mock_factory.from_url_auth.return_value = mock_claude_client

        client = UnifiedLLMClient(
            provider="claude",
            claude_auth_url="https://example.com/auth"
        )

        # Call multiple times
        await client._ensure_initialized()
        await client._ensure_initialized()
        await client._ensure_initialized()

        # Should only initialize once
        mock_factory.from_url_auth.assert_called_once()
        mock_claude_client.authenticate.assert_called_once()
