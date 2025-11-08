"""
API Key generation and validation.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID
from app.settings import settings
from app.database import db


class APIKeyHandler:
    """Handles API key generation and validation"""

    @staticmethod
    def generate_api_key() -> Tuple[str, str, str]:
        """
        Generate a new API key.
        Returns: (full_key, key_hash, key_prefix)
        """
        # Generate random key
        random_bytes = secrets.token_bytes(32)
        key_suffix = random_bytes.hex()

        # Full key with prefix
        full_key = f"{settings.API_KEY_PREFIX}{key_suffix}"

        # Hash for storage
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()

        # Prefix for identification (first 12 chars)
        key_prefix = full_key[:12]

        return full_key, key_hash, key_prefix

    @staticmethod
    async def create_api_key(
        name: str,
        tenant_id: UUID,
        user_id: Optional[UUID],
        scopes: list[str],
        expires_in_days: Optional[int] = None
    ) -> Tuple[UUID, str]:
        """
        Create and store a new API key.
        Returns: (api_key_id, full_key)
        """
        full_key, key_hash, key_prefix = APIKeyHandler.generate_api_key()

        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        api_key_id = await db.fetchval(
            """
            INSERT INTO api_keys (
                key_hash, key_prefix, name, tenant_id, user_id,
                scopes, expires_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
            """,
            key_hash, key_prefix, name, str(tenant_id),
            str(user_id) if user_id else None,
            scopes, expires_at
        )

        return api_key_id, full_key

    @staticmethod
    async def validate_api_key(api_key: str) -> Optional[dict]:
        """
        Validate an API key and return associated data.
        Returns None if invalid.
        """
        # Hash the provided key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Look up key in database
        row = await db.fetchrow(
            """
            SELECT
                ak.id,
                ak.tenant_id,
                ak.user_id,
                ak.scopes,
                ak.expires_at,
                t.name as tenant_name,
                u.email as user_email,
                u.is_superuser
            FROM api_keys ak
            JOIN tenants t ON ak.tenant_id = t.id
            LEFT JOIN users u ON ak.user_id = u.id
            WHERE ak.key_hash = $1
              AND ak.is_active = true
              AND t.is_active = true
              AND (ak.expires_at IS NULL OR ak.expires_at > CURRENT_TIMESTAMP)
            """,
            key_hash
        )

        if not row:
            return None

        # Update last_used_at
        await db.execute(
            "UPDATE api_keys SET last_used_at = CURRENT_TIMESTAMP WHERE id = $1",
            row["id"]
        )

        # Convert UUIDs to strings for consistent API responses
        result = dict(row)
        result["id"] = str(result["id"])
        result["tenant_id"] = str(result["tenant_id"])
        if result["user_id"]:
            result["user_id"] = str(result["user_id"])

        return result

    @staticmethod
    async def revoke_api_key(api_key_id: UUID):
        """Revoke an API key"""
        await db.execute(
            "UPDATE api_keys SET is_active = false WHERE id = $1",
            str(api_key_id)
        )

    @staticmethod
    async def list_api_keys(tenant_id: UUID) -> list[dict]:
        """List all API keys for a tenant"""
        rows = await db.fetch(
            """
            SELECT
                id,
                key_prefix,
                name,
                scopes,
                expires_at,
                last_used_at,
                created_at,
                is_active
            FROM api_keys
            WHERE tenant_id = $1
            ORDER BY created_at DESC
            """,
            str(tenant_id)
        )
        return [dict(row) for row in rows]
