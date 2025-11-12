"""
Authentication client for scheduler service.
Validates JWT tokens and API keys by calling the auth service.
"""

import httpx
from typing import Optional, List
from pydantic import BaseModel


class AuthContext(BaseModel):
    """Authenticated user context"""
    user_id: str
    tenant_id: str
    email: str
    roles: List[str]
    permissions: List[str]
    is_superuser: bool


class AuthClient:
    """Client to validate authentication with the auth service"""

    def __init__(self, auth_service_url: str = "http://auth:9002", jwt_secret: str = ""):
        self.auth_service_url = auth_service_url
        self.jwt_secret = jwt_secret
        self.client = httpx.AsyncClient(timeout=5.0)

    async def verify_token(self, token: str) -> Optional[AuthContext]:
        """
        Verify a JWT token or API key with the auth service.
        Returns AuthContext if valid, None if invalid.
        """
        try:
            # Try to decode JWT with signature verification
            import jwt
            from datetime import datetime

            # Verify JWT signature and expiration
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
            # API keys start with "sk_"
            if token.startswith("sk_"):
                # Call auth service to validate API key
                return await self._verify_api_key(token)
            return None
        except Exception as e:
            print(f"Token verification error: {e}")
            return None

    async def _verify_api_key(self, api_key: str) -> Optional[AuthContext]:
        """Verify API key by calling auth service"""
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
        """Check if user has a specific permission"""
        if auth_context.is_superuser:
            return True

        return permission in auth_context.permissions

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
