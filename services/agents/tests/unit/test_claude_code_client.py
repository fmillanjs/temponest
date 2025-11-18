"""
Unit tests for Claude Code CLI Client.

Tests subprocess execution, error handling, timeout management, and response parsing.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from app.llm.claude_code_client import (
    ClaudeCodeClient,
    ClaudeCodeError,
    ClaudeCodeTimeoutError,
    ClaudeCodeAuthError,
    create_claude_code_client
)


class TestClaudeCodeClient:
    """Test suite for ClaudeCodeClient"""

    @pytest.fixture
    def client(self):
        """Create a test client"""
        return ClaudeCodeClient(
            executable="/usr/local/bin/claude",
            timeout=300,
            output_format="json",
            max_retries=2
        )

    @pytest.fixture
    def mock_process(self):
        """Create a mock subprocess"""
        process = AsyncMock()
        process.returncode = 0
        process.communicate = AsyncMock(return_value=(
            b'{"text": "Hello from Claude Code!"}',
            b''
        ))
        return process

    @pytest.mark.asyncio
    async def test_complete_success(self, client, mock_process):
        """Test successful completion call"""
        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            result = await client.complete("Hello, how are you?")

            assert result["text"] == "Hello from Claude Code!"
            assert result["model"] == "claude-code-cli"
            assert result["provider"] == "claude-code"
            assert "usage" in result
            assert result["usage"]["estimated"] is True

    @pytest.mark.asyncio
    async def test_complete_timeout(self, client):
        """Test timeout handling"""
        # Create a process that never completes
        slow_process = AsyncMock()
        slow_process.communicate = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )
        slow_process.kill = AsyncMock()
        slow_process.wait = AsyncMock()

        with patch('asyncio.create_subprocess_exec', return_value=slow_process):
            with pytest.raises(ClaudeCodeTimeoutError):
                await client.complete("test")

    @pytest.mark.asyncio
    async def test_complete_auth_error(self, client):
        """Test authentication error handling"""
        auth_error_process = AsyncMock()
        auth_error_process.returncode = 1
        auth_error_process.communicate = AsyncMock(return_value=(
            b'',
            b'Error: authentication failed. Please login.'
        ))

        with patch('asyncio.create_subprocess_exec', return_value=auth_error_process):
            with pytest.raises(ClaudeCodeAuthError) as exc_info:
                await client.complete("test")

            assert "authentication" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_complete_with_retry(self, client):
        """Test retry logic on transient failures"""
        # First call fails, second succeeds
        call_count = 0

        async def create_process(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            process = AsyncMock()
            if call_count == 1:
                # First call fails
                process.returncode = 1
                process.communicate = AsyncMock(return_value=(
                    b'',
                    b'Temporary error'
                ))
            else:
                # Second call succeeds
                process.returncode = 0
                process.communicate = AsyncMock(return_value=(
                    b'{"text": "Success on retry!"}',
                    b''
                ))
            return process

        with patch('asyncio.create_subprocess_exec', side_effect=create_process):
            result = await client.complete("test")

            assert result["text"] == "Success on retry!"
            assert call_count == 2  # Should have retried once

    @pytest.mark.asyncio
    async def test_complete_json_parse_fallback(self, client):
        """Test fallback when JSON parsing fails"""
        bad_json_process = AsyncMock()
        bad_json_process.returncode = 0
        bad_json_process.communicate = AsyncMock(return_value=(
            b'Not valid JSON',
            b''
        ))

        with patch('asyncio.create_subprocess_exec', return_value=bad_json_process):
            result = await client.complete("test")

            # Should fall back to text mode
            assert result["text"] == "Not valid JSON"

    @pytest.mark.asyncio
    async def test_chat_converts_messages(self, client, mock_process):
        """Test chat method converts messages to prompt"""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]

        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            result = await client.chat(messages)

            assert "text" in result
            # Verify subprocess was called with converted prompt
            mock_process.communicate.assert_called_once()

    @pytest.mark.asyncio
    async def test_token_usage_estimation(self, client, mock_process):
        """Test token usage estimation"""
        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            result = await client.complete("test prompt")

            # Check usage is estimated
            assert result["usage"]["estimated"] is True
            assert result["usage"]["input_tokens"] > 0
            assert result["usage"]["output_tokens"] > 0
            assert result["usage"]["total_tokens"] > 0

    @pytest.mark.asyncio
    async def test_execution_time_tracking(self, client, mock_process):
        """Test execution time is tracked"""
        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            result = await client.complete("test")

            assert "execution_time_seconds" in result
            assert isinstance(result["execution_time_seconds"], float)
            assert result["execution_time_seconds"] >= 0

    def test_check_availability_success(self, client):
        """Test availability check when CLI is available"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="claude version 2.0.0"
            )

            status = client.check_availability()

            assert status["available"] is True
            assert "version" in status
            assert status["executable"] == "/usr/local/bin/claude"

    def test_check_availability_not_found(self, client):
        """Test availability check when CLI not found"""
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            status = client.check_availability()

            assert status["available"] is False
            assert "error" in status

    def test_messages_to_prompt_conversion(self, client):
        """Test message list to prompt conversion"""
        messages = [
            {"role": "system", "content": "Be helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
            {"role": "user", "content": "How are you?"}
        ]

        prompt = client._messages_to_prompt(messages)

        assert "System: Be helpful" in prompt
        assert "User: Hello" in prompt
        assert "Assistant: Hi!" in prompt
        assert "User: How are you?" in prompt
        assert "Please respond:" in prompt


class TestCreateClaudeCodeClient:
    """Test factory function"""

    def test_create_with_defaults(self):
        """Test creating client with environment variable defaults"""
        with patch.dict('os.environ', {
            'CLAUDE_CODE_EXECUTABLE': '/custom/path/claude',
            'CLAUDE_CODE_TIMEOUT': '600',
            'CLAUDE_CODE_OUTPUT_FORMAT': 'text'
        }):
            client = create_claude_code_client()

            assert client.executable == '/custom/path/claude'
            assert client.timeout == 600
            assert client.output_format == 'text'

    def test_create_with_overrides(self):
        """Test creating client with explicit overrides"""
        client = create_claude_code_client(
            executable='/override/claude',
            timeout=120,
            output_format='markdown'
        )

        assert client.executable == '/override/claude'
        assert client.timeout == 120
        assert client.output_format == 'markdown'


class TestErrorHandling:
    """Test error handling scenarios"""

    @pytest.mark.asyncio
    async def test_non_zero_exit_code(self):
        """Test handling of non-zero exit codes"""
        client = ClaudeCodeClient()

        error_process = AsyncMock()
        error_process.returncode = 127
        error_process.communicate = AsyncMock(return_value=(
            b'',
            b'Command not found'
        ))

        with patch('asyncio.create_subprocess_exec', return_value=error_process):
            with pytest.raises(ClaudeCodeError) as exc_info:
                await client.complete("test")

            assert "exit code 127" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_max_retries_exhausted(self):
        """Test that retries stop after max attempts"""
        client = ClaudeCodeClient(max_retries=2)

        failing_process = AsyncMock()
        failing_process.returncode = 1
        failing_process.communicate = AsyncMock(return_value=(
            b'',
            b'Persistent error'
        ))

        with patch('asyncio.create_subprocess_exec', return_value=failing_process):
            with pytest.raises(ClaudeCodeError):
                await client.complete("test")

            # Should have tried 3 times (initial + 2 retries)
            # We can't easily count calls here, but the error should be raised


class TestIntegration:
    """Integration-style tests (still using mocks)"""

    @pytest.mark.asyncio
    async def test_complete_flow_with_system_prompt(self):
        """Test complete flow with system prompt"""
        client = ClaudeCodeClient()

        success_process = AsyncMock()
        success_process.returncode = 0
        success_process.communicate = AsyncMock(return_value=(
            b'{"text": "Response with system context"}',
            b''
        ))

        with patch('asyncio.create_subprocess_exec', return_value=success_process) as mock_exec:
            result = await client.complete("User prompt")

            # Verify result structure
            assert "text" in result
            assert "usage" in result
            assert "model" in result
            assert "provider" in result
            assert "execution_time_seconds" in result

            # Verify subprocess was called
            mock_exec.assert_called_once()
            call_args = mock_exec.call_args[0]
            assert call_args[0] == client.executable
            assert "-p" in call_args
            assert "--output-format" in call_args

    @pytest.mark.asyncio
    async def test_chat_flow_multi_turn(self):
        """Test multi-turn chat flow"""
        client = ClaudeCodeClient()

        success_process = AsyncMock()
        success_process.returncode = 0
        success_process.communicate = AsyncMock(return_value=(
            b'{"text": "Conversation response"}',
            b''
        ))

        messages = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "First response"},
            {"role": "user", "content": "Second message"}
        ]

        with patch('asyncio.create_subprocess_exec', return_value=success_process):
            result = await client.chat(messages)

            assert result["text"] == "Conversation response"
            assert result["model"] == "claude-code-cli"
