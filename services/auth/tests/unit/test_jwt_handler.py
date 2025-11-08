"""
Unit tests for JWTHandler.

Tests JWT token creation and validation.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from jose import jwt
from app.handlers.jwt_handler import JWTHandler
from app.settings import settings


@pytest.mark.unit
class TestJWTHandler:
    """Test JWT token operations"""

    def test_create_access_token_returns_string(self):
        """Test that create_access_token returns a string"""
        user_id = uuid4()
        tenant_id = uuid4()

        token = JWTHandler.create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            email="test@example.com",
            roles=["viewer"],
            permissions=["agents:read"],
            is_superuser=False
        )

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_contains_correct_claims(self):
        """Test that access token contains all required claims"""
        user_id = uuid4()
        tenant_id = uuid4()
        email = "test@example.com"
        roles = ["admin", "developer"]
        permissions = ["agents:read", "workflows:create"]

        token = JWTHandler.create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            email=email,
            roles=roles,
            permissions=permissions,
            is_superuser=True
        )

        # Decode without verification for inspection
        payload = JWTHandler.decode_token_unsafe(token)

        assert payload["sub"] == str(user_id)
        assert payload["tenant_id"] == str(tenant_id)
        assert payload["email"] == email
        assert payload["roles"] == roles
        assert payload["permissions"] == permissions
        assert payload["is_superuser"] is True
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_refresh_token_returns_string(self):
        """Test that create_refresh_token returns a string"""
        user_id = uuid4()
        tenant_id = uuid4()

        token = JWTHandler.create_refresh_token(
            user_id=user_id,
            tenant_id=tenant_id
        )

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_contains_correct_claims(self):
        """Test that refresh token contains required claims"""
        user_id = uuid4()
        tenant_id = uuid4()

        token = JWTHandler.create_refresh_token(
            user_id=user_id,
            tenant_id=tenant_id
        )

        payload = JWTHandler.decode_token_unsafe(token)

        assert payload["sub"] == str(user_id)
        assert payload["tenant_id"] == str(tenant_id)
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload
        # Refresh tokens should NOT contain sensitive info
        assert "email" not in payload
        assert "roles" not in payload
        assert "permissions" not in payload

    def test_verify_token_valid_access_token(self):
        """Test that verify_token accepts valid access token"""
        user_id = uuid4()
        tenant_id = uuid4()

        token = JWTHandler.create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            email="test@example.com",
            roles=["viewer"],
            permissions=[],
            is_superuser=False
        )

        payload = JWTHandler.verify_token(token, expected_type="access")

        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"

    def test_verify_token_valid_refresh_token(self):
        """Test that verify_token accepts valid refresh token"""
        user_id = uuid4()
        tenant_id = uuid4()

        token = JWTHandler.create_refresh_token(
            user_id=user_id,
            tenant_id=tenant_id
        )

        payload = JWTHandler.verify_token(token, expected_type="refresh")

        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"

    def test_verify_token_wrong_type(self):
        """Test that verify_token rejects token with wrong type"""
        user_id = uuid4()
        tenant_id = uuid4()

        # Create access token
        token = JWTHandler.create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            email="test@example.com",
            roles=["viewer"],
            permissions=[],
            is_superuser=False
        )

        # Try to verify as refresh token
        payload = JWTHandler.verify_token(token, expected_type="refresh")

        assert payload is None

    @pytest.mark.security
    def test_verify_token_expired(self):
        """Test that verify_token rejects expired token"""
        user_id = uuid4()
        tenant_id = uuid4()

        # Create token with immediate expiry
        payload_data = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "email": "test@example.com",
            "roles": ["viewer"],
            "permissions": [],
            "is_superuser": False,
            "exp": datetime.utcnow() - timedelta(seconds=1),  # Already expired
            "iat": datetime.utcnow() - timedelta(seconds=2),
            "type": "access"
        }

        expired_token = jwt.encode(
            payload_data,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

        payload = JWTHandler.verify_token(expired_token, expected_type="access")

        assert payload is None

    @pytest.mark.security
    def test_verify_token_invalid_signature(self):
        """Test that verify_token rejects token with invalid signature"""
        user_id = uuid4()
        tenant_id = uuid4()

        # Create token with wrong key
        payload_data = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "type": "access",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow()
        }

        invalid_token = jwt.encode(
            payload_data,
            "wrong-secret-key",
            algorithm=settings.JWT_ALGORITHM
        )

        payload = JWTHandler.verify_token(invalid_token, expected_type="access")

        assert payload is None

    @pytest.mark.security
    def test_verify_token_malformed(self):
        """Test that verify_token rejects malformed token"""
        malformed_token = "not.a.valid.jwt.token"

        payload = JWTHandler.verify_token(malformed_token, expected_type="access")

        assert payload is None

    def test_verify_token_empty_string(self):
        """Test that verify_token rejects empty string"""
        payload = JWTHandler.verify_token("", expected_type="access")

        assert payload is None

    def test_decode_token_unsafe_valid_token(self):
        """Test that decode_token_unsafe decodes without verification"""
        user_id = uuid4()
        tenant_id = uuid4()

        token = JWTHandler.create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            email="test@example.com",
            roles=["viewer"],
            permissions=[],
            is_superuser=False
        )

        payload = JWTHandler.decode_token_unsafe(token)

        assert payload is not None
        assert payload["sub"] == str(user_id)

    def test_decode_token_unsafe_expired_token(self):
        """Test that decode_token_unsafe decodes even expired tokens"""
        payload_data = {
            "sub": str(uuid4()),
            "tenant_id": str(uuid4()),
            "type": "access",
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired
            "iat": datetime.utcnow() - timedelta(hours=2)
        }

        expired_token = jwt.encode(
            payload_data,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

        payload = JWTHandler.decode_token_unsafe(expired_token)

        # Should decode despite expiration
        assert payload is not None
        assert payload["sub"] == payload_data["sub"]

    def test_decode_token_unsafe_invalid_signature(self):
        """Test that decode_token_unsafe decodes even with wrong signature"""
        payload_data = {
            "sub": str(uuid4()),
            "type": "access"
        }

        token = jwt.encode(
            payload_data,
            "wrong-secret-key",
            algorithm=settings.JWT_ALGORITHM
        )

        payload = JWTHandler.decode_token_unsafe(token)

        # Should decode despite wrong signature
        assert payload is not None
        assert payload["sub"] == payload_data["sub"]

    def test_decode_token_unsafe_malformed(self):
        """Test that decode_token_unsafe handles malformed tokens"""
        payload = JWTHandler.decode_token_unsafe("not.a.valid.jwt")

        assert payload is None

    def test_access_token_expiration_time(self):
        """Test that access token has correct expiration time"""
        user_id = uuid4()
        tenant_id = uuid4()

        before = datetime.utcnow()
        token = JWTHandler.create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            email="test@example.com",
            roles=["viewer"],
            permissions=[],
            is_superuser=False
        )
        after = datetime.utcnow()

        payload = JWTHandler.decode_token_unsafe(token)
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        expected_exp = before + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

        # Should be within 5 seconds of expected (allow for test execution time)
        assert abs((exp_time - expected_exp).total_seconds()) < 5

    def test_refresh_token_expiration_time(self):
        """Test that refresh token has correct expiration time"""
        user_id = uuid4()
        tenant_id = uuid4()

        before = datetime.utcnow()
        token = JWTHandler.create_refresh_token(
            user_id=user_id,
            tenant_id=tenant_id
        )
        after = datetime.utcnow()

        payload = JWTHandler.decode_token_unsafe(token)
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        expected_exp = before + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

        # Should be within 5 seconds of expected (allow for test execution time)
        assert abs((exp_time - expected_exp).total_seconds()) < 5

    def test_tokens_are_unique(self):
        """Test that multiple tokens for same user are different"""
        import time
        user_id = uuid4()
        tenant_id = uuid4()

        token1 = JWTHandler.create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            email="test@example.com",
            roles=["viewer"],
            permissions=[],
            is_superuser=False
        )

        # Wait 1 second to ensure different iat timestamp
        time.sleep(1)

        token2 = JWTHandler.create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            email="test@example.com",
            roles=["viewer"],
            permissions=[],
            is_superuser=False
        )

        # Tokens should be different due to different iat timestamps
        assert token1 != token2
