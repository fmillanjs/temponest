"""
Password hashing and verification using bcrypt.
"""

import bcrypt


class PasswordHandler:
    """Handles password hashing and verification"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a plain text password"""
        # Encode password to bytes
        password_bytes = password.encode('utf-8')

        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)

        # Return as string
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            # Encode both password and hash to bytes
            password_bytes = plain_password.encode('utf-8')
            hash_bytes = hashed_password.encode('utf-8')

            # Verify
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception as e:
            print(f"Password verification error: {e}")
            return False

    @staticmethod
    def needs_rehash(hashed_password: str) -> bool:
        """Check if password hash needs to be updated (always False for now)"""
        # bcrypt hashes don't need rehashing in our current setup
        return False
