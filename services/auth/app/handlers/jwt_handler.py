"""
JWT token generation and validation.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from uuid import UUID, uuid4
from app.settings import settings


class JWTHandler:
    """Handles JWT token creation and validation"""

    @staticmethod
    def create_access_token(
        user_id: UUID,
        tenant_id: UUID,
        email: str,
        roles: list[str],
        permissions: list[str],
        is_superuser: bool = False
    ) -> str:
        """Create JWT access token"""
        expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        now = datetime.now(timezone.utc)
        expire = now + expires_delta

        payload = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "email": email,
            "roles": roles,
            "permissions": permissions,
            "is_superuser": is_superuser,
            "exp": expire,
            "iat": now,
            "jti": str(uuid4()),  # Unique token identifier
            "type": "access"
        }

        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def create_refresh_token(user_id: UUID, tenant_id: UUID) -> str:
        """Create JWT refresh token"""
        expires_delta = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        now = datetime.now(timezone.utc)
        expire = now + expires_delta

        payload = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "exp": expire,
            "iat": now,
            "jti": str(uuid4()),  # Unique token identifier
            "type": "refresh"
        }

        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def verify_token(token: str, expected_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token.
        Returns payload if valid, None if invalid.
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )

            # Check token type
            if payload.get("type") != expected_type:
                return None

            # Check expiration (jose library does this automatically)
            return payload

        except JWTError as e:
            print(f"JWT verification failed: {e}")
            return None

    @staticmethod
    def decode_token_unsafe(token: str) -> Optional[Dict[str, Any]]:
        """
        Decode token without verification (for debugging/logging).
        DO NOT use for authentication!
        """
        try:
            return jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_signature": False, "verify_exp": False}
            )
        except JWTError:
            return None
