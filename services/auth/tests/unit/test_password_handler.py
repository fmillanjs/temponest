"""
Unit tests for PasswordHandler.

Tests password hashing and verification using bcrypt.
"""

import pytest
from app.handlers.password import PasswordHandler


@pytest.mark.unit
class TestPasswordHandler:
    """Test password hashing and verification"""

    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string"""
        password = "TestPassword123!"
        hashed = PasswordHandler.hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_different_each_time(self):
        """Test that hash_password generates different hashes (salt works)"""
        password = "TestPassword123!"
        hash1 = PasswordHandler.hash_password(password)
        hash2 = PasswordHandler.hash_password(password)

        # Hashes should be different due to different salts
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test that verify_password accepts correct password"""
        password = "TestPassword123!"
        hashed = PasswordHandler.hash_password(password)

        assert PasswordHandler.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test that verify_password rejects incorrect password"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = PasswordHandler.hash_password(password)

        assert PasswordHandler.verify_password(wrong_password, hashed) is False

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case sensitive"""
        password = "TestPassword123!"
        hashed = PasswordHandler.hash_password(password)

        assert PasswordHandler.verify_password("testpassword123!", hashed) is False
        assert PasswordHandler.verify_password("TESTPASSWORD123!", hashed) is False

    def test_verify_password_empty_password(self):
        """Test that empty password is rejected"""
        hashed = PasswordHandler.hash_password("TestPassword123!")

        assert PasswordHandler.verify_password("", hashed) is False

    def test_verify_password_with_special_characters(self):
        """Test passwords with special characters"""
        password = "T3st!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        hashed = PasswordHandler.hash_password(password)

        assert PasswordHandler.verify_password(password, hashed) is True

    def test_verify_password_with_unicode(self):
        """Test passwords with unicode characters"""
        password = "Test密码🔐Пароль"
        hashed = PasswordHandler.hash_password(password)

        assert PasswordHandler.verify_password(password, hashed) is True

    def test_verify_password_long_password(self):
        """Test very long passwords"""
        password = "A" * 1000  # 1000 character password
        hashed = PasswordHandler.hash_password(password)

        assert PasswordHandler.verify_password(password, hashed) is True

    def test_verify_password_handles_invalid_hash(self):
        """Test that verify_password handles invalid hash gracefully"""
        password = "TestPassword123!"
        invalid_hash = "not-a-valid-bcrypt-hash"

        # Should return False, not raise exception
        assert PasswordHandler.verify_password(password, invalid_hash) is False

    def test_hash_password_consistency(self):
        """Test that same password verifies against old hash"""
        password = "TestPassword123!"
        hashed = PasswordHandler.hash_password(password)

        # Simulate password verification after some time
        # Should still work
        assert PasswordHandler.verify_password(password, hashed) is True

    def test_needs_rehash_returns_false(self):
        """Test that needs_rehash returns False (not implemented yet)"""
        hashed = PasswordHandler.hash_password("TestPassword123!")

        assert PasswordHandler.needs_rehash(hashed) is False

    @pytest.mark.security
    def test_hash_password_minimum_length(self):
        """Test that short passwords can still be hashed (validation should be elsewhere)"""
        # Note: Password length validation should be in Pydantic models, not here
        short_password = "12345"
        hashed = PasswordHandler.hash_password(short_password)

        assert isinstance(hashed, str)
        assert PasswordHandler.verify_password(short_password, hashed) is True

    @pytest.mark.security
    def test_timing_attack_resistance(self):
        """Test that incorrect passwords don't leak timing information"""
        import time

        password = "TestPassword123!"
        hashed = PasswordHandler.hash_password(password)

        # Verify correct password
        start = time.time()
        result1 = PasswordHandler.verify_password(password, hashed)
        time1 = time.time() - start

        # Verify wrong password
        start = time.time()
        result2 = PasswordHandler.verify_password("WrongPassword456!", hashed)
        time2 = time.time() - start

        assert result1 is True
        assert result2 is False

        # Times should be similar (within an order of magnitude)
        # bcrypt is designed to have constant time comparison
        assert 0.1 < (time1 / time2) < 10  # Allow 10x variance
