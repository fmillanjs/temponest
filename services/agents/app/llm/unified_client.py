"""
Unified LLM Client - supports Ollama, Claude, and OpenAI.

Automatically selects the correct provider based on configuration.
"""

import httpx
from typing import Dict, Any, Optional, List, Literal
from .claude_client import ClaudeClient, ClaudeClientFactory


class UnifiedLLMClient:
    """
    Unified client that works with multiple LLM providers.

    Usage:
        client = UnifiedLLMClient(
            provider="claude",
            model="claude-sonnet-4-20250514",
            claude_auth_url="https://opencode.ai/api/auth"
        )

        response = await client.complete("Write a function...")
    """

    def __init__(
        self,
        provider: Literal["ollama", "claude", "openai"] = "ollama",
        model: str = "mistral:7b-instruct",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        top_p: float = 0.9,
        seed: int = 42,
        # Ollama config
        ollama_base_url: str = "http://ollama:11434",
        # Claude config
        claude_auth_url: Optional[str] = None,
        claude_session_token: Optional[str] = None,
        claude_api_url: str = "https://api.anthropic.com/v1/messages",
        # OpenAI config
        openai_api_key: Optional[str] = None,
        openai_base_url: str = "https://api.openai.com/v1"
    ):
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.seed = seed

        # Store config
        self.ollama_base_url = ollama_base_url
        self.claude_auth_url = claude_auth_url
        self.claude_session_token = claude_session_token
        self.claude_api_url = claude_api_url
        self.openai_api_key = openai_api_key
        self.openai_base_url = openai_base_url

        # Initialize provider-specific clients
        self._claude_client: Optional[ClaudeClient] = None
        self._initialized = False

    async def _ensure_initialized(self):
        """Initialize provider-specific clients if needed"""
        if self._initialized:
            return

        if self.provider == "claude":
            # Initialize Claude client
            if self.claude_auth_url:
                self._claude_client = ClaudeClientFactory.from_url_auth(self.claude_auth_url)
            elif self.claude_session_token:
                self._claude_client = ClaudeClientFactory.from_session_token(
                    self.claude_session_token,
                    self.claude_api_url
                )
            else:
                raise ValueError("Claude provider requires either claude_auth_url or claude_session_token")

            # Authenticate
            await self._claude_client.authenticate()

        self._initialized = True

    async def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate completion from prompt.

        Args:
            prompt: User prompt
            system: System prompt (optional)
            temperature: Override default temperature
            max_tokens: Override default max_tokens

        Returns:
            {
                "text": "generated text",
                "usage": {"input_tokens": 10, "output_tokens": 100},
                "model": "model-name"
            }
        """
        await self._ensure_initialized()

        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens

        if self.provider == "ollama":
            return await self._complete_ollama(prompt, system, temp, max_tok)
        elif self.provider == "claude":
            return await self._complete_claude(prompt, system, temp, max_tok)
        elif self.provider == "openai":
            return await self._complete_openai(prompt, system, temp, max_tok)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def _complete_ollama(
        self,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Complete using Ollama"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            request_body = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": self.top_p,
                    "num_predict": max_tokens,
                    "seed": self.seed
                }
            }

            if system:
                request_body["system"] = system

            response = await client.post(
                f"{self.ollama_base_url}/api/generate",
                json=request_body
            )
            response.raise_for_status()

            data = response.json()

            return {
                "text": data.get("response", ""),
                "usage": {
                    "input_tokens": data.get("prompt_eval_count", 0),
                    "output_tokens": data.get("eval_count", 0)
                },
                "model": self.model
            }

    async def _complete_claude(
        self,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Complete using Claude"""
        if not self._claude_client:
            raise ValueError("Claude client not initialized")

        result = await self._claude_client.complete(
            prompt=prompt,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=self.top_p,
            system=system
        )

        return {
            "text": result["text"],
            "usage": result["usage"],
            "model": result["model"]
        }

    async def _complete_openai(
        self,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Complete using OpenAI"""
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not provided")

        async with httpx.AsyncClient(timeout=120.0) as client:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            request_body = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": self.top_p,
                "seed": self.seed
            }

            response = await client.post(
                f"{self.openai_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                },
                json=request_body
            )
            response.raise_for_status()

            data = response.json()

            return {
                "text": data["choices"][0]["message"]["content"],
                "usage": data.get("usage", {}),
                "model": data["model"]
            }

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Chat completion with message history.

        Args:
            messages: List of {"role": "user/assistant", "content": "..."}
            system: System prompt
            temperature: Override default
            max_tokens: Override default

        Returns:
            Same as complete()
        """
        await self._ensure_initialized()

        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens

        if self.provider == "claude":
            if not self._claude_client:
                raise ValueError("Claude client not initialized")

            return await self._claude_client.chat(
                messages=messages,
                model=self.model,
                temperature=temp,
                max_tokens=max_tok,
                top_p=self.top_p,
                system=system
            )

        elif self.provider == "openai":
            if not self.openai_api_key:
                raise ValueError("OpenAI API key not provided")

            async with httpx.AsyncClient(timeout=120.0) as client:
                msgs = messages.copy()
                if system:
                    msgs.insert(0, {"role": "system", "content": system})

                request_body = {
                    "model": self.model,
                    "messages": msgs,
                    "temperature": temp,
                    "max_tokens": max_tok,
                    "top_p": self.top_p,
                    "seed": self.seed
                }

                response = await client.post(
                    f"{self.openai_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json=request_body
                )
                response.raise_for_status()

                data = response.json()

                return {
                    "text": data["choices"][0]["message"]["content"],
                    "usage": data.get("usage", {}),
                    "model": data["model"]
                }

        else:
            # For Ollama, convert to single prompt
            prompt_parts = []
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                prompt_parts.append(f"{role.capitalize()}: {content}")

            prompt = "\n\n".join(prompt_parts) + "\n\nAssistant:"

            return await self._complete_ollama(prompt, system, temp, max_tok)
