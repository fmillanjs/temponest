"""
Claude Code CLI Client - Subprocess-based integration with Claude Code CLI.

This client executes the `claude` CLI command via subprocess to leverage
Claude Code subscriptions instead of API tokens.

Note: This approach has performance overhead and limitations compared to
using the Anthropic API directly. See documentation for trade-offs.
"""

import asyncio
import json
import logging
import os
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ClaudeCodeError(Exception):
    """Base exception for Claude Code client errors."""
    pass


class ClaudeCodeTimeoutError(ClaudeCodeError):
    """Raised when Claude Code CLI call times out."""
    pass


class ClaudeCodeAuthError(ClaudeCodeError):
    """Raised when Claude Code authentication fails."""
    pass


class ClaudeCodeClient:
    """
    Client for calling Claude Code CLI via subprocess.

    This client provides a programmatic interface to the Claude Code CLI,
    allowing integration with the TempoNest agent system.

    Features:
    - Subprocess execution with timeout
    - JSON output parsing
    - Error handling and retry logic
    - Token usage estimation
    - Async support

    Limitations:
    - Each call spawns a new process (~2-5s overhead)
    - No conversation state between calls
    - Limited control compared to API
    - Requires Claude Code installation in container
    """

    def __init__(
        self,
        executable: str = "/usr/local/bin/claude",
        timeout: int = 300,
        output_format: str = "json",
        max_retries: int = 2
    ):
        """
        Initialize Claude Code client.

        Args:
            executable: Path to claude CLI executable
            timeout: Timeout in seconds for CLI calls
            output_format: Output format (json, text, markdown)
            max_retries: Maximum number of retries for transient failures
        """
        self.executable = executable
        self.timeout = timeout
        self.output_format = output_format
        self.max_retries = max_retries

        # Verify executable exists
        if not os.path.exists(self.executable):
            logger.warning(
                f"Claude Code executable not found at {self.executable}. "
                "CLI calls will fail until it's installed."
            )

    async def complete(
        self,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a completion request using Claude Code CLI.

        Args:
            prompt: The prompt to send to Claude
            **kwargs: Additional parameters (ignored for CLI)

        Returns:
            Dict with 'text', 'usage', 'model' keys

        Raises:
            ClaudeCodeTimeoutError: If CLI call times out
            ClaudeCodeAuthError: If authentication fails
            ClaudeCodeError: For other errors
        """
        logger.info(f"Calling Claude Code CLI with prompt length: {len(prompt)}")

        # Build CLI command
        command = [
            self.executable,
            "-p",  # Print mode (headless)
            "--output-format", self.output_format
        ]

        # Add prompt as argument
        command.append(prompt)

        # Execute with retry
        for attempt in range(self.max_retries + 1):
            try:
                result = await self._execute_command(command)
                return result
            except ClaudeCodeTimeoutError:
                if attempt < self.max_retries:
                    logger.warning(f"CLI call timed out, retrying ({attempt + 1}/{self.max_retries})...")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise
            except ClaudeCodeAuthError:
                # Don't retry auth errors
                raise
            except ClaudeCodeError as e:
                if attempt < self.max_retries:
                    logger.warning(f"CLI call failed: {e}, retrying ({attempt + 1}/{self.max_retries})...")
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise

    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a chat request using Claude Code CLI.

        Since CLI doesn't support multi-turn conversations natively,
        we convert the message history to a single prompt.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters

        Returns:
            Dict with 'text', 'usage', 'model' keys
        """
        # Convert messages to single prompt
        prompt = self._messages_to_prompt(messages)
        return await self.complete(prompt, **kwargs)

    async def _execute_command(self, command: List[str]) -> Dict[str, Any]:
        """
        Execute the CLI command and parse output.

        Args:
            command: List of command arguments

        Returns:
            Parsed response dict

        Raises:
            ClaudeCodeTimeoutError: If timeout exceeded
            ClaudeCodeAuthError: If auth failed
            ClaudeCodeError: For other errors
        """
        start_time = datetime.now()

        try:
            # Run subprocess with timeout
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise ClaudeCodeTimeoutError(
                    f"CLI call exceeded timeout of {self.timeout}s"
                )

            # Check return code
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace')

                # Check for auth errors
                if "authentication" in error_msg.lower() or "login" in error_msg.lower():
                    raise ClaudeCodeAuthError(
                        f"Authentication failed. Please set CLAUDE_CODE_TOKEN. Error: {error_msg}"
                    )

                raise ClaudeCodeError(
                    f"CLI returned non-zero exit code {process.returncode}: {error_msg}"
                )

            # Parse output
            output_text = stdout.decode('utf-8', errors='replace')

            if self.output_format == "json":
                try:
                    response = json.loads(output_text)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON output: {e}")
                    logger.debug(f"Raw output: {output_text[:500]}")
                    # Fallback to text mode
                    response = {"text": output_text}
            else:
                response = {"text": output_text}

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()

            # Estimate token usage (rough approximation: 1 token ≈ 4 chars)
            estimated_input_tokens = len(' '.join(command)) // 4
            estimated_output_tokens = len(response.get("text", "")) // 4

            # Return standardized format
            return {
                "text": response.get("text", ""),
                "usage": {
                    "input_tokens": estimated_input_tokens,
                    "output_tokens": estimated_output_tokens,
                    "total_tokens": estimated_input_tokens + estimated_output_tokens,
                    "estimated": True  # CLI doesn't return exact counts
                },
                "model": "claude-code-cli",
                "provider": "claude-code",
                "execution_time_seconds": execution_time,
                "raw_response": response
            }

        except ClaudeCodeError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Claude Code CLI: {e}")
            raise ClaudeCodeError(f"Failed to execute CLI: {e}")

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """
        Convert chat messages to a single prompt.

        Args:
            messages: List of message dicts

        Returns:
            Combined prompt string
        """
        prompt_parts = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                prompt_parts.append(f"System: {content}\n")
            elif role == "user":
                prompt_parts.append(f"User: {content}\n")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}\n")

        # Add final instruction for latest user message
        if messages and messages[-1].get("role") == "user":
            prompt_parts.append("\nPlease respond:")

        return "\n".join(prompt_parts)

    def check_availability(self) -> Dict[str, Any]:
        """
        Check if Claude Code CLI is available and working.

        Returns:
            Dict with status information
        """
        try:
            # Try to run --version
            result = subprocess.run(
                [self.executable, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return {
                    "available": True,
                    "executable": self.executable,
                    "version": result.stdout.strip(),
                    "authenticated": self._check_auth()
                }
            else:
                return {
                    "available": False,
                    "executable": self.executable,
                    "error": result.stderr
                }

        except FileNotFoundError:
            return {
                "available": False,
                "executable": self.executable,
                "error": "Executable not found"
            }
        except Exception as e:
            return {
                "available": False,
                "executable": self.executable,
                "error": str(e)
            }

    def _check_auth(self) -> bool:
        """
        Check if Claude Code is authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        # Check if auth token is set
        token = os.environ.get("CLAUDE_CODE_TOKEN")
        if token:
            return True

        # Check if config file exists (would be created by 'claude login')
        config_path = os.path.expanduser("~/.claude/config.json")
        return os.path.exists(config_path)


# Factory function for easy instantiation
def create_claude_code_client(
    executable: Optional[str] = None,
    timeout: Optional[int] = None,
    output_format: Optional[str] = None
) -> ClaudeCodeClient:
    """
    Create a Claude Code client with settings from environment variables.

    Args:
        executable: Override executable path (default from CLAUDE_CODE_EXECUTABLE)
        timeout: Override timeout (default from CLAUDE_CODE_TIMEOUT)
        output_format: Override format (default from CLAUDE_CODE_OUTPUT_FORMAT)

    Returns:
        Configured ClaudeCodeClient instance
    """
    return ClaudeCodeClient(
        executable=executable or os.environ.get("CLAUDE_CODE_EXECUTABLE", "/usr/local/bin/claude"),
        timeout=timeout or int(os.environ.get("CLAUDE_CODE_TIMEOUT", "300")),
        output_format=output_format or os.environ.get("CLAUDE_CODE_OUTPUT_FORMAT", "json")
    )
