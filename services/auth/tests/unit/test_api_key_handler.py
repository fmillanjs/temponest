"""
Unit tests for APIKeyHandler.

Tests API key generation and validation logic (database-independent parts).
"""

import pytest
import hashlib
from uuid import uuid4
from app.handlers.api_key import APIKeyHandler
from app.settings import settings


@pytest.mark.unit
class TestAPIKeyGeneration:
    """Test API key generation logic"""

    def test_generate_api_key_returns_tuple(self):
        """Test that generate_api_key returns a tuple"""
        result = APIKeyHandler.generate_api_key()

        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_generate_api_key_format(self):
        """Test that generated API key has correct format"""
        full_key, key_hash, key_prefix = APIKeyHandler.generate_api_key()

        # Check full key format
        assert isinstance(full_key, str)
        assert full_key.startswith(settings.API_KEY_PREFIX)
        assert len(full_key) > len(settings.API_KEY_PREFIX)

        # Check hash format (SHA256 = 64 hex chars)
        assert isinstance(key_hash, str)
        assert len(key_hash) == 64
        assert all(c in "0123456789abcdef" for c in key_hash)

        # Check prefix format
        assert isinstance(key_prefix, str)
        assert len(key_prefix) == 12
        assert key_prefix == full_key[:12]

    def test_generate_api_key_unique(self):
        """Test that generated API keys are unique"""
        key1, hash1, prefix1 = APIKeyHandler.generate_api_key()
        key2, hash2, prefix2 = APIKeyHandler.generate_api_key()

        assert key1 != key2
        assert hash1 != hash2
        # Prefix might collide but very unlikely
        # assert prefix1 != prefix2  # Optional check

    def test_generate_api_key_hash_matches(self):
        """Test that the hash matches the full key"""
        full_key, key_hash, key_prefix = APIKeyHandler.generate_api_key()

        # Manually compute hash and verify
        expected_hash = hashlib.sha256(full_key.encode()).hexdigest()

        assert key_hash == expected_hash

    def test_generate_api_key_multiple_times(self):
        """Test generating multiple API keys in sequence"""
        keys = []
        hashes = []

        for _ in range(10):
            full_key, key_hash, key_prefix = APIKeyHandler.generate_api_key()
            keys.append(full_key)
            hashes.append(key_hash)

        # All keys should be unique
        assert len(set(keys)) == 10
        assert len(set(hashes)) == 10

    @pytest.mark.security
    def test_generate_api_key_entropy(self):
        """Test that generated keys have sufficient entropy"""
        full_key, _, _ = APIKeyHandler.generate_api_key()

        # Remove prefix for entropy check
        key_suffix = full_key[len(settings.API_KEY_PREFIX):]

        # Should be 64 hex characters (32 bytes = 256 bits)
        assert len(key_suffix) == 64
        assert all(c in "0123456789abcdef" for c in key_suffix)

    @pytest.mark.security
    def test_api_key_prefix_consistent(self):
        """Test that API key prefix is consistent"""
        for _ in range(5):
            full_key, _, key_prefix = APIKeyHandler.generate_api_key()
            assert full_key.startswith(settings.API_KEY_PREFIX)
            assert key_prefix.startswith(settings.API_KEY_PREFIX)


@pytest.mark.integration
class TestAPIKeyDatabaseOperations:
    """Test API key database operations"""

    async def test_create_api_key(self, test_tenant, test_user):
        """Test creating an API key in database"""
        api_key_id, full_key = await APIKeyHandler.create_api_key(
            name="Test Key",
            tenant_id=test_tenant["id"],
            user_id=test_user["id"],
            scopes=["agents:read"],
            expires_in_days=30
        )

        assert api_key_id is not None
        assert isinstance(full_key, str)
        assert full_key.startswith(settings.API_KEY_PREFIX)

    async def test_create_api_key_without_expiry(self, test_tenant, test_user):
        """Test creating an API key without expiration"""
        api_key_id, full_key = await APIKeyHandler.create_api_key(
            name="Never Expires",
            tenant_id=test_tenant["id"],
            user_id=test_user["id"],
            scopes=["agents:read"],
            expires_in_days=None
        )

        assert api_key_id is not None
        assert full_key is not None

    async def test_create_api_key_without_user(self, test_tenant):
        """Test creating an API key without associated user (service key)"""
        api_key_id, full_key = await APIKeyHandler.create_api_key(
            name="Service Key",
            tenant_id=test_tenant["id"],
            user_id=None,
            scopes=["agents:execute", "workflows:create"],
            expires_in_days=None
        )

        assert api_key_id is not None
        assert full_key is not None

    async def test_validate_api_key_valid(self, test_api_key):
        """Test validating a valid API key"""
        result = await APIKeyHandler.validate_api_key(test_api_key["key"])

        assert result is not None
        assert result["id"] == str(test_api_key["id"])
        assert result["tenant_id"] == str(test_api_key["tenant_id"])
        assert result["scopes"] == ["agents:read", "workflows:create"]

    async def test_validate_api_key_invalid(self):
        """Test validating an invalid API key"""
        invalid_key = "sk_test_" + "0" * 64

        result = await APIKeyHandler.validate_api_key(invalid_key)

        assert result is None

    async def test_validate_api_key_wrong_format(self):
        """Test validating a malformed API key"""
        result = await APIKeyHandler.validate_api_key("not-a-valid-key")

        assert result is None

    async def test_validate_api_key_updates_last_used(self, test_api_key):
        """Test that validating updates last_used_at"""
        from app.database import db

        # Get initial last_used_at
        before = await db.fetchval(
            "SELECT last_used_at FROM api_keys WHERE id = $1",
            test_api_key["id"]
        )

        # Validate key
        await APIKeyHandler.validate_api_key(test_api_key["key"])

        # Check last_used_at was updated
        after = await db.fetchval(
            "SELECT last_used_at FROM api_keys WHERE id = $1",
            test_api_key["id"]
        )

        assert after is not None
        assert after > before if before else True

    async def test_revoke_api_key(self, test_api_key):
        """Test revoking an API key"""
        # Revoke key
        await APIKeyHandler.revoke_api_key(test_api_key["id"])

        # Try to validate revoked key
        result = await APIKeyHandler.validate_api_key(test_api_key["key"])

        assert result is None

    async def test_list_api_keys(self, test_tenant, test_user):
        """Test listing API keys for a tenant"""
        # Create multiple keys
        await APIKeyHandler.create_api_key(
            name="Key 1",
            tenant_id=test_tenant["id"],
            user_id=test_user["id"],
            scopes=["agents:read"],
            expires_in_days=30
        )

        await APIKeyHandler.create_api_key(
            name="Key 2",
            tenant_id=test_tenant["id"],
            user_id=test_user["id"],
            scopes=["workflows:create"],
            expires_in_days=None
        )

        # List keys
        keys = await APIKeyHandler.list_api_keys(test_tenant["id"])

        assert len(keys) == 2
        assert keys[0]["name"] in ["Key 1", "Key 2"]
        assert keys[1]["name"] in ["Key 1", "Key 2"]

    async def test_list_api_keys_empty(self, test_tenant):
        """Test listing API keys when tenant has none"""
        keys = await APIKeyHandler.list_api_keys(test_tenant["id"])

        assert len(keys) == 0

    async def test_list_api_keys_includes_revoked(self, test_tenant, test_user):
        """Test that list_api_keys includes revoked keys"""
        # Create and revoke a key
        api_key_id, _ = await APIKeyHandler.create_api_key(
            name="To Be Revoked",
            tenant_id=test_tenant["id"],
            user_id=test_user["id"],
            scopes=[],
            expires_in_days=None
        )

        await APIKeyHandler.revoke_api_key(api_key_id)

        # List should include revoked key
        keys = await APIKeyHandler.list_api_keys(test_tenant["id"])

        assert len(keys) == 1
        assert keys[0]["is_active"] is False

    async def test_validate_expired_api_key(self, test_tenant, test_user):
        """Test that expired API keys are rejected"""
        from app.database import db
        from datetime import datetime, timedelta

        # Create key
        api_key_id, full_key = await APIKeyHandler.create_api_key(
            name="Expired Key",
            tenant_id=test_tenant["id"],
            user_id=test_user["id"],
            scopes=["agents:read"],
            expires_in_days=1
        )

        # Manually set expiration to the past
        await db.execute(
            "UPDATE api_keys SET expires_at = $1 WHERE id = $2",
            datetime.utcnow() - timedelta(days=1),
            api_key_id
        )

        # Try to validate
        result = await APIKeyHandler.validate_api_key(full_key)

        assert result is None

    async def test_validate_api_key_inactive_tenant(self, test_tenant, test_user):
        """Test that keys from inactive tenants are rejected"""
        from app.database import db

        # Create key
        api_key_id, full_key = await APIKeyHandler.create_api_key(
            name="Tenant Inactive",
            tenant_id=test_tenant["id"],
            user_id=test_user["id"],
            scopes=["agents:read"],
            expires_in_days=None
        )

        # Deactivate tenant
        await db.execute(
            "UPDATE tenants SET is_active = false WHERE id = $1",
            test_tenant["id"]
        )

        # Try to validate
        result = await APIKeyHandler.validate_api_key(full_key)

        assert result is None
