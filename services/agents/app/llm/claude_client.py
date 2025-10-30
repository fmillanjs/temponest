"""
Claude API Client with URL-based authentication.

Supports authentication via:
1. Direct session token (from environment)
2. URL-based authentication (like opencode.ai)
"""

import httpx
from typing import Dict, Any, Optional, List
import json


class ClaudeClient:
    """Claude API client with flexible authentication"""

    def __init__(
        self,
        auth_url: Optional[str] = None,
        session_token: Optional[str] = None,
        api_url: str = "https://api.anthropic.com/v1/messages",
        anthropic_version: str = "2023-06-01"
    ):
        """
        Initialize Claude client.

        Args:
            auth_url: URL for authentication (e.g., "https://opencode.ai/api/auth")
            session_token: Pre-authenticated session token
            api_url: Claude API endpoint
            anthropic_version: Anthropic API version
        """
        self.auth_url = auth_url
        self.session_token = session_token
        self.api_url = api_url
        self.anthropic_version = anthropic_version
        self._authenticated = False

    async def authenticate(self) -> bool:
        """
        Authenticate with Claude API.

        If auth_url is provided, fetch session token from URL.
        Otherwise, use existing session_token.

        Returns:
            True if authenticated successfully
        """
        if self.session_token:
            self._authenticated = True
            return True

        if not self.auth_url:
            raise ValueError("Either auth_url or session_token must be provided")

        # Fetch session token from auth URL
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(self.auth_url)
                response.raise_for_status()

                data = response.json()

                # Expected response format: {"token": "...", "expires_at": "..."}
                self.session_token = data.get("token") or data.get("session_token")

                if not self.session_token:
                    raise ValueError(f"No token found in auth response: {data}")

                self._authenticated = True
                print(f"✅ Authenticated with Claude via {self.auth_url}")
                return True

            except Exception as e:
                print(f"❌ Authentication failed: {e}")
                raise

    async def complete(
        self,
        prompt: str,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        top_p: float = 0.9,
        system: Optional[str] = None,
        stop_sequences: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Call Claude API for completion.

        Args:
            prompt: User prompt
            model: Claude model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            system: System prompt
            stop_sequences: Stop sequences

        Returns:
            {
                "text": "completion text",
                "stop_reason": "end_turn",
                "usage": {
                    "input_tokens": 10,
                    "output_tokens": 100
                }
            }
        """
        # Ensure authenticated
        if not self._authenticated:
            await self.authenticate()

        if not self.session_token:
            raise ValueError("Not authenticated. Call authenticate() first.")

        # Build request
        headers = {
            "anthropic-version": self.anthropic_version,
            "content-type": "application/json"
        }

        # Add authentication
        # Support both standard API key and session token
        if self.session_token.startswith("sk-ant-"):
            headers["x-api-key"] = self.session_token
        else:
            headers["authorization"] = f"Bearer {self.session_token}"

        request_body = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        if system:
            request_body["system"] = system

        if stop_sequences:
            request_body["stop_sequences"] = stop_sequences

        # Call API
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=request_body
                )
                response.raise_for_status()

                data = response.json()

                # Extract text from response
                content = data.get("content", [])
                text = ""
                if content and len(content) > 0:
                    text = content[0].get("text", "")

                return {
                    "text": text,
                    "stop_reason": data.get("stop_reason", "unknown"),
                    "usage": data.get("usage", {}),
                    "model": data.get("model", model),
                    "raw_response": data
                }

            except httpx.HTTPStatusError as e:
                error_detail = e.response.text
                print(f"❌ Claude API error: {e.response.status_code} - {error_detail}")
                raise Exception(f"Claude API error: {error_detail}")

            except Exception as e:
                print(f"❌ Claude API request failed: {e}")
                raise

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        top_p: float = 0.9,
        system: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Chat completion with message history.

        Args:
            messages: List of {"role": "user/assistant", "content": "..."}
            model: Claude model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            system: System prompt

        Returns:
            Same as complete()
        """
        # Ensure authenticated
        if not self._authenticated:
            await self.authenticate()

        if not self.session_token:
            raise ValueError("Not authenticated. Call authenticate() first.")

        # Build request
        headers = {
            "anthropic-version": self.anthropic_version,
            "content-type": "application/json"
        }

        # Add authentication
        if self.session_token.startswith("sk-ant-"):
            headers["x-api-key"] = self.session_token
        else:
            headers["authorization"] = f"Bearer {self.session_token}"

        request_body = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "messages": messages
        }

        if system:
            request_body["system"] = system

        # Call API
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=request_body
                )
                response.raise_for_status()

                data = response.json()

                # Extract text from response
                content = data.get("content", [])
                text = ""
                if content and len(content) > 0:
                    text = content[0].get("text", "")

                return {
                    "text": text,
                    "stop_reason": data.get("stop_reason", "unknown"),
                    "usage": data.get("usage", {}),
                    "model": data.get("model", model),
                    "raw_response": data
                }

            except httpx.HTTPStatusError as e:
                error_detail = e.response.text
                print(f"❌ Claude API error: {e.response.status_code} - {error_detail}")
                raise Exception(f"Claude API error: {error_detail}")

            except Exception as e:
                print(f"❌ Claude API request failed: {e}")
                raise


class ClaudeClientFactory:
    """Factory for creating Claude clients with different auth methods"""

    @staticmethod
    def from_url_auth(auth_url: str) -> ClaudeClient:
        """Create client that authenticates via URL"""
        return ClaudeClient(auth_url=auth_url)

    @staticmethod
    def from_session_token(token: str, api_url: str = "https://api.anthropic.com/v1/messages") -> ClaudeClient:
        """Create client with pre-authenticated token"""
        return ClaudeClient(session_token=token, api_url=api_url)

    @staticmethod
    def from_api_key(api_key: str, api_url: str = "https://api.anthropic.com/v1/messages") -> ClaudeClient:
        """Create client with Anthropic API key"""
        return ClaudeClient(session_token=api_key, api_url=api_url)
