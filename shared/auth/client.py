"""
Shared authentication client for validating JWT tokens and API keys.
Used by all microservices to communicate with the auth service.
"""

import httpx
import hashlib
import jwt
from typing import Optional
from datetime import datetime

from .models import AuthContext


class AuthClient:
    """
    Client to validate authentication with the auth service.
    Supports JWT tokens and API keys with optional Redis caching.
    """

    def __init__(
        self,
        auth_service_url: str = "http://auth:9002",
        jwt_secret: str = "",
        cache=None
    ):
        """
        Initialize auth client.

        Args:
            auth_service_url: URL of the auth service
            jwt_secret: Secret key for JWT validation
            cache: Optional Redis cache instance for token caching
        """
        self.auth_service_url = auth_service_url
        self.jwt_secret = jwt_secret
        self.client = httpx.AsyncClient(timeout=5.0)
        self.cache = cache

    async def verify_token(self, token: str) -> Optional[AuthContext]:
        """
        Verify a JWT token or API key with optional Redis caching.

        Args:
            token: JWT token or API key to verify

        Returns:
            AuthContext if valid, None if invalid

        Cache:
            Key: jwt:{sha256(token)}
            TTL: 30 seconds
        """
        # Generate cache key if caching is enabled
        if self.cache:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            cache_key = f"jwt:{token_hash}"

            # Try to get from cache
            try:
                cached_data = await self.cache.get(cache_key)
                if cached_data:
                    return AuthContext(**cached_data)
            except Exception as e:
                print(f"Cache read error: {e}")

        # Cache miss or no cache - verify token
        auth_context = await self._verify_token_internal(token)

        # Cache the result if valid and caching is enabled
        if auth_context and self.cache:
            try:
                await self.cache.set(cache_key, auth_context.dict(), ttl=30)
            except Exception as e:
                print(f"Cache write error: {e}")

        return auth_context

    async def _verify_token_internal(self, token: str) -> Optional[AuthContext]:
        """Internal token verification without caching"""
        try:
            # Try to decode JWT with signature verification
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"],
                options={"verify_signature": True, "verify_exp": True}
            )

            # Build auth context from JWT payload
            return AuthContext(
                user_id=payload.get("sub", "unknown"),
                tenant_id=payload.get("tenant_id", "unknown"),
                email=payload.get("email", "unknown"),
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
                is_superuser=payload.get("is_superuser", False)
            )

        except jwt.ExpiredSignatureError:
            print("Token has expired")
            return None
        except jwt.InvalidTokenError:
            # If JWT decode fails, might be an API key
            if token.startswith("sk_"):
                return await self._verify_api_key(token)
            return None
        except Exception as e:
            print(f"Token verification error: {e}")
            return None

    async def _verify_api_key(self, api_key: str) -> Optional[AuthContext]:
        """
        Verify API key by calling auth service.

        Args:
            api_key: API key to verify

        Returns:
            AuthContext if valid, None if invalid
        """
        try:
            response = await self.client.get(
                f"{self.auth_service_url}/api-keys/verify",
                headers={"Authorization": f"Bearer {api_key}"}
            )

            if response.status_code == 200:
                data = response.json()
                return AuthContext(**data)

            return None

        except Exception as e:
            print(f"API key verification error: {e}")
            return None

    async def check_permission(self, auth_context: AuthContext, permission: str) -> bool:
        """
        Check if user has a specific permission.

        Args:
            auth_context: Authenticated user context
            permission: Permission to check (e.g., "agents:execute")

        Returns:
            True if user has permission, False otherwise
        """
        if auth_context.is_superuser:
            return True

        return permission in auth_context.permissions

    async def close(self):
        """Close HTTP client connection"""
        await self.client.aclose()
