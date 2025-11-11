# CORS Security Configuration

## Current Configuration

**File**: `app/settings.py`
```python
CORS_ORIGINS: list = ["*"]  # Configure in production
```

**Status**: ⚠️ **INSECURE FOR PRODUCTION** - Allows all origins

---

## Security Risks

### 1. Wildcard Origin with Credentials
**Risk Level**: 🔴 **HIGH**

Current setup allows:
- `allow_origins=["*"]`
- `allow_credentials=True`

**Problem**: This combination is **extremely dangerous** as it allows any website to:
- Send authenticated requests to your API
- Access sensitive user data
- Perform actions on behalf of authenticated users

**OWASP Category**: A01:2021 - Broken Access Control

---

## Recommended Configuration

### Development Environment
```python
CORS_ORIGINS: list = [
    "http://localhost:3000",      # Next.js dev server
    "http://localhost:8080",      # Web UI
    "http://localhost:8081",      # Open WebUI
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
]
```

### Production Environment
```python
CORS_ORIGINS: list = [
    "https://app.yourdomain.com",       # Production console
    "https://console.yourdomain.com",   # Alternative console domain
    "https://yourdomain.com",           # Main website
]
```

### Configuration via Environment Variable
```bash
# .env file
CORS_ORIGINS=https://app.yourdomain.com,https://console.yourdomain.com
```

**Updated settings.py**:
```python
import os

class Settings(BaseSettings):
    # CORS - Parse comma-separated list from environment
    CORS_ORIGINS: list = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:8080"
    ).split(",")
```

---

## Implementation Steps

### 1. Update settings.py (IMMEDIATE)
```python
class Settings(BaseSettings):
    """Authentication service settings"""

    # ... other settings ...

    # CORS Configuration
    # ⚠️ SECURITY: Do NOT use ["*"] in production!
    # Set CORS_ORIGINS environment variable with comma-separated list of allowed origins
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"

    @property
    def cors_origins_list(self) -> list:
        """Parse CORS origins from comma-separated string"""
        if self.CORS_ORIGINS == "*":
            # Log warning in production
            import logging
            logging.warning("⚠️ CORS configured with wildcard (*) - INSECURE FOR PRODUCTION!")
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # ... rest of settings ...
```

### 2. Update main.py
```python
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # Use parsed list
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],  # Explicit methods
    allow_headers=["Authorization", "Content-Type"],  # Explicit headers
    max_age=600,  # Cache preflight requests for 10 minutes
)
```

### 3. Environment Variables

**Development (.env.development)**:
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost:8081
```

**Production (.env.production)**:
```bash
CORS_ORIGINS=https://app.yourdomain.com,https://console.yourdomain.com
```

**Docker Compose**:
```yaml
services:
  auth:
    environment:
      - CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

---

## Testing CORS Configuration

### 1. Manual Testing
```bash
# Test from allowed origin
curl -X OPTIONS http://localhost:9002/auth/login \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -v

# Should return:
# Access-Control-Allow-Origin: http://localhost:3000
# Access-Control-Allow-Credentials: true
```

```bash
# Test from disallowed origin
curl -X OPTIONS http://localhost:9002/auth/login \
  -H "Origin: http://evil.com" \
  -H "Access-Control-Request-Method: POST" \
  -v

# Should NOT return Access-Control-Allow-Origin header
```

### 2. Automated Testing
See `tests/security/test_csrf.py`:
- `test_cors_allows_credentials_with_wildcard()`
- `test_cors_origin_reflection()`
- `test_cors_with_sensitive_operations()`

---

## Best Practices

### 1. ✅ DO
- ✅ Explicitly list all allowed origins
- ✅ Use HTTPS in production origins
- ✅ Validate origins against whitelist
- ✅ Log CORS violations for monitoring
- ✅ Use environment-specific configuration
- ✅ Regularly review and update allowed origins
- ✅ Document why each origin is allowed

### 2. ❌ DON'T
- ❌ Use wildcard (`*`) with credentials in production
- ❌ Reflect the `Origin` header without validation
- ❌ Allow overly broad origin patterns (e.g., `*.com`)
- ❌ Allow `null` origin (used in sandboxed iframes)
- ❌ Forget to test CORS in staging environment
- ❌ Allow file:// or localhost origins in production

---

## Additional Security Headers

### Content Security Policy (CSP)
While CORS protects the API, CSP protects the frontend:

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Add to main.py
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "yourdomain.com", "*.yourdomain.com"]
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

---

## Monitoring and Alerting

### Log CORS Violations
```python
import logging

@app.middleware("http")
async def log_cors_violations(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin and origin not in settings.cors_origins_list:
        logging.warning(f"⚠️ CORS violation attempt from: {origin}")
        # Optional: Send alert to security monitoring system
    response = await call_next(request)
    return response
```

### Metrics
Track CORS-related metrics:
- Number of CORS preflight requests
- Number of CORS violations
- Origins attempting access

---

## Migration Plan

### Phase 1: Audit (Week 1)
1. ✅ Document current CORS configuration
2. ✅ Identify all legitimate frontend applications
3. ✅ List all required origins

### Phase 2: Update (Week 2)
1. ⏳ Update settings.py with environment-based configuration
2. ⏳ Add CORS origin validation
3. ⏳ Add security headers
4. ⏳ Add logging for CORS violations

### Phase 3: Test (Week 3)
1. ⏳ Test with all legitimate frontends
2. ⏳ Verify CORS blocks unauthorized origins
3. ⏳ Run security test suite
4. ⏳ Penetration testing

### Phase 4: Deploy (Week 4)
1. ⏳ Deploy to staging with restrictive CORS
2. ⏳ Monitor for issues
3. ⏳ Deploy to production
4. ⏳ Continuous monitoring

---

## References

- [OWASP CORS Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [MDN Web Docs - CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/)
- [OWASP Top 10 2021 - A01:2021 Broken Access Control](https://owasp.org/Top10/A01_2021-Broken_Access_Control/)

---

**Last Updated**: 2025-11-11
**Status**: ⚠️ **ACTION REQUIRED** - Update CORS configuration before production deployment
**Priority**: 🔴 **HIGH** - Security vulnerability
